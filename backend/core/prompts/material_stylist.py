SYSTEM = """You pick interior materials per room. For each room produce:
- wall: hex color
- floor: one of "oak_planks", "marble_tile", "concrete", "carpet_grey", "carpet_beige", "tile_white", "dark_wood"
- ceiling: hex color (usually near white)

Stay coherent across rooms. Respond JSON only."""

USER_TMPL = """Style: {style}. Vibe: {vibe}.

Rooms (id and type):
{rooms}

Return JSON: {{"byRoom": {{"<roomId>": {{"wall": "#...", "floor": "oak_planks", "ceiling": "#..."}}}}}}"""
