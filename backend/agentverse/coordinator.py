"""Coordinator agent — public entry point for the Conjure swarm.

Flow when a user DMs the Coordinator on ASI:One:
1. Ack the chat message.
2. Create a Stripe Checkout session for $5 (configurable via
   STRIPE_AMOUNT_CENTS) and send a `RequestPayment`. The user's prompt
   is stashed in an in-memory `_pending` dict keyed by sender address.
3. ASI:One renders the embedded Stripe checkout from the
   `metadata.stripe` payload. After the user pays, the buyer agent
   sends `CommitPayment(transaction_id=<checkout_session_id>)`.
4. We verify the session is `paid` via the Stripe API. If so, we
   reply `CompletePayment` and kick off the 10-stage pipeline using
   the stashed prompt. Otherwise we send `RejectPayment`.
5. The pipeline calls each of the 10 worker handlers in-process on
   a fixed schedule per stage; a status card is re-sent each stage.
6. When all 10 stages are done, send the final world link and end.

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
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv
from uagents import Agent, Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    TextContent,
    chat_protocol_spec,
)
from uagents_core.contrib.protocols.payment import (
    CommitPayment,
    CompletePayment,
    Funds,
    RejectPayment,
    RequestPayment,
    payment_protocol_spec,
)

from agentverse.messages import BuildRequest
from agentverse.pre_gen import _make_handler
from agentverse.registry import COORDINATOR, WORKERS

# Load backend/.env so Stripe + Agentverse creds resolve when launched as
# `python -m agentverse.coordinator` from the backend/ directory. Must run
# before the STRIPE_* env reads below.
load_dotenv()

README_PATH = str(Path(__file__).parent / "readmes" / COORDINATOR.readme_filename)

# Per-stage wall-clock budget. 10 stages × 10s ≈ 100s end-to-end.
# We send exactly ONE status bubble per stage (no mid-stage ticker),
# so message cadence == STAGE_DURATION_S. ASI:One/Flockx rate-limits
# the chat webhook somewhere around 1 msg / few seconds — at 10s
# spacing we stay comfortably under it for the full pipeline.
STAGE_DURATION_S = 10.0

FRONTEND_BASE = os.environ.get("CONJURE_FRONTEND_BASE", "http://localhost:3000")


# ---------- Stripe payment config ----------
# Loaded lazily so the agent can boot for unrelated testing without Stripe
# configured. The first checkout-creation call will raise if these are unset.
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY")
STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY")
STRIPE_AMOUNT_CENTS = int(os.environ.get("STRIPE_AMOUNT_CENTS", "500"))  # $5.00
STRIPE_CURRENCY = (os.environ.get("STRIPE_CURRENCY", "usd") or "usd").strip().lower()
STRIPE_PRODUCT_NAME = (
    os.environ.get("STRIPE_PRODUCT_NAME", "Conjure world generation")
    or "Conjure world generation"
).strip()
STRIPE_SUCCESS_URL = (
    os.environ.get("STRIPE_SUCCESS_URL", "https://agentverse.ai/payment-success") or ""
).strip()
STRIPE_CHECKOUT_DEADLINE_S = int(os.environ.get("STRIPE_CHECKOUT_DEADLINE_S", "300"))

# Per-sender pending payment state. Resets on agent restart — by design.
# value: {"prompt": str, "checkout": dict, "session_id": str}
_pending: dict[str, dict] = {}


def _stripe_sdk():
    """Lazy stripe import + api_key install. Raises if creds missing."""
    if not (STRIPE_SECRET_KEY and STRIPE_PUBLISHABLE_KEY):
        raise RuntimeError(
            "Missing STRIPE_SECRET_KEY / STRIPE_PUBLISHABLE_KEY in env — "
            "the Coordinator's payment flow cannot run without these."
        )
    import stripe  # type: ignore

    stripe.api_key = STRIPE_SECRET_KEY
    return stripe


def _create_embedded_checkout(*, prompt: str, user_address: str, chat_session_id: str) -> dict:
    """Create a Stripe embedded Checkout session for one $5 generation.

    Returns the dict shape ASI:One's payment UI consumes — matches the
    Innovation Lab horoscope reference exactly.
    """
    stripe = _stripe_sdk()
    return_url = (
        f"{STRIPE_SUCCESS_URL}"
        f"?session_id={{CHECKOUT_SESSION_ID}}"
        f"&chat_session_id={chat_session_id}"
        f"&user={user_address}"
    )
    # Stripe requires expires_at >= 30 min in the future for Checkout Sessions.
    expires_at = int(time.time()) + 1800
    description = f"World generation: {prompt[:120]}"
    # Stripe deprecated `ui_mode="embedded"` — current value is `embedded_page`.
    session = stripe.checkout.Session.create(
        ui_mode="embedded_page",
        redirect_on_completion="if_required",
        payment_method_types=["card"],
        mode="payment",
        return_url=return_url,
        expires_at=expires_at,
        line_items=[
            {
                "price_data": {
                    "currency": STRIPE_CURRENCY,
                    "product_data": {
                        "name": STRIPE_PRODUCT_NAME,
                        "description": description,
                    },
                    "unit_amount": STRIPE_AMOUNT_CENTS,
                },
                "quantity": 1,
            }
        ],
        metadata={
            "user_address": user_address,
            "session_id": chat_session_id,
            "service": "world_generation",
            "prompt": prompt[:500],
        },
    )
    return {
        "client_secret": session.client_secret,
        # Both keys for compatibility with different ASI:One UI builds.
        "id": session.id,
        "checkout_session_id": session.id,
        "publishable_key": STRIPE_PUBLISHABLE_KEY,
        "currency": STRIPE_CURRENCY,
        "amount_cents": STRIPE_AMOUNT_CENTS,
        "ui_mode": "embedded_page",
    }


def _verify_checkout_session_paid(checkout_session_id: str) -> bool:
    stripe = _stripe_sdk()
    session = stripe.checkout.Session.retrieve(checkout_session_id)
    return getattr(session, "payment_status", None) == "paid"


def _amount_str() -> str:
    """Format the configured price as a 'X.YY' string for Funds.amount."""
    return f"{STRIPE_AMOUNT_CENTS / 100:.2f}"


def _amount_display() -> str:
    """Format for human-readable messages — drops trailing .00."""
    dollars = STRIPE_AMOUNT_CENTS / 100
    return f"${dollars:.0f}" if dollars == int(dollars) else f"${dollars:.2f}"


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
# ASI:One prefixes DMs with @<agent_name_or_address>. Match either the
# raw bech32 form (`@agent1…`) or a slug like `@conjure-coordinator`.
_MENTION_RE = re.compile(r"^@[\w-]+\s*", re.IGNORECASE)


def _strip_mentions(text: str) -> str:
    """Remove leading @agent1… or @<slug> mentions ASI:One adds to DMs."""
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


# ---------- Pipeline runner (extracted; called after CommitPayment is verified) ----------
async def _run_pipeline(ctx: Context, sender: str, prompt: str) -> None:
    request_id = uuid4().hex
    await _send_text(
        ctx, sender,
        f"Routing '{prompt}' through the pre-gen pipeline "
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
        req = BuildRequest(request_id=request_id, prompt=prompt, context=context)
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


# ---------- Chat handler (gates pipeline behind a $5 Stripe payment) ----------
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
            "the pre-gen swarm.\n\n"
            f"Each generation is **{_amount_display()} USD** via Stripe.",
            end=True,
        )
        return

    # If a payment is already pending for this sender, don't create a second
    # checkout — re-send the existing RequestPayment so ASI:One can re-render
    # the embedded checkout. Mirrors the Innovation Lab horoscope behaviour.
    pending = _pending.get(sender)
    if pending:
        ctx.logger.info(f"re-sending pending RequestPayment to {sender[:14]}…")
        req = RequestPayment(
            accepted_funds=[
                Funds(currency="USD", amount=_amount_str(), payment_method="stripe"),
            ],
            recipient=str(ctx.agent.address),
            deadline_seconds=STRIPE_CHECKOUT_DEADLINE_S,
            reference=str(ctx.session),
            description=(
                f"Pay {_amount_display()} to generate your world: "
                f"{pending['prompt'][:120]}"
            ),
            metadata={"stripe": pending["checkout"], "service": "world_generation"},
        )
        await ctx.send(sender, req)
        await _send_text(
            ctx, sender,
            "You have a pending payment. Complete the Stripe checkout above "
            "and I'll start the build.",
        )
        return

    # Fresh prompt → create a new Stripe Checkout session and stash the prompt.
    try:
        checkout = await asyncio.to_thread(
            _create_embedded_checkout,
            prompt=incoming,
            user_address=sender,
            chat_session_id=str(ctx.session),
        )
    except Exception as e:
        ctx.logger.error(f"stripe checkout creation failed: {e}")
        await _send_text(
            ctx, sender,
            "Sorry — I couldn't open a Stripe checkout session. "
            "Please try again in a moment.",
            end=True,
        )
        return

    _pending[sender] = {
        "prompt": incoming,
        "checkout": checkout,
        "session_id": str(ctx.session),
    }

    req = RequestPayment(
        accepted_funds=[
            Funds(currency="USD", amount=_amount_str(), payment_method="stripe"),
        ],
        recipient=str(ctx.agent.address),
        deadline_seconds=STRIPE_CHECKOUT_DEADLINE_S,
        reference=str(ctx.session),
        description=(
            f"Pay {_amount_display()} to generate your world: {incoming[:120]}"
        ),
        metadata={"stripe": checkout, "service": "world_generation"},
    )
    await ctx.send(sender, req)
    await _send_text(
        ctx, sender,
        f"Got it: '{incoming}'.\n\n"
        f"Each generation is **{_amount_display()} USD**. Complete the Stripe "
        "checkout above and I'll kick off the {n}-agent pipeline.".format(
            n=len(WORKERS)
        ),
    )


@chat.on_message(ChatAcknowledgement)
async def on_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.debug(f"ack from {sender[:14]}… for {msg.acknowledged_msg_id}")


# ---------- Payment handlers ----------
payment = Protocol(spec=payment_protocol_spec, role="seller")


@payment.on_message(CommitPayment)
async def on_commit(ctx: Context, sender: str, msg: CommitPayment):
    ctx.logger.info(
        f"CommitPayment from {sender[:14]}… "
        f"method={msg.funds.payment_method} txn={msg.transaction_id}"
    )

    if msg.funds.payment_method != "stripe" or not msg.transaction_id:
        await ctx.send(
            sender,
            RejectPayment(reason="Unsupported payment method (expected stripe)."),
        )
        return

    try:
        paid = await asyncio.to_thread(
            _verify_checkout_session_paid, msg.transaction_id
        )
    except Exception as e:
        ctx.logger.error(f"stripe verify failed: {e}")
        await ctx.send(
            sender,
            RejectPayment(reason="Could not verify Stripe session — please retry."),
        )
        return

    if not paid:
        await ctx.send(
            sender,
            RejectPayment(
                reason="Stripe payment not completed yet. Please finish checkout."
            ),
        )
        return

    pending = _pending.pop(sender, None)
    await ctx.send(sender, CompletePayment(transaction_id=msg.transaction_id))

    if not pending:
        # Coordinator restarted between RequestPayment and CommitPayment, or
        # we got a stale commit. Apologise and ask for a fresh prompt.
        await _send_text(
            ctx, sender,
            "Payment received, but I no longer have your original prompt "
            "(this can happen if the agent restarted). Send your world "
            "prompt again to start a new generation.",
            end=True,
        )
        return

    await _send_text(ctx, sender, "✅ Payment received. Starting your build now…")
    await _run_pipeline(ctx, sender, pending["prompt"])


@payment.on_message(RejectPayment)
async def on_reject(ctx: Context, sender: str, msg: RejectPayment):
    ctx.logger.info(f"RejectPayment from {sender[:14]}…: {msg.reason!r}")
    _pending.pop(sender, None)
    reason = (msg.reason or "").strip()
    tail = f" Reason: {reason}" if reason else ""
    await _send_text(
        ctx, sender,
        f"Payment cancelled.{tail}\nSend a new prompt anytime to try again.",
        end=True,
    )


agent.include(chat, publish_manifest=True)
agent.include(payment, publish_manifest=True)


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
    if STRIPE_SECRET_KEY and STRIPE_PUBLISHABLE_KEY:
        print(f"  Stripe: configured — {_amount_display()} per generation.")
    else:
        print("  Stripe: NOT configured — set STRIPE_SECRET_KEY and "
              "STRIPE_PUBLISHABLE_KEY in backend/.env.")
    print("=" * 60)
    agent.run()
