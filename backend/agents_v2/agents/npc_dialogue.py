"""Tier 3 — NPC Dialogue Pack."""
from agents_v2.messages import AgentRequest, NPCDialogue
from core.gemini_client import structured


SYSTEM = (
    "Given a list of characters, write 6-10 short dialogue lines a game NPC "
    "in this space might say. Each line tagged with the character's name."
)


def run(req: AgentRequest) -> dict:
    chars = req.upstream.get("character_suggester", {}).get("characters", [])
    char_text = "\n".join(f"- {c.get('name')}: {c.get('role')}" for c in chars)
    prompt = f"Characters:\n{char_text}\n\nWrite 6-10 dialogue lines."
    out: NPCDialogue = structured(prompt=prompt, schema=NPCDialogue, system=SYSTEM)
    return out.model_dump()
