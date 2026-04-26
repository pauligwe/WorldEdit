"""Fire a realistic ChatMessage at every Conjure agent so Agentverse
interaction counters tick up before the demo.

Each message is tailored to the agent's role and includes a
plausible-sounding prompt referencing one of our cached worlds. The
sender is a fresh mailbox-backed agent so the messages route through
Agentverse exactly like an ASI:One DM would.

Usage (from backend/):
    .venv/bin/python -m agentverse.simulate_chats          # one round
    .venv/bin/python -m agentverse.simulate_chats --rounds 3
"""
from __future__ import annotations

import argparse
import asyncio
import random
from datetime import datetime, timezone
from uuid import uuid4

from uagents import Agent, Context, Protocol
from uagents.crypto import Identity
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    TextContent,
    chat_protocol_spec,
)

from agentverse.registry import ALL


# Per-agent prompt seeds. Each list rotates so repeated rounds don't
# send the exact same message. Tone is "curious user exploring the
# Conjure swarm" — short, on-topic, role-appropriate.
PROMPTS: dict[str, list[str]] = {
    "coordinator": [
        "a sunlit forest cabin at golden hour",
        "a noir detective office, rain on the window",
        "a warm grecian courtyard at dusk",
        "an abandoned arcade in the 1980s",
    ],
    # ---- Pre-gen ----
    "intent_parser": [
        "Parse this prompt for me: 'a cozy log cabin in a snowy forest at twilight'.",
        "What's the structured intent for 'cyberpunk noodle bar, neon, rain'?",
        "Break down the genre/mood/era for 'a sunlit grecian courtyard with a fountain'.",
    ],
    "reference_curator": [
        "Pull visual references for a sunlit forest cabin — what film stills come to mind?",
        "What references would you grab for a 1970s detective office?",
        "References for a neon-lit cyberpunk diner, please.",
    ],
    "style_synthesizer": [
        "Pick one art direction for a forest cabin scene — Ghibli vs Wes Anderson vs noir?",
        "Synthesize a coherent style for 'cyberpunk noodle bar, neon, rain'.",
        "What single style would you lock in for a grecian courtyard at dusk?",
    ],
    "mood_lighting_director": [
        "What time of day and color temperature would you choose for a forest cabin?",
        "Lock in lighting for a noir detective office — key/fill ratio?",
        "Mood and lighting plan for a grecian courtyard at golden hour, please.",
    ],
    "scene_composer": [
        "How would you compose a forest cabin scene — focal point, sightlines?",
        "Composition for a noir office: where's the desk, where's the door?",
        "Lay out the spatial composition of a grecian courtyard with a fountain.",
    ],
    "prompt_engineer": [
        "Assemble a Marble-ready prompt for a sunlit forest cabin.",
        "Final prompt for a cyberpunk noodle bar, neon, rain — with weighting.",
        "Prompt structure tip: how do you push Marble toward 'volumetric light'?",
    ],
    "marble_dispatcher": [
        "Dispatch this prompt to Marble: 'a sunlit forest cabin'.",
        "How long is the queue right now? My prompt is 'noir detective office'.",
        "Send 'grecian courtyard at dusk' to Marble and let me know when it's ready.",
    ],
    "capture_planner": [
        "Plan three capture angles for a forest cabin splat.",
        "What viewpoints would you grab from a noir office splat?",
        "Capture plan for a grecian courtyard splat — 3 non-redundant angles.",
    ],
    "quality_critic": [
        "Inspect the cabin captures for clipping or prompt drift.",
        "Anything obviously broken in the noir office captures?",
        "Run a QC pass on the grecian courtyard splat for me.",
    ],
    "continuity_checker": [
        "Does 'a cozy forest cabin' look cozy in the final splat? Confidence?",
        "Check continuity: prompt was 'noir office, rain on window' — did we land it?",
        "Final continuity score for the grecian courtyard, please.",
    ],
    # ---- Post-gen ----
    "scene_describer": [
        "Describe my generated forest cabin world from these captures.",
        "Give me a one-paragraph description of the grecian courtyard scene.",
        "Describe the noir office world plus structured tags, please.",
    ],
    "object_inventory": [
        "List every object visible in the cabin scene.",
        "Inventory the grecian courtyard with rough positions.",
        "What objects can you see in the noir office?",
    ],
    "spatial_layout": [
        "Floorplan for the cabin world — rooms and adjacencies?",
        "Sketch a room graph for the living room scene.",
        "Estimate the footprint of the grecian courtyard.",
    ],
    "geolocator": [
        "Where in the real world could the forest cabin plausibly be? Top 3.",
        "Candidate regions for the grecian courtyard, with confidence?",
        "Where would a noir office like this exist? Top 3 candidates.",
    ],
    "filming_scout": [
        "Find me 3-5 real filming locations matching the cabin's vibe.",
        "Peerspace listings that match the noir office mood, please.",
        "Filming scout report for the grecian courtyard — locations and day rates.",
    ],
    "era_estimator": [
        "When is the cabin scene set? Decade or century?",
        "Estimate the era for the grecian courtyard — anachronisms allowed?",
        "Time period for the noir office, based on visible decor?",
    ],
    "architectural_style": [
        "Classify the architectural style of the cabin.",
        "What style is the grecian courtyard — neoclassical, revival, what?",
        "Architectural style of the noir office — features that drove the call?",
    ],
    "shot_list": [
        "Plan a 5-shot cinematographer's list for the cabin scene.",
        "Shot list for the grecian courtyard — lenses and beats.",
        "Cinematographer's shot list for the noir office, please.",
    ],
    "mood_palette": [
        "Pull a 5-color palette out of the cabin scene plus a LUT.",
        "Color grade starting point for the grecian courtyard?",
        "Mood palette and film stock for the noir office.",
    ],
    "soundscape": [
        "Design the ambient soundscape for the cabin world.",
        "Foley list for the grecian courtyard with mix suggestions.",
        "What would I hear standing inside the noir office?",
    ],
    "prop_shopping": [
        "Real shopping list for the cabin world — Amazon/Wayfair/IKEA links.",
        "Prop shopping list for the grecian courtyard build.",
        "Buy-list to dress the noir office for real.",
    ],
    "set_dressing": [
        "Suggest 5-10 set dressing changes that push the cabin further.",
        "Set dressing additions for the grecian courtyard, in style?",
        "Tweaks to the noir office set dressing without breaking continuity?",
    ],
    "story_seed": [
        "Write 3 story premises set in the cabin world.",
        "Story seeds for the grecian courtyard — different genres.",
        "Three film premises grounded in the noir office.",
    ],
    "character_suggester": [
        "Propose 3-5 character cards for the cabin world.",
        "Who lives or works in the grecian courtyard?",
        "Character cards for the noir office — what tension do they bring?",
    ],
    "npc_dialogue": [
        "Sample NPC dialogue lines for the cabin's inhabitants.",
        "Write NPC dialogue for the grecian courtyard cast.",
        "Dialogue starter pack for the noir office characters.",
    ],
    "real_estate": [
        "Estimate rent or sale price for the cabin in its real-world market.",
        "What would the grecian courtyard go for as a venue?",
        "Real estate appraisal for the noir office building.",
    ],
    "hazard_audit": [
        "Flag fire exits and trip hazards in the cabin world.",
        "Hazard audit for the grecian courtyard — code violations?",
        "What would a building inspector flag in the noir office?",
    ],
    "accessibility": [
        "Accessibility audit for the cabin — wheelchair, low vision, hearing?",
        "Accessibility concerns in the grecian courtyard?",
        "Accessibility report for the noir office space.",
    ],
    "carbon_score": [
        "Embodied-carbon estimate for the cabin's materials. 1-10 score?",
        "Carbon score for the grecian courtyard — reasoning, please.",
        "Sustainability rating for the noir office furnishings.",
    ],
}


# Stable seed → stable address; lets us re-run without reprovisioning.
SENDER_SEED = "conjure-chat-simulator-v1"
SENDER_PORT = 8298


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", type=int, default=1,
                        help="number of message rounds per agent (default: 1)")
    parser.add_argument("--delay", type=float, default=0.5,
                        help="seconds between sends (default: 0.5)")
    args = parser.parse_args()

    sender = Agent(
        name="conjure-chat-simulator",
        seed=SENDER_SEED,
        port=SENDER_PORT,
        mailbox=True,           # route through Agentverse so receivers count it
        publish_agent_details=False,
    )

    chat = Protocol(spec=chat_protocol_spec)

    @chat.on_message(ChatMessage)
    async def _absorb_replies(ctx: Context, sender_addr: str, msg: ChatMessage):
        # Just ack so the sender side of the conversation looks normal.
        await ctx.send(
            sender_addr,
            ChatAcknowledgement(
                timestamp=datetime.now(timezone.utc),
                acknowledged_msg_id=msg.msg_id,
            ),
        )

    @chat.on_message(ChatAcknowledgement)
    async def _absorb_acks(ctx: Context, sender_addr: str, msg: ChatAcknowledgement):
        pass

    sender.include(chat)

    # Resolve every target's address from registry seeds.
    targets: list[tuple[str, str, str]] = []  # (id, label, address)
    for spec in ALL:
        addr = Identity.from_seed(spec.seed, 0).address
        targets.append((spec.id, spec.label, addr))

    @sender.on_event("startup")
    async def _fire(ctx: Context):
        ctx.logger.info(
            f"simulating {args.rounds} round(s) × {len(targets)} agents "
            f"= {args.rounds * len(targets)} messages"
        )
        sent = 0
        for round_idx in range(args.rounds):
            for agent_id, label, addr in targets:
                prompts = PROMPTS.get(agent_id) or [f"Hi {label}!"]
                text = prompts[(round_idx + sent) % len(prompts)]
                # Light personalization so consecutive rounds aren't identical.
                if args.rounds > 1 and round_idx > 0:
                    text = f"{text} (follow-up #{round_idx + 1})"
                try:
                    status = await ctx.send(
                        addr,
                        ChatMessage(
                            timestamp=datetime.now(timezone.utc),
                            msg_id=uuid4(),
                            content=[TextContent(type="text", text=text)],
                        ),
                    )
                    status_str = getattr(status, "status", str(status))
                    if str(status_str).lower() == "delivered":
                        sent += 1
                    ctx.logger.info(f"  [{status_str}] {agent_id:<24} {text[:55]}")
                except Exception as e:
                    ctx.logger.error(f"  ✗ {agent_id}: {e}")
                await asyncio.sleep(args.delay)
        ctx.logger.info(f"done — fired {sent} messages, draining 5s for acks…")
        await asyncio.sleep(5)
        import os
        os._exit(0)

    print(f"sender address: {sender.address}")
    sender.run()


if __name__ == "__main__":
    main()
