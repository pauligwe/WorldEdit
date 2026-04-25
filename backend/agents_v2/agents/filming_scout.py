"""Tier 1 — Filming Location Scout.

Given a geolocated region, suggests 3-5 real-world filming locations
matching the scene's vibe. Uses Google Search grounding for richer results
when available.
"""
from agents_v2.messages import AgentRequest, FilmingScoutResult
from core.gemini_client import structured


SYSTEM = (
    "You are a film location scout. Given a target region and scene "
    "description, suggest 3-5 specific real-world locations a director "
    "could book or visit, each with name, rough address, and why it matches."
)


def run(req: AgentRequest) -> dict:
    geo = req.upstream.get("geolocator", {})
    region = ""
    cands = geo.get("candidates", [])
    if cands:
        region = cands[0].get("region", "")
    scene = req.upstream.get("scene_describer", {})
    summary = scene.get("summary", "")

    prompt = (
        f"Target region: {region or 'unspecified'}\n"
        f"Scene: {summary or req.prompt}\n\n"
        "Return 3-5 plausible filming locations within this region."
    )
    out: FilmingScoutResult = structured(prompt=prompt, schema=FilmingScoutResult, system=SYSTEM)
    return out.model_dump()
