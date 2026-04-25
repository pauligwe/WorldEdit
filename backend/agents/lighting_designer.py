import json
from core.world_spec import WorldSpec, LightingByRoom
from core.gemini_client import structured
from core.prompts.lighting_designer import SYSTEM, USER_TMPL


def _rooms_summary(spec: WorldSpec) -> str:
    items = []
    assert spec.blueprint
    for fl in spec.blueprint.floors:
        for r in fl.rooms:
            items.append({
                "id": r.id, "type": r.type, "x": r.x, "y": r.y,
                "width": r.width, "depth": r.depth, "ceilingHeight": fl.ceilingHeight,
            })
    return json.dumps(items, indent=2)


def run(spec: WorldSpec) -> WorldSpec:
    assert spec.intent and spec.blueprint
    user = USER_TMPL.format(
        style=spec.intent.style,
        vibe=", ".join(spec.intent.vibe),
        rooms=_rooms_summary(spec),
    )
    spec.lighting = structured(user, LightingByRoom, system=SYSTEM)
    return spec
