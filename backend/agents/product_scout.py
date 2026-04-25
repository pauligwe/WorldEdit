import json
import re
import uuid
import httpx
from core.world_spec import WorldSpec, Product, FurnitureItem
from core.gemini_client import grounded_search
from core.prompts.product_scout import SYSTEM, USER_TMPL

JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


def _extract_json(s: str) -> dict | None:
    m = JSON_FENCE_RE.search(s)
    candidate = m.group(1) if m else s
    candidate = candidate.strip()
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(candidate[start:end + 1])
            except json.JSONDecodeError:
                return None
    return None


_BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*",
    "Accept-Language": "en-US,en;q=0.9",
}


def _url_alive(url: str, timeout: float = 6.0) -> bool:
    try:
        r = httpx.get(url, follow_redirects=True, timeout=timeout, headers=_BROWSER_HEADERS)
        if r.status_code != 200:
            return False
        body = r.text.lower()
        if "out of stock" in body and "currently unavailable" in body:
            return False
        if "we can't find the page" in body or "page not found" in body or "this item is no longer available" in body:
            return False
        return True
    except Exception:
        return False


def _search_for_type(furniture_type: str, style: str, w: float, h: float, d: float, broad: bool = False) -> list[Product]:
    style_str = "" if broad else style
    user = USER_TMPL.format(n=5, style=style_str, furniture_type=furniture_type, width=w, depth=d, height=h)
    raw = grounded_search(user, system=SYSTEM)
    data = _extract_json(raw)
    if not data:
        return []
    out: list[Product] = []
    for item in data.get("products", []):
        url = item.get("url")
        img = item.get("imageUrl")
        if not url or not img:
            continue
        if not _url_alive(url):
            continue
        out.append(Product(
            name=item.get("name") or "Unnamed",
            price=item.get("price"),
            imageUrl=img,
            vendor=item.get("vendor"),
            url=url,
            fitsTypes=[furniture_type],
        ))
    return out


def run(spec: WorldSpec) -> WorldSpec:
    assert spec.intent
    style = spec.intent.style

    types: dict[str, list[FurnitureItem]] = {}
    for f in spec.furniture:
        types.setdefault(f.type, []).append(f)

    products: dict[str, Product] = {}
    type_to_pids: dict[str, list[str]] = {}

    for t, items in types.items():
        avg_w = sum(i.size[0] for i in items) / len(items)
        avg_h = sum(i.size[1] for i in items) / len(items)
        avg_d = sum(i.size[2] for i in items) / len(items)
        results = _search_for_type(t, style, avg_w, avg_h, avg_d, broad=False)
        if len(results) < 3:
            results.extend(_search_for_type(t, style, avg_w, avg_h, avg_d, broad=True))
        ids: list[str] = []
        for p in results:
            pid = "p_" + uuid.uuid4().hex[:8]
            products[pid] = p
            ids.append(pid)
        type_to_pids[t] = ids

    for f in spec.furniture:
        ids = type_to_pids.get(f.type, [])
        f.alternates = ids
        f.selectedProductId = ids[0] if ids else None

    spec.products = products
    return spec
