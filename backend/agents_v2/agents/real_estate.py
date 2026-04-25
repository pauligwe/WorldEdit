"""Tier 4 — Real Estate Appraisal."""
from agents_v2.messages import AgentRequest, RealEstate
from core.gemini_client import structured


SYSTEM = (
    "Given a likely market region and approximate square footage, estimate a "
    "plausible monthly rent in USD for an equivalent real-world property. "
    "If the square footage estimate is missing or clearly came from "
    "exterior-only views (no interior rooms enumerated), produce a midpoint "
    "number but explicitly say in the narrative that the figure is a "
    "rough range based on limited information, and call out the uncertainty "
    "(e.g. 'somewhere between $X and $Y')."
)


def run(req: AgentRequest) -> dict:
    geo = req.upstream.get("geolocator", {})
    cands = geo.get("candidates", [])
    region = cands[0].get("region", "unknown") if cands else "unknown"
    layout = req.upstream.get("spatial_layout", {})
    sqft = layout.get("total_sqft_estimate", 0)
    rooms = layout.get("rooms", [])
    interior_known = bool(rooms) and any(
        r.get("name", "").strip() and r.get("approx_sqft", 0) > 0 for r in rooms
    )
    capture_note = (
        "Interior layout is known (rooms enumerated)."
        if interior_known
        else "WARNING: layout came from exterior-only views; sqft is a guess."
    )
    prompt = (
        f"Region: {region}\n"
        f"Approx sqft: {sqft}\n"
        f"{capture_note}"
    )
    out: RealEstate = structured(prompt=prompt, schema=RealEstate, system=SYSTEM)
    return out.model_dump()
