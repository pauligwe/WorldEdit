"""Procedural lighting designer.

Generates ceiling lights per room based on room size and type. No LLM call --
this is geometric placement. One light for tiny rooms, a 2x1 grid for medium,
a 2x2 grid for large rooms. Color temperature varies per room type.
"""

from core.world_spec import Light, LightingByRoom, WorldSpec


# (color_hex, intensity) by room type. Color is the bulb tint -- warmer for
# residential/comfort rooms, cooler for offices and tech rooms.
_LIGHT_BY_TYPE: dict[str, tuple[str, float]] = {
    "lobby":          ("#fff4d6", 1.4),
    "office":         ("#f8f1d9", 1.2),
    "office_open":    ("#f8f1d9", 1.3),
    "conference":     ("#f8f1d9", 1.2),
    "conference_room": ("#f8f1d9", 1.2),
    "breakroom":      ("#ffe4b3", 1.1),
    "kitchen":        ("#fff0c0", 1.2),
    "corridor":       ("#fbe9b8", 0.9),
    "hallway":        ("#fbe9b8", 0.9),
    "foyer":          ("#fff0c0", 1.1),
    "bathroom":       ("#fafafa", 1.0),
    "restroom":       ("#fafafa", 1.0),
    "bedroom":        ("#ffd9a0", 1.0),
    "living_room":    ("#fff0c0", 1.2),
    "dining_room":    ("#ffd9a0", 1.1),
    "studio":         ("#fff0c0", 1.2),
    "open_living":    ("#fff0c0", 1.2),
    "stairwell":      ("#f5e4c0", 1.0),
    "server_room":    ("#cfe6ff", 0.9),
}
_FALLBACK_LIGHT = ("#f8f1d9", 1.1)


def _lights_for_room(
    room_id: str,
    room_type: str,
    rx: float, ry: float, rw: float, rd: float,
    ax: float, ay: float,
    level_y: float, ceiling_height: float,
) -> list[Light]:
    """Place ceiling lights at scene coords. Hangs them 0.3m below the ceiling.

    Coord mapping matches geometry.py:
        scene_x =  ax + room.x + dx
        scene_z = -(ay + room.y + dy)
    """
    color, intensity = _LIGHT_BY_TYPE.get(room_type, _FALLBACK_LIGHT)
    light_y = level_y + ceiling_height - 0.3

    area = rw * rd
    if area <= 12.0:
        # Tiny: one light dead center.
        offsets = [(rw / 2, rd / 2)]
    elif area <= 40.0:
        # Medium: two lights spaced along the longer axis.
        if rw >= rd:
            offsets = [(rw * 0.30, rd / 2), (rw * 0.70, rd / 2)]
        else:
            offsets = [(rw / 2, rd * 0.30), (rw / 2, rd * 0.70)]
    else:
        # Large: 2x2 grid.
        offsets = [
            (rw * 0.27, rd * 0.27),
            (rw * 0.73, rd * 0.27),
            (rw * 0.27, rd * 0.73),
            (rw * 0.73, rd * 0.73),
        ]

    out: list[Light] = []
    for dx, dy in offsets:
        sx = ax + rx + dx
        sz = -(ay + ry + dy)
        out.append(Light(
            type="ceiling",
            position=[sx, light_y, sz],
            color=color,
            intensity=intensity,
        ))
    return out


def run(spec: WorldSpec) -> WorldSpec:
    assert spec.intent and spec.blueprint and spec.site

    ax, ay = spec.site.buildingAnchor
    by_room: dict[str, list[Light]] = {}

    for fl in spec.blueprint.floors:
        level_y = fl.level * fl.ceilingHeight
        for room in fl.rooms:
            by_room[room.id] = _lights_for_room(
                room.id, room.type,
                room.x, room.y, room.width, room.depth,
                ax, ay,
                level_y, fl.ceilingHeight,
            )

    spec.lighting = LightingByRoom(byRoom=by_room)
    return spec
