"""Tier 3 — Story Seeds."""
from agents_v2.messages import AgentRequest, StorySeed
from core.gemini_client import structured


SYSTEM = (
    "You write loglines. Generate 3 short film/novel premises set in this "
    "scene. Each: title, one-sentence logline, genre."
)


def run(req: AgentRequest) -> dict:
    scene = req.upstream.get("scene_describer", {})
    era = req.upstream.get("era_estimator", {})
    prompt = (
        f"Scene: {scene.get('summary','')}\n"
        f"Era: {era.get('period','')}\n\n"
        "Generate 3 distinct premises."
    )
    out: StorySeed = structured(prompt=prompt, schema=StorySeed, system=SYSTEM)
    return out.model_dump()
