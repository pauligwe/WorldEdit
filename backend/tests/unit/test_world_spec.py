import pytest
from pydantic import ValidationError
from core.world_spec import (
    WorldSpec, FurnitureItem, Intent, Blueprint, Floor, Room, Door, Window, Stairs,
)


def test_minimal_world_spec_validates():
    spec = WorldSpec(
        worldId="abc",
        prompt="a tiny house",
        intent=Intent(buildingType="house", style="modern", floors=1, vibe=["cozy"], sizeHint="small"),
        blueprint=Blueprint(
            gridSize=0.5,
            floors=[Floor(level=0, ceilingHeight=3.0, rooms=[
                Room(id="r1", type="living_room", x=0, y=0, width=4, depth=4,
                     doors=[Door(wall="south", offset=2, width=1.0)],
                     windows=[]),
            ], stairs=[])],
        ),
    )
    assert spec.worldId == "abc"
    assert spec.intent.floors == 1
    assert spec.blueprint.floors[0].rooms[0].id == "r1"


def test_room_rejects_negative_size():
    with pytest.raises(ValidationError):
        Room(id="r1", type="bedroom", x=0, y=0, width=-1, depth=4, doors=[], windows=[])


def test_door_wall_must_be_compass_direction():
    with pytest.raises(ValidationError):
        Door(wall="up", offset=1, width=1.0)


def test_grid_alignment_validator_rejects_off_grid_room():
    with pytest.raises(ValidationError):
        Blueprint(
            gridSize=0.5,
            floors=[Floor(level=0, ceilingHeight=3.0, rooms=[
                Room(id="r1", type="bedroom", x=0.3, y=0, width=4, depth=4,
                     doors=[Door(wall="south", offset=2, width=1.0)], windows=[]),
            ], stairs=[])],
        )


def test_world_spec_has_site_field():
    spec = WorldSpec(worldId="x", prompt="test")
    assert spec.site is None
    assert not hasattr(spec, "products")


def test_furniture_item_no_product_fields():
    f = FurnitureItem(id="f1", roomId="r1", type="desk",
                     position=[0, 0, 0], size=[1, 1, 1])
    assert not hasattr(f, "selectedProductId")
    assert not hasattr(f, "alternates")
    assert not hasattr(f, "subtype")
    assert not hasattr(f, "tint")
