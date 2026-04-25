"""Tier 2 — Set Dressing Improvements."""
from agents_v2.messages import AgentRequest, SetDressing
from core.gemini_client import structured


SYSTEM = (
    "Propose 3-5 'to make this scene more X, add Y' suggestions. Each "
    "suggestion has a theme (e.g. 'more lived-in', 'more dramatic') and "
    "specific additions."
)


def run(req: AgentRequest) -> dict:
    scene = req.upstream.get("scene_describer", {})
    inv = req.upstream.get("object_inventory", {})
    prompt = (
        f"Scene: {scene.get('summary','')}\n"
        f"Existing objects: {[o.get('name') for o in inv.get('objects',[])]}\n\n"
        "Propose 3-5 themed set dressing additions."
    )
    out: SetDressing = structured(prompt=prompt, schema=SetDressing, system=SYSTEM)
    return out.model_dump()
