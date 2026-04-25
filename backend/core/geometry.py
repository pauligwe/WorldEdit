"""Convert validated Blueprint + Site into 3D geometry primitives.

Coord mapping: blueprint (x, y) building-local -> plot-world by adding the
buildingAnchor; then plot-world -> scene (x, height_y, -y_p).
"""
from typing import Optional

from .world_spec import (
    Blueprint, Geometry, GeometryPrimitive, Room, Site, Stairs,
)

WALL_THICKNESS = 0.1
EXTERIOR_WALL_THICKNESS = 0.2
ROOF_THICKNESS = 0.2
SLAB_THICKNESS = 0.05
STAIR_HOLE_PAD = 0.1  # carve a slightly-bigger hole than the stair for clearance


def _floor_y_offset(level: int, ceiling_height: float) -> float:
    return level * ceiling_height


def _slab_with_hole(
    prim_type: str,
    room: Room,
    slab_y: float,
    ax: float, ay: float,
    hole: Optional[tuple[float, float, float, float]],
) -> list[GeometryPrimitive]:
    """Emit one or more box primitives covering the room's footprint at y=slab_y.

    If `hole` is provided as building-local (x0, y0, x1, y1), split the slab
    into up to 4 L-shaped pieces that surround the hole. Hole is clipped to
    the room bounds first; if the clipped hole is empty, a single full slab
    is returned.
    """
    rx0, ry0 = room.x, room.y
    rx1, ry1 = room.x + room.width, room.y + room.depth

    if hole is None:
        cx = ax + (rx0 + rx1) / 2
        cy = ay + (ry0 + ry1) / 2
        return [GeometryPrimitive(
            type=prim_type,
            roomId=room.id,
            position=[cx, slab_y, -cy],
            size=[room.width, SLAB_THICKNESS, room.depth],
        )]

    hx0, hy0, hx1, hy1 = hole
    hx0 = max(hx0, rx0)
    hy0 = max(hy0, ry0)
    hx1 = min(hx1, rx1)
    hy1 = min(hy1, ry1)
    if hx1 - hx0 <= 1e-6 or hy1 - hy0 <= 1e-6:
        # Hole doesn't actually intersect the room.
        cx = ax + (rx0 + rx1) / 2
        cy = ay + (ry0 + ry1) / 2
        return [GeometryPrimitive(
            type=prim_type,
            roomId=room.id,
            position=[cx, slab_y, -cy],
            size=[room.width, SLAB_THICKNESS, room.depth],
        )]

    out: list[GeometryPrimitive] = []

    def emit(x0: float, y0: float, x1: float, y1: float) -> None:
        if x1 - x0 <= 1e-6 or y1 - y0 <= 1e-6:
            return
        cx = ax + (x0 + x1) / 2
        cy = ay + (y0 + y1) / 2
        out.append(GeometryPrimitive(
            type=prim_type,
            roomId=room.id,
            position=[cx, slab_y, -cy],
            size=[x1 - x0, SLAB_THICKNESS, y1 - y0],
        ))

    # South strip below the hole (full width).
    emit(rx0, ry0, rx1, hy0)
    # North strip above the hole (full width).
    emit(rx0, hy1, rx1, ry1)
    # West strip beside the hole (only between hole's y bounds).
    emit(rx0, hy0, hx0, hy1)
    # East strip beside the hole.
    emit(hx1, hy0, rx1, hy1)
    return out


def _floor_primitives(
    room: Room,
    level_y: float,
    ax: float, ay: float,
    hole: Optional[tuple[float, float, float, float]],
) -> list[GeometryPrimitive]:
    return _slab_with_hole("floor", room, level_y, ax, ay, hole)


def _ceiling_primitives(
    room: Room,
    level_y: float,
    ceiling_height: float,
    ax: float, ay: float,
    hole: Optional[tuple[float, float, float, float]],
) -> list[GeometryPrimitive]:
    slab_y = level_y + ceiling_height - SLAB_THICKNESS / 2
    return _slab_with_hole("ceiling", room, slab_y, ax, ay, hole)


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


def _hole_for_room(
    room: Room, stairs: list[Stairs], directions: tuple[str, ...],
) -> Optional[tuple[float, float, float, float]]:
    """Find the first stair (matching one of `directions`) that overlaps this
    room and return its building-local (x0, y0, x1, y1) bounds, padded for
    clearance. Returns None if no matching stair sits inside this room.
    """
    for s in stairs:
        if s.direction not in directions:
            continue
        sx0 = s.x - STAIR_HOLE_PAD
        sy0 = s.y - STAIR_HOLE_PAD
        sx1 = s.x + s.width + STAIR_HOLE_PAD
        sy1 = s.y + s.depth + STAIR_HOLE_PAD
        # Test stair center against room bounds.
        scx = s.x + s.width / 2
        scy = s.y + s.depth / 2
        if (room.x - 1e-6 <= scx <= room.x + room.width + 1e-6 and
                room.y - 1e-6 <= scy <= room.y + room.depth + 1e-6):
            return (sx0, sy0, sx1, sy1)
    return None


def build_geometry(bp: Blueprint, site: Site) -> Geometry:
    prims: list[GeometryPrimitive] = []
    ax, ay = site.buildingAnchor

    prims.append(_ground_primitive(site))

    top_y = 0.0
    for fl in bp.floors:
        level_y = _floor_y_offset(fl.level, fl.ceilingHeight)
        top_y = max(top_y, level_y + fl.ceilingHeight)

        # Up-stairs on this floor punch a hole in this floor's ceiling.
        up_stairs = [s for s in fl.stairs if s.direction == "north"]
        # And a hole in the FLOOR slab of the level above (where this stair lands).
        # We carve the hole on the upper level using its own down-stairs entry
        # (every upper level emits a corresponding "south" stair at the same xy).

        # Down-stairs on this floor mean there's a stair-shaft from below;
        # the floor slab here gets a hole over it.
        down_stairs = [s for s in fl.stairs if s.direction == "south"]

        for r in fl.rooms:
            ceiling_hole = _hole_for_room(r, up_stairs, ("north",))
            floor_hole = _hole_for_room(r, down_stairs, ("south",))
            prims.extend(_floor_primitives(r, level_y, ax, ay, floor_hole))
            prims.extend(_ceiling_primitives(
                r, level_y, fl.ceilingHeight, ax, ay, ceiling_hole,
            ))
            for w in ("north", "south", "east", "west"):
                prims.append(_wall_primitive(r, w, level_y, fl.ceilingHeight, ax, ay))
        for s in fl.stairs:
            prims.append(_stair_primitive(s, level_y, fl.ceilingHeight, ax, ay))
        prims.extend(_exterior_walls_for_floor(site, fl.level, level_y, fl.ceilingHeight))

    prims.append(_roof_primitive(site, top_y))

    return Geometry(primitives=prims)
