SYSTEM = """You extract structured intent from a natural-language description of a building.
Respond with valid JSON only, no prose. Conform to the schema you are given."""

USER_TMPL = """Extract intent from this prompt:

PROMPT:
{prompt}

Return JSON with fields:
- buildingType: one of "house", "apartment", "cabin", "loft" (default "house")
- style: short descriptor like "modern", "mid-century", "scandinavian", "industrial", "beach"
- floors: integer 1-4 (infer from prompt; default 1)
- vibe: array of 1-4 mood adjectives (e.g. ["cozy","airy"])
- sizeHint: one of "small", "medium", "large"
"""
