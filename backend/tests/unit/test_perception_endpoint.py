import base64
from pathlib import Path
from fastapi.testclient import TestClient
from bridge.main import app


def _data_url(payload_bytes: bytes) -> str:
    b64 = base64.b64encode(payload_bytes).decode()
    return f"data:image/jpeg;base64,{b64}"


def test_saves_three_frames_to_disk(tmp_path, monkeypatch):
    monkeypatch.setattr("bridge.main.WORLDS_DIR", tmp_path)
    client = TestClient(app)
    r = client.post("/api/perception-frames", json={
        "world_id": "cabin_test",
        "view_0": _data_url(b"\xff\xd8\xff\xe0_view0"),
        "view_120": _data_url(b"\xff\xd8\xff\xe0_view120"),
        "view_240": _data_url(b"\xff\xd8\xff\xe0_view240"),
    })
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    views_dir = tmp_path / "cabin_test" / "views"
    assert (views_dir / "view_0.jpg").exists()
    assert (views_dir / "view_120.jpg").exists()
    assert (views_dir / "view_240.jpg").exists()


def test_rejects_bad_id(monkeypatch, tmp_path):
    monkeypatch.setattr("bridge.main.WORLDS_DIR", tmp_path)
    client = TestClient(app)
    r = client.post("/api/perception-frames", json={
        "world_id": "../etc",
        "view_0": _data_url(b"x"),
        "view_120": _data_url(b"x"),
        "view_240": _data_url(b"x"),
    })
    assert r.status_code == 400


def test_rejects_non_data_url(monkeypatch, tmp_path):
    monkeypatch.setattr("bridge.main.WORLDS_DIR", tmp_path)
    client = TestClient(app)
    r = client.post("/api/perception-frames", json={
        "world_id": "cabin",
        "view_0": "https://example.com/x.jpg",
        "view_120": _data_url(b"x"),
        "view_240": _data_url(b"x"),
    })
    assert r.status_code == 400
