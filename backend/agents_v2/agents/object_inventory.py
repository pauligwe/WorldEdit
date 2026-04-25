"""Tier 0 — Object Inventory.

Lists every visible object across the 3 captures with rough position labels.
Feeds prop_shopping, set_dressing, hazard_audit, carbon_score.
"""
from pathlib import Path
from agents_v2.messages import AgentRequest, ObjectInventory
from core.gemini_client import vision


SYSTEM = (
    "You catalog visible objects in a 3D scene. Look at the 3 captures and "
    "list every distinct object you can identify, with a short position "
    "phrase (e.g. 'center-left', 'far wall', 'on the table near window')."
)


def run(req: AgentRequest) -> dict:
    images = [("image/jpeg", Path(p).read_bytes()) for p in req.view_paths]
    prompt = (
        f"Generation prompt: {req.prompt!r}\n\n"
        f"Enumerate every visible object as {{name, position}}."
    )
    out: ObjectInventory = vision(prompt=prompt, images=images, schema=ObjectInventory, system=SYSTEM)
    return out.model_dump()
