"""End-to-end test client: DM the Coordinator, print every reply.

Sends a ChatMessage with the prompt, then listens for ChatMessages back
until we see EndSessionContent (or timeout).

Usage (from backend/):
    .venv/bin/python -m agentverse.test_client "a sunlit forest cabin"
"""
from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timezone
from uuid import uuid4

from uagents import Agent, Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    TextContent,
    chat_protocol_spec,
)

from agentverse.registry import COORDINATOR

# Stable seed → stable address; lets us re-run without changing identity.
TEST_SEED = "conjure-test-client-v1"
TEST_PORT = 8299

PROMPT = sys.argv[1] if len(sys.argv) > 1 else "a sunlit forest cabin"

agent = Agent(
    name="conjure-test-client",
    seed=TEST_SEED,
    port=TEST_PORT,
    mailbox=False,         # local-only; we don't need Agentverse routing
    endpoint=[f"http://127.0.0.1:{TEST_PORT}/submit"],
)

chat = Protocol(spec=chat_protocol_spec)

# Resolve coordinator address from registry.
from uagents.crypto import Identity
COORD_ADDR = Identity.from_seed(COORDINATOR.seed, 0).address

start_time: float | None = None
done = asyncio.Event()


@agent.on_event("startup")
async def kick_off(ctx: Context):
    global start_time
    start_time = asyncio.get_event_loop().time()
    ctx.logger.info(f"sending prompt to coordinator {COORD_ADDR[:16]}…: {PROMPT!r}")
    await ctx.send(
        COORD_ADDR,
        ChatMessage(
            timestamp=datetime.now(timezone.utc),
            msg_id=uuid4(),
            content=[TextContent(type="text", text=PROMPT)],
        ),
    )


@chat.on_message(ChatMessage)
async def on_reply(ctx: Context, sender: str, msg: ChatMessage):
    elapsed = asyncio.get_event_loop().time() - (start_time or 0)
    # Ack like ASI:One would.
    await ctx.send(
        sender,
        ChatAcknowledgement(
            timestamp=datetime.now(timezone.utc),
            acknowledged_msg_id=msg.msg_id,
        ),
    )
    text = "".join(c.text for c in msg.content if isinstance(c, TextContent))
    print(f"[{elapsed:5.1f}s] {text}", flush=True)
    if any(isinstance(c, EndSessionContent) for c in msg.content):
        print(f"\n--- session ended after {elapsed:.1f}s ---", flush=True)
        done.set()


@chat.on_message(ChatAcknowledgement)
async def on_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    pass


agent.include(chat)


async def watchdog():
    """Force-exit after 180s even if no end-session arrives."""
    try:
        await asyncio.wait_for(done.wait(), timeout=180.0)
    except asyncio.TimeoutError:
        print("\n--- watchdog: 180s elapsed, forcing exit ---", flush=True)
    # Give in-flight sends a moment, then exit.
    await asyncio.sleep(0.5)
    import os
    os._exit(0)


@agent.on_event("startup")
async def start_watchdog(ctx: Context):
    asyncio.create_task(watchdog())


if __name__ == "__main__":
    print(f"test client address: {agent.address}")
    print(f"coordinator address: {COORD_ADDR}")
    print()
    agent.run()
