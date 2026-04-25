"""Tier 3 — Character Suggester."""
from agents_v2.messages import AgentRequest, Characters
from core.gemini_client import structured


SYSTEM = "Propose 3-5 plausible characters who might live or work in this scene. Each: name, role, 1-sentence bio."


def run(req: AgentRequest) -> dict:
    scene = req.upstream.get("scene_describer", {})
    prompt = f"Scene: {scene.get('summary','')}"
    out: Characters = structured(prompt=prompt, schema=Characters, system=SYSTEM)
    return out.model_dump()
