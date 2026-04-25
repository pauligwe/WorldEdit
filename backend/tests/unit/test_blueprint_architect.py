import os
import pytest
from core.world_spec import WorldSpec, Intent
from core.validators import validate_blueprint
from agents.blueprint_architect import run

pytestmark = pytest.mark.skipif(not os.environ.get("GOOGLE_API_KEY"), reason="no Gemini key")


def test_generates_valid_blueprint():
    spec = WorldSpec(
        worldId="t1",
        prompt="A small one-story modern house with a kitchen and two bedrooms",
        intent=Intent(buildingType="house", style="modern", floors=1, vibe=["minimal"], sizeHint="small"),
    )
    out = run(spec)
    assert out.blueprint is not None
    report = validate_blueprint(out.blueprint)
    assert report.ok, f"validation errors: {report.errors}"


def test_generates_two_story():
    spec = WorldSpec(
        worldId="t2",
        prompt="A two-story house with a living room and dining room downstairs and three bedrooms upstairs",
        intent=Intent(buildingType="house", style="traditional", floors=2, vibe=["family"], sizeHint="medium"),
    )
    out = run(spec)
    assert out.blueprint is not None
    assert len(out.blueprint.floors) == 2
