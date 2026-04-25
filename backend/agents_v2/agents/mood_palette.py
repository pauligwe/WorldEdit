"""Tier 2 — Mood & Palette."""
from agents_v2.messages import AgentRequest, MoodPalette
from core.gemini_client import structured


SYSTEM = (
    "Pick a 5-color palette (hex strings starting with '#') that captures "
    "the mood, plus 2-3 LUTs and 2-3 film stocks that would suit this scene."
)


def run(req: AgentRequest) -> dict:
    scene = req.upstream.get("scene_describer", {})
    prompt = f"Scene: {scene.get('summary','')}\nTags: {', '.join(scene.get('tags',[]))}"
    out: MoodPalette = structured(prompt=prompt, schema=MoodPalette, system=SYSTEM)
    return out.model_dump()
