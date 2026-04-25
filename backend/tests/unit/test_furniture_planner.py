from core.world_spec import (WorldSpec, Intent, Blueprint, Floor, Room, Door)
from core.site import derive_site_from_intent
from agents.furniture_planner import run as planner_run


def _spec_with_offices():
    intent = Intent(buildingType="office", style="modern", floors=1,
                    vibe=[], sizeHint="medium")
    site = derive_site_from_intent(intent)
    bp = Blueprint(floors=[Floor(level=0, ceilingHeight=3.0, rooms=[
        Room(id="off1", type="office", x=0, y=0, width=4, depth=4,
             doors=[Door(wall="south", offset=2, width=1)]),
        Room(id="conf1", type="conference_room", x=4, y=0, width=6, depth=5,
             doors=[Door(wall="south", offset=2, width=1)]),
    ])])
    return WorldSpec(worldId="x", prompt="t", intent=intent,
                     site=site, blueprint=bp)


def test_furniture_planner_produces_items_per_room():
    spec = _spec_with_offices()
    out = planner_run(spec)
    assert any(f.type == "desk" and f.roomId == "off1" for f in out.furniture)
    assert any(f.type == "conference_table" and f.roomId == "conf1" for f in out.furniture)


def test_furniture_planner_no_llm_call_required():
    spec = _spec_with_offices()
    planner_run(spec)


def test_furniture_planner_positions_in_plot_world():
    spec = _spec_with_offices()
    out = planner_run(spec)
    desk = next(f for f in out.furniture if f.type == "desk")
    assert desk.position[0] > 20
