from unittest.mock import patch
from agents_v2.agents import shot_list
from agents_v2.messages import AgentRequest, ShotList


def test_returns_shots():
    fake = ShotList(shots=[
        {"name": "low-angle dolly through doorway", "angle": "low", "lens_mm": 35,
         "time_of_day": "golden hour", "notes": ""},
    ])
    with patch.object(shot_list, "structured", return_value=fake):
        out = shot_list.run(AgentRequest(
            world_id="cabin", agent_id="shot_list", prompt="cabin", view_paths=[],
            upstream={
                "scene_describer": {"summary": "cabin", "tags": []},
                "spatial_layout": {"rooms": [], "entrances": [], "sightlines": [], "total_sqft_estimate": 300},
            },
        ))
    assert len(out["shots"]) == 1
    assert out["shots"][0]["lens_mm"] == 35
