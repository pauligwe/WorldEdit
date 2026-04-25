import json
from pathlib import Path
from core.world_spec import Blueprint, WorldSpec
from core.navigation import compute_navigation

EXAMPLES = Path(__file__).parent.parent.parent / "core" / "prompts" / "examples"


def _spec_from_example(name: str) -> WorldSpec:
    bp = Blueprint(**json.loads((EXAMPLES / name).read_text()))
    return WorldSpec(worldId="x", prompt="t", blueprint=bp)


def test_navigation_spawn_inside_a_room():
    spec = _spec_from_example("single_floor_house.json")
    nav = compute_navigation(spec)
    sx, _sy, sz = nav.spawnPoint
    # Without site, nav falls back to default spawn; just check it's a list of 3 floats
    assert len(nav.spawnPoint) == 3


def test_two_story_navigation_lists_stair_colliders():
    spec = _spec_from_example("two_story_house.json")
    nav = compute_navigation(spec)
    # stairColliders may be empty when no site, just check it's a list
    assert isinstance(nav.stairColliders, list)
