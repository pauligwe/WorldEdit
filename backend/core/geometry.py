"""Convert validated Blueprint into 3D geometry primitives.

Coord mapping: blueprint (x, y) -> scene (x, 0, -y). Heights map to scene y.
This means blueprint +y (north) renders to scene -z. Three.js right-handed y-up.
"""
from .world_spec import Blueprint, Room, Stairs, Geometry, GeometryPrimitive

WALL_THICKNESS = 0.1


def _floor_y_offset(level: int, ceiling_height: float) -> float:
    return level * ceiling_height


def _floor_primitive(room: Room, level_y: float) -> GeometryPrimitive:
    cx = room.x + room.width / 2
    cy = room.y + room.depth / 2
    return GeometryPrimitive(
        type="floor",
        roomId=room.id,
        position=[cx, level_y, -cy],
        size=[room.width, 0.05, room.depth],
    )


def _ceiling_primitive(room: Room, level_y: float, ceiling_height: float) -> GeometryPrimitive:
    cx = room.x + room.width / 2
    cy = room.y + room.depth / 2
    return GeometryPrimitive(
        type="ceiling",
        roomId=room.id,
        position=[cx, level_y + ceiling_height - 0.025, -cy],
        size=[room.width, 0.05, room.depth],
    )


def _wall_primitive(room: Room, wall: str, level_y: float, ceiling_height: float) -> GeometryPrimitive:
    """One wall on a room. Position is wall center; size is (length_x, height_y, length_z).
    For north/south walls the longer axis is x; for east/west the longer axis is z.
    Holes are door/window cutouts described as
    {offset, width, height, bottom} in wall-local coords (offset along the wall length).
    """
    holes: list[dict] = []
    for d in room.doors:
        if d.wall == wall:
            holes.append({"offset": d.offset, "width": d.width, "height": 2.1, "bottom": 0.0})
    for w in room.windows:
        if w.wall == wall:
            holes.append({"offset": w.offset, "width": w.width, "height": w.height, "bottom": w.sill})

    if wall == "north":
        cx = room.x + room.width / 2
        cz = -(room.y + room.depth)
        size = [room.width, ceiling_height, WALL_THICKNESS]
    elif wall == "south":
        cx = room.x + room.width / 2
        cz = -room.y
        size = [room.width, ceiling_height, WALL_THICKNESS]
    elif wall == "west":
        cx = room.x
        cz = -(room.y + room.depth / 2)
        size = [WALL_THICKNESS, ceiling_height, room.depth]
    elif wall == "east":
        cx = room.x + room.width
        cz = -(room.y + room.depth / 2)
        size = [WALL_THICKNESS, ceiling_height, room.depth]
    else:
        raise ValueError(f"unknown wall {wall}")

    return GeometryPrimitive(
        type="wall",
        roomId=room.id,
        wall=wall,
        position=[cx, level_y + ceiling_height / 2, cz],
        size=size,
        rotation=0.0,
        holes=holes,
    )


def _stair_primitive(s: Stairs, level_y: float, ceiling_height: float) -> GeometryPrimitive:
    cx = s.x + s.width / 2
    cy = s.y + s.depth / 2
    rot_map = {"north": 0.0, "south": 3.14159, "east": 1.5708, "west": -1.5708}
    return GeometryPrimitive(
        type="stair",
        roomId=s.id,
        position=[cx, level_y, -cy],
        size=[s.width, ceiling_height, s.depth],
        rotation=rot_map[s.direction],
    )


def build_geometry(bp: Blueprint) -> Geometry:
    prims: list[GeometryPrimitive] = []
    for fl in bp.floors:
        level_y = _floor_y_offset(fl.level, fl.ceilingHeight)
        for r in fl.rooms:
            prims.append(_floor_primitive(r, level_y))
            prims.append(_ceiling_primitive(r, level_y, fl.ceilingHeight))
            for w in ("north", "south", "east", "west"):
                prims.append(_wall_primitive(r, w, level_y, fl.ceilingHeight))
        for s in fl.stairs:
            prims.append(_stair_primitive(s, level_y, fl.ceilingHeight))
    return Geometry(primitives=prims)
