from unittest.mock import patch
from agents_v2.agents import soundscape
from agents_v2.messages import AgentRequest, Soundscape


def test_returns_audio_design():
    fake = Soundscape(ambient=["wind through pines"], foley=["floorboard creaks", "fire crackle"])
    with patch.object(soundscape, "structured", return_value=fake):
        out = soundscape.run(AgentRequest(
            world_id="cabin", agent_id="soundscape", prompt="cabin", view_paths=[],
            upstream={"scene_describer": {"summary": "cabin in forest", "tags": []}},
        ))
    assert "wind through pines" in out["ambient"]
