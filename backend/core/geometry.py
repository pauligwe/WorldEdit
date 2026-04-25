"""Convert validated Blueprint + Site into 3D geometry primitives.

Coord mapping: blueprint (x, y) building-local -> plot-world by adding the
buildingAnchor; then plot-world -> scene (x, height_y, -y_p).
"""
from .world_spec import (
    Blueprint, Room, Stairs, Site, Geometry, GeometryPrimitive
)

WALL_THICKNESS = 0.1
EXTERIOR_WALL_THICKNESS = 0.2
ROOF_THICKNESS = 0.2


def _floor_y_offset(level: int, ceiling_height: float) -> float:
    return level * ceiling_height


def _floor_primitive(room: Room, level_y: float, ax: float, ay: float) -> GeometryPrimitive:
    cx = ax + room.x + room.width / 2
    cy = ay + room.y + room.depth / 2
    return GeometryPrimitive(
        type="floor",
        roomId=room.id,
        position=[cx, level_y, -cy],
        size=[room.width, 0.05, room.depth],
    )


def _ceiling_primitive(room: Room, level_y: float, ceiling_height: float,
                       ax: float, ay: float) -> GeometryPrimitive:
    cx = ax + room.x + room.width / 2
    cy = ay + room.y + room.depth / 2
    return GeometryPrimitive(
        type="ceiling",
        roomId=room.id,
        position=[cx, level_y + ceiling_height - 0.025, -cy],
        size=[room.width, 0.05, room.depth],
    )


def _wall_primitive(room: Room, wall: str, level_y: float, ceiling_height: float,
                    ax: float, ay: float) -> GeometryPrimitive:
    holes: list[dict] = []
    for d in room.doors:
        if d.wall == wall:
            holes.append({"offset": d.offset, "width": d.width, "height": 2.1, "bottom": 0.0})
    for w in room.windows:
        if w.wall == wall:
            holes.append({"offset": w.offset, "width": w.width, "height": w.height, "bottom": w.sill})

    if wall == "north":
        cx = ax + room.x + room.width / 2
        cz = -(ay + room.y + room.depth)
        size = [room.width, ceiling_height, WALL_THICKNESS]
    elif wall == "south":
        cx = ax + room.x + room.width / 2
        cz = -(ay + room.y)
        size = [room.width, ceiling_height, WALL_THICKNESS]
    elif wall == "west":
        cx = ax + room.x
        cz = -(ay + room.y + room.depth / 2)
        size = [WALL_THICKNESS, ceiling_height, room.depth]
    elif wall == "east":
        cx = ax + room.x + room.width
        cz = -(ay + room.y + room.depth / 2)
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


def _stair_primitive(s: Stairs, level_y: float, ceiling_height: float,
                     ax: float, ay: float) -> GeometryPrimitive:
    cx = ax + s.x + s.width / 2
    cy = ay + s.y + s.depth / 2
    rot_map = {"north": 0.0, "south": 3.14159, "east": 1.5708, "west": -1.5708}
    return GeometryPrimitive(
        type="stair",
        roomId=s.id,
        position=[cx, level_y, -cy],
        size=[s.width, ceiling_height, s.depth],
        rotation=rot_map[s.direction],
    )


def _ground_primitive(site: Site) -> GeometryPrimitive:
    p = site.plot
    return GeometryPrimitive(
        type="ground",
        position=[p.width / 2, -0.025, -p.depth / 2],
        size=[p.width, 0.05, p.depth],
    )


def _exterior_walls_for_floor(site: Site, level: int, level_y: float,
                              ceiling_height: float) -> list[GeometryPrimitive]:
    fw, fd = site.buildingFootprint
    ax, ay = site.buildingAnchor
    e = site.entrance

    def hole_for(wall: str) -> list[dict]:
        if level != 0 or wall != e.wall:
            return []
        return [{
            "offset": e.offset,
            "width": e.width,
            "height": e.height,
            "bottom": 0.0,
        }]

    walls: list[GeometryPrimitive] = []
    # south
    walls.append(GeometryPrimitive(
        type="exterior_wall", wall="south",
        position=[ax + fw / 2, level_y + ceiling_height / 2, -ay],
        size=[fw, ceiling_height, EXTERIOR_WALL_THICKNESS],
        holes=hole_for("south"),
    ))
    # north
    walls.append(GeometryPrimitive(
        type="exterior_wall", wall="north",
        position=[ax + fw / 2, level_y + ceiling_height / 2, -(ay + fd)],
        size=[fw, ceiling_height, EXTERIOR_WALL_THICKNESS],
        holes=hole_for("north"),
    ))
    # west
    walls.append(GeometryPrimitive(
        type="exterior_wall", wall="west",
        position=[ax, level_y + ceiling_height / 2, -(ay + fd / 2)],
        size=[EXTERIOR_WALL_THICKNESS, ceiling_height, fd],
        holes=hole_for("west"),
    ))
    # east
    walls.append(GeometryPrimitive(
        type="exterior_wall", wall="east",
        position=[ax + fw, level_y + ceiling_height / 2, -(ay + fd / 2)],
        size=[EXTERIOR_WALL_THICKNESS, ceiling_height, fd],
        holes=hole_for("east"),
    ))
    return walls


def _roof_primitive(site: Site, top_y: float) -> GeometryPrimitive:
    fw, fd = site.buildingFootprint
    ax, ay = site.buildingAnchor
    return GeometryPrimitive(
        type="roof",
        position=[ax + fw / 2, top_y + ROOF_THICKNESS / 2, -(ay + fd / 2)],
        size=[fw + 0.2, ROOF_THICKNESS, fd + 0.2],
    )


def build_geometry(bp: Blueprint, site: Site) -> Geometry:
    prims: list[GeometryPrimitive] = []
    ax, ay = site.buildingAnchor

    prims.append(_ground_primitive(site))

    top_y = 0.0
    for fl in bp.floors:
        level_y = _floor_y_offset(fl.level, fl.ceilingHeight)
        top_y = max(top_y, level_y + fl.ceilingHeight)
        for r in fl.rooms:
            prims.append(_floor_primitive(r, level_y, ax, ay))
            prims.append(_ceiling_primitive(r, level_y, fl.ceilingHeight, ax, ay))
            for w in ("north", "south", "east", "west"):
                prims.append(_wall_primitive(r, w, level_y, fl.ceilingHeight, ax, ay))
        for s in fl.stairs:
            prims.append(_stair_primitive(s, level_y, fl.ceilingHeight, ax, ay))
        prims.extend(_exterior_walls_for_floor(site, fl.level, level_y, fl.ceilingHeight))

    prims.append(_roof_primitive(site, top_y))

    return Geometry(primitives=prims)
