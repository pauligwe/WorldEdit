import pytest
from core.floor_packer import pack_floor_plan
from core.room_library import ROOM_LIBRARY


def test_pack_simple_two_rooms():
    floor = pack_floor_plan(
        ["office_private_small", "office_private_small"],
        footprint=(30.0, 25.0),
        level=1,
    )
    assert floor.level == 1
    assert len(floor.rooms) == 2
    # second room should not overlap first
    r1, r2 = floor.rooms
    assert r2.x >= r1.x + r1.width or r2.y >= r1.y + r1.depth


def test_level0_auto_includes_lobby():
    floor = pack_floor_plan(
        ["office_private_small"],  # caller forgot lobby
        footprint=(30.0, 25.0),
        level=0,
    )
    types = [r.type for r in floor.rooms]
    assert "lobby" in types


def test_overflowing_template_dropped():
    huge = ["lobby_modern"] * 50
    floor = pack_floor_plan(huge, footprint=(30.0, 25.0), level=1)
    # Plenty get dropped because the lobby is 12x6 and footprint is 30x25
    assert len(floor.rooms) < 50


def test_unknown_template_skipped():
    floor = pack_floor_plan(
        ["does_not_exist", "office_private_small"],
        footprint=(30.0, 25.0),
        level=1,
    )
    assert len(floor.rooms) == 1
    assert floor.rooms[0].type == "office"


def test_rooms_have_doors():
    floor = pack_floor_plan(
        ["conference_small"], footprint=(30.0, 25.0), level=1,
    )
    assert len(floor.rooms[0].doors) >= 1
