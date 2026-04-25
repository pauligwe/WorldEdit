"""Run one Conjure worker (pre-gen OR post-gen) as a standalone agent.

Bureau is unsuitable: it binds one shared HTTP port and doesn't generate
per-agent Inspector URLs (mailbox provisioning needs one URL per agent).
So each worker runs in its own process, on its own port, printing its
own Inspector URL.

Pre-gen workers (8201-8210) get a `work_handler` so the Coordinator can
dispatch BuildRequests to them; post-gen workers (8101-8119) are chat-
only (the v2 orchestrator runs analysis in-process).

Usage (from backend/):
    .venv/bin/python -m agentverse.worker <agent_id>
"""
from __future__ import annotations

import sys

from agentverse.base import build_agent
from agentverse.pre_gen import PERSONAS as PRE_GEN_PERSONAS
from agentverse.pre_gen import _make_handler
from agentverse.post_gen import PERSONAS as POST_GEN_PERSONAS
from agentverse.registry import POST_GEN_BY_ID, WORKERS_BY_ID


def main():
    if len(sys.argv) != 2:
        print("usage: python -m agentverse.worker <agent_id>", file=sys.stderr)
        sys.exit(2)
    agent_id = sys.argv[1]

    if agent_id in WORKERS_BY_ID:
        spec = WORKERS_BY_ID[agent_id]
        persona = PRE_GEN_PERSONAS.get(agent_id, f"Hi — I'm {spec.label}.")
        work_handler = _make_handler(agent_id)
    elif agent_id in POST_GEN_BY_ID:
        spec = POST_GEN_BY_ID[agent_id]
        persona = POST_GEN_PERSONAS.get(agent_id, f"Hi — I'm {spec.label}.")
        work_handler = None  # post-gen agents are chat-only on Agentverse
    else:
        print(f"unknown agent_id: {agent_id!r}", file=sys.stderr)
        valid = list(WORKERS_BY_ID) + list(POST_GEN_BY_ID)
        print(f"valid ids: {', '.join(valid)}", file=sys.stderr)
        sys.exit(2)

    agent = build_agent(
        spec=spec,
        chat_persona=persona,
        work_handler=work_handler,
    )

    print(f"[{spec.id}] address: {agent.address}", flush=True)
    agent.run()


if __name__ == "__main__":
    main()
