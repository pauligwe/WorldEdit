import json
from pathlib import Path
from core.world_spec import Blueprint, Intent
from core.geometry import build_geometry
from core.site import derive_site_from_intent

EXAMPLES = Path(__file__).parent.parent.parent / "core" / "prompts" / "examples"


def _bp(name: str) -> Blueprint:
    return Blueprint(**json.loads((EXAMPLES / name).read_text()))


def test_geometry_has_floor_per_room():
    bp = _bp("tiny_apartment.json")
    geo = build_geometry(bp, derive_site_from_intent(Intent(buildingType="office", style="modern", floors=1, vibe=[], sizeHint="large")))
    floor_prims = [p for p in geo.primitives if p.type == "floor"]
    room_count = sum(len(f.rooms) for f in bp.floors)
    assert len(floor_prims) == room_count


def test_geometry_has_4_walls_per_room():
    bp = _bp("tiny_apartment.json")
    geo = build_geometry(bp, derive_site_from_intent(Intent(buildingType="office", style="modern", floors=1, vibe=[], sizeHint="large")))
    by_room: dict[str, int] = {}
    for p in geo.primitives:
        if p.type == "wall":
            by_room[p.roomId] = by_room.get(p.roomId, 0) + 1
    for fl in bp.floors:
        for r in fl.rooms:
            assert by_room.get(r.id, 0) == 4, f"room {r.id} expected 4 walls, got {by_room.get(r.id, 0)}"


def test_doors_appear_as_holes():
    bp = _bp("tiny_apartment.json")
    geo = build_geometry(bp, derive_site_from_intent(Intent(buildingType="office", style="modern", floors=1, vibe=[], sizeHint="large")))
    walls_with_holes = [p for p in geo.primitives if p.type == "wall" and p.holes]
    assert walls_with_holes, "expected some walls to have door holes"


def test_two_story_has_stair_primitive():
    bp = _bp("two_story_house.json")
    geo = build_geometry(bp, derive_site_from_intent(Intent(buildingType="office", style="modern", floors=1, vibe=[], sizeHint="large")))
    stair_prims = [p for p in geo.primitives if p.type == "stair"]
    assert len(stair_prims) >= 1
