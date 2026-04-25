from unittest.mock import patch
from agents_v2.agents import geolocator
from agents_v2.messages import AgentRequest, GeolocationResult


def test_uses_scene_summary_in_prompt():
    fake = GeolocationResult(candidates=[
        {"region": "Pacific Northwest, USA", "confidence": 0.7, "reasoning": "conifers"}
    ])
    with patch.object(geolocator, "structured", return_value=fake) as m:
        req = AgentRequest(
            world_id="cabin", agent_id="geolocator", prompt="cabin",
            view_paths=[],
            upstream={"scene_describer": {"summary": "Log cabin in dense conifer forest", "tags": ["pnw"]}},
        )
        out = geolocator.run(req)
    assert out["candidates"][0]["region"].startswith("Pacific Northwest")
    args, kwargs = m.call_args
    assert "Log cabin" in kwargs["prompt"] or "Log cabin" in args[0]
