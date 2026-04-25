from .world_spec import Blueprint, Room, FurnitureItem

DOOR_CLEARANCE = 0.5  # meters in front of door must be empty


def _room_for(items_room_id: str, bp: Blueprint) -> Room | None:
    for fl in bp.floors:
        for r in fl.rooms:
            if r.id == items_room_id:
                return r
    return None


def _aabb_in_blueprint(item: FurnitureItem) -> tuple[float, float, float, float]:
    """Return (x_min, y_min, x_max, y_max) in blueprint top-down coords.

    item.position is in scene coords [scene_x, scene_y, scene_z];
    blueprint x = scene_x; blueprint y = -scene_z.
    """
    cx = item.position[0]
    cy = -item.position[2]
    half_w = item.size[0] / 2
    half_d = item.size[2] / 2
    return (cx - half_w, cy - half_d, cx + half_w, cy + half_d)


def _fits_in_room(item: FurnitureItem, room: Room) -> bool:
    x0, y0, x1, y1 = _aabb_in_blueprint(item)
    return x0 >= room.x and y0 >= room.y and x1 <= room.x + room.width and y1 <= room.y + room.depth


def _overlaps(a: FurnitureItem, b: FurnitureItem) -> bool:
    ax0, ay0, ax1, ay1 = _aabb_in_blueprint(a)
    bx0, by0, bx1, by1 = _aabb_in_blueprint(b)
    return not (ax1 <= bx0 or bx1 <= ax0 or ay1 <= by0 or by1 <= ay0)


def _intrudes_doorway(item: FurnitureItem, room: Room) -> bool:
    x0, y0, x1, y1 = _aabb_in_blueprint(item)
    for d in room.doors:
        if d.wall == "south":
            dx0 = room.x + d.offset - d.width / 2
            dx1 = room.x + d.offset + d.width / 2
            dy0 = room.y
            dy1 = room.y + DOOR_CLEARANCE
        elif d.wall == "north":
            dx0 = room.x + d.offset - d.width / 2
            dx1 = room.x + d.offset + d.width / 2
            dy0 = room.y + room.depth - DOOR_CLEARANCE
            dy1 = room.y + room.depth
        elif d.wall == "west":
            dx0 = room.x
            dx1 = room.x + DOOR_CLEARANCE
            dy0 = room.y + d.offset - d.width / 2
            dy1 = room.y + d.offset + d.width / 2
        else:  # east
            dx0 = room.x + room.width - DOOR_CLEARANCE
            dx1 = room.x + room.width
            dy0 = room.y + d.offset - d.width / 2
            dy1 = room.y + d.offset + d.width / 2
        if not (x1 <= dx0 or dx1 <= x0 or y1 <= dy0 or dy1 <= y0):
            return True
    return False


def _area(item: FurnitureItem) -> float:
    return item.size[0] * item.size[2]


def validate_and_fix_placements(items: list[FurnitureItem], bp: Blueprint) -> list[FurnitureItem]:
    kept: list[FurnitureItem] = []
    sorted_items = sorted(items, key=_area, reverse=True)  # bigger first wins overlap
    for item in sorted_items:
        room = _room_for(item.roomId, bp)
        if room is None:
            continue
        if not _fits_in_room(item, room):
            continue
        if _intrudes_doorway(item, room):
            continue
        if any(_overlaps(item, k) for k in kept):
            continue
        kept.append(item)
    return kept
