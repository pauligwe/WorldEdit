import pytest
from pydantic import ValidationError
from core.world_spec import Plot, Entrance, Site


def test_plot_defaults():
    p = Plot()
    assert p.width == 100.0
    assert p.depth == 100.0
    assert p.groundColor == "#5a7c3a"


def test_entrance_validates_positive_dimensions():
    with pytest.raises(ValidationError):
        Entrance(wall="south", offset=10, width=0, height=2.2)
    with pytest.raises(ValidationError):
        Entrance(wall="south", offset=-1, width=1.6, height=2.2)


def test_site_construction():
    s = Site(
        buildingFootprint=[40.0, 25.0],
        buildingAnchor=[30.0, 37.0],
        entrance=Entrance(wall="south", offset=20.0),
    )
    assert s.plot.width == 100.0
    assert s.buildingFootprint == [40.0, 25.0]
    assert s.entrance.width == 1.6  # default


from core.world_spec import Intent
from core.site import derive_site_from_intent


def test_derive_site_centers_building_on_plot():
    intent = Intent(buildingType="office", style="modern", floors=3,
                    vibe=["minimal"], sizeHint="medium")
    site = derive_site_from_intent(intent)
    assert site.plot.width == 100.0
    assert site.plot.depth == 100.0
    fw, fd = site.buildingFootprint
    ax, ay = site.buildingAnchor
    assert ax == (100 - fw) / 2
    assert ay == (100 - fd) / 2


def test_derive_site_size_hint_scales_footprint():
    small = derive_site_from_intent(Intent(buildingType="office", style="modern",
                                           floors=1, vibe=[], sizeHint="small"))
    large = derive_site_from_intent(Intent(buildingType="office", style="modern",
                                           floors=1, vibe=[], sizeHint="large"))
    assert large.buildingFootprint[0] > small.buildingFootprint[0]


def test_derive_site_entrance_on_south_wall():
    site = derive_site_from_intent(Intent(buildingType="office", style="modern",
                                          floors=1, vibe=[], sizeHint="medium"))
    assert site.entrance.wall == "south"
    assert 0 < site.entrance.offset < site.buildingFootprint[0]


def test_derive_site_leaves_grass_margin():
    site = derive_site_from_intent(Intent(buildingType="office", style="modern",
                                          floors=1, vibe=[], sizeHint="large"))
    fw, fd = site.buildingFootprint
    ax, ay = site.buildingAnchor
    assert ax >= 10  # 10m margin
    assert ay >= 10
    assert ax + fw <= 90
    assert ay + fd <= 90


from core.world_spec import (Blueprint, Floor, Room, Door, WorldSpec)
from core.site_validators import check_site_constraints


def _spec_with(site, floors):
    return WorldSpec(worldId="x", prompt="t", site=site,
                     blueprint=Blueprint(floors=floors))


def _good_site():
    return derive_site_from_intent(
        Intent(buildingType="office", style="modern", floors=1,
               vibe=[], sizeHint="medium"))


def test_site_validator_accepts_room_inside_footprint():
    site = _good_site()
    fw, fd = site.buildingFootprint
    floor = Floor(level=0, ceilingHeight=3.0, rooms=[
        Room(id="lobby", type="lobby", x=0, y=0, width=fw, depth=fd,
             doors=[Door(wall="south", offset=site.entrance.offset, width=1.6)])
    ])
    spec = _spec_with(site, [floor])
    errors = check_site_constraints(spec)
    assert errors == []


def test_site_validator_rejects_room_outside_footprint():
    site = _good_site()
    fw, fd = site.buildingFootprint
    floor = Floor(level=0, ceilingHeight=3.0, rooms=[
        Room(id="lobby", type="lobby", x=0, y=0, width=fw + 5, depth=fd,
             doors=[Door(wall="south", offset=site.entrance.offset, width=1.6)])
    ])
    spec = _spec_with(site, [floor])
    errors = check_site_constraints(spec)
    assert any("outside building footprint" in e for e in errors)


def test_site_validator_rejects_no_room_on_entrance_edge():
    """No ground-floor room sits on the entrance wall (south) edge."""
    site = _good_site()
    fw, fd = site.buildingFootprint
    floor = Floor(level=0, ceilingHeight=3.0, rooms=[
        Room(id="lobby", type="lobby", x=0, y=2, width=fw, depth=fd - 2,
             doors=[])
    ])
    spec = _spec_with(site, [floor])
    errors = check_site_constraints(spec)
    assert any("south edge" in e.lower() for e in errors)
