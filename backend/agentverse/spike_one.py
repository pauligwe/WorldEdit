"""
Spike: a single mailbox-backed Agentverse agent that responds to chat.

Run from backend/:
    .venv/bin/python -m agentverse.spike_one

On first run the console prints an Agent Inspector URL. Open it while
logged into agentverse.ai, choose "Connect → Mailbox", and Agentverse
will provision the mailbox bound to your account. After that the agent
should be discoverable on Agentverse and chattable from ASI:One.

The seed below is what makes the address stable across restarts —
keep it secret if you ever ship this beyond a demo, since whoever has
the seed can impersonate the agent.
"""
from datetime import datetime, timezone
from uuid import uuid4

from uagents import Agent, Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatMessage,
    ChatAcknowledgement,
    TextContent,
    EndSessionContent,
    chat_protocol_spec,
)


# Stable per-agent seed → stable agent1q... address. Do not reuse.
SEED = "conjure-spike-scene-describer-v1"

# AgentProfile limits `description` to 300 chars — keep it tight; long-form
# content goes in the README file referenced via readme_path.
DESCRIPTION = (
    "Tier 0 perception agent in the Conjure swarm. Given splat captures of "
    "an imagined 3D space, I produce a prose scene description and tags "
    "that downstream agents (Geolocator, Era, Mood & Palette, Story Seeds) "
    "consume as their seed context."
)

README_PATH = str(
    __import__("pathlib").Path(__file__).parent / "spike_one_README.md"
)

agent = Agent(
    name="scene-describer",
    seed=SEED,
    port=8200,
    mailbox=True,
    publish_agent_details=True,
    readme_path=README_PATH,
    description=DESCRIPTION,
)

chat = Protocol(spec=chat_protocol_spec)


@chat.on_message(ChatMessage)
async def on_chat(ctx: Context, sender: str, msg: ChatMessage):
    # Acknowledge receipt first — ASI:One expects this.
    await ctx.send(
        sender,
        ChatAcknowledgement(
            timestamp=datetime.now(timezone.utc),
            acknowledged_msg_id=msg.msg_id,
        ),
    )

    incoming = "".join(c.text for c in msg.content if isinstance(c, TextContent))
    ctx.logger.info(f"chat from {sender[:14]}…: {incoming!r}")

    reply_text = (
        "Hi — I'm Scene Describer, one of the perception agents in the "
        "Conjure swarm. Given splat captures I produce a short prose "
        "summary plus tags. You said: "
        f"{incoming!r}"
    )

    await ctx.send(
        sender,
        ChatMessage(
            timestamp=datetime.now(timezone.utc),
            msg_id=uuid4(),
            content=[
                TextContent(type="text", text=reply_text),
                EndSessionContent(type="end-session"),
            ],
        ),
    )


@chat.on_message(ChatAcknowledgement)
async def on_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.debug(f"ack from {sender[:14]}… for {msg.acknowledged_msg_id}")


agent.include(chat, publish_manifest=True)


if __name__ == "__main__":
    print(f"agent address: {agent.address}")
    agent.run()
