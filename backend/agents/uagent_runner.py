"""Spin up 14 uAgents on local ports, register to Agentverse, implement Chat Protocol echo.

This is symbolic: the actual pipeline runs via direct function calls in orchestrator.run_pipeline.
The uAgents satisfy the Fetch.ai track requirement: 14 agents on Agentverse with Chat Protocol.
"""
import os
import asyncio
import threading
from dotenv import load_dotenv
from uagents import Agent, Context, Protocol, Model

load_dotenv()
AV_KEY = os.environ.get("AGENTVERSE_API_KEY")

AGENT_NAMES = [
    "world_build_orchestrator",
    "world_build_intent_parser",
    "world_build_blueprint_architect",
    "world_build_compliance_critic",
    "world_build_geometry_builder",
    "world_build_lighting_designer",
    "world_build_material_stylist",
    "world_build_furniture_planner",
    "world_build_placement_validator",
    "world_build_product_scout",
    "world_build_style_matcher",
    "world_build_pricing_estimator",
    "world_build_navigation_planner",
    "world_build_chat_edit_coordinator",
]


class ChatMessage(Model):
    content: str


def _make_agent(name: str, port: int) -> Agent:
    seed = f"world-build-{name}-seed-2026"
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
        await ctx.send(sender, ChatMessage(content=f"[{name}] received: {msg.content[:80]}"))

    agent.include(proto, publish_manifest=True)
    return agent


def start_all_in_background() -> None:
    """Start all 14 uAgents in a daemon thread. They register asynchronously."""
    def runner():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        agents = [_make_agent(name, 8100 + i) for i, name in enumerate(AGENT_NAMES)]
        for a in agents:
            loop.create_task(a.run_async())
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass

    t = threading.Thread(target=runner, name="uagent-runner", daemon=True)
    t.start()
