"""BSP-style floor-plan packer.

Subdivides a building footprint into binary-space-partition leaves and fits
hand-designed RoomTemplates into each leaf. Pre-reserves a lobby on level 0
(centered along the south edge so the entrance lands on the building front)
and an optional stairwell rectangle. Remaining templates are matched into
BSP leaves greedily (largest unplaced template that fits, center-placed).

This is a drop-in alternative to ``floor_packer.pack_floor_plan`` with the
same template-name -> Floor signature plus a stairwell hook.

Determinism: layout is reproducible per-level via ``random.Random(level)``.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Optional

from .room_library import ROOM_LIBRARY, RoomTemplate
from .world_spec import Door, Floor, Room, Stairs


# --------------------------------------------------------------------------- #
# Internal rectangle / BSP helpers
# --------------------------------------------------------------------------- #

@dataclass
class _Rect:
    """Axis-aligned rectangle. (x, y) is the SW corner; width spans +x,
    depth spans +y."""
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

    def overlaps(self, other: "_Rect", eps: float = 1e-6) -> bool:
        return not (
            self.x2 <= other.x + eps
            or other.x2 <= self.x + eps
            or self.y2 <= other.y + eps
            or other.y2 <= self.y + eps
        )


_MIN_LEAF_SIDE = 3.0  # below this we stop subdividing
_GRID = 0.5  # Blueprint grid_size; we snap room positions/sizes to this.


def _snap(v: float, grid: float = _GRID) -> float:
    return round(v / grid) * grid


def _rect_minus(rect: _Rect, hole: _Rect) -> list[_Rect]:
    """Return up to four rectangles covering ``rect`` minus ``hole``.

    Used to carve fixed regions (lobby, stairwell) out of the working area
    before BSP. Pieces with zero/negative size are dropped.
    """
    if not rect.overlaps(hole):
        return [rect]

    pieces: list[_Rect] = []
    # Clip the hole to the rect so we never produce negative sizes.
    hx1 = max(rect.x, hole.x)
    hy1 = max(rect.y, hole.y)
    hx2 = min(rect.x2, hole.x2)
    hy2 = min(rect.y2, hole.y2)

    # South strip (below hole)
    if hy1 - rect.y > 1e-6:
        pieces.append(_Rect(rect.x, rect.y, rect.width, hy1 - rect.y))
    # North strip (above hole)
    if rect.y2 - hy2 > 1e-6:
        pieces.append(_Rect(rect.x, hy2, rect.width, rect.y2 - hy2))
    # West strip (left of hole, between hy1..hy2)
    if hx1 - rect.x > 1e-6:
        pieces.append(_Rect(rect.x, hy1, hx1 - rect.x, hy2 - hy1))
    # East strip (right of hole, between hy1..hy2)
    if rect.x2 - hx2 > 1e-6:
        pieces.append(_Rect(hx2, hy1, rect.x2 - hx2, hy2 - hy1))

    # Filter out degenerate (eps-thin) pieces
    return [p for p in pieces if p.width > 1e-6 and p.depth > 1e-6]


def _bsp_subdivide(
    rect: _Rect,
    rng: random.Random,
    target_leaf_size: float,
) -> list[_Rect]:
    """Recursively subdivide ``rect`` until each leaf is at most
    ``target_leaf_size`` on each side, or further splits would create a
    sub-rect smaller than ``_MIN_LEAF_SIDE``. Splits are along whichever
    axis is longer; the offset is in the 30%..70% band."""
    leaves: list[_Rect] = []
    stack: list[_Rect] = [rect]

    while stack:
        r = stack.pop()
        # Stop subdividing if the leaf is small enough overall.
        if r.width <= target_leaf_size and r.depth <= target_leaf_size:
            leaves.append(r)
            continue

        split_vertical = r.width >= r.depth  # vertical = split along x
        # If splitting an axis would not yield two big-enough sides, fall
        # back to the other axis (or stop).
        can_split_v = r.width >= 2 * _MIN_LEAF_SIDE
        can_split_h = r.depth >= 2 * _MIN_LEAF_SIDE

        if split_vertical and not can_split_v and can_split_h:
            split_vertical = False
        elif (not split_vertical) and not can_split_h and can_split_v:
            split_vertical = True

        if split_vertical and can_split_v:
            lo = max(_MIN_LEAF_SIDE, 0.3 * r.width)
            hi = min(r.width - _MIN_LEAF_SIDE, 0.7 * r.width)
            if hi <= lo:
                leaves.append(r)
                continue
            split = _snap(rng.uniform(lo, hi))
            split = max(_MIN_LEAF_SIDE, min(r.width - _MIN_LEAF_SIDE, split))
            left = _Rect(r.x, r.y, split, r.depth)
            right = _Rect(r.x + split, r.y, r.width - split, r.depth)
            stack.append(left)
            stack.append(right)
        elif can_split_h:
            lo = max(_MIN_LEAF_SIDE, 0.3 * r.depth)
            hi = min(r.depth - _MIN_LEAF_SIDE, 0.7 * r.depth)
            if hi <= lo:
                leaves.append(r)
                continue
            split = _snap(rng.uniform(lo, hi))
            split = max(_MIN_LEAF_SIDE, min(r.depth - _MIN_LEAF_SIDE, split))
            bottom = _Rect(r.x, r.y, r.width, split)
            top = _Rect(r.x, r.y + split, r.width, r.depth - split)
            stack.append(bottom)
            stack.append(top)
        else:
            leaves.append(r)

    return leaves


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #

def bsp_pack_floor(
    template_names: list[str],
    footprint: tuple[float, float],
    level: int,
    ceiling_height: float = 3.0,
    stair_position: Optional[tuple[float, float, float, float]] = None,
) -> Floor:
    """BSP-style packer.

    Subdivide ``footprint`` into leaves, fit each requested template into a
    leaf greedily (largest first, center-placed). Reserves a lobby on the
    south edge (level 0) and an optional stairwell rectangle so no room
    overlaps them.

    Args:
        template_names: Ordered list of RoomTemplate names. Unknown names are
            silently skipped (a debug line is printed).
        footprint: ``(width, depth)`` of the building.
        level: Floor level. Level 0 always gets a south-edge lobby.
        ceiling_height: Passed straight through to ``Floor``.
        stair_position: Optional ``(x, y, w, d)`` rectangle to carve out for
            a stairwell. A matching ``Stairs`` entry is added to the Floor.

    Returns:
        ``Floor`` with ``rooms`` (lobby first if level 0) and ``stairs``.
    """
    fw, fd = footprint
    rng = random.Random(level)

    # ------------------------------------------------------------------ #
    # 1. Build the working set of templates.
    # ------------------------------------------------------------------ #
    names = list(template_names)
    if level == 0 and "lobby_modern" not in names:
        names.insert(0, "lobby_modern")

    # Resolve template names. Preserve original index so room IDs stay
    # stable regardless of placement order. Unknown names are dropped.
    pending: list[tuple[int, RoomTemplate]] = []
    lobby_entry: Optional[tuple[int, RoomTemplate]] = None
    for slot_index, name in enumerate(names):
        tpl = ROOM_LIBRARY.get(name)
        if tpl is None:
            print(f"[bsp_packer] skipping unknown template: {name}")
            continue
        if level == 0 and lobby_entry is None and name == "lobby_modern":
            lobby_entry = (slot_index, tpl)
        else:
            pending.append((slot_index, tpl))

    rooms: list[Room] = []
    reserved: list[_Rect] = []  # rectangles BSP must avoid

    # ------------------------------------------------------------------ #
    # 2. Reserve fixed regions: lobby (level 0) and stairwell.
    # ------------------------------------------------------------------ #
    if level == 0 and lobby_entry is not None:
        slot_index, tpl = lobby_entry
        # Center along x; if footprint is narrower than the lobby template,
        # fall back to anchoring at x=0 and clipping the stored width to fw.
        lobby_w = min(tpl.width, fw)
        lobby_x = _snap(max(0.0, (fw - lobby_w) / 2.0))
        lobby_y = 0.0
        lobby_d = min(tpl.depth, fd)
        rooms.append(
            Room(
                id=f"{tpl.name}_{level}_{slot_index}",
                type=tpl.type,
                x=lobby_x,
                y=lobby_y,
                width=lobby_w,
                depth=lobby_d,
                doors=[
                    Door(wall=d.wall, offset=d.offset, width=d.width)
                    for d in tpl.door_specs
                ],
                windows=[],
            )
        )
        reserved.append(_Rect(lobby_x, lobby_y, lobby_w, lobby_d))

    stairs_list: list[Stairs] = []
    if stair_position is not None:
        sx, sy, sw, sd = stair_position
        # Snap to grid so the carved hole aligns with placed rooms.
        sx_s = _snap(sx)
        sy_s = _snap(sy)
        sw_s = _snap(sw)
        sd_s = _snap(sd)
        reserved.append(_Rect(sx_s, sy_s, sw_s, sd_s))

        # One stair per floor: go up from level 0, otherwise go down.
        if level == 0:
            direction = "north"
            to_level = 1
        else:
            direction = "south"
            to_level = level - 1
        stairs_list.append(
            Stairs(
                id=f"stair_{level}",
                x=sx_s,
                y=sy_s,
                width=sw_s,
                depth=sd_s,
                direction=direction,
                toLevel=to_level,
            )
        )

    # ------------------------------------------------------------------ #
    # 3. Carve reserved regions out of the footprint to get the BSP area.
    # ------------------------------------------------------------------ #
    working: list[_Rect] = [_Rect(0.0, 0.0, fw, fd)]
    for hole in reserved:
        next_pieces: list[_Rect] = []
        for piece in working:
            next_pieces.extend(_rect_minus(piece, hole))
        working = next_pieces

    # ------------------------------------------------------------------ #
    # 4. BSP subdivide each working piece into leaves.
    # ------------------------------------------------------------------ #
    if pending:
        largest_side = max(
            max(t.width, t.depth) for _, t in pending
        )
        # Aim for leaves ~1.4x the largest template so something fits with slack.
        target = max(_MIN_LEAF_SIDE * 1.5, largest_side * 1.4)
    else:
        target = _MIN_LEAF_SIDE * 2.0

    leaves: list[_Rect] = []
    for piece in working:
        if piece.width < _MIN_LEAF_SIDE or piece.depth < _MIN_LEAF_SIDE:
            # Too small to meaningfully subdivide; leave as-is (corridor).
            continue
        leaves.extend(_bsp_subdivide(piece, rng, target))

    # Shuffle deterministically so placement order isn't strictly spatial.
    rng.shuffle(leaves)

    # ------------------------------------------------------------------ #
    # 5. Greedy: largest unplaced template that fits this leaf wins.
    # ------------------------------------------------------------------ #
    placed_indices: set[int] = set()
    # Sort pending by area desc so a leaf prefers the biggest template
    # that fits inside it.
    def _area(item: tuple[int, RoomTemplate]) -> float:
        return item[1].width * item[1].depth

    for leaf in leaves:
        # Find the largest unplaced template that fits in this leaf.
        candidates = [
            (i, t) for (i, t) in pending
            if i not in placed_indices
            and t.width <= leaf.width + 1e-6
            and t.depth <= leaf.depth + 1e-6
        ]
        if not candidates:
            continue
        candidates.sort(key=_area, reverse=True)
        slot_index, tpl = candidates[0]
        placed_indices.add(slot_index)

        # Center the template inside the leaf, snap to grid.
        rx = _snap(leaf.x + (leaf.width - tpl.width) / 2.0)
        ry = _snap(leaf.y + (leaf.depth - tpl.depth) / 2.0)
        # Clamp inside the leaf in case snapping nudged us out.
        rx = min(max(rx, leaf.x), leaf.x2 - tpl.width)
        ry = min(max(ry, leaf.y), leaf.y2 - tpl.depth)

        rooms.append(
            Room(
                id=f"{tpl.name}_{level}_{slot_index}",
                type=tpl.type,
                x=rx,
                y=ry,
                width=tpl.width,
                depth=tpl.depth,
                doors=[
                    Door(wall=d.wall, offset=d.offset, width=d.width)
                    for d in tpl.door_specs
                ],
                windows=[],
            )
        )

    # Templates that didn't fit into any leaf are silently dropped — same
    # behaviour as ``floor_packer.pack_floor_plan``.
    for slot_index, tpl in pending:
        if slot_index not in placed_indices:
            print(
                f"[bsp_packer] dropping {tpl.name}: no BSP leaf accommodates "
                f"{tpl.width}x{tpl.depth}"
            )

    return Floor(
        level=level,
        ceilingHeight=ceiling_height,
        rooms=rooms,
        stairs=stairs_list,
    )
