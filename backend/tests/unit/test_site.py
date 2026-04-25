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
