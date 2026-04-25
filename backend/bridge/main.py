import asyncio
import json
import os
import uuid
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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


def _save_world(spec: WorldSpec) -> None:
    (WORLDS_DIR / f"{spec.worldId}.json").write_text(spec.model_dump_json(indent=2))


def _load_world(world_id: str) -> WorldSpec | None:
    cached = worlds.get(world_id)
    if cached is not None:
        return cached
    path = WORLDS_DIR / f"{world_id}.json"
    if not path.exists():
        return None
    spec = WorldSpec.model_validate_json(path.read_text())
    worlds[world_id] = spec
    return spec


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
    spec = _load_world(req.worldId)
    if spec is None:
        raise HTTPException(404, "unknown worldId")
    new_spec = chat_edit_run(spec.model_copy(deep=True), req.edit)
    new_id = uuid.uuid4().hex[:12]
    new_spec.worldId = new_id
    worlds[new_id] = new_spec
    asyncio.create_task(_drive(new_spec))
    return {"worldId": new_id}


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
