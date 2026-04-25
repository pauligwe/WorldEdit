"""End-to-end test: simulate a full analyze run with all 19 agents stubbed.
This catches integration regressions across manifest, orchestrator, registry,
and bridge."""
import base64
import json
from unittest.mock import patch
from fastapi.testclient import TestClient
from bridge.main import app
from agents_v2.manifest import AGENTS


def _data_url(b: bytes) -> str:
    return f"data:image/jpeg;base64,{base64.b64encode(b).decode()}"


def test_perception_then_analyze_writes_full_json(tmp_path, monkeypatch):
    backend_worlds = tmp_path / "backend_worlds"
    frontend_worlds = tmp_path / "frontend_worlds"
    frontend_worlds.mkdir()
    monkeypatch.setattr("bridge.main.WORLDS_DIR", backend_worlds)
    monkeypatch.setattr("bridge.main.FRONTEND_WORLDS_DIR", frontend_worlds)

    stubs = {a.id: (lambda req, _id=a.id: {"marker": _id, "got": list(req.upstream.keys())})
             for a in AGENTS}

    client = TestClient(app)

    r = client.post("/api/perception-frames", json={
        "world_id": "smoke",
        "view_0":   _data_url(b"\xff\xd8\xff\xe0v0"),
        "view_120": _data_url(b"\xff\xd8\xff\xe0v120"),
        "view_240": _data_url(b"\xff\xd8\xff\xe0v240"),
    })
    assert r.status_code == 200

    with patch("agents_v2.registry.AGENT_RUNS", stubs):
        r = client.post("/api/analyze/smoke", json={"prompt": "smoke prompt"})
        assert r.status_code == 202
        for _ in range(40):
            s = client.get("/api/analyze/smoke/status").json()
            if s["state"] == "done":
                break

    out = frontend_worlds / "smoke.agents.json"
    assert out.exists()
    data = json.loads(out.read_text())
    assert data["world_id"] == "smoke"
    assert len(data["agents"]) == 19
    for aid in (a.id for a in AGENTS):
        assert data["agents"][aid]["status"] == "done"
        assert data["agents"][aid]["output"]["marker"] == aid
