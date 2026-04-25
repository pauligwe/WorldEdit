"""Tier 1 — Architectural Style Classifier."""
from agents_v2.messages import AgentRequest, ArchitecturalStyle
from core.gemini_client import structured


SYSTEM = "Classify the architectural style of a scene (Craftsman, mid-century modern, brutalist, etc)."


def run(req: AgentRequest) -> dict:
    scene = req.upstream.get("scene_describer", {})
    prompt = f"Scene: {scene.get('summary','')}\nTags: {', '.join(scene.get('tags',[]))}"
    out: ArchitecturalStyle = structured(prompt=prompt, schema=ArchitecturalStyle, system=SYSTEM)
    return out.model_dump()
