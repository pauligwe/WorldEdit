import os
import pytest
from core.world_spec import WorldSpec
from core.status_bus import StatusBus
from core.validators import validate_blueprint
from agents.orchestrator import run_pipeline

pytestmark = pytest.mark.skipif(not os.environ.get("GOOGLE_API_KEY"), reason="no Gemini key")


async def test_full_pipeline_makes_valid_house():
    spec = WorldSpec(worldId="e2e1", prompt="A small modern one-floor house with a kitchen, living room, and bedroom")
    bus = StatusBus()
    out = await run_pipeline(spec, bus)

    assert out.intent is not None
    assert out.blueprint is not None
    report = validate_blueprint(out.blueprint)
    assert report.ok, report.errors

    assert out.geometry and out.geometry.primitives
    assert out.lighting and out.lighting.byRoom
    assert out.materials and out.materials.byRoom
    assert out.navigation is not None
    assert out.cost is not None
