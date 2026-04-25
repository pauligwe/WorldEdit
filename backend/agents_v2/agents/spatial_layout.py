"""Tier 0 — Spatial Layout.

Infers the rough floorplan from the 3 captures: room count, entrances,
sightlines, total square footage estimate. Feeds shot_list, real_estate,
hazard_audit, accessibility.
"""
from pathlib import Path
from agents_v2.messages import AgentRequest, SpatialLayout
from core.gemini_client import vision


SYSTEM = (
    "You are an architectural surveyor. From 3 views of a 3D space, infer "
    "the floor plan: list rooms with rough square footage, list visible "
    "entrances, list notable sightlines, and estimate total square footage."
)


def run(req: AgentRequest) -> dict:
    images = [("image/jpeg", Path(p).read_bytes()) for p in req.view_paths]
    prompt = (
        f"Generation prompt: {req.prompt!r}\n\n"
        f"Infer the floor plan as JSON with rooms, entrances, sightlines, total_sqft_estimate."
    )
    out: SpatialLayout = vision(prompt=prompt, images=images, schema=SpatialLayout, system=SYSTEM)
    return out.model_dump()
