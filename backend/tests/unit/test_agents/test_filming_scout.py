from unittest.mock import patch
from agents_v2.agents import filming_scout
from agents_v2.messages import AgentRequest, FilmingScoutResult


def test_uses_geolocator_top_region():
    fake = FilmingScoutResult(locations=[
        {"name": "Mt. Hood Cabin Rentals", "address": "Welches, OR", "match_reason": "log cabin in PNW conifer forest"},
    ])
    with patch.object(filming_scout, "structured", return_value=fake) as m:
        req = AgentRequest(
            world_id="cabin", agent_id="filming_scout", prompt="cabin",
            view_paths=[],
            upstream={
                "geolocator": {"candidates": [{"region": "Pacific Northwest, USA", "confidence": 0.7}]},
            },
        )
        out = filming_scout.run(req)
    assert out["locations"][0]["name"]
    args, kwargs = m.call_args
    body = kwargs.get("prompt") or (args and args[0]) or ""
    assert "Pacific Northwest" in body
