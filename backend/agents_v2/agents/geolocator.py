"""Tier 1 — Geolocator.

Given the scene description, guesses the top-3 real-world regions the place
could be. Reads only text (cheap), not images. Feeds filming_scout,
real_estate.
"""
from agents_v2.messages import AgentRequest, GeolocationResult
from core.gemini_client import structured


SYSTEM = (
    "You are a geolocation analyst. Given a scene description, return the "
    "top-3 most plausible real-world regions where the scene could exist, "
    "each with a confidence (0-1) and short reasoning."
)


def run(req: AgentRequest) -> dict:
    scene = req.upstream.get("scene_describer", {})
    summary = scene.get("summary", "")
    tags = scene.get("tags", [])
    prompt = (
        f"Scene description: {summary}\n"
        f"Tags: {', '.join(tags)}\n"
        f"User generation prompt: {req.prompt!r}\n\n"
        "Return up to 3 candidate regions, ordered by confidence."
    )
    out: GeolocationResult = structured(prompt=prompt, schema=GeolocationResult, system=SYSTEM)
    return out.model_dump()
