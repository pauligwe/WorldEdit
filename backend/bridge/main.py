import asyncio
import json
import os
import re
import uuid
from pathlib import Path
from urllib.parse import urlparse
import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from dotenv import load_dotenv

from core.world_spec import WorldSpec
from core.status_bus import StatusBus, AgentStatus
from agents.orchestrator import run_pipeline
from agents.chat_edit_coordinator import run as chat_edit_run

load_dotenv()

WORLDS_DIR = Path(__file__).parent.parent / "worlds"
WORLDS_DIR.mkdir(exist_ok=True)

app = FastAPI(title="World Build Bridge")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

bus = StatusBus()
worlds: dict[str, WorldSpec] = {}
running: set[str] = set()


@app.on_event("startup")
def _start_uagents():
    if os.environ.get("WORLD_BUILD_DISABLE_UAGENTS") == "1":
        return
    from agents.uagent_runner import start_all_in_background
    start_all_in_background()


class GenerateReq(BaseModel):
    prompt: str


class EditReq(BaseModel):
    worldId: str
    edit: str


class SelectProductReq(BaseModel):
    worldId: str
    furnitureId: str
    productId: str


def _save_world(spec: WorldSpec) -> None:
    (WORLDS_DIR / f"{spec.worldId}.json").write_text(spec.model_dump_json(indent=2))


async def _drive(spec: WorldSpec) -> None:
    running.add(spec.worldId)
    try:
        result = await run_pipeline(spec, bus)
        worlds[spec.worldId] = result
        _save_world(result)
        await bus.publish(spec.worldId, AgentStatus(agent="__final__", state="done", data=result.model_dump()))
    except Exception as e:
        await bus.publish(spec.worldId, AgentStatus(agent="__pipeline__", state="error", message=str(e)))
    finally:
        running.discard(spec.worldId)


@app.post("/api/generate")
async def generate(req: GenerateReq) -> dict:
    world_id = uuid.uuid4().hex[:12]
    spec = WorldSpec(worldId=world_id, prompt=req.prompt)
    worlds[world_id] = spec
    asyncio.create_task(_drive(spec))
    return {"worldId": world_id}


@app.post("/api/edit")
async def edit(req: EditReq) -> dict:
    spec = worlds.get(req.worldId)
    if spec is None:
        raise HTTPException(404, "unknown worldId")
    new_spec = chat_edit_run(spec.model_copy(deep=True), req.edit)
    new_id = uuid.uuid4().hex[:12]
    new_spec.worldId = new_id
    worlds[new_id] = new_spec
    asyncio.create_task(_drive(new_spec))
    return {"worldId": new_id}


@app.post("/api/select-product")
async def select_product(req: SelectProductReq) -> dict:
    spec = worlds.get(req.worldId)
    if spec is None:
        raise HTTPException(404, "unknown worldId")
    target = next((f for f in spec.furniture if f.id == req.furnitureId), None)
    if target is None:
        raise HTTPException(404, "unknown furnitureId")
    if req.productId not in spec.products:
        raise HTTPException(404, "unknown productId")
    target.selectedProductId = req.productId
    _save_world(spec)
    return {"ok": True}


_OG_RE = re.compile(rb'<meta\s+[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']', re.IGNORECASE)
_OG_RE_REV = re.compile(rb'<meta\s+[^>]*content=["\']([^"\']+)["\'][^>]*property=["\']og:image["\']', re.IGNORECASE)
_TWITTER_RE = re.compile(rb'<meta\s+[^>]*name=["\']twitter:image["\'][^>]*content=["\']([^"\']+)["\']', re.IGNORECASE)
_image_cache: dict[str, bytes | None] = {}
_image_ct_cache: dict[str, str] = {}


def _browser_headers(referer: str) -> dict[str, str]:
    return {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,image/avif,image/webp,image/*,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": referer,
    }


async def _fetch_og_image(page_url: str, client: httpx.AsyncClient) -> str | None:
    parsed = urlparse(page_url)
    referer = f"{parsed.scheme}://{parsed.hostname}/"
    try:
        r = await client.get(page_url, headers=_browser_headers(referer))
    except Exception:
        return None
    if r.status_code != 200:
        return None
    body = r.content
    m = _OG_RE.search(body) or _OG_RE_REV.search(body) or _TWITTER_RE.search(body)
    if not m:
        return None
    raw = m.group(1).decode("utf-8", errors="ignore").replace("&amp;", "&")
    if raw.startswith("//"):
        raw = parsed.scheme + ":" + raw
    elif raw.startswith("/"):
        raw = f"{parsed.scheme}://{parsed.hostname}{raw}"
    return raw


@app.get("/api/img")
async def proxy_image(url: str = Query(...), product: str | None = Query(None)) -> Response:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise HTTPException(400, "bad url")

    cache_key = product or url
    if cache_key in _image_cache:
        cached = _image_cache[cache_key]
        if cached is None:
            raise HTTPException(404, "no image")
        return Response(content=cached, media_type=_image_ct_cache.get(cache_key, "image/jpeg"),
                        headers={"cache-control": "public, max-age=86400"})

    async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
        async def _try(u: str) -> tuple[bytes, str] | None:
            p = urlparse(u)
            ref = f"{p.scheme}://{p.hostname}/"
            try:
                rr = await client.get(u, headers=_browser_headers(ref))
            except Exception:
                return None
            if rr.status_code != 200: return None
            ct = rr.headers.get("content-type", "")
            if not ct.startswith("image/"): return None
            return rr.content, ct

        result = await _try(url)
        if result is None and product:
            og = await _fetch_og_image(product, client)
            if og:
                result = await _try(og)
        if result is None:
            og = await _fetch_og_image(url, client)
            if og:
                result = await _try(og)

    if result is None:
        _image_cache[cache_key] = None
        raise HTTPException(404, "no image")
    body, ct = result
    _image_cache[cache_key] = body
    _image_ct_cache[cache_key] = ct
    return Response(content=body, media_type=ct, headers={"cache-control": "public, max-age=86400"})


@app.get("/api/world/{world_id}")
async def get_world(world_id: str) -> dict:
    spec = worlds.get(world_id)
    if spec is None:
        path = WORLDS_DIR / f"{world_id}.json"
        if path.exists():
            return json.loads(path.read_text())
        raise HTTPException(404)
    return spec.model_dump()


@app.websocket("/ws/build/{world_id}")
async def ws_build(websocket: WebSocket, world_id: str):
    await websocket.accept()
    q = bus.subscribe(world_id)
    try:
        while True:
            try:
                evt: AgentStatus = await asyncio.wait_for(q.get(), timeout=120)
            except asyncio.TimeoutError:
                await websocket.send_json({"agent": "__heartbeat__", "state": "running"})
                continue
            await websocket.send_json({"agent": evt.agent, "state": evt.state, "message": evt.message, "data": evt.data})
            if evt.agent in ("__final__", "__pipeline__"):
                break
    except WebSocketDisconnect:
        pass
    finally:
        bus.unsubscribe(world_id, q)
