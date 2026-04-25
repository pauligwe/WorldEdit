from unittest.mock import patch
from agents_v2.agents import story_seed
from agents_v2.messages import AgentRequest, StorySeed


def test_returns_premises():
    fake = StorySeed(premises=[
        {"title": "Snowed In", "logline": "Estranged siblings reunite for a funeral and get snowed into the family cabin.", "genre": "drama"}
    ])
    with patch.object(story_seed, "structured", return_value=fake):
        out = story_seed.run(AgentRequest(
            world_id="cabin", agent_id="story_seed", prompt="cabin", view_paths=[],
            upstream={
                "scene_describer": {"summary": "cabin", "tags": []},
                "era_estimator": {"period": "modern", "confidence": 0.5, "reasoning": ""},
            },
        ))
    assert len(out["premises"]) == 1
    assert "Snowed In" == out["premises"][0]["title"]
