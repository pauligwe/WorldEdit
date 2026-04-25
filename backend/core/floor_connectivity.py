from collections import deque
from typing import Optional

from .world_spec import Blueprint, Door, Floor, Room, Site, Stairs

EPS = 1e-6


def _door_interval(room: Room, door: Door) -> tuple[float, float]:
    if door.wall in ("north", "south"):
        base = room.x
    else:
        base = room.y
    return base + door.offset, base + door.offset + door.width


def _shared_edge_y(a: Room, b: Room) -> Optional[tuple[float, float]]:
    lo = max(a.y, b.y)
    hi = min(a.y + a.depth, b.y + b.depth)
    if hi - lo > EPS:
        return lo, hi
    return None


def _shared_edge_x(a: Room, b: Room) -> Optional[tuple[float, float]]:
    lo = max(a.x, b.x)
    hi = min(a.x + a.width, b.x + b.width)
    if hi - lo > EPS:
        return lo, hi
    return None


def _interval_within(inner: tuple[float, float], outer: tuple[float, float]) -> bool:
    return inner[0] >= outer[0] - EPS and inner[1] <= outer[1] + EPS


def _door_on_wall_in_segment(
    room: Room, wall: str, segment: tuple[float, float]
) -> bool:
    for d in room.doors:
        if d.wall != wall:
            continue
        if _interval_within(_door_interval(room, d), segment):
            return True
    return False


def _rooms_connected(a: Room, b: Room) -> bool:
    # A east <-> B west
    if abs((a.x + a.width) - b.x) < EPS:
        seg = _shared_edge_y(a, b)
        if seg is not None:
            if _door_on_wall_in_segment(a, "east", seg) or _door_on_wall_in_segment(b, "west", seg):
                return True
    # A west <-> B east
    if abs(a.x - (b.x + b.width)) < EPS:
        seg = _shared_edge_y(a, b)
        if seg is not None:
            if _door_on_wall_in_segment(a, "west", seg) or _door_on_wall_in_segment(b, "east", seg):
                return True
    # A north <-> B south
    if abs((a.y + a.depth) - b.y) < EPS:
        seg = _shared_edge_x(a, b)
        if seg is not None:
            if _door_on_wall_in_segment(a, "north", seg) or _door_on_wall_in_segment(b, "south", seg):
                return True
    # A south <-> B north
    if abs(a.y - (b.y + b.depth)) < EPS:
        seg = _shared_edge_x(a, b)
        if seg is not None:
            if _door_on_wall_in_segment(a, "south", seg) or _door_on_wall_in_segment(b, "north", seg):
                return True
    return False


def _build_adjacency(rooms: list[Room]) -> dict[str, list[str]]:
    adj: dict[str, list[str]] = {r.id: [] for r in rooms}
    for i, a in enumerate(rooms):
        for b in rooms[i + 1:]:
            if _rooms_connected(a, b):
                adj[a.id].append(b.id)
                adj[b.id].append(a.id)
    return adj


def _bfs(adj: dict[str, list[str]], starts: list[str]) -> set[str]:
    seen: set[str] = set()
    q: deque[str] = deque()
    for s in starts:
        if s not in seen:
            seen.add(s)
            q.append(s)
    while q:
        cur = q.popleft()
        for nxt in adj.get(cur, []):
            if nxt not in seen:
                seen.add(nxt)
                q.append(nxt)
    return seen


def _entrance_rooms(floor: Floor, site: Site) -> list[Room]:
    e = site.entrance
    fw, fd = site.buildingFootprint
    matches: list[Room] = []
    for r in floor.rooms:
        on_edge = (
            (e.wall == "south" and abs(r.y) < EPS)
            or (e.wall == "north" and abs((r.y + r.depth) - fd) < EPS)
            or (e.wall == "west" and abs(r.x) < EPS)
            or (e.wall == "east" and abs((r.x + r.width) - fw) < EPS)
        )
        if not on_edge:
            continue
        for d in r.doors:
            if d.wall != e.wall:
                continue
            lo, hi = _door_interval(r, d)
            if lo - EPS <= e.offset <= hi + EPS:
                matches.append(r)
                break
    return matches


def _stair_room(rooms: list[Room], stair: Stairs) -> Optional[Room]:
    cx = stair.x + stair.width / 2
    cy = stair.y + stair.depth / 2
    for r in rooms:
        if (
            r.x - EPS <= cx <= r.x + r.width + EPS
            and r.y - EPS <= cy <= r.y + r.depth + EPS
        ):
            return r
    return None


def validate_floor_connectivity(blueprint: Blueprint, site: Site) -> list[str]:
    """Returns a list of error strings. Empty list = valid."""
    errors: list[str] = []
    if not blueprint.floors:
        return errors

    floors_by_level: dict[int, Floor] = {f.level: f for f in blueprint.floors}

    ground = floors_by_level.get(0)
    if ground is None:
        return errors

    entrance_rooms = _entrance_rooms(ground, site)
    if not entrance_rooms:
        errors.append(
            f"floor 0: no room has a {site.entrance.wall} door covering "
            f"site entrance offset {site.entrance.offset}"
        )

    reachable_by_level: dict[int, set[str]] = {}
    ground_adj = _build_adjacency(ground.rooms)
    ground_reachable = _bfs(ground_adj, [r.id for r in entrance_rooms])
    reachable_by_level[0] = ground_reachable

    for r in ground.rooms:
        if r.id not in ground_reachable:
            errors.append(f"floor 0: room {r.id} is not reachable from the entrance")

    levels = sorted(floors_by_level.keys())
    for level in levels:
        next_level = level + 1
        if next_level not in floors_by_level:
            continue
        cur_floor = floors_by_level[level]
        nxt_floor = floors_by_level[next_level]

        if not cur_floor.stairs:
            errors.append(
                f"floor {level} has no stair leading to floor {next_level}"
            )
            reachable_by_level[next_level] = set()
            continue

        nxt_stairs = nxt_floor.stairs
        landing_room_ids: list[str] = []
        for s in cur_floor.stairs:
            mate = next(
                (
                    t for t in nxt_stairs
                    if abs(t.x - s.x) < 0.01 and abs(t.y - s.y) < 0.01
                ),
                None,
            )
            if mate is None:
                errors.append(
                    f"stair at ({s.x}, {s.y}) on floor {level} has no aligned "
                    f"stair on floor {next_level}"
                )
                continue
            landing = _stair_room(nxt_floor.rooms, mate)
            if landing is None:
                errors.append(
                    f"floor {next_level}: stair at ({mate.x}, {mate.y}) is not "
                    f"inside any room"
                )
                continue
            if level in reachable_by_level:
                origin = _stair_room(cur_floor.rooms, s)
                if origin is None or origin.id not in reachable_by_level[level]:
                    continue
            landing_room_ids.append(landing.id)

        for s in nxt_stairs:
            mate = next(
                (
                    t for t in cur_floor.stairs
                    if abs(t.x - s.x) < 0.01 and abs(t.y - s.y) < 0.01
                ),
                None,
            )
            if mate is None:
                errors.append(
                    f"stair at ({s.x}, {s.y}) on floor {next_level} has no "
                    f"aligned stair on floor {level}"
                )

        nxt_adj = _build_adjacency(nxt_floor.rooms)
        nxt_reachable = _bfs(nxt_adj, landing_room_ids)
        reachable_by_level[next_level] = nxt_reachable

        if not landing_room_ids:
            for r in nxt_floor.rooms:
                errors.append(
                    f"floor {next_level}: room {r.id} is not reachable from "
                    f"any stair landing"
                )
        else:
            for r in nxt_floor.rooms:
                if r.id not in nxt_reachable:
                    errors.append(
                        f"floor {next_level}: room {r.id} is not reachable "
                        f"from any stair landing"
                    )

    return errors
