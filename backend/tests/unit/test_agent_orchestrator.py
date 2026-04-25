import asyncio
from unittest.mock import patch
import pytest
from agents_v2.orchestrator import run_dag
from agents_v2.messages import PerceptionInput


def _stub_run(agent_id):
    """Returns a stub run() that produces a deterministic dict including its deps."""
    def _run(req):
        return {"agent": agent_id, "got_upstream": list(req.upstream.keys())}
    return _run


@pytest.mark.asyncio
async def test_dag_runs_all_19_agents_in_dependency_order():
    """Every agent runs exactly once. Dependent agents see their upstreams."""
    from agents_v2.manifest import AGENTS
    stubs = {a.id: _stub_run(a.id) for a in AGENTS}

    with patch("agents_v2.registry.AGENT_RUNS", stubs):
        result = await run_dag(PerceptionInput(
            world_id="t1", prompt="test", view_paths=[],
        ))

    assert len(result["agents"]) == 19
    for aid, entry in result["agents"].items():
        assert entry["status"] == "done"

    geo = result["agents"]["geolocator"]
    assert "scene_describer" in geo["output"]["got_upstream"]

    real = result["agents"]["real_estate"]
    assert "geolocator" in real["output"]["got_upstream"]
    assert "spatial_layout" in real["output"]["got_upstream"]


@pytest.mark.asyncio
async def test_failed_upstream_marks_downstream_skipped():
    from agents_v2.manifest import AGENTS

    def _failing_scene_describer(req):
        raise RuntimeError("boom")

    stubs = {a.id: _stub_run(a.id) for a in AGENTS}
    stubs["scene_describer"] = _failing_scene_describer

    with patch("agents_v2.registry.AGENT_RUNS", stubs):
        result = await run_dag(PerceptionInput(world_id="t2", prompt="x", view_paths=[]))

    assert result["agents"]["scene_describer"]["status"] == "error"
    assert result["agents"]["geolocator"]["status"] == "skipped"
    assert result["agents"]["geolocator"]["reason"] == "upstream_failed"


@pytest.mark.asyncio
async def test_independent_agents_unaffected_by_other_failures():
    from agents_v2.manifest import AGENTS

    def _failing_object_inventory(req):
        raise RuntimeError("boom")

    stubs = {a.id: _stub_run(a.id) for a in AGENTS}
    stubs["object_inventory"] = _failing_object_inventory

    with patch("agents_v2.registry.AGENT_RUNS", stubs):
        result = await run_dag(PerceptionInput(world_id="t3", prompt="x", view_paths=[]))

    assert result["agents"]["scene_describer"]["status"] == "done"
    assert result["agents"]["spatial_layout"]["status"] == "done"
    assert result["agents"]["geolocator"]["status"] == "done"
    assert result["agents"]["prop_shopping"]["status"] == "skipped"
