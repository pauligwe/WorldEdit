import asyncio
import pytest
from core.status_bus import StatusBus, AgentStatus


async def test_publish_subscribe_roundtrip():
    bus = StatusBus()
    q = bus.subscribe("w1")
    await bus.publish("w1", AgentStatus(agent="intent_parser", state="running", message="parsing"))
    evt = await asyncio.wait_for(q.get(), timeout=1)
    assert evt.agent == "intent_parser"
    assert evt.state == "running"


async def test_unknown_world_no_subscribers():
    bus = StatusBus()
    await bus.publish("nope", AgentStatus(agent="x", state="done"))
