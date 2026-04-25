import os
import pytest
from core.world_spec import WorldSpec, Intent, Site, Plot, Entrance
from core.site import derive_site_from_intent
from core.validators import validate_blueprint
from core.prompts.blueprint_architect import make_user_prompt
from agents.blueprint_architect import run

_live = pytest.mark.skipif(not os.environ.get("GOOGLE_API_KEY"), reason="no Gemini key")


def _make_spec(world_id: str, prompt: str, intent: Intent) -> WorldSpec:
    return WorldSpec(
        worldId=world_id,
        prompt=prompt,
        intent=intent,
        site=derive_site_from_intent(intent),
    )


def test_make_user_prompt_includes_footprint():
    """make_user_prompt renders footprint placeholders into the output."""
    result = make_user_prompt(
        intent_json='{"buildingType": "office"}',
        prompt="test office",
        footprint_w=40.0,
        footprint_d=25.0,
        entrance_offset=20.0,
        entrance_width=1.6,
    )
    assert "40.0 m × 25.0 m" in result
    assert "offset 20.0 m" in result
    assert "width 1.6 m" in result


def test_run_raises_without_site():
    """run() raises ValueError when spec.site is None."""
    intent = Intent(buildingType="house", style="modern", floors=1, vibe=[], sizeHint="small")
    spec = WorldSpec(
        worldId="no-site",
        prompt="A house",
        intent=intent,
        site=None,
    )
    with pytest.raises(ValueError, match="site"):
        run(spec)


@_live
def test_generates_valid_blueprint():
    spec = _make_spec(
        "t1",
        "A small one-story modern house with a kitchen and two bedrooms",
        Intent(buildingType="house", style="modern", floors=1, vibe=["minimal"], sizeHint="small"),
    )
    out = run(spec)
    assert out.blueprint is not None
    report = validate_blueprint(out.blueprint)
    assert report.ok, f"validation errors: {report.errors}"


@_live
def test_generates_two_story():
    spec = _make_spec(
        "t2",
        "A two-story house with a living room and dining room downstairs and three bedrooms upstairs",
        Intent(buildingType="house", style="traditional", floors=2, vibe=["family"], sizeHint="medium"),
    )
    out = run(spec)
    assert out.blueprint is not None
    assert len(out.blueprint.floors) == 2
