from core.world_spec import Room, Door
from core.room_templates import (
    ROOM_FURNITURE, FurnitureTemplate, apply_template
)


def test_every_known_room_type_has_template():
    expected = {"office", "conference_room", "lobby", "breakroom",
                "corridor", "restroom", "stairwell", "reception",
                "bedroom", "kitchen", "living_room", "bathroom", "default"}
    assert expected.issubset(set(ROOM_FURNITURE.keys()))


def test_office_template_produces_desk_and_chair():
    room = Room(id="o1", type="office", x=0, y=0, width=4, depth=4,
                doors=[Door(wall="south", offset=2, width=1)])
    items = apply_template(room, level_y=0.0, anchor=(30.0, 30.0))
    types = [i.type for i in items]
    assert "desk" in types
    assert "office_chair" in types


def test_apply_template_skips_oversized_furniture():
    # tiny room: should skip a desk that needs >1m
    room = Room(id="tiny", type="office", x=0, y=0, width=0.5, depth=0.5,
                doors=[Door(wall="south", offset=0.1, width=0.3)])
    items = apply_template(room, level_y=0.0, anchor=(0.0, 0.0))
    assert items == []


def test_apply_template_offsets_by_anchor():
    room = Room(id="o1", type="office", x=2.0, y=3.0, width=4, depth=4,
                doors=[Door(wall="south", offset=2, width=1)])
    items = apply_template(room, level_y=0.0, anchor=(30.0, 50.0))
    desks = [i for i in items if i.type == "desk"]
    assert desks
    # desk position x should include anchor + room.x
    assert desks[0].position[0] > 32.0


def test_apply_template_unknown_type_returns_empty():
    room = Room(id="weird", type="alien_lab", x=0, y=0, width=4, depth=4,
                doors=[Door(wall="south", offset=2, width=1)])
    items = apply_template(room, level_y=0.0, anchor=(0.0, 0.0))
    assert items == []
