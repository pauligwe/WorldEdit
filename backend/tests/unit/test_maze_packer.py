import random

import pytest

from core.floor_connectivity import _bfs, _build_adjacency
from core.maze_packer import maze_pack_floor
from core.validators import _rects_overlap


_OFFICE_TEMPLATES = [
    "office_private_small",
    "conference_small",
    "conference_large",
    "breakroom",
    "office_open_bullpen",
    "restroom",
    "server_room",
    "corridor_wide",
]


def _random_template_names(rng: random.Random, n: int = 8) -> list[str]:
    return [rng.choice(_OFFICE_TEMPLATES) for _ in range(n)]


def test_seed_room_on_south_edge_for_level_0():
    floor, _ = maze_pack_floor(
        ["office_private_small", "conference_small"],
        footprint=(30.0, 30.0),
        level=0,
        entrance_offset=10.0,
    )
    # At least one room must sit on y=0 and overlap x=10.
    on_south = [r for r in floor.rooms if r.y == pytest.approx(0.0)]
    assert on_south, "no room sits on the south edge"
    assert any(r.x <= 10.0 <= r.x + r.width for r in on_south), (
        f"no south-edge room overlaps x=10; rooms: "
        f"{[(r.x, r.y, r.width, r.depth) for r in on_south]}"
    )


def test_all_rooms_reachable_from_entrance_property():
    for seed in range(50):
        rng = random.Random(seed)
        names = _random_template_names(rng)
        floor, _ = maze_pack_floor(
            names,
            footprint=(30.0, 30.0),
            level=0,
            entrance_offset=15.0,
            seed=seed,
        )
        assert floor.rooms, f"seed={seed}: no rooms placed"
        adj = _build_adjacency(floor.rooms)
        # Seed/entrance is the first placed room.
        reachable = _bfs(adj, [floor.rooms[0].id])
        assert len(reachable) == len(floor.rooms), (
            f"seed={seed}: only {len(reachable)}/{len(floor.rooms)} rooms "
            f"reachable from entrance"
        )


def test_no_room_overlaps_property():
    for seed in range(50):
        rng = random.Random(seed)
        names = _random_template_names(rng)
        floor, _ = maze_pack_floor(
            names,
            footprint=(30.0, 30.0),
            level=0,
            entrance_offset=15.0,
            seed=seed,
        )
        rooms = floor.rooms
        for i, a in enumerate(rooms):
            for b in rooms[i + 1:]:
                assert not _rects_overlap(a, b), (
                    f"seed={seed}: rooms {a.id} and {b.id} overlap"
                )


def test_all_rooms_inside_footprint_property():
    for seed in range(50):
        rng = random.Random(seed)
        names = _random_template_names(rng)
        floor, _ = maze_pack_floor(
            names,
            footprint=(30.0, 30.0),
            level=0,
            entrance_offset=15.0,
            seed=seed,
        )
        for r in floor.rooms:
            assert r.x >= -1e-6, f"seed={seed}: room {r.id} x<0"
            assert r.y >= -1e-6, f"seed={seed}: room {r.id} y<0"
            assert r.x + r.width <= 30.0 + 1e-6, (
                f"seed={seed}: room {r.id} extends past width"
            )
            assert r.y + r.depth <= 30.0 + 1e-6, (
                f"seed={seed}: room {r.id} extends past depth"
            )


def test_stair_lands_in_a_reachable_room_for_multi_floor():
    floor, stair_xy = maze_pack_floor(
        _OFFICE_TEMPLATES,
        footprint=(30.0, 30.0),
        level=0,
        entrance_offset=15.0,
        stair_position=(13.0, 13.0, 3.0, 4.0),
        seed=7,
    )
    assert stair_xy is not None, "expected stair_xy to be returned"
    sx, sy = stair_xy
    # The Stairs object should exist.
    assert len(floor.stairs) == 1
    s = floor.stairs[0]
    assert (s.x, s.y) == (sx, sy)

    # The stair (use its center) lies inside some room.
    cx = s.x + s.width / 2.0
    cy = s.y + s.depth / 2.0
    container = next(
        (
            r for r in floor.rooms
            if r.x - 1e-6 <= cx <= r.x + r.width + 1e-6
            and r.y - 1e-6 <= cy <= r.y + r.depth + 1e-6
        ),
        None,
    )
    assert container is not None, "stair is not inside any room"

    # And that room is reachable from the entrance.
    adj = _build_adjacency(floor.rooms)
    reachable = _bfs(adj, [floor.rooms[0].id])
    assert container.id in reachable, (
        f"stair room {container.id} is not reachable from entrance"
    )


def test_determinism():
    a, _ = maze_pack_floor(
        _OFFICE_TEMPLATES,
        footprint=(30.0, 30.0),
        level=0,
        entrance_offset=15.0,
        seed=42,
    )
    b, _ = maze_pack_floor(
        _OFFICE_TEMPLATES,
        footprint=(30.0, 30.0),
        level=0,
        entrance_offset=15.0,
        seed=42,
    )
    assert len(a.rooms) == len(b.rooms)
    for ra, rb in zip(a.rooms, b.rooms):
        assert ra.model_dump() == rb.model_dump()


def test_upper_floor_honors_stair_position_exactly():
    """Stairs on level >= 1 must land at the exact (x, y) passed in."""
    floor, stair_xy = maze_pack_floor(
        _OFFICE_TEMPLATES,
        footprint=(30.0, 30.0),
        level=1,
        stair_position=(12.0, 8.0, 3.0, 4.0),
        seed=3,
        is_top_floor=True,
    )
    assert stair_xy == (12.0, 8.0), (
        f"expected stair_xy=(12.0, 8.0), got {stair_xy}"
    )
    assert len(floor.stairs) == 1, "top floor should have only the down stair"
    s = floor.stairs[0]
    assert (s.x, s.y) == (12.0, 8.0)
    assert s.direction == "south"


def test_intermediate_floor_emits_both_up_and_down_stairs():
    floor, stair_xy = maze_pack_floor(
        _OFFICE_TEMPLATES,
        footprint=(30.0, 30.0),
        level=1,
        stair_position=(10.0, 10.0, 3.0, 4.0),
        seed=5,
        is_top_floor=False,
    )
    assert stair_xy == (10.0, 10.0)
    # Intermediate floor: one down-stair (to level 0) and one up-stair (to level 2).
    assert len(floor.stairs) == 2
    directions = sorted(s.direction for s in floor.stairs)
    assert directions == ["north", "south"]
    # Both must be at the same (x, y).
    for s in floor.stairs:
        assert (s.x, s.y) == (10.0, 10.0)


def test_stairs_align_across_three_floors():
    """Run level 0 -> 1 -> 2 with the caller threading stair_xy. All stair
    (x, y) coords must be identical."""
    floor0, xy0 = maze_pack_floor(
        _OFFICE_TEMPLATES,
        footprint=(30.0, 30.0),
        level=0,
        entrance_offset=15.0,
        stair_position=((30.0 - 3.0) / 2, (30.0 - 4.0) / 2, 3.0, 4.0),  # sentinel
        seed=11,
    )
    assert xy0 is not None and len(floor0.stairs) == 1
    assert floor0.stairs[0].direction == "north"

    seed1 = (xy0[0], xy0[1], 3.0, 4.0)
    floor1, xy1 = maze_pack_floor(
        _OFFICE_TEMPLATES,
        footprint=(30.0, 30.0),
        level=1,
        stair_position=seed1,
        seed=12,
        is_top_floor=False,
    )
    assert xy1 == xy0, f"floor 1 stair {xy1} != floor 0 stair {xy0}"

    seed2 = (xy1[0], xy1[1], 3.0, 4.0)
    floor2, xy2 = maze_pack_floor(
        _OFFICE_TEMPLATES,
        footprint=(30.0, 30.0),
        level=2,
        stair_position=seed2,
        seed=13,
        is_top_floor=True,
    )
    assert xy2 == xy0, f"floor 2 stair {xy2} != floor 0 stair {xy0}"

    # Top floor should have only a down-stair.
    assert len(floor2.stairs) == 1
    assert floor2.stairs[0].direction == "south"


def test_upper_floor_landing_contains_the_stair():
    """The landing room seeded on upper floors must contain the stair."""
    floor, stair_xy = maze_pack_floor(
        _OFFICE_TEMPLATES,
        footprint=(30.0, 30.0),
        level=1,
        stair_position=(20.0, 18.0, 3.0, 4.0),
        seed=21,
        is_top_floor=True,
    )
    assert stair_xy == (20.0, 18.0)
    s = floor.stairs[0]
    cx, cy = s.x + s.width / 2.0, s.y + s.depth / 2.0
    container = next(
        (
            r for r in floor.rooms
            if r.x - 1e-6 <= cx <= r.x + r.width + 1e-6
            and r.y - 1e-6 <= cy <= r.y + r.depth + 1e-6
        ),
        None,
    )
    assert container is not None, "stair on upper floor not inside any room"


def test_skips_unknown_templates_gracefully():
    floor, _ = maze_pack_floor(
        ["nonexistent_template", "office_private_small"],
        footprint=(30.0, 30.0),
        level=0,
        entrance_offset=15.0,
    )
    types = [r.type for r in floor.rooms]
    # The bad name was skipped (no "nonexistent_template" type).
    assert "nonexistent_template" not in types
    # The good template made it in.
    assert "office" in types
