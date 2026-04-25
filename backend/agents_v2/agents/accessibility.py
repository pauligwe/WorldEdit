"""Tier 4 — Accessibility Audit."""
from agents_v2.messages import AgentRequest, Accessibility
from core.gemini_client import structured


SYSTEM = (
    "Audit accessibility (mobility, vision, hearing, cognitive) for the "
    "specific space described. List 3-5 issues, each citing a concrete "
    "feature of the scene (e.g. 'narrow stairs at entry', 'low-contrast "
    "signage'), plus 3-5 actionable suggestions tied to those issues. "
    "If only exterior views are described, focus on entry/approach/wayfinding "
    "and acknowledge that interior features are inferred."
)


def run(req: AgentRequest) -> dict:
    layout = req.upstream.get("spatial_layout", {})
    scene = req.upstream.get("scene_describer", {})
    summary = scene.get("summary", "")
    layout_summary = layout.get("narrative") or layout.get("summary") or str(layout)

    prompt = (
        f"Scene: {summary or req.prompt}\n"
        f"Spatial layout: {layout_summary}\n\n"
        "Audit this space for accessibility. Reference specific features "
        "from the scene, not generic categories."
    )
    out: Accessibility = structured(prompt=prompt, schema=Accessibility, system=SYSTEM)
    return out.model_dump()
