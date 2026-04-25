from unittest.mock import patch
from agents_v2.agents import hazard_audit
from agents_v2.messages import AgentRequest, HazardAudit


def test_returns_hazards():
    fake = HazardAudit(hazards=[
        {"type": "fire", "severity": "high", "description": "no smoke detector visible"}
    ])
    with patch.object(hazard_audit, "structured", return_value=fake):
        out = hazard_audit.run(AgentRequest(
            world_id="cabin", agent_id="hazard_audit", prompt="cabin", view_paths=[],
            upstream={
                "object_inventory": {"objects": []},
                "spatial_layout": {"rooms": [], "entrances": [], "sightlines": [], "total_sqft_estimate": 0},
            },
        ))
    assert out["hazards"][0]["severity"] == "high"
