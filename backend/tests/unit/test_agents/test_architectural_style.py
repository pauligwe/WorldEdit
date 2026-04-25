from unittest.mock import patch
from agents_v2.agents import architectural_style
from agents_v2.messages import AgentRequest, ArchitecturalStyle


def test_returns_style():
    fake = ArchitecturalStyle(style="Craftsman log cabin", confidence=0.8, reasoning="exposed log walls")
    with patch.object(architectural_style, "structured", return_value=fake):
        out = architectural_style.run(AgentRequest(
            world_id="cabin", agent_id="architectural_style", prompt="cabin", view_paths=[],
            upstream={"scene_describer": {"summary": "log cabin", "tags": []}},
        ))
    assert out["style"] == "Craftsman log cabin"
