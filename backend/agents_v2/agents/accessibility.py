"""Tier 4 — Accessibility Audit."""
from agents_v2.messages import AgentRequest, Accessibility
from core.gemini_client import structured


SYSTEM = (
    "Audit accessibility (mobility, vision, hearing, cognitive). List 3-5 "
    "issues with category + description, plus 3-5 actionable suggestions."
)


def run(req: AgentRequest) -> dict:
    layout = req.upstream.get("spatial_layout", {})
    prompt = f"Layout: {layout}"
    out: Accessibility = structured(prompt=prompt, schema=Accessibility, system=SYSTEM)
    return out.model_dump()
