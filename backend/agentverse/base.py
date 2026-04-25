"""Shared scaffolding for every pre-gen agent.

All workers and the coordinator share the same skeleton: a uagents Agent
bound to a mailbox, a chat protocol that acks + replies with a canned
explanation, and a custom-message protocol for the BuildRequest →
BuildArtifact pipeline. This module hides that boilerplate so each
agent file is just a thin descriptor.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Awaitable, Callable, Optional
from uuid import uuid4

from uagents import Agent, Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    TextContent,
    chat_protocol_spec,
)

from agentverse.messages import BuildArtifact, BuildRequest
from agentverse.registry import PreGenAgent

README_DIR = Path(__file__).parent / "readmes"


WorkHandler = Callable[[Context, str, BuildRequest], Awaitable[BuildArtifact]]


def _readme_path(filename: str) -> str:
    return str(README_DIR / filename)


def make_chat_reply(persona: str, incoming: str) -> str:
    """Build the canned chat reply for an agent's ASI:One DMs."""
    return (
        f"{persona}\n\n"
        f"You said: {incoming!r}\n\n"
        "I'm one of ten pre-generation agents in the Conjure swarm. "
        "I run as part of a pipeline orchestrated by the Coordinator — "
        "if you want to actually build a world, message the Coordinator "
        "with a one-line scene description."
    )


def build_agent(
    spec: PreGenAgent,
    chat_persona: str,
    work_handler: Optional[WorkHandler] = None,
) -> Agent:
    """Construct a mailbox-backed agent that handles chat + (optionally) work.

    `chat_persona` is the first line of the canned chat reply — a short
    self-introduction shown when a user DMs this agent on ASI:One.

    `work_handler` is the BuildRequest handler. Coordinator passes None
    here (it has its own orchestration logic); each worker passes a
    handler that returns its canned BuildArtifact.
    """
    # Workers exist primarily so they appear on Agentverse for
    # judges/users to inspect. The Coordinator does NOT actually dispatch
    # BuildRequests over the wire — it calls each worker's handler
    # in-process (see coordinator.py). So the only endpoint we need
    # advertised is the Agentverse mailbox URL, which is what lets
    # ASI:One DMs reach the agent for its standalone chat persona.
    mailbox_endpoint = "https://agentverse.ai/v2/agents/mailbox/submit"
    agent = Agent(
        name=spec.name,
        seed=spec.seed,
        port=spec.port,
        endpoint=[mailbox_endpoint],
        publish_agent_details=True,
        readme_path=_readme_path(spec.readme_filename),
        description=spec.description,
    )

    chat = Protocol(spec=chat_protocol_spec)

    @chat.on_message(ChatMessage)
    async def _on_chat(ctx: Context, sender: str, msg: ChatMessage):
        await ctx.send(
            sender,
            ChatAcknowledgement(
                timestamp=datetime.now(timezone.utc),
                acknowledged_msg_id=msg.msg_id,
            ),
        )
        incoming = "".join(c.text for c in msg.content if isinstance(c, TextContent))
        ctx.logger.info(f"chat from {sender[:14]}…: {incoming!r}")
        await ctx.send(
            sender,
            ChatMessage(
                timestamp=datetime.now(timezone.utc),
                msg_id=uuid4(),
                content=[
                    TextContent(type="text", text=make_chat_reply(chat_persona, incoming)),
                    EndSessionContent(type="end-session"),
                ],
            ),
        )

    @chat.on_message(ChatAcknowledgement)
    async def _on_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
        ctx.logger.debug(f"ack from {sender[:14]}… for {msg.acknowledged_msg_id}")

    agent.include(chat, publish_manifest=True)

    if work_handler is not None:
        work = Protocol(name=f"conjure-build-{spec.id}", version="1.0.0")

        @work.on_message(BuildRequest)
        async def _on_build(ctx: Context, sender: str, req: BuildRequest):
            ctx.logger.info(
                f"build request {req.request_id[:8]}… from coordinator: "
                f"{req.prompt!r}"
            )
            artifact = await work_handler(ctx, sender, req)
            await ctx.send(sender, artifact)

        agent.include(work)

    return agent
