import os
import pytest
from core.gemini_client import text, structured
from pydantic import BaseModel


pytestmark = pytest.mark.skipif(not os.environ.get("GOOGLE_API_KEY"), reason="no Gemini key")


class _Greeting(BaseModel):
    greeting: str
    language: str


def test_text_returns_string():
    out = text("Say hello in one short sentence.")
    assert isinstance(out, str) and len(out) > 0


def test_structured_returns_schema():
    g = structured(
        'Respond with JSON: {"greeting": "hi", "language": "en"}',
        _Greeting,
    )
    assert g.greeting and g.language
