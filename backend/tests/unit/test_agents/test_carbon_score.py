from unittest.mock import patch
from agents_v2.agents import carbon_score
from agents_v2.messages import AgentRequest, CarbonScore


def test_returns_score():
    fake = CarbonScore(
        embodied_carbon_kg_co2e=12000,
        breakdown=[{"material": "logs", "kg_co2e": 4000}],
        reasoning="rough",
    )
    with patch.object(carbon_score, "structured", return_value=fake):
        out = carbon_score.run(AgentRequest(
            world_id="cabin", agent_id="carbon_score", prompt="cabin", view_paths=[],
            upstream={
                "object_inventory": {"objects": []},
                "scene_describer": {"summary": "log cabin", "tags": []},
            },
        ))
    assert out["embodied_carbon_kg_co2e"] == 12000
