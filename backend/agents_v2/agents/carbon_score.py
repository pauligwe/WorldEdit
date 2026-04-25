"""Tier 4 — Carbon / Sustainability Score."""
from agents_v2.messages import AgentRequest, CarbonScore
from core.gemini_client import structured


SYSTEM = (
    "Estimate the embodied carbon (kg CO2e) of building this scene from its "
    "materials and contents. Return a total + breakdown by material + brief "
    "reasoning. Be conservative; this is a rough estimate. "
    "If only exterior building views are available (the object inventory is "
    "empty or only lists facade/exterior elements), score only the visible "
    "shell (concrete, glass, steel) and explicitly note in the narrative "
    "that interior fit-out is excluded due to limited captures, giving the "
    "figure as a rough range."
)


def run(req: AgentRequest) -> dict:
    scene = req.upstream.get("scene_describer", {})
    inv = req.upstream.get("object_inventory", {})
    objects = [o.get("name") for o in inv.get("objects", []) if o.get("name")]
    exterior_only = len(objects) == 0
    capture_note = (
        "WARNING: no interior objects captured; score visible exterior shell only."
        if exterior_only
        else f"Interior objects captured: {len(objects)}."
    )
    prompt = (
        f"Scene: {scene.get('summary','')}\n"
        f"Objects: {objects}\n"
        f"{capture_note}"
    )
    out: CarbonScore = structured(prompt=prompt, schema=CarbonScore, system=SYSTEM)
    return out.model_dump()
