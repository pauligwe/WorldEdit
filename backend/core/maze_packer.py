"""Maze / spanning-tree floor-plan packer.

Grows rooms outward from a single seed (the entrance on level 0, or wherever
we land on upper floors). Each new room is placed flush against an existing
room's wall and only accepted if it shares >= 1.0m of wall with that parent.
After placement, the shared wall between every pair of adjacent rooms gets a
matching pair of Door objects (one on each room's wall, both centered on the
overlap), so the geometry builder cuts a doorway in both walls.

Result: every room is reachable from the seed by construction AND the
generated geometry has visible doorways between connected rooms.

Returns ``(Floor, stair_xy)`` -- the caller uses ``stair_xy`` to align stairs
across levels.
"""

from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass
from typing import Optional

from .room_library import ROOM_LIBRARY, RoomTemplate
from .world_spec import Door, Floor, Room, Stairs


_DOOR_WIDTH = 0.9
_DOOR_MARGIN = 0.2  # min clearance from each end of the shared overlap


_GRID = 0.5
_MIN_SHARED_WALL = 1.0
_MAX_ATTEMPTS_PER_TEMPLATE = 16
_EPS = 1e-6


def _snap(v: float, grid: float = _GRID) -> float:
    return round(v / grid) * grid


@dataclass
class _Rect:
    x: float
    y: float
    width: float
    depth: float

    @property
    def x2(self) -> float:
        return self.x + self.width

    @property
    def y2(self) -> float:
        return self.y + self.depth


def _rects_overlap(a: _Rect, b: _Rect) -> bool:
    if a.x2 <= b.x + _EPS or b.x2 <= a.x + _EPS:
        return False
    if a.y2 <= b.y + _EPS or b.y2 <= a.y + _EPS:
        return False
    return True


def _inside_footprint(r: _Rect, fw: float, fd: float) -> bool:
    return (
        r.x >= -_EPS
        and r.y >= -_EPS
        and r.x2 <= fw + _EPS
        and r.y2 <= fd + _EPS
    )


def _shared_wall_length(parent: _Rect, child: _Rect, wall: str) -> float:
    """Length of overlap on the wall of `parent` that `child` is flush against.
    Returns 0 if the two rects are not flush on that wall."""
    if wall == "north":
        if abs(parent.y2 - child.y) > _EPS:
            return 0.0
        return max(0.0, min(parent.x2, child.x2) - max(parent.x, child.x))
    if wall == "south":
        if abs(parent.y - child.y2) > _EPS:
            return 0.0
        return max(0.0, min(parent.x2, child.x2) - max(parent.x, child.x))
    if wall == "east":
        if abs(parent.x2 - child.x) > _EPS:
            return 0.0
        return max(0.0, min(parent.y2, child.y2) - max(parent.y, child.y))
    if wall == "west":
        if abs(parent.x - child.x2) > _EPS:
            return 0.0
        return max(0.0, min(parent.y2, child.y2) - max(parent.y, child.y))
    return 0.0


def _candidate_rect(
    parent: _Rect, wall: str, w: float, d: float, slide: float
) -> _Rect:
    """Build a candidate placed flush against `parent`'s `wall`. `slide` shifts
    the candidate along the shared edge so we don't always center."""
    if wall == "north":
        cx = parent.x + (parent.width - w) / 2.0 + slide
        return _Rect(_snap(cx), _snap(parent.y2), _snap(w), _snap(d))
    if wall == "south":
        cx = parent.x + (parent.width - w) / 2.0 + slide
        return _Rect(_snap(cx), _snap(parent.y - d), _snap(w), _snap(d))
    if wall == "east":
        cy = parent.y + (parent.depth - d) / 2.0 + slide
        return _Rect(_snap(parent.x2), _snap(cy), _snap(w), _snap(d))
    # west
    cy = parent.y + (parent.depth - d) / 2.0 + slide
    return _Rect(_snap(parent.x - w), _snap(cy), _snap(w), _snap(d))


def _try_place(
    parent_rects: list[_Rect],
    placed: list[_Rect],
    fw: float,
    fd: float,
    w: float,
    d: float,
    rng: random.Random,
) -> Optional[tuple[_Rect, int]]:
    """Try to place a (w, d) rectangle adjacent to some parent. Returns
    (rect, parent_index) on success or None."""
    walls = ["north", "south", "east", "west"]
    for _ in range(_MAX_ATTEMPTS_PER_TEMPLATE):
        idx = rng.randrange(len(parent_rects))
        parent = parent_rects[idx]
        wall = rng.choice(walls)
        # Slide along the shared edge so adjacent rooms don't all stack centered.
        if wall in ("north", "south"):
            max_slide = max(0.0, (parent.width + w) / 2.0 - _MIN_SHARED_WALL)
        else:
            max_slide = max(0.0, (parent.depth + d) / 2.0 - _MIN_SHARED_WALL)
        slide = _snap(rng.uniform(-max_slide, max_slide))
        cand = _candidate_rect(parent, wall, w, d, slide)

        if cand.width <= 0 or cand.depth <= 0:
            continue
        if not _inside_footprint(cand, fw, fd):
            continue
        if any(_rects_overlap(cand, p) for p in placed):
            continue
        if _shared_wall_length(parent, cand, wall) + _EPS < _MIN_SHARED_WALL:
            continue
        return cand, idx
    return None


def _seed_rect_level0(
    tpl: RoomTemplate, fw: float, fd: float, entrance_offset: Optional[float]
) -> _Rect:
    w = min(tpl.width, fw)
    d = min(tpl.depth, fd)
    if entrance_offset is not None:
        x = entrance_offset - w / 2.0
    else:
        x = (fw - w) / 2.0
    x = max(0.0, min(fw - w, x))
    return _Rect(_snap(x), 0.0, _snap(w), _snap(d))


def _pick_seed_template(template_names: list[str]) -> tuple[str, RoomTemplate]:
    """Find the first lobby/foyer/entry-like template in the list, falling
    back to the first known template, then `lobby_modern`."""
    for name in template_names:
        tpl = ROOM_LIBRARY.get(name)
        if tpl is None:
            continue
        if (
            tpl.type in ("lobby", "foyer", "entry")
            or "lobby" in name
            or "foyer" in name
            or "entry" in name
        ):
            return name, tpl
    for name in template_names:
        tpl = ROOM_LIBRARY.get(name)
        if tpl is not None:
            return name, tpl
    return "lobby_modern", ROOM_LIBRARY["lobby_modern"]


def _derive_doors(rects: list[_Rect]) -> list[list[Door]]:
    """For every pair of rects sharing >= _MIN_SHARED_WALL of wall, emit a
    matching pair of Door objects -- one on each room's facing wall, both
    centered on the overlap. Returns a list parallel to `rects`, where each
    entry is the list of doors for that room.

    Door offset is the center position along the wall, in the room's local
    coordinate frame (matching geometry._wall_primitive's expectations).
    """
    doors: list[list[Door]] = [[] for _ in rects]
    n = len(rects)
    for i in range(n):
        for j in range(i + 1, n):
            a, b = rects[i], rects[j]
            # north/south: one rect's y2 == other's y
            if abs(a.y2 - b.y) <= _EPS or abs(b.y2 - a.y) <= _EPS:
                if abs(a.y2 - b.y) <= _EPS:
                    south_room, north_room, south_idx, north_idx = a, b, i, j
                else:
                    south_room, north_room, south_idx, north_idx = b, a, j, i
                lo = max(south_room.x, north_room.x)
                hi = min(south_room.x2, north_room.x2)
                if hi - lo + _EPS < _MIN_SHARED_WALL:
                    continue
                center_x = (lo + hi) / 2.0
                door_w = max(0.6, min(_DOOR_WIDTH, hi - lo - _DOOR_MARGIN))
                # south_room's NORTH wall has the door; north_room's SOUTH wall does too.
                doors[south_idx].append(Door(
                    wall="north",
                    offset=center_x - south_room.x,
                    width=door_w,
                ))
                doors[north_idx].append(Door(
                    wall="south",
                    offset=center_x - north_room.x,
                    width=door_w,
                ))
                continue
            # east/west: one rect's x2 == other's x
            if abs(a.x2 - b.x) <= _EPS or abs(b.x2 - a.x) <= _EPS:
                if abs(a.x2 - b.x) <= _EPS:
                    west_room, east_room, west_idx, east_idx = a, b, i, j
                else:
                    west_room, east_room, west_idx, east_idx = b, a, j, i
                lo = max(west_room.y, east_room.y)
                hi = min(west_room.y2, east_room.y2)
                if hi - lo + _EPS < _MIN_SHARED_WALL:
                    continue
                center_y = (lo + hi) / 2.0
                door_w = max(0.6, min(_DOOR_WIDTH, hi - lo - _DOOR_MARGIN))
                doors[west_idx].append(Door(
                    wall="east",
                    offset=center_y - west_room.y,
                    width=door_w,
                ))
                doors[east_idx].append(Door(
                    wall="west",
                    offset=center_y - east_room.y,
                    width=door_w,
                ))
    return doors


def _bfs_distances(
    rects: list[_Rect], adj_min: float = _MIN_SHARED_WALL
) -> list[int]:
    """BFS distances from index 0 over rects connected by shared walls."""
    n = len(rects)
    adj: list[list[int]] = [[] for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            shared = max(
                _shared_wall_length(rects[i], rects[j], w)
                for w in ("north", "south", "east", "west")
            )
            if shared + _EPS >= adj_min:
                adj[i].append(j)
                adj[j].append(i)
    dist = [-1] * n
    dist[0] = 0
    q = deque([0])
    while q:
        cur = q.popleft()
        for nxt in adj[cur]:
            if dist[nxt] < 0:
                dist[nxt] = dist[cur] + 1
                q.append(nxt)
    return dist


def maze_pack_floor(
    template_names: list[str],
    footprint: tuple[float, float],
    level: int,
    ceiling_height: float = 3.0,
    stair_position: Optional[tuple[float, float, float, float]] = None,
    entrance_offset: Optional[float] = None,
    seed: Optional[int] = None,
    is_top_floor: bool = False,
) -> tuple[Floor, Optional[tuple[float, float]]]:
    """Grow a floor plan outward from a single seed room.

    On level 0, if stairs are requested, they're placed in the BFS-furthest
    room from the entrance. On levels >= 1, stairs are placed at the EXACT
    (x, y) passed in via `stair_position` -- the upper-floor seed landing is
    sized to contain the stair, so this guarantees vertical alignment across
    floors.

    Returns `(Floor, stair_xy)`. `stair_xy` is None if the floor has no stairs.
    """
    fw, fd = footprint
    rng = random.Random(seed if seed is not None else level)

    # ------------------------------------------------------------------ #
    # 1. Seed
    # ------------------------------------------------------------------ #
    placed_rects: list[_Rect] = []
    placed_meta: list[tuple[str, str]] = []  # (room_id, type) per rect

    remaining_names = list(template_names)
    if level == 0:
        seed_name, seed_tpl = _pick_seed_template(remaining_names)
        if seed_name in remaining_names:
            remaining_names.remove(seed_name)
        seed_rect = _seed_rect_level0(seed_tpl, fw, fd, entrance_offset)
        placed_rects.append(seed_rect)
        placed_meta.append((f"{seed_tpl.name}_{level}_0", seed_tpl.type))
    else:
        # Upper floor: seed is a 2x2 stairwell-sized landing room. Position
        # honors an advisory stair_position if given, else center-snap.
        sw = sd = 2.0
        if stair_position is not None:
            sx, sy, _, _ = stair_position
            sx = max(0.0, min(fw - sw, _snap(sx)))
            sy = max(0.0, min(fd - sd, _snap(sy)))
        else:
            sx = _snap((fw - sw) / 2.0)
            sy = _snap((fd - sd) / 2.0)
        # Promote to a usable landing room: snap to a real template if we can
        # find one that fits, else just use a 4x4 lobby-sized footprint.
        landing_w = 4.0
        landing_d = 4.0
        landing_x = max(0.0, min(fw - landing_w, _snap(sx - 1.0)))
        landing_y = max(0.0, min(fd - landing_d, _snap(sy - 1.0)))
        landing = _Rect(landing_x, landing_y, landing_w, landing_d)
        placed_rects.append(landing)
        placed_meta.append((f"landing_{level}_0", "lobby"))

    # ------------------------------------------------------------------ #
    # 2. Expansion loop
    # ------------------------------------------------------------------ #
    for slot_index, name in enumerate(remaining_names, start=1):
        tpl = ROOM_LIBRARY.get(name)
        if tpl is None:
            print(f"[maze_packer] skipping unknown template: {name}")
            continue

        # Try the template at its native orientation, then swapped (rotated 90).
        orientations = [(tpl.width, tpl.depth), (tpl.depth, tpl.width)]
        rng.shuffle(orientations)

        result = None
        for w, d in orientations:
            result = _try_place(placed_rects, placed_rects, fw, fd, w, d, rng)
            if result is not None:
                break

        if result is None:
            continue

        cand, _parent_idx = result
        placed_rects.append(cand)
        placed_meta.append((f"{tpl.name}_{level}_{slot_index}", tpl.type))

    # ------------------------------------------------------------------ #
    # 3. Build Room objects. Each pair of adjacent rooms gets a matching
    # pair of Doors (one on each wall) so the geometry builder can punch a
    # doorway through both walls.
    # ------------------------------------------------------------------ #
    door_lists = _derive_doors(placed_rects)
    rooms: list[Room] = []
    for rect, (rid, rtype), drs in zip(placed_rects, placed_meta, door_lists):
        rooms.append(
            Room(
                id=rid,
                type=rtype,
                x=rect.x,
                y=rect.y,
                width=rect.width,
                depth=rect.depth,
                doors=drs,
                windows=[],
            )
        )

    # ------------------------------------------------------------------ #
    # 4. Stairs: pick the room furthest from the entrance, drop a 2x2 inside.
    # ------------------------------------------------------------------ #
    stairs_list: list[Stairs] = []
    stair_xy: Optional[tuple[float, float]] = None

    # Caller drives stair emission. On level 0 they pass stair_position as a
    # sentinel to mean "emit upward stairs". On levels >= 1 they pass the
    # actual (x, y) of the stair from the floor below, which we MUST honor so
    # stairs align vertically. is_top_floor suppresses the up-stair on the
    # highest level.
    emit_up_stairs = stair_position is not None and not is_top_floor
    emit_down_stairs = level > 0  # always pair the down-stair on upper floors

    if rooms and (emit_up_stairs or emit_down_stairs):
        sw = sd = 2.0

        if level == 0:
            # Pick BFS-furthest room from the entrance, drop a 2x2 inside it.
            dists = _bfs_distances(placed_rects)
            best_idx = max(
                range(len(placed_rects)),
                key=lambda i: (dists[i] if dists[i] >= 0 else -1),
            )
            target = placed_rects[best_idx]
            sx = _snap(target.x + (target.width - sw) / 2.0)
            sy = _snap(target.y + (target.depth - sd) / 2.0)
            sx = max(target.x, min(target.x2 - sw, sx))
            sy = max(target.y, min(target.y2 - sd, sy))
        else:
            # Honor the incoming stair_position EXACTLY -- the landing room
            # at index 0 was sized to contain this stair.
            assert stair_position is not None, (
                "upper floor must receive stair_position to align stairs"
            )
            sx_in, sy_in, _, _ = stair_position
            sx = _snap(sx_in)
            sy = _snap(sy_in)
            # Clamp into footprint (the landing already covers this region).
            sx = max(0.0, min(fw - sw, sx))
            sy = max(0.0, min(fd - sd, sy))

        # Down-stair (on every upper floor).
        if emit_down_stairs:
            stairs_list.append(
                Stairs(
                    id=f"stair_{level}_down",
                    x=_snap(sx),
                    y=_snap(sy),
                    width=sw,
                    depth=sd,
                    direction="south",
                    toLevel=level - 1,
                )
            )

        # Up-stair (on level 0 and intermediate floors).
        if emit_up_stairs:
            stairs_list.append(
                Stairs(
                    id=f"stair_{level}_up",
                    x=_snap(sx),
                    y=_snap(sy),
                    width=sw,
                    depth=sd,
                    direction="north",
                    toLevel=level + 1,
                )
            )

        stair_xy = (_snap(sx), _snap(sy))

    floor = Floor(
        level=level,
        ceilingHeight=ceiling_height,
        rooms=rooms,
        stairs=stairs_list,
    )
    return floor, stair_xy
