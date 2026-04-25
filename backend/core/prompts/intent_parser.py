SYSTEM = """You extract structured intent from a natural-language description of a building.
Respond with valid JSON only, no prose. Conform to the schema you are given."""

USER_TMPL = """Extract intent from this prompt:

PROMPT:
{prompt}

Return JSON with fields:
- buildingType: pick the closest match from this list:
    Residential: "house", "apartment", "cabin", "loft", "studio", "cottage", "condo", "mansion", "villa", "bungalow", "townhouse"
    Commercial:  "office", "school", "hospital", "library", "museum", "hotel", "mall", "restaurant"
  Use commercial types for prompts about offices, startups, workplaces, schools, etc.
  Use residential types ONLY when the prompt clearly describes a place to live.
  Default "office" if uncertain about a non-residential prompt; default "house" only if explicitly a home.
- style: short descriptor like "modern", "mid-century", "scandinavian", "industrial", "corporate", "minimal"
- floors: integer 1-4 (infer from prompt; default 1)
- vibe: array of 1-4 mood adjectives (e.g. ["cozy","airy","collaborative","focused"])
- sizeHint: one of "small", "medium", "large"
"""
