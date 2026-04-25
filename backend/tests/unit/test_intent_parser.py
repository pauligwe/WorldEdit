import os
import pytest
from core.world_spec import WorldSpec
from agents.intent_parser import run

pytestmark = pytest.mark.skipif(not os.environ.get("GOOGLE_API_KEY"), reason="no Gemini key")


def test_parses_simple_prompt():
    spec = WorldSpec(worldId="t1", prompt="A two-story modern beach house with three bedrooms")
    out = run(spec)
    assert out.intent is not None
    assert out.intent.floors >= 2
    assert "modern" in out.intent.style.lower() or "beach" in out.intent.style.lower()
