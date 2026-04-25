import os
import pytest
from core.world_spec import WorldSpec
from agents.intent_parser import run

LIVE = pytest.mark.skipif(not os.environ.get("GOOGLE_API_KEY"), reason="no Gemini key")


@LIVE
def test_parses_simple_prompt():
    spec = WorldSpec(worldId="t1", prompt="A two-story modern beach house with three bedrooms")
    out = run(spec)
    assert out.intent is not None
    assert out.intent.floors >= 2
    assert "modern" in out.intent.style.lower() or "beach" in out.intent.style.lower()


def test_intent_parser_writes_site_from_intent(monkeypatch):
    from agents import intent_parser
    from core.world_spec import Intent
    fake_intent = Intent(buildingType="office", style="modern", floors=2,
                         vibe=[], sizeHint="medium")
    monkeypatch.setattr("agents.intent_parser.structured",
                        lambda *a, **kw: fake_intent)
    spec = WorldSpec(worldId="x", prompt="an office")
    out = intent_parser.run(spec)
    assert out.site is not None
    assert out.site.entrance.wall == "south"
    assert out.site.plot.width == 100.0
