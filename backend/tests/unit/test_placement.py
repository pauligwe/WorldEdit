from core.world_spec import Blueprint, Floor, Room, Door, FurnitureItem
from core.placement import validate_and_fix_placements


def _simple_bp() -> Blueprint:
    return Blueprint(
        gridSize=0.5,
        floors=[Floor(level=0, ceilingHeight=3.0, rooms=[
            Room(id="r1", type="living_room", x=0, y=0, width=6, depth=6,
                 doors=[Door(wall="south", offset=3, width=1.0)], windows=[]),
        ], stairs=[])],
    )


def test_valid_furniture_passes():
    bp = _simple_bp()
    items = [FurnitureItem(id="c1", roomId="r1", type="couch", position=[3, 0, -3], rotation=0, size=[2, 0.9, 1])]
    out = validate_and_fix_placements(items, bp)
    assert len(out) == 1


def test_overlapping_furniture_removes_smaller():
    bp = _simple_bp()
    items = [
        FurnitureItem(id="big", roomId="r1", type="couch", position=[3, 0, -3], rotation=0, size=[3, 0.9, 2]),
        FurnitureItem(id="small", roomId="r1", type="chair", position=[3, 0, -3], rotation=0, size=[1, 0.9, 1]),
    ]
    out = validate_and_fix_placements(items, bp)
    assert len(out) == 1
    assert out[0].id == "big"


def test_furniture_outside_room_removed():
    bp = _simple_bp()
    items = [FurnitureItem(id="oob", roomId="r1", type="couch", position=[20, 0, -20], rotation=0, size=[2, 0.9, 1])]
    out = validate_and_fix_placements(items, bp)
    assert len(out) == 0


def test_furniture_in_doorway_removed():
    bp = _simple_bp()
    # door is at south wall offset 3 width 1 -> covers blueprint x in [2.5, 3.5] at y=0..0.5
    items = [FurnitureItem(id="door_block", roomId="r1", type="rug", position=[3, 0, -0.3], rotation=0, size=[1.5, 0.05, 1])]
    out = validate_and_fix_placements(items, bp)
    assert len(out) == 0
