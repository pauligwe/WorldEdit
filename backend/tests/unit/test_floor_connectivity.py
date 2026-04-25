from core.world_spec import (
    Blueprint,
    Door,
    Entrance,
    Floor,
    Plot,
    Room,
    Site,
    Stairs,
)
from core.floor_connectivity import validate_floor_connectivity


def _site(fw: float = 10.0, fd: float = 10.0, ent_offset: float = 5.0) -> Site:
    return Site(
        plot=Plot(),
        buildingFootprint=[fw, fd],
        buildingAnchor=[(100 - fw) / 2, (100 - fd) / 2],
        entrance=Entrance(wall="south", offset=ent_offset, width=1.0),
    )


def test_single_room_with_entrance_door_passes():
    site = _site(fw=10, fd=10, ent_offset=5)
    bp = Blueprint(floors=[Floor(level=0, ceilingHeight=3.0, rooms=[
        Room(id="lobby", type="lobby", x=0, y=0, width=10, depth=10,
             doors=[Door(wall="south", offset=4.5, width=1.0)])
    ])])
    assert validate_floor_connectivity(bp, site) == []


def test_two_adjacent_rooms_with_connecting_door_pass():
    site = _site(fw=10, fd=10, ent_offset=2.5)
    bp = Blueprint(floors=[Floor(level=0, ceilingHeight=3.0, rooms=[
        Room(id="a", type="lobby", x=0, y=0, width=5, depth=10,
             doors=[
                 Door(wall="south", offset=2, width=1.0),
                 Door(wall="east", offset=4, width=1.0),
             ]),
        Room(id="b", type="office", x=5, y=0, width=5, depth=10,
             doors=[]),
    ])])
    errors = validate_floor_connectivity(bp, site)
    assert errors == [], errors


def test_two_adjacent_rooms_without_doors_still_pass():
    """Doors are no longer required; any shared wall counts as a connection."""
    site = _site(fw=10, fd=10, ent_offset=2.5)
    bp = Blueprint(floors=[Floor(level=0, ceilingHeight=3.0, rooms=[
        Room(id="a", type="lobby", x=0, y=0, width=5, depth=10, doors=[]),
        Room(id="b", type="office", x=5, y=0, width=5, depth=10, doors=[]),
    ])])
    errors = validate_floor_connectivity(bp, site)
    assert errors == [], errors


def test_two_disjoint_rooms_fail():
    site = _site(fw=12, fd=10, ent_offset=2.5)
    bp = Blueprint(floors=[Floor(level=0, ceilingHeight=3.0, rooms=[
        Room(id="a", type="lobby", x=0, y=0, width=4, depth=4, doors=[]),
        Room(id="b", type="office", x=8, y=6, width=4, depth=4, doors=[]),
    ])])
    errors = validate_floor_connectivity(bp, site)
    assert any("b" in e and "not reachable" in e for e in errors), errors


def test_two_floor_aligned_stairs_pass():
    site = _site(fw=10, fd=10, ent_offset=5)
    bp = Blueprint(floors=[
        Floor(level=0, ceilingHeight=3.0, rooms=[
            Room(id="ground", type="lobby", x=0, y=0, width=10, depth=10,
                 doors=[Door(wall="south", offset=4.5, width=1.0)]),
        ], stairs=[Stairs(id="s1", x=4, y=4, width=2, depth=2,
                          direction="north", toLevel=1)]),
        Floor(level=1, ceilingHeight=3.0, rooms=[
            Room(id="upper", type="hall", x=0, y=0, width=10, depth=10,
                 doors=[]),
        ], stairs=[Stairs(id="s1", x=4, y=4, width=2, depth=2,
                          direction="south", toLevel=0)]),
    ])
    errors = validate_floor_connectivity(bp, site)
    assert errors == [], errors


def test_misaligned_stairs_fail():
    site = _site(fw=10, fd=10, ent_offset=5)
    bp = Blueprint(floors=[
        Floor(level=0, ceilingHeight=3.0, rooms=[
            Room(id="ground", type="lobby", x=0, y=0, width=10, depth=10,
                 doors=[Door(wall="south", offset=4.5, width=1.0)]),
        ], stairs=[Stairs(id="s1", x=5, y=4, width=2, depth=2,
                          direction="north", toLevel=1)]),
        Floor(level=1, ceilingHeight=3.0, rooms=[
            Room(id="upper", type="hall", x=0, y=0, width=10, depth=10,
                 doors=[]),
        ], stairs=[Stairs(id="s2", x=5, y=6, width=2, depth=2,
                          direction="south", toLevel=0)]),
    ])
    errors = validate_floor_connectivity(bp, site)
    assert any("no aligned stair" in e for e in errors), errors


def test_missing_stair_on_upper_floor_fails():
    site = _site(fw=10, fd=10, ent_offset=5)
    bp = Blueprint(floors=[
        Floor(level=0, ceilingHeight=3.0, rooms=[
            Room(id="ground", type="lobby", x=0, y=0, width=10, depth=10,
                 doors=[Door(wall="south", offset=4.5, width=1.0)]),
        ], stairs=[Stairs(id="s1", x=4, y=4, width=2, depth=2,
                          direction="north", toLevel=1)]),
        Floor(level=1, ceilingHeight=3.0, rooms=[
            Room(id="upper", type="hall", x=0, y=0, width=10, depth=10,
                 doors=[]),
        ], stairs=[]),
    ])
    errors = validate_floor_connectivity(bp, site)
    assert any("no aligned stair" in e for e in errors), errors


def test_three_room_transitive_reachability_passes():
    site = _site(fw=15, fd=10, ent_offset=2.5)
    bp = Blueprint(floors=[Floor(level=0, ceilingHeight=3.0, rooms=[
        Room(id="a", type="lobby", x=0, y=0, width=5, depth=10,
             doors=[
                 Door(wall="south", offset=2, width=1.0),
                 Door(wall="east", offset=4, width=1.0),
             ]),
        Room(id="b", type="hall", x=5, y=0, width=5, depth=10,
             doors=[Door(wall="east", offset=4, width=1.0)]),
        Room(id="c", type="office", x=10, y=0, width=5, depth=10,
             doors=[]),
    ])])
    errors = validate_floor_connectivity(bp, site)
    assert errors == [], errors


def test_no_room_on_entrance_edge_fails():
    """If no ground-floor room sits on the entrance wall edge, that's an error."""
    site = _site(fw=10, fd=10, ent_offset=5)
    bp = Blueprint(floors=[Floor(level=0, ceilingHeight=3.0, rooms=[
        Room(id="lobby", type="lobby", x=0, y=2, width=10, depth=8, doors=[])
    ])])
    errors = validate_floor_connectivity(bp, site)
    assert any("south edge" in e.lower() for e in errors), errors
