"""Tier 4 — Hazard Audit."""
from agents_v2.messages import AgentRequest, HazardAudit
from core.gemini_client import structured


SYSTEM = (
    "List 3-7 fire / trip / structural / code-related hazards a building "
    "inspector would flag in this space. Each: type, severity (low/medium/high), "
    "description."
)


def run(req: AgentRequest) -> dict:
    inv = req.upstream.get("object_inventory", {})
    layout = req.upstream.get("spatial_layout", {})
    prompt = (
        f"Objects: {[o.get('name') for o in inv.get('objects',[])]}\n"
        f"Layout: rooms={layout.get('rooms',[])} entrances={layout.get('entrances',[])}"
    )
    out: HazardAudit = structured(prompt=prompt, schema=HazardAudit, system=SYSTEM)
    return out.model_dump()
