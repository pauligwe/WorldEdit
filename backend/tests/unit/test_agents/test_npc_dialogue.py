from unittest.mock import patch
from agents_v2.agents import npc_dialogue
from agents_v2.messages import AgentRequest, NPCDialogue


def test_returns_lines():
    fake = NPCDialogue(lines=[
        {"character": "Marta", "line": "Storm's coming. You should head down by sundown."}
    ])
    with patch.object(npc_dialogue, "structured", return_value=fake):
        out = npc_dialogue.run(AgentRequest(
            world_id="cabin", agent_id="npc_dialogue", prompt="cabin", view_paths=[],
            upstream={"character_suggester": {"characters": [{"name": "Marta", "role": "ranger", "bio": ""}]}},
        ))
    assert out["lines"][0]["character"] == "Marta"
