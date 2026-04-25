from core.world_spec import (
    Blueprint, Floor, Room, Door, Site, Plot, Entrance, Intent
)
from core.site import derive_site_from_intent
from core.geometry import build_geometry


def _setup():
    intent = Intent(buildingType="office", style="modern", floors=2,
                    vibe=[], sizeHint="medium")
    site = derive_site_from_intent(intent)
    fw, fd = site.buildingFootprint
    floors = [
        Floor(level=0, ceilingHeight=3.0, rooms=[
            Room(id="lobby", type="lobby", x=0, y=0, width=fw, depth=fd,
                 doors=[Door(wall="south", offset=site.entrance.offset, width=1.6)])
        ]),
        Floor(level=1, ceilingHeight=3.0, rooms=[
            Room(id="offices", type="office", x=0, y=0, width=fw, depth=fd,
                 doors=[Door(wall="south", offset=2.0, width=1.0)])
        ]),
    ]
    bp = Blueprint(floors=floors)
    return site, bp


def test_geometry_includes_ground_primitive():
    site, bp = _setup()
    geo = build_geometry(bp, site)
    grounds = [p for p in geo.primitives if p.type == "ground"]
    assert len(grounds) == 1
    assert grounds[0].size[0] == site.plot.width
    assert grounds[0].size[2] == site.plot.depth


def test_exterior_walls_one_perimeter_per_floor():
    site, bp = _setup()
    geo = build_geometry(bp, site)
    ext = [p for p in geo.primitives if p.type == "exterior_wall"]
    # 4 walls × 2 floors
    assert len(ext) == 8
    walls_by_dir = {"north": 0, "south": 0, "east": 0, "west": 0}
    for p in ext:
        walls_by_dir[p.wall] += 1
    assert walls_by_dir == {"north": 2, "south": 2, "east": 2, "west": 2}


def test_ground_floor_south_wall_has_entrance_hole():
    site, bp = _setup()
    geo = build_geometry(bp, site)
    south_walls = [p for p in geo.primitives if p.type == "exterior_wall" and p.wall == "south"]
    ground_south = [p for p in south_walls if abs(p.position[1] - 1.5) < 0.5]
    assert len(ground_south) == 1
    assert len(ground_south[0].holes) == 1
    hole = ground_south[0].holes[0]
    assert abs(hole["width"] - site.entrance.width) < 1e-6


def test_upper_floor_south_wall_has_no_entrance_hole():
    site, bp = _setup()
    geo = build_geometry(bp, site)
    south_walls = [p for p in geo.primitives if p.type == "exterior_wall" and p.wall == "south"]
    upper = [p for p in south_walls if p.position[1] > 3.0]
    assert len(upper) == 1
    assert upper[0].holes == []


def test_roof_exists_above_top_floor():
    site, bp = _setup()
    geo = build_geometry(bp, site)
    roofs = [p for p in geo.primitives if p.type == "roof"]
    assert len(roofs) == 1
    # Above level 1 (top of 2 floors at 3m each = 6m)
    assert roofs[0].position[1] >= 6.0


def test_existing_primitives_offset_by_anchor():
    site, bp = _setup()
    geo = build_geometry(bp, site)
    floors = [p for p in geo.primitives if p.type == "floor"]
    assert floors
    # First floor's first room is at building-local (0,0); plot-world should be anchor
    expected_x = site.buildingAnchor[0] + bp.floors[0].rooms[0].width / 2
    assert abs(floors[0].position[0] - expected_x) < 1e-6
