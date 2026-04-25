import json
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from bridge.main import app


def test_analyze_writes_json_and_returns_202(tmp_path, monkeypatch):
    monkeypatch.setattr("bridge.main.WORLDS_DIR", tmp_path / "backend_worlds")
    output_dir = tmp_path / "frontend_worlds"
    output_dir.mkdir()
    monkeypatch.setattr("bridge.main.FRONTEND_WORLDS_DIR", output_dir)

    views = (tmp_path / "backend_worlds" / "abc" / "views")
    views.mkdir(parents=True)
    for n in (0, 120, 240):
        (views / f"view_{n}.jpg").write_bytes(b"x")

    fake_result = {"world_id": "abc", "agents": {"scene_describer": {"status": "done"}}}

    async def fake_run_dag(p):
        return fake_result

    with patch("bridge.main.run_dag", side_effect=fake_run_dag):
        client = TestClient(app)
        r = client.post("/api/analyze/abc", json={"prompt": "test prompt"})
        assert r.status_code == 202
        for _ in range(20):
            s = client.get("/api/analyze/abc/status").json()
            if s["state"] == "done":
                break
        assert (output_dir / "abc.agents.json").exists()
        loaded = json.loads((output_dir / "abc.agents.json").read_text())
        assert loaded["world_id"] == "abc"


def test_analyze_404_when_views_missing(tmp_path, monkeypatch):
    monkeypatch.setattr("bridge.main.WORLDS_DIR", tmp_path / "backend_worlds")
    monkeypatch.setattr("bridge.main.FRONTEND_WORLDS_DIR", tmp_path / "frontend_worlds")
    (tmp_path / "frontend_worlds").mkdir()
    client = TestClient(app)
    r = client.post("/api/analyze/missing", json={"prompt": "x"})
    assert r.status_code == 404


def test_analyze_409_when_already_running(tmp_path, monkeypatch):
    monkeypatch.setattr("bridge.main.WORLDS_DIR", tmp_path / "backend_worlds")
    monkeypatch.setattr("bridge.main.FRONTEND_WORLDS_DIR", tmp_path / "frontend_worlds")
    (tmp_path / "frontend_worlds").mkdir()
    views = (tmp_path / "backend_worlds" / "abc" / "views")
    views.mkdir(parents=True)
    for n in (0, 120, 240):
        (views / f"view_{n}.jpg").write_bytes(b"x")

    async def slow_run_dag(p):
        import asyncio
        await asyncio.sleep(0.5)
        return {"world_id": "abc", "agents": {}}

    with patch("bridge.main.run_dag", side_effect=slow_run_dag):
        client = TestClient(app)
        r1 = client.post("/api/analyze/abc", json={"prompt": "x"})
        assert r1.status_code == 202
        r2 = client.post("/api/analyze/abc", json={"prompt": "x"})
        assert r2.status_code == 409
