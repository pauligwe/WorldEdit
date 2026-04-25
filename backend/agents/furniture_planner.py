import json
from pydantic import BaseModel
from core.world_spec import WorldSpec, FurnitureItem
from core.gemini_client import structured
from core.prompts.furniture_planner import SYSTEM, USER_TMPL


class _ItemList(BaseModel):
    items: list[FurnitureItem]


def run(spec: WorldSpec) -> WorldSpec:
    assert spec.intent and spec.blueprint
    all_items: list[FurnitureItem] = []
    for fl in spec.blueprint.floors:
        for r in fl.rooms:
            user = USER_TMPL.format(
                style=spec.intent.style,
                vibe=", ".join(spec.intent.vibe),
                id=r.id, type=r.type, x=r.x, y=r.y, width=r.width, depth=r.depth,
                doors=json.dumps([d.model_dump() for d in r.doors]),
            )
            try:
                items = structured(user, _ItemList, system=SYSTEM).items
            except Exception:
                items = []
            for it in items:
                it.roomId = r.id
            all_items.extend(items)
    spec.furniture = all_items
    return spec
