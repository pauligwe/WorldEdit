"""Tier 2 — Cinematographer's Shot List."""
from agents_v2.messages import AgentRequest, ShotList
from core.gemini_client import structured


SYSTEM = (
    "You are a cinematographer. Propose 5-8 specific shots a director should "
    "capture in this space — name, angle, lens (mm), time of day, brief notes."
)


def run(req: AgentRequest) -> dict:
    scene = req.upstream.get("scene_describer", {})
    layout = req.upstream.get("spatial_layout", {})
    prompt = (
        f"Scene: {scene.get('summary','')}\n"
        f"Layout: {layout}\n\n"
        "Propose 5-8 distinct shots."
    )
    out: ShotList = structured(prompt=prompt, schema=ShotList, system=SYSTEM)
    return out.model_dump()
