import json
from pathlib import Path
from core.world_spec import Blueprint
from core.navigation import compute_navigation

EXAMPLES = Path(__file__).parent.parent.parent / "core" / "prompts" / "examples"


def test_navigation_spawn_inside_a_room():
    bp = Blueprint(**json.loads((EXAMPLES / "single_floor_house.json").read_text()))
    nav = compute_navigation(bp)
    sx, _sy, sz = nav.spawnPoint
    bp_y = -sz
    found = False
    for fl in bp.floors:
        for r in fl.rooms:
            if r.x <= sx <= r.x + r.width and r.y <= bp_y <= r.y + r.depth:
                found = True
    assert found, f"spawn ({sx}, {bp_y}) not in any room"


def test_two_story_navigation_lists_stair_colliders():
    bp = Blueprint(**json.loads((EXAMPLES / "two_story_house.json").read_text()))
    nav = compute_navigation(bp)
    assert len(nav.stairColliders) >= 1
