from unittest.mock import patch, MagicMock
from pydantic import BaseModel
from core import gemini_client


class _Out(BaseModel):
    summary: str


def test_vision_calls_with_inline_image_parts():
    """vision() builds a request with one text prompt + N image parts and parses
    structured response."""
    mock_resp = MagicMock()
    mock_resp.parsed = _Out(summary="hi")
    mock_resp.text = '{"summary": "hi"}'

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_resp

    with patch.object(gemini_client, "_client", mock_client):
        img_bytes = bytes.fromhex(
            "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
            "890000000d49444154789c63000100000005000100"
            "5d8a0a3a0000000049454e44ae426082"
        )
        out = gemini_client.vision(
            prompt="describe",
            images=[("image/png", img_bytes), ("image/png", img_bytes)],
            schema=_Out,
        )
        assert out.summary == "hi"

    assert mock_client.models.generate_content.call_count == 1


def test_vision_raises_when_no_api_key():
    with patch.object(gemini_client, "_client", None):
        try:
            gemini_client.vision(prompt="x", images=[], schema=_Out)
        except gemini_client.GeminiError as e:
            assert "GOOGLE_API_KEY" in str(e)
        else:
            raise AssertionError("expected GeminiError")
