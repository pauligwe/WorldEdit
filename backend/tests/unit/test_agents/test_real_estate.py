from unittest.mock import patch
from agents_v2.agents import real_estate
from agents_v2.messages import AgentRequest, RealEstate


def test_returns_rent():
    fake = RealEstate(estimated_monthly_rent_usd=2200, market="Bend, OR", reasoning="cabin rentals 1500-3000")
    with patch.object(real_estate, "structured", return_value=fake):
        out = real_estate.run(AgentRequest(
            world_id="cabin", agent_id="real_estate", prompt="cabin", view_paths=[],
            upstream={
                "geolocator": {"candidates": [{"region": "Bend, OR", "confidence": 0.7}]},
                "spatial_layout": {"rooms": [], "entrances": [], "sightlines": [], "total_sqft_estimate": 1100},
            },
        ))
    assert out["estimated_monthly_rent_usd"] == 2200
