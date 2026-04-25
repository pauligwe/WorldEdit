"""Tier 4 — Carbon / Sustainability Score."""
from agents_v2.messages import AgentRequest, CarbonScore
from core.gemini_client import structured


SYSTEM = (
    "Estimate the embodied carbon (kg CO2e) of building this scene from its "
    "materials and contents. Return a total + breakdown by material + brief "
    "reasoning. Be conservative; this is a rough estimate."
)


def run(req: AgentRequest) -> dict:
    scene = req.upstream.get("scene_describer", {})
    inv = req.upstream.get("object_inventory", {})
    prompt = (
        f"Scene: {scene.get('summary','')}\n"
        f"Objects: {[o.get('name') for o in inv.get('objects',[])]}"
    )
    out: CarbonScore = structured(prompt=prompt, schema=CarbonScore, system=SYSTEM)
    return out.model_dump()
