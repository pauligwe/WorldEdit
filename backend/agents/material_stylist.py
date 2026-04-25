import json
from core.world_spec import WorldSpec, MaterialsByRoom
from core.gemini_client import structured
from core.prompts.material_stylist import SYSTEM, USER_TMPL


def run(spec: WorldSpec) -> WorldSpec:
    assert spec.intent and spec.blueprint
    rooms = [{"id": r.id, "type": r.type} for fl in spec.blueprint.floors for r in fl.rooms]
    user = USER_TMPL.format(
        style=spec.intent.style,
        vibe=", ".join(spec.intent.vibe),
        rooms=json.dumps(rooms, indent=2),
    )
    spec.materials = structured(user, MaterialsByRoom, system=SYSTEM)
    return spec
