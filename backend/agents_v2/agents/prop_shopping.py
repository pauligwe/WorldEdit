"""Tier 2 — Prop Shopping List."""
from agents_v2.messages import AgentRequest, PropShopping
from core.gemini_client import structured


SYSTEM = (
    "Given an object inventory, suggest plausible store products that would "
    "match each item. Vendors: Amazon, Wayfair, IKEA, West Elm, Target. "
    "URLs may be search URLs (e.g. https://www.wayfair.com/keyword/sb0/leather-couch.html). "
    "Estimate price in USD."
)


def run(req: AgentRequest) -> dict:
    inventory = req.upstream.get("object_inventory", {})
    objects = inventory.get("objects", [])
    items_text = "\n".join(f"- {o.get('name')} ({o.get('position','')})" for o in objects)
    prompt = f"Objects to shop for:\n{items_text}\n\nReturn one product per object."
    out: PropShopping = structured(prompt=prompt, schema=PropShopping, system=SYSTEM)
    return out.model_dump()
