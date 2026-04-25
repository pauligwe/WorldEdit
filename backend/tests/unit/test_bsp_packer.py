import pytest
from core.bsp_packer import bsp_pack_floor


def test_level0_has_lobby_at_south_edge():
    floor = bsp_pack_floor(
        ["office_private_small", "conference_small"],
        footprint=(40.0, 25.0),
        level=0,
    )
    lobby = next((r for r in floor.rooms if r.type == "lobby"), None)
    assert lobby is not None
    assert lobby.y == pytest.approx(0.0)
    assert any(d.wall == "south" for d in lobby.doors)


def test_no_room_outside_footprint():
    floor = bsp_pack_floor(
        ["office_private_small"] * 6,
        footprint=(30.0, 25.0),
        level=1,
    )
    for r in floor.rooms:
        assert r.x >= 0
        assert r.y >= 0
        assert r.x + r.width <= 30.0 + 0.01
        assert r.y + r.depth <= 25.0 + 0.01


def test_no_rooms_overlap():
    floor = bsp_pack_floor(
        ["office_private_small"] * 4 + ["conference_small"],
        footprint=(40.0, 30.0),
        level=2,
    )
    rooms = floor.rooms
    for i, a in enumerate(rooms):
        for b in rooms[i+1:]:
            ax2, ay2 = a.x + a.width, a.y + a.depth
            bx2, by2 = b.x + b.width, b.y + b.depth
            no_overlap = (ax2 <= b.x or bx2 <= a.x or
                         ay2 <= b.y or by2 <= a.y)
            assert no_overlap, f"{a.id} overlaps {b.id}"


def test_stairwell_carved_out():
    floor = bsp_pack_floor(
        ["office_private_small"] * 4,
        footprint=(40.0, 30.0),
        level=0,
        stair_position=(15.0, 10.0, 3.0, 4.0),
    )
    # No room should overlap the stairwell
    for r in floor.rooms:
        ax2, ay2 = r.x + r.width, r.y + r.depth
        sx2, sy2 = 15.0 + 3.0, 10.0 + 4.0
        no_overlap = (ax2 <= 15.0 or sx2 <= r.x or
                     ay2 <= 10.0 or sy2 <= r.y)
        assert no_overlap, f"{r.id} overlaps stairwell"
    assert len(floor.stairs) == 1


def test_deterministic_for_same_level():
    f1 = bsp_pack_floor(["office_private_small"] * 4, footprint=(40, 25), level=2)
    f2 = bsp_pack_floor(["office_private_small"] * 4, footprint=(40, 25), level=2)
    ids1 = sorted(r.id for r in f1.rooms)
    ids2 = sorted(r.id for r in f2.rooms)
    assert ids1 == ids2


def test_unknown_templates_skipped():
    floor = bsp_pack_floor(
        ["nonexistent_thing", "office_private_small"],
        footprint=(40.0, 25.0),
        level=1,
    )
    types = [r.type for r in floor.rooms]
    assert "office" in types
    assert "nonexistent_thing" not in types
