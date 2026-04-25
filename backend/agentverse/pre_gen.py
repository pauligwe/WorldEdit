"""Multi-process launcher for the 10 pre-gen workers.

Each worker runs as a standalone uagents Agent in its own subprocess on
its own port (8201-8210). We can't use uagents.Bureau because it binds
one shared HTTP port (8000) and doesn't emit per-agent Inspector URLs —
mailbox provisioning requires one Inspector URL per agent.

This module also exports the per-agent `_make_handler` and `PERSONAS`
that `worker.py` and `coordinator.py` import.

Usage (from backend/):
    .venv/bin/python -m agentverse.pre_gen
Each worker's logs go to logs/agentverse/<id>.log; Inspector URLs are
extracted and printed to stdout for easy mailbox provisioning.
"""
from __future__ import annotations

import asyncio
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from uagents import Context

from agentverse.canned import artifact_for
from agentverse.messages import BuildArtifact, BuildRequest
from agentverse.registry import WORKERS

# Per-agent persona lines used in chat replies. Keep these in sync with the
# `description` strings in registry.py — these are friendlier rephrasings
# tuned for direct conversation rather than ASI:One previews.
PERSONAS: dict[str, str] = {
    "intent_parser": (
        "Hi — I'm Intent Parser. I read one-line world prompts and pull out "
        "structured intent (genre, mood, era, scale, anchors)."
    ),
    "reference_curator": (
        "Hi — I'm Reference Curator. I gather visual references — film "
        "stills, photographs, concept art — that match a parsed intent."
    ),
    "style_synthesizer": (
        "Hi — I'm Style Synthesizer. I pick a single coherent art direction "
        "from the reference set so the pipeline doesn't drift."
    ),
    "mood_lighting_director": (
        "Hi — I'm the Mood & Lighting Director. I lock in time of day, "
        "weather, color temperature, and key/fill ratios."
    ),
    "scene_composer": (
        "Hi — I'm Scene Composer. I lay out the spatial composition — "
        "foreground, focal point, sightlines, negative space."
    ),
    "prompt_engineer": (
        "Hi — I'm Prompt Engineer. I assemble the final Marble-ready prompt "
        "from intent, style, lighting, and composition."
    ),
    "marble_dispatcher": (
        "Hi — I'm Marble Dispatcher. I send the assembled prompt to World "
        "Labs Marble and wait for the resulting Gaussian splat."
    ),
    "capture_planner": (
        "Hi — I'm Capture Planner. Once Marble returns a splat I pick the "
        "camera viewpoints to capture from it."
    ),
    "quality_critic": (
        "Hi — I'm Quality Critic. I inspect rendered captures for blurry "
        "surfaces, clipping, missing geometry, and prompt drift."
    ),
    "continuity_checker": (
        "Hi — I'm Continuity Checker. I score how well the final splat "
        "matches the original user intent."
    ),
}


def _make_handler(agent_id: str):
    """Closure that returns this agent's canned artifact for any prompt.

    Imported by worker.py to bind into each subprocess's Agent.
    """
    async def handler(ctx: Context, sender: str, req: BuildRequest) -> BuildArtifact:
        # Light synthetic work delay; the dominant pacing comes from
        # mailbox round-trip latency between the coordinator and us.
        await asyncio.sleep(2.0)
        canned = artifact_for(agent_id, req.prompt)
        return BuildArtifact(
            request_id=req.request_id,
            agent_id=agent_id,
            headline=canned["headline"],
            payload=canned.get("payload", {}),
        )
    return handler


# ---------- Multi-process launcher ----------

LOG_DIR = Path(__file__).resolve().parents[1] / "logs" / "agentverse"
INSPECTOR_RE = re.compile(r"Agent inspector available at (\S+)")


def spawn_worker(spec, log_path: Path) -> subprocess.Popen:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log = open(log_path, "wb", buffering=0)
    return subprocess.Popen(
        [sys.executable, "-u", "-m", "agentverse.worker", spec.id],
        stdout=log,
        stderr=subprocess.STDOUT,
        cwd=str(Path(__file__).resolve().parents[1]),  # backend/
    )


def wait_for_inspector(log_path: Path, timeout_s: float = 20.0) -> str | None:
    """Tail a worker's log until it prints its Inspector URL (or timeout)."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if log_path.exists():
            try:
                text = log_path.read_text(errors="replace")
            except OSError:
                text = ""
            m = INSPECTOR_RE.search(text)
            if m:
                return m.group(1)
        time.sleep(0.3)
    return None


def main():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    procs: list[tuple[str, subprocess.Popen, Path]] = []
    for spec in WORKERS:
        log_path = LOG_DIR / f"{spec.id}.log"
        # Truncate previous log
        log_path.write_bytes(b"")
        p = spawn_worker(spec, log_path)
        procs.append((spec.id, p, log_path))
        time.sleep(0.4)  # stagger to avoid login-burst rate-limits

    print()
    print("=" * 70)
    print("Conjure pre-gen workers — Inspector URLs (open each, Connect → Mailbox)")
    print("=" * 70)
    for spec in WORKERS:
        log_path = LOG_DIR / f"{spec.id}.log"
        url = wait_for_inspector(log_path)
        if url:
            print(f"  {spec.label:30s} {url}")
        else:
            print(f"  {spec.label:30s} <NO INSPECTOR URL — see {log_path}>")
    print("=" * 70)
    print("Ctrl-C to shut down all workers.")
    print(f"Per-worker logs: {LOG_DIR}")
    print()

    # Wait on subprocesses; forward Ctrl-C.
    def _shutdown(signum, frame):
        for _, p, _ in procs:
            if p.poll() is None:
                p.send_signal(signal.SIGINT)
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)
    while True:
        all_dead = True
        for _, p, _ in procs:
            if p.poll() is None:
                all_dead = False
                break
        if all_dead:
            print("all workers exited.")
            return
        time.sleep(1.0)


if __name__ == "__main__":
    main()
