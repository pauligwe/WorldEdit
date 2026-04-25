import pytest

from core.archetype_packer import (
    RESIDENTIAL_ARCHETYPES,
    archetype_pack_floor,
)


def _has_south_edge_entrance(floor) -> bool:
    """Exactly one room sits on y == 0 with a south-wall door."""
    south_entrants = [
        r for r in floor.rooms
        if r.y == 0.0 and any(d.wall == "south" for d in r.doors)
    ]
    return len(south_entrants) == 1


def _all_inside_footprint(floor, footprint, eps=1e-6) -> bool:
    fw, fd = footprint
    for r in floor.rooms:
        if r.x < -eps or r.y < -eps:
            return False
        if r.x + r.width > fw + eps or r.y + r.depth > fd + eps:
            return False
    return True


# --------------------------------------------------------------------------- #
# Ranch
# --------------------------------------------------------------------------- #

def test_ranch_level0_layout():
    floor = archetype_pack_floor("ranch", level=0)
    assert len(floor.rooms) == 5
    assert _has_south_edge_entrance(floor)
    assert _all_inside_footprint(floor, RESIDENTIAL_ARCHETYPES["ranch"].footprint)


def test_ranch_level1_raises():
    with pytest.raises(ValueError):
        archetype_pack_floor("ranch", level=1)


# --------------------------------------------------------------------------- #
# Two-story colonial
# --------------------------------------------------------------------------- #

def test_colonial_level0_layout():
    floor = archetype_pack_floor("two_story_colonial", level=0)
    assert len(floor.rooms) == 7
    assert _has_south_edge_entrance(floor)
    assert _all_inside_footprint(
        floor, RESIDENTIAL_ARCHETYPES["two_story_colonial"].footprint
    )
    assert len(floor.stairs) == 1


def test_colonial_level1_layout():
    floor = archetype_pack_floor("two_story_colonial", level=1)
    assert len(floor.rooms) == 6
    assert _all_inside_footprint(
        floor, RESIDENTIAL_ARCHETYPES["two_story_colonial"].footprint
    )
    assert len(floor.stairs) == 1


def test_colonial_levels_differ_and_stairs_align():
    f0 = archetype_pack_floor("two_story_colonial", level=0)
    f1 = archetype_pack_floor("two_story_colonial", level=1)

    ids0 = sorted(r.id for r in f0.rooms)
    ids1 = sorted(r.id for r in f1.rooms)
    assert ids0 != ids1

    assert f0.stairs[0].x == f1.stairs[0].x
    assert f0.stairs[0].y == f1.stairs[0].y


# --------------------------------------------------------------------------- #
# Studio
# --------------------------------------------------------------------------- #

def test_studio_level0_layout():
    floor = archetype_pack_floor("studio", level=0)
    assert len(floor.rooms) == 2
    assert _has_south_edge_entrance(floor)
    assert _all_inside_footprint(floor, RESIDENTIAL_ARCHETYPES["studio"].footprint)


# --------------------------------------------------------------------------- #
# Loft
# --------------------------------------------------------------------------- #

def test_loft_level0_layout():
    floor = archetype_pack_floor("loft", level=0)
    assert len(floor.rooms) == 2
    assert _has_south_edge_entrance(floor)
    assert _all_inside_footprint(floor, RESIDENTIAL_ARCHETYPES["loft"].footprint)
    assert len(floor.stairs) == 1


def test_loft_levels_differ_and_stairs_align():
    f0 = archetype_pack_floor("loft", level=0)
    f1 = archetype_pack_floor("loft", level=1)

    ids0 = sorted(r.id for r in f0.rooms)
    ids1 = sorted(r.id for r in f1.rooms)
    assert ids0 != ids1

    assert f0.stairs[0].x == f1.stairs[0].x
    assert f0.stairs[0].y == f1.stairs[0].y


def test_loft_level2_raises():
    with pytest.raises(ValueError):
        archetype_pack_floor("loft", level=2)


# --------------------------------------------------------------------------- #
# Registry / determinism
# --------------------------------------------------------------------------- #

def test_archetype_names_exported():
    expected = {"ranch", "two_story_colonial", "studio", "loft"}
    assert expected.issubset(set(RESIDENTIAL_ARCHETYPES.keys()))


def test_unknown_archetype_raises():
    with pytest.raises(ValueError):
        archetype_pack_floor("mansion", level=0)


def test_deterministic():
    a = archetype_pack_floor("ranch", level=0)
    b = archetype_pack_floor("ranch", level=0)
    assert [r.model_dump() for r in a.rooms] == [r.model_dump() for r in b.rooms]
