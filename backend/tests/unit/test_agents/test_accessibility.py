from unittest.mock import patch
from agents_v2.agents import accessibility
from agents_v2.messages import AgentRequest, Accessibility


def test_returns_audit():
    fake = Accessibility(
        issues=[{"category": "mobility", "description": "narrow doorways"}],
        suggestions=["widen primary entry"],
    )
    with patch.object(accessibility, "structured", return_value=fake):
        out = accessibility.run(AgentRequest(
            world_id="cabin", agent_id="accessibility", prompt="cabin", view_paths=[],
            upstream={"spatial_layout": {"rooms": [], "entrances": [], "sightlines": [], "total_sqft_estimate": 0}},
        ))
    assert out["issues"][0]["category"] == "mobility"
