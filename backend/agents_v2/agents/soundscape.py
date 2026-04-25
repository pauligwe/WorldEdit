"""Tier 2 — Soundscape Designer."""
from agents_v2.messages import AgentRequest, Soundscape
from core.gemini_client import structured


SYSTEM = (
    "Design the audio for this scene: 3-5 ambient layers (continuous bed) "
    "plus 5-10 specific Foley sounds."
)


def run(req: AgentRequest) -> dict:
    scene = req.upstream.get("scene_describer", {})
    prompt = f"Scene: {scene.get('summary','')}"
    out: Soundscape = structured(prompt=prompt, schema=Soundscape, system=SYSTEM)
    return out.model_dump()
