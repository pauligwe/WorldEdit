from unittest.mock import patch, MagicMock
from agents_v2.agents import scene_describer
from agents_v2.messages import AgentRequest, SceneDescription


def _request(tmp_path):
    (tmp_path / "v0.jpg").write_bytes(b"\xff\xd8\xff\xe0")
    (tmp_path / "v1.jpg").write_bytes(b"\xff\xd8\xff\xe0")
    (tmp_path / "v2.jpg").write_bytes(b"\xff\xd8\xff\xe0")
    return AgentRequest(
        world_id="cabin", agent_id="scene_describer",
        prompt="rustic cabin",
        view_paths=[str(tmp_path / "v0.jpg"), str(tmp_path / "v1.jpg"), str(tmp_path / "v2.jpg")],
        upstream={},
    )


def test_returns_summary_and_tags(tmp_path):
    fake = SceneDescription(summary="A rustic log cabin", tags=["rustic", "warm"])
    with patch.object(scene_describer, "vision", return_value=fake) as m:
        out = scene_describer.run(_request(tmp_path))
    assert out["summary"].startswith("A rustic")
    assert "rustic" in out["tags"]
    args, kwargs = m.call_args
    assert len(kwargs["images"]) == 3
    for mime, _ in kwargs["images"]:
        assert mime == "image/jpeg"
    assert kwargs["schema"] is SceneDescription
