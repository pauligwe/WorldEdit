"""DAG executor for the 19-agent swarm.

Walks the dependency graph in topological order. Each agent runs as soon as
all its upstream dependencies are done. Independent agents run in parallel
via asyncio.to_thread.

If an upstream agent errors, all downstream agents are marked 'skipped' with
reason='upstream_failed'. Independent agents continue.
"""
import asyncio
import time
from datetime import datetime, timezone
from agents_v2.manifest import AGENTS, by_id
from agents_v2.messages import PerceptionInput, AgentRequest
from agents_v2 import registry


async def _run_one(agent_id: str, req: AgentRequest) -> dict:
    fn = registry.AGENT_RUNS[agent_id]
    started = time.monotonic()
    try:
        output = await asyncio.to_thread(fn, req)
        duration_ms = int((time.monotonic() - started) * 1000)
        return {"status": "done", "duration_ms": duration_ms, "output": output}
    except Exception as e:
        duration_ms = int((time.monotonic() - started) * 1000)
        return {"status": "error", "duration_ms": duration_ms, "error_message": str(e)}


async def run_dag(perception: PerceptionInput) -> dict:
    """Run all 19 agents respecting dependency order. Returns the final JSON dict."""
    defs = list(AGENTS)
    by = by_id()
    results: dict[str, dict] = {}

    pending = {a.id for a in defs}
    in_flight: dict[str, asyncio.Task] = {}

    def _ready(agent_id: str) -> bool:
        deps = by[agent_id].dependencies
        return all(d in results for d in deps)

    def _any_dep_failed(agent_id: str) -> bool:
        return any(results.get(d, {}).get("status") in ("error", "skipped")
                   for d in by[agent_id].dependencies)

    def _start(agent_id: str):
        if _any_dep_failed(agent_id):
            results[agent_id] = {
                "status": "skipped",
                "duration_ms": 0,
                "reason": "upstream_failed",
            }
            return
        upstream = {dep: results[dep]["output"] for dep in by[agent_id].dependencies}
        req = AgentRequest(
            world_id=perception.world_id,
            agent_id=agent_id,
            prompt=perception.prompt,
            view_paths=perception.view_paths,
            upstream=upstream,
        )
        in_flight[agent_id] = asyncio.create_task(_run_one(agent_id, req))

    while pending or in_flight:
        ready_now = [aid for aid in list(pending) if _ready(aid)]
        for aid in ready_now:
            pending.discard(aid)
            _start(aid)

        if not in_flight:
            if pending:
                raise RuntimeError(f"DAG starved with pending: {pending}")
            break

        done, _ = await asyncio.wait(in_flight.values(), return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            aid = next(k for k, v in in_flight.items() if v is task)
            results[aid] = task.result()
            del in_flight[aid]

    for aid, entry in results.items():
        entry.setdefault("display", by[aid].display)

    return {
        "world_id": perception.world_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "schema_version": 1,
        "agents": results,
    }
