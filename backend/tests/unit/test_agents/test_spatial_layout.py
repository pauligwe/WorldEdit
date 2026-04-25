from unittest.mock import patch
from agents_v2.agents import spatial_layout
from agents_v2.messages import AgentRequest, SpatialLayout


def _req(tmp_path):
    for i in range(3):
        (tmp_path / f"v{i}.jpg").write_bytes(b"\xff\xd8\xff\xe0")
    return AgentRequest(
        world_id="cabin", agent_id="spatial_layout",
        prompt="cabin", view_paths=[str(tmp_path / f"v{i}.jpg") for i in range(3)],
        upstream={},
    )


def test_returns_layout(tmp_path):
    fake = SpatialLayout(
        rooms=[{"name": "living room", "approx_sqft": 300}],
        entrances=["front door (south wall)"],
        sightlines=["from couch to fireplace"],
        total_sqft_estimate=300,
    )
    with patch.object(spatial_layout, "vision", return_value=fake):
        out = spatial_layout.run(_req(tmp_path))
    assert out["total_sqft_estimate"] == 300
    assert out["rooms"][0]["name"] == "living room"
