SYSTEM = """You design interior lighting. For each room you produce a list of lights, each:
- type: "ceiling" | "lamp" | "ambient"
- position: [x, y, z] in scene coords (y is up). Ceiling about 0.2 below ceilingHeight.
- color: hex like "#ffeacc"
- intensity: 0.3-2.0

Aim for 2-4 lights per room. Respond JSON only matching schema."""

USER_TMPL = """Style/vibe: {style} {vibe}

Rooms:
{rooms}

Each room has: id, type, x, y, width, depth, ceilingHeight.
Coord mapping: scene_x = blueprint x; scene_z = -blueprint y; light positions in those scene coords.

Return JSON: {{"byRoom": {{"<roomId>": [{{"type": "...", "position": [...], "color": "#...", "intensity": 1.0}}]}}}}"""
