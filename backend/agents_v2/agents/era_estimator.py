"""Tier 1 — Era / Period Estimator."""
from agents_v2.messages import AgentRequest, EraEstimate
from core.gemini_client import structured


SYSTEM = "Estimate the historical period or design era a scene evokes (e.g. '1970s Scandinavian modern', 'Edwardian')."


def run(req: AgentRequest) -> dict:
    scene = req.upstream.get("scene_describer", {})
    prompt = f"Scene: {scene.get('summary','')}\nTags: {', '.join(scene.get('tags',[]))}"
    out: EraEstimate = structured(prompt=prompt, schema=EraEstimate, system=SYSTEM)
    return out.model_dump()
