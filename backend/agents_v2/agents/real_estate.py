"""Tier 4 — Real Estate Appraisal."""
from agents_v2.messages import AgentRequest, RealEstate
from core.gemini_client import structured


SYSTEM = (
    "Given a likely market region and approximate square footage, estimate a "
    "plausible monthly rent in USD for an equivalent real-world property."
)


def run(req: AgentRequest) -> dict:
    geo = req.upstream.get("geolocator", {})
    cands = geo.get("candidates", [])
    region = cands[0].get("region", "unknown") if cands else "unknown"
    layout = req.upstream.get("spatial_layout", {})
    sqft = layout.get("total_sqft_estimate", 0)
    prompt = f"Region: {region}\nApprox sqft: {sqft}"
    out: RealEstate = structured(prompt=prompt, schema=RealEstate, system=SYSTEM)
    return out.model_dump()
