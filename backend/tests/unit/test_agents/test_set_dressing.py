from unittest.mock import patch
from agents_v2.agents import set_dressing
from agents_v2.messages import AgentRequest, SetDressing


def test_returns_suggestions():
    fake = SetDressing(suggestions=[
        {"theme": "more lived-in", "additions": ["scattered books", "knit throw"]},
    ])
    with patch.object(set_dressing, "structured", return_value=fake):
        out = set_dressing.run(AgentRequest(
            world_id="cabin", agent_id="set_dressing", prompt="cabin", view_paths=[],
            upstream={
                "scene_describer": {"summary": "minimal cabin", "tags": []},
                "object_inventory": {"objects": [{"name": "couch", "position": ""}]},
            },
        ))
    assert out["suggestions"][0]["theme"]
