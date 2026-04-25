import json
from core.world_spec import WorldSpec, MaterialsByRoom, RoomMaterial
from core.gemini_client import structured, GeminiError
from core.prompts.material_stylist import SYSTEM, USER_TMPL


_DEFAULTS_BY_TYPE: dict[str, RoomMaterial] = {
    "lobby": RoomMaterial(wall="#e7e1d5", floor="marble_tile", ceiling="#ffffff"),
    "office": RoomMaterial(wall="#f4f0e8", floor="carpet_grey", ceiling="#ffffff"),
    "office_open": RoomMaterial(wall="#f4f0e8", floor="carpet_grey", ceiling="#ffffff"),
    "conference": RoomMaterial(wall="#e8eef5", floor="carpet_beige", ceiling="#ffffff"),
    "breakroom": RoomMaterial(wall="#f0e8d8", floor="oak_planks", ceiling="#ffffff"),
    "corridor": RoomMaterial(wall="#e7e1d5", floor="tile_white", ceiling="#ffffff"),
    "bathroom": RoomMaterial(wall="#f8f8f5", floor="tile_white", ceiling="#fafafa"),
    "kitchen": RoomMaterial(wall="#f5f5dc", floor="oak_planks", ceiling="#fafafa"),
    "bedroom": RoomMaterial(wall="#f5e8e0", floor="carpet_beige", ceiling="#ffffff"),
    "living_room": RoomMaterial(wall="#f5f5dc", floor="oak_planks", ceiling="#fafafa"),
    "dining_room": RoomMaterial(wall="#e0ffff", floor="oak_planks", ceiling="#fafafa"),
    "hallway": RoomMaterial(wall="#e7e1d5", floor="oak_planks", ceiling="#ffffff"),
    "foyer": RoomMaterial(wall="#f8f8f8", floor="oak_planks", ceiling="#fafafa"),
    "studio": RoomMaterial(wall="#f0eee5", floor="oak_planks", ceiling="#ffffff"),
    "open_living": RoomMaterial(wall="#f0eee5", floor="oak_planks", ceiling="#ffffff"),
    "stairwell": RoomMaterial(wall="#e0d8c8", floor="concrete", ceiling="#ffffff"),
    "server_room": RoomMaterial(wall="#dcdcdc", floor="concrete", ceiling="#cccccc"),
}

_FALLBACK = RoomMaterial(wall="#e7e1d5", floor="oak_planks", ceiling="#ffffff")


def _default_materials(spec: WorldSpec) -> MaterialsByRoom:
    out: dict[str, RoomMaterial] = {}
    for fl in spec.blueprint.floors:
        for r in fl.rooms:
            out[r.id] = _DEFAULTS_BY_TYPE.get(r.type, _FALLBACK)
    return MaterialsByRoom(byRoom=out)


def run(spec: WorldSpec) -> WorldSpec:
    assert spec.intent and spec.blueprint
    rooms = [{"id": r.id, "type": r.type} for fl in spec.blueprint.floors for r in fl.rooms]
    user = USER_TMPL.format(
        style=spec.intent.style,
        vibe=", ".join(spec.intent.vibe),
        rooms=json.dumps(rooms, indent=2),
    )
    try:
        spec.materials = structured(user, MaterialsByRoom, system=SYSTEM)
    except GeminiError as e:
        print(f"[material_stylist] Gemini failed, using type-based defaults: {e}")
        spec.materials = _default_materials(spec)
    return spec
