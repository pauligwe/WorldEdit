"""Boot all 19 uagents.Agent processes on local ports.

These agents are real members of the Agentverse network when AGENTVERSE_API_KEY
is set: they register, accept Chat Protocol messages, and respond.

The orchestrator does NOT route work through these uagent instances — it
calls run() functions directly via the registry. The uagents are the
'on-network presence' that satisfies the Fetch.ai track requirement; the
orchestrator's in-process DAG is what produces results.

This separation is intentional: it keeps the in-process pipeline fast and
debuggable while still giving us 19 agents listed on Agentverse.
"""
import asyncio
import os
import threading
from dotenv import load_dotenv
from uagents import Agent, Context, Protocol, Model

from agents_v2.manifest import AGENTS

load_dotenv()
AV_KEY = os.environ.get("AGENTVERSE_API_KEY")


class ChatMessage(Model):
    content: str


def _make_agent(agent_id: str, label: str, port: int) -> Agent:
    name = f"conjure_{agent_id}"
    seed = f"conjure-{agent_id}-seed-2026"
    agent = Agent(
        name=name,
        seed=seed,
        port=port,
        endpoint=[f"http://127.0.0.1:{port}/submit"],
        mailbox=AV_KEY or "",
    )
    proto = Protocol(name="chat", version="0.1")

    @proto.on_message(model=ChatMessage)
    async def handle(ctx: Context, sender: str, msg: ChatMessage):
        await ctx.send(sender, ChatMessage(content=f"[{label}] received: {msg.content[:80]}"))

    agent.include(proto, publish_manifest=True)
    return agent


def build_agents() -> list[Agent]:
    return [_make_agent(a.id, a.label, a.port) for a in AGENTS]


def start_all_in_background() -> None:
    """Daemon thread runs all 19 uagents in their own asyncio loop."""
    def runner_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        agents = build_agents()
        for a in agents:
            loop.create_task(a.run_async())
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass

    t = threading.Thread(target=runner_thread, name="conjure-uagent-runner", daemon=True)
    t.start()
