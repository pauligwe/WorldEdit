"""Coordinator agent — public entry point for the Conjure swarm.

Flow when a user DMs the Coordinator on ASI:One:
1. Ack the chat message.
2. Reply once with a "kicking off the pipeline" preamble.
3. Call each of the 10 worker handlers in-process, on a fixed 6s
   schedule per stage (≈60s total wall time).
4. While each stage is "running", a ticker re-sends the full status
   card every ~1s with the active row marked, the progress bar
   counting up, and the leading-edge cell flickering for liveness.
5. When all 10 stages are done, send the final world link and end.

Why in-process: each worker handler returns a *canned* artifact (see
pre_gen._make_handler). Routing those over Agentverse mailboxes adds
30-60s per hop, blowing total wall time well past 5 minutes. Workers
still run separately so they show up on Agentverse for judges to
inspect; the Coordinator just doesn't need the wire to drive them.

Run from backend/:
    .venv/bin/python -m agentverse.coordinator
"""
from __future__ import annotations

import asyncio
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from uagents import Agent, Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    TextContent,
    chat_protocol_spec,
)

from agentverse.messages import BuildRequest
from agentverse.pre_gen import _make_handler
from agentverse.registry import COORDINATOR, WORKERS

README_PATH = str(Path(__file__).parent / "readmes" / COORDINATOR.readme_filename)

# Per-stage wall-clock budget. 10 stages × 10s ≈ 100s end-to-end.
# We send exactly ONE status bubble per stage (no mid-stage ticker),
# so message cadence == STAGE_DURATION_S. ASI:One/Flockx rate-limits
# the chat webhook somewhere around 1 msg / few seconds — at 10s
# spacing we stay comfortably under it for the full pipeline.
STAGE_DURATION_S = 10.0

FRONTEND_BASE = os.environ.get("CONJURE_FRONTEND_BASE", "http://localhost:3000")


# ---------- Build the agent ----------
COORD_MAILBOX_ENDPOINT = "https://agentverse.ai/v2/agents/mailbox/submit"
agent = Agent(
    name=COORDINATOR.name,
    seed=COORDINATOR.seed,
    port=COORDINATOR.port,
    endpoint=[COORD_MAILBOX_ENDPOINT],
    publish_agent_details=True,
    readme_path=README_PATH,
    description=COORDINATOR.description,
)

chat = Protocol(spec=chat_protocol_spec)


# ---------- Helpers ----------
_MENTION_RE = re.compile(r"^@agent1\w+\s*", re.IGNORECASE)


def _strip_mentions(text: str) -> str:
    """Remove leading @agent1… mentions ASI:One adds to DMs."""
    cleaned = text
    while True:
        m = _MENTION_RE.match(cleaned)
        if not m:
            break
        cleaned = cleaned[m.end():]
    return cleaned.strip()


async def _send_text(ctx: Context, recipient: str, text: str, end: bool = False) -> None:
    content = [TextContent(type="text", text=text)]
    if end:
        content.append(EndSessionContent(type="end-session"))
    await ctx.send(
        recipient,
        ChatMessage(
            timestamp=datetime.now(timezone.utc),
            msg_id=uuid4(),
            content=content,
        ),
    )


# ---------- Status card rendering ----------
BAR_TOTAL = 10  # one square per pipeline stage


def _render_status_card(active_idx: int | None, done_ids: set[str]) -> str:
    """Render the full agent checklist with a progress bar footer.

    ASI:One renders messages as Markdown; we use blank lines between
    rows to force paragraph breaks (single \\n collapses to a space).
    Bar uses square emoji (⬛ filled / 🟧 active / ⬜ empty) so each
    cell renders as a proper tile.
    """
    lines = []
    for i, spec in enumerate(WORKERS):
        if spec.id in done_ids:
            mark = "✅"
        elif i == active_idx:
            mark = "🔸"
        else:
            mark = "⬜"
        lines.append(f"{mark} {spec.label}")
    body = "\n\n".join(lines)

    total = len(WORKERS)
    completed = len(done_ids)
    if active_idx is not None and completed < BAR_TOTAL:
        bar = "⬛" * completed + "🟧" + "⬜" * (BAR_TOTAL - completed - 1)
    else:
        bar = "⬛" * completed + "⬜" * (BAR_TOTAL - completed)

    footer = f"\n\n**Progress:** {bar} {completed}/{total}"
    return body + footer


# ---------- Chat handler ----------
@chat.on_message(ChatMessage)
async def on_chat(ctx: Context, sender: str, msg: ChatMessage):
    await ctx.send(
        sender,
        ChatAcknowledgement(
            timestamp=datetime.now(timezone.utc),
            acknowledged_msg_id=msg.msg_id,
        ),
    )

    raw = "".join(c.text for c in msg.content if isinstance(c, TextContent)).strip()
    incoming = _strip_mentions(raw)
    ctx.logger.info(f"chat from {sender[:14]}…: {raw!r} → cleaned {incoming!r}")

    if not incoming:
        await _send_text(
            ctx, sender,
            "Send me a one-line world prompt — e.g. 'a sunlit forest cabin' "
            "or 'a downtown office at golden hour' — and I'll route it through "
            "the pre-gen swarm.",
            end=True,
        )
        return

    request_id = uuid4().hex
    await _send_text(
        ctx, sender,
        f"Got it. Routing '{incoming}' through the pre-gen pipeline "
        f"({len(WORKERS)} agents)…",
    )

    context: dict = {}
    done_ids: set[str] = set()
    for i, spec in enumerate(WORKERS):
        # Send one status card per stage (active row marked, prior
        # rows checked). Cadence == STAGE_DURATION_S, well under the
        # ASI:One/Flockx rate-limit threshold.
        await _send_text(ctx, sender, _render_status_card(i, done_ids))

        # Run the worker handler in-process AND wait out the stage's
        # fixed wall-clock budget so the user has time to read.
        handler = _make_handler(spec.id)
        req = BuildRequest(request_id=request_id, prompt=incoming, context=context)
        artifact, _ = await asyncio.gather(
            handler(ctx, sender, req),
            asyncio.sleep(STAGE_DURATION_S),
        )

        if artifact.error:
            await _send_text(
                ctx, sender,
                f"⚠ {spec.label} returned an error: {artifact.error}. Aborting.",
                end=True,
            )
            return

        context[spec.id] = artifact.payload
        done_ids.add(spec.id)

    # Final all-checked card.
    await _send_text(ctx, sender, _render_status_card(None, done_ids))

    world_id = context.get("marble_dispatcher", {}).get("world_id", "cabin")
    world_url = f"{FRONTEND_BASE}/world/{world_id}"
    await _send_text(
        ctx, sender,
        f"\n🎉 World ready — open it here:\n{world_url}\n\n"
        "(The post-generation analysis swarm runs once you load the world.)",
        end=True,
    )


@chat.on_message(ChatAcknowledgement)
async def on_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.debug(f"ack from {sender[:14]}… for {msg.acknowledged_msg_id}")


agent.include(chat, publish_manifest=True)


if __name__ == "__main__":
    print("=" * 60)
    print("Conjure Coordinator")
    print("=" * 60)
    print(f"  address: {agent.address}")
    print(f"  port:    {COORDINATOR.port}")
    print()
    print(f"  Calls {len(WORKERS)} pre-gen worker handlers in-process.")
    print(f"  Pacing: {STAGE_DURATION_S:.0f}s per stage ≈ "
          f"{STAGE_DURATION_S * len(WORKERS):.0f}s total.")
    print("=" * 60)
    agent.run()
