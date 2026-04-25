"""Multi-process launcher for the 19 post-generation analysis agents.

Mirrors `pre_gen.py`. Each agent runs as a standalone uagents Agent in
its own subprocess on its own port (8101-8119) so it gets a per-agent
Inspector URL — required for mailbox provisioning on Agentverse.

These agents have NO build pipeline (`work_handler=None`). They exist
purely as on-network presences that judges can DM directly. The actual
analysis swarm runs in-process via `agents_v2/orchestrator.py` once a
world is loaded in the frontend.

Usage (from backend/):
    .venv/bin/python -m agentverse.post_gen
"""
from __future__ import annotations

import re
import signal
import subprocess
import sys
import time
from pathlib import Path

from agentverse.registry import POST_GEN_WORKERS

PERSONAS: dict[str, str] = {
    "scene_describer": (
        "Hi — I'm Scene Describer. I read the captures from a generated "
        "world and produce a dense paragraph plus structured tags. I'm the "
        "foundation that most other post-gen agents read from."
    ),
    "object_inventory": (
        "Hi — I'm Object Inventory. I list every visible object in a "
        "generated world with rough position. Prop Shopping, Set Dressing "
        "and Hazard Audit all read my list."
    ),
    "spatial_layout": (
        "Hi — I'm Spatial Layout. I extract a rough floorplan and room "
        "graph — room count, adjacencies, footprint — from the overhead "
        "capture of a world."
    ),
    "geolocator": (
        "Hi — I'm Geolocator. Given a scene description I propose top-3 "
        "candidate real-world regions where the place could plausibly "
        "exist, with reasoning and confidence scores."
    ),
    "filming_scout": (
        "Hi — I'm Filming Location Scout. I find 3-5 real-world filming "
        "locations matching a world's vibe — Peerspace/Giggster-style "
        "listings with addresses and rough rates."
    ),
    "era_estimator": (
        "Hi — I'm Era Estimator. I estimate when a scene is set — decade, "
        "century, or geological epoch — from architecture, tech, materials, "
        "and decor."
    ),
    "architectural_style": (
        "Hi — I'm Architectural Style. I classify the architectural style "
        "of a scene — Brutalist, Victorian, Mid-Century, etc. — and call "
        "out the features that drove the call."
    ),
    "shot_list": (
        "Hi — I'm Shot List. I plan a 5-8 shot cinematographer's shot list "
        "for filming a generated world — lens, position, framing, and the "
        "story beat each shot serves."
    ),
    "mood_palette": (
        "Hi — I'm Mood & Palette. I pull a 5-color palette from a scene "
        "plus LUT/film stock suggestions — the color-grade starting point "
        "for anyone using this world in post."
    ),
    "soundscape": (
        "Hi — I'm Soundscape. I design the ambient sound and Foley list "
        "for a generated world — what you'd hear standing in it, with "
        "rough mix suggestions."
    ),
    "prop_shopping": (
        "Hi — I'm Prop Shopping. From an object inventory I produce a "
        "real shopping list with Amazon/Wayfair/IKEA-style links so a "
        "decorator could actually build the room."
    ),
    "set_dressing": (
        "Hi — I'm Set Dressing. I suggest 5-10 specific dressing additions "
        "that would push a scene further in its intended direction without "
        "breaking continuity."
    ),
    "story_seed": (
        "Hi — I'm Story Seeds. I write 3 short story or film premises set "
        "in a generated world — different genres, different tones, all "
        "grounded in the actual scene."
    ),
    "character_suggester": (
        "Hi — I'm Characters. I propose 3-5 character cards — who lives "
        "or works in a place, what they want, what tension they bring "
        "into the room."
    ),
    "npc_dialogue": (
        "Hi — I'm NPC Dialogue. I write sample NPC dialogue for the "
        "characters in a world — a starting pack for game writers or "
        "improv-style scene work."
    ),
    "real_estate": (
        "Hi — I'm Real Estate Appraisal. Given the inferred location and "
        "floorplan I estimate what a place would rent or sell for in its "
        "real-world market."
    ),
    "hazard_audit": (
        "Hi — I'm Hazard Audit. I flag fire exits, trip hazards, and "
        "obvious code violations — the kind of pass a building inspector "
        "or location manager would do on a real set."
    ),
    "accessibility": (
        "Hi — I'm Accessibility. I audit a scene for wheelchair access, "
        "lighting for low vision, hearing-loop friendliness, and other "
        "accessibility concerns."
    ),
    "carbon_score": (
        "Hi — I'm Carbon Score. I estimate the embodied-carbon footprint "
        "of a scene's visible materials and objects and produce a 1-10 "
        "sustainability score with reasoning."
    ),
}


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
    for spec in POST_GEN_WORKERS:
        log_path = LOG_DIR / f"{spec.id}.log"
        log_path.write_bytes(b"")
        p = spawn_worker(spec, log_path)
        procs.append((spec.id, p, log_path))
        time.sleep(0.4)  # stagger to avoid login-burst rate-limits

    print()
    print("=" * 70)
    print("Conjure post-gen workers — Inspector URLs (open each, Connect → Mailbox)")
    print("=" * 70)
    for spec in POST_GEN_WORKERS:
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
            print("all post-gen workers exited.")
            return
        time.sleep(1.0)


if __name__ == "__main__":
    main()
