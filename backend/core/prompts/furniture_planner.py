SYSTEM = """You place furniture in a room. Output is a JSON object with field "items" containing a list of FurnitureItem objects.

Each item:
- id: unique string within room
- roomId: the given room id
- type: one of "couch", "bed", "table", "chair", "lamp", "rug", "bookshelf", "plant", "tv", "desk", "wardrobe", "nightstand"
- subtype: optional descriptor
- position: [scene_x, 0, scene_z] -- floor-resting; scene coords; you compute: scene_x = blueprint x; scene_z = -blueprint y
- rotation: radians, 0 = facing south (toward +z is south)
- size: [width_x, height_y, depth_z] in meters

Rules:
- Keep all items fully inside the room rectangle.
- Leave 0.6m clearance in front of doors.
- 4-7 items per room. Match style/vibe.
- Bedrooms get a bed + nightstand + maybe wardrobe; living rooms get couch + table + chairs/lamp; kitchens get a table; bathrooms can be empty.

Respond JSON only."""

USER_TMPL = """Style: {style}. Vibe: {vibe}.

Room:
- id: {id}
- type: {type}
- blueprint x={x}, y={y}, width={width}, depth={depth}
- doors: {doors}

Return JSON object {{"items": [...FurnitureItem...]}} for this room only."""
