import json
from pathlib import Path
from core.world_spec import Blueprint, Floor, Room, Door, Stairs
from core.validators import validate_blueprint

EXAMPLES = Path(__file__).parent.parent.parent / "core" / "prompts" / "examples"


def _ex(name: str) -> Blueprint:
    return Blueprint(**json.loads((EXAMPLES / name).read_text()))


def test_examples_pass_validation():
    for name in ("tiny_apartment.json", "single_floor_house.json", "two_story_house.json"):
        report = validate_blueprint(_ex(name))
        assert report.ok, f"{name}: {report.errors}"


def test_room_with_no_doors_fails():
    bp = Blueprint(
        gridSize=0.5,
        floors=[Floor(level=0, ceilingHeight=3.0, rooms=[
            Room(id="r1", type="bedroom", x=0, y=0, width=4, depth=4, doors=[], windows=[]),
        ], stairs=[])],
    )
    report = validate_blueprint(bp)
    assert not report.ok
    assert any("door" in e.lower() for e in report.errors)


def test_overlapping_rooms_fail():
    bp = Blueprint(
        gridSize=0.5,
        floors=[Floor(level=0, ceilingHeight=3.0, rooms=[
            Room(id="r1", type="bedroom", x=0, y=0, width=4, depth=4,
                 doors=[Door(wall="south", offset=2, width=1)], windows=[]),
            Room(id="r2", type="bedroom", x=2, y=2, width=4, depth=4,
                 doors=[Door(wall="south", offset=2, width=1)], windows=[]),
        ], stairs=[])],
    )
    report = validate_blueprint(bp)
    assert not report.ok
    assert any("overlap" in e.lower() for e in report.errors)


def test_stairs_must_align_between_floors():
    bp = Blueprint(
        gridSize=0.5,
        floors=[
            Floor(level=0, ceilingHeight=3.0, rooms=[
                Room(id="r1", type="hallway", x=0, y=0, width=4, depth=4,
                     doors=[Door(wall="south", offset=2, width=1)], windows=[]),
            ], stairs=[Stairs(id="s1", x=0, y=0, width=2, depth=2, direction="north", toLevel=1)]),
            Floor(level=1, ceilingHeight=3.0, rooms=[
                Room(id="r2", type="hallway", x=0, y=0, width=4, depth=4,
                     doors=[Door(wall="south", offset=2, width=1)], windows=[]),
            ], stairs=[Stairs(id="s1", x=10, y=10, width=2, depth=2, direction="south", toLevel=0)]),
        ],
    )
    report = validate_blueprint(bp)
    assert not report.ok
    assert any("stair" in e.lower() and "align" in e.lower() for e in report.errors)


import pytest
from core.world_spec import (WorldSpec, Blueprint, Floor, Room, Door, Intent)
from core.site import derive_site_from_intent
from agents.compliance_critic import run as critic_run, ComplianceError


def test_critic_rejects_room_outside_footprint():
    intent = Intent(buildingType="office", style="modern", floors=1,
                    vibe=[], sizeHint="medium")
    site = derive_site_from_intent(intent)
    fw, fd = site.buildingFootprint
    bp = Blueprint(floors=[Floor(level=0, ceilingHeight=3.0, rooms=[
        Room(id="big", type="office", x=0, y=0, width=fw + 50, depth=fd,
             doors=[Door(wall="south", offset=1, width=1)])])])
    spec = WorldSpec(worldId="x", prompt="t", intent=intent, site=site, blueprint=bp)
    with pytest.raises(ComplianceError):
        critic_run(spec)


def test_critic_passes_with_valid_site():
    intent = Intent(buildingType="office", style="modern", floors=1,
                    vibe=[], sizeHint="medium")
    site = derive_site_from_intent(intent)
    fw, fd = site.buildingFootprint
    bp = Blueprint(floors=[Floor(level=0, ceilingHeight=3.0, rooms=[
        Room(id="lobby", type="lobby", x=0, y=0, width=fw, depth=fd,
             doors=[Door(wall="south", offset=site.entrance.offset, width=1.6)])])])
    spec = WorldSpec(worldId="x", prompt="t", intent=intent, site=site, blueprint=bp)
    out = critic_run(spec)
    assert out is spec
