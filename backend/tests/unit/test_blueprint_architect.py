import os
import pytest
from core.world_spec import WorldSpec, Intent, Site, Plot, Entrance
from core.site import derive_site_from_intent
from core.validators import validate_blueprint
from agents.blueprint_architect import run

_live = pytest.mark.skipif(not os.environ.get("GOOGLE_API_KEY"), reason="no Gemini key")


def _make_spec(world_id: str, prompt: str, intent: Intent) -> WorldSpec:
    return WorldSpec(
        worldId=world_id,
        prompt=prompt,
        intent=intent,
        site=derive_site_from_intent(intent),
    )


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


def test_residential_routes_to_archetype_packer():
    """A residential building type uses an archetype, no LLM call required."""
    intent = Intent(buildingType="house", style="modern", floors=1, vibe=[], sizeHint="small")
    spec = _make_spec("t-res", "A cozy ranch home with a kitchen", intent)
    out = run(spec)
    assert out.blueprint is not None
    assert len(out.blueprint.floors) >= 1
    # ranch archetype has 5 rooms on level 0
    assert len(out.blueprint.floors[0].rooms) == 5


def test_residential_two_story_picks_colonial():
    intent = Intent(buildingType="house", style="traditional", floors=2, vibe=[], sizeHint="medium")
    spec = _make_spec("t-col", "A two-story family home", intent)
    out = run(spec)
    assert out.blueprint is not None
    assert len(out.blueprint.floors) == 2
    # both floors should have aligned stairs
    s0 = out.blueprint.floors[0].stairs
    s1 = out.blueprint.floors[1].stairs
    assert len(s0) == 1 and len(s1) == 1
    assert (s0[0].x, s0[0].y) == (s1[0].x, s1[0].y)


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
