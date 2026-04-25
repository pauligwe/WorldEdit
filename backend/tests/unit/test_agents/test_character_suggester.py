from unittest.mock import patch
from agents_v2.agents import character_suggester
from agents_v2.messages import AgentRequest, Characters


def test_returns_characters():
    fake = Characters(characters=[
        {"name": "Marta Lindquist", "role": "retired park ranger", "bio": "Solo dweller, knows every trail."}
    ])
    with patch.object(character_suggester, "structured", return_value=fake):
        out = character_suggester.run(AgentRequest(
            world_id="cabin", agent_id="character_suggester", prompt="cabin", view_paths=[],
            upstream={"scene_describer": {"summary": "cabin", "tags": []}},
        ))
    assert out["characters"][0]["name"] == "Marta Lindquist"
