from unittest.mock import patch
from agents_v2.agents import era_estimator
from agents_v2.messages import AgentRequest, EraEstimate


def test_returns_period():
    fake = EraEstimate(period="1970s rustic Americana", confidence=0.6, reasoning="x")
    with patch.object(era_estimator, "structured", return_value=fake):
        out = era_estimator.run(AgentRequest(
            world_id="cabin", agent_id="era_estimator", prompt="cabin", view_paths=[],
            upstream={"scene_describer": {"summary": "log cabin", "tags": []}},
        ))
    assert out["period"] == "1970s rustic Americana"
