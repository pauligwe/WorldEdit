import json
from pathlib import Path
from core.world_spec import Blueprint

EXAMPLES = Path(__file__).parent.parent.parent / "core" / "prompts" / "examples"


def test_tiny_apartment_loads():
    raw = json.loads((EXAMPLES / "tiny_apartment.json").read_text())
    bp = Blueprint(**raw)
    assert len(bp.floors) == 1
    assert len(bp.floors[0].rooms) >= 3


def test_single_floor_house_loads():
    raw = json.loads((EXAMPLES / "single_floor_house.json").read_text())
    bp = Blueprint(**raw)
    assert len(bp.floors) == 1
    assert any(r.type == "kitchen" for r in bp.floors[0].rooms)


def test_two_story_house_has_stairs():
    raw = json.loads((EXAMPLES / "two_story_house.json").read_text())
    bp = Blueprint(**raw)
    assert len(bp.floors) == 2
    assert len(bp.floors[0].stairs) >= 1
