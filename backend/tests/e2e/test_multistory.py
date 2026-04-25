import os
import pytest
from core.world_spec import WorldSpec
from core.status_bus import StatusBus
from core.validators import validate_blueprint
from agents.orchestrator import run_pipeline

pytestmark = pytest.mark.skipif(not os.environ.get("GOOGLE_API_KEY"), reason="no Gemini key")


async def test_two_story_house():
    spec = WorldSpec(worldId="ms1", prompt="A two-story modern beach house with three bedrooms upstairs and an open living room and kitchen downstairs")
    bus = StatusBus()
    out = await run_pipeline(spec, bus)
    assert out.blueprint and len(out.blueprint.floors) == 2
    report = validate_blueprint(out.blueprint)
    assert report.ok, report.errors
    assert out.navigation and len(out.navigation.stairColliders) >= 1
    upstairs_room_ids = {r.id for fl in out.blueprint.floors for r in fl.rooms if fl.level == 1}
    assert any(f.roomId in upstairs_room_ids for f in out.furniture), "expected at least one furniture item upstairs"

    spec = out
    ext_walls = [p for p in spec.geometry.primitives if p.type == "exterior_wall"]
    assert len(ext_walls) >= 4 * spec.intent.floors  # 4 walls per floor
    ground_south = [p for p in ext_walls if p.wall == "south" and p.position[1] < 3]
    assert len(ground_south) == 1
    assert len(ground_south[0].holes) == 1  # entrance
