"""Single source of truth for all pre-gen agents.

Each agent has a stable seed → stable address. Update SEEDS *carefully* —
changing a seed changes the address, which breaks any frontend deep-links
already published.

Ports 8201-8210 are reserved for the 10 workers. 8200 is reserved for the
spike. 8211 is the Coordinator. Add new agents at the bottom; never reuse
a port or seed.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class PreGenAgent:
    id: str
    name: str            # human-readable, used as Agent(name=…)
    label: str           # display label for chat narration
    port: int
    seed: str
    description: str     # ≤ 300 chars — shown on ASI:One previews
    readme_filename: str # file in agentverse/readmes/ rendered on profile


COORDINATOR = PreGenAgent(
    id="coordinator",
    name="conjure-coordinator",
    label="Coordinator",
    port=8211,
    seed="conjure-coordinator-v1",
    description=(
        "Public entry point for the Conjure agent swarm. Send me a one-line "
        "prompt like 'a sunlit forest cabin' and I'll route it through 10 "
        "specialist agents (intent, references, style, lighting, prompt, "
        "Marble call, capture, QC) and reply with a link to your 3D world."
    ),
    readme_filename="coordinator.md",
)

WORKERS: list[PreGenAgent] = [
    PreGenAgent(
        id="intent_parser",
        name="conjure-intent-parser",
        label="Intent Parser",
        port=8201,
        seed="conjure-intent-parser-v1",
        description=(
            "Pre-gen agent. I read the user's one-line world prompt and "
            "extract structured intent: genre, mood, era, scale, interior vs "
            "exterior, and anchor objects. Downstream agents use this as the "
            "scaffolding for everything they do."
        ),
        readme_filename="intent_parser.md",
    ),
    PreGenAgent(
        id="reference_curator",
        name="conjure-reference-curator",
        label="Reference Curator",
        port=8202,
        seed="conjure-reference-curator-v1",
        description=(
            "Pre-gen agent. Given parsed intent, I gather visual references "
            "(film stills, photographs, concept art) that match the target "
            "vibe. Downstream style + composition agents lean on my picks "
            "to keep the eventual Marble prompt grounded."
        ),
        readme_filename="reference_curator.md",
    ),
    PreGenAgent(
        id="style_synthesizer",
        name="conjure-style-synthesizer",
        label="Style Synthesizer",
        port=8203,
        seed="conjure-style-synthesizer-v1",
        description=(
            "Pre-gen agent. I pick a single coherent art direction from the "
            "reference set — Ghibli watercolor, Wes Anderson symmetric, gritty "
            "noir, etc. — so the rest of the pipeline doesn't drift across "
            "incompatible visual languages."
        ),
        readme_filename="style_synthesizer.md",
    ),
    PreGenAgent(
        id="mood_lighting_director",
        name="conjure-mood-lighting-director",
        label="Mood & Lighting Director",
        port=8204,
        seed="conjure-mood-lighting-director-v1",
        description=(
            "Pre-gen agent. I lock in time of day, weather, color "
            "temperature, and key/fill ratios — the lighting decisions that "
            "set the emotional register of the scene before Marble ever sees "
            "the prompt."
        ),
        readme_filename="mood_lighting_director.md",
    ),
    PreGenAgent(
        id="scene_composer",
        name="conjure-scene-composer",
        label="Scene Composer",
        port=8205,
        seed="conjure-scene-composer-v1",
        description=(
            "Pre-gen agent. I lay out the spatial composition: foreground vs "
            "background, focal point, negative space, sightlines. My output "
            "is what gives the eventual splat a sense of intentional framing."
        ),
        readme_filename="scene_composer.md",
    ),
    PreGenAgent(
        id="prompt_engineer",
        name="conjure-prompt-engineer",
        label="Prompt Engineer",
        port=8206,
        seed="conjure-prompt-engineer-v1",
        description=(
            "Pre-gen agent. I assemble the final Marble-ready prompt from "
            "intent, style, lighting, and composition decisions made upstream. "
            "Ask me about prompt structure, weighting, negative prompts, or "
            "how to push Marble toward a specific look."
        ),
        readme_filename="prompt_engineer.md",
    ),
    PreGenAgent(
        id="marble_dispatcher",
        name="conjure-marble-dispatcher",
        label="Marble Dispatcher",
        port=8207,
        seed="conjure-marble-dispatcher-v1",
        description=(
            "Pre-gen agent. I send the assembled prompt to World Labs Marble "
            "and wait for the resulting Gaussian splat. I handle retries, "
            "queue position, and timeouts. (For demo runs I serve a cached "
            "splat from disk to avoid rate limits.)"
        ),
        readme_filename="marble_dispatcher.md",
    ),
    PreGenAgent(
        id="capture_planner",
        name="conjure-capture-planner",
        label="Capture Planner",
        port=8208,
        seed="conjure-capture-planner-v1",
        description=(
            "Pre-gen agent. Once Marble returns a splat, I pick the camera "
            "viewpoints to capture from it — typically 3 angles that together "
            "show the space without redundancy. These captures feed the "
            "Tier 0 perception agents."
        ),
        readme_filename="capture_planner.md",
    ),
    PreGenAgent(
        id="quality_critic",
        name="conjure-quality-critic",
        label="Quality Critic",
        port=8209,
        seed="conjure-quality-critic-v1",
        description=(
            "Pre-gen agent. I inspect the rendered captures for obvious "
            "failures: blurry surfaces, clipping, missing geometry, prompt "
            "drift. If something's wrong I flag it and the pipeline can "
            "request a regen."
        ),
        readme_filename="quality_critic.md",
    ),
    PreGenAgent(
        id="continuity_checker",
        name="conjure-continuity-checker",
        label="Continuity Checker",
        port=8210,
        seed="conjure-continuity-checker-v1",
        description=(
            "Pre-gen agent. I compare the final splat against the original "
            "user intent — does a 'cozy forest cabin' actually look cozy and "
            "forested? — and produce a confidence score before the world is "
            "handed off to the user."
        ),
        readme_filename="continuity_checker.md",
    ),
]


# Post-generation analysis swarm — 19 agents that run after a world is
# built, producing the sidebar drawer (scene description, geolocation,
# shot list, story seeds, hazard audit, etc.). Each is a standalone
# uAgent on Agentverse so judges can DM individual specialists; the
# actual orchestration runs in-process via agents_v2/orchestrator.py.
# Ports 8101-8119 are reserved for these mailbox wrappers. Tier 0-4
# tagging is informative only; the registry doesn't care.
POST_GEN_WORKERS: list[PreGenAgent] = [
    # Tier 0 — Perception
    PreGenAgent(
        id="scene_describer",
        name="conjure-scene-describer",
        label="Scene Describer",
        port=8101,
        seed="conjure-scene-describer-v1",
        description=(
            "Post-gen agent. I read 3 captured views of a generated world and "
            "produce a dense one-paragraph description plus structured tags. "
            "Almost every other analysis agent depends on my output."
        ),
        readme_filename="scene_describer.md",
    ),
    PreGenAgent(
        id="object_inventory",
        name="conjure-object-inventory",
        label="Object Inventory",
        port=8102,
        seed="conjure-object-inventory-v1",
        description=(
            "Post-gen agent. I enumerate every visible object in the world "
            "with rough position. Prop Shopping, Set Dressing, and Hazard "
            "Audit downstream all read my list."
        ),
        readme_filename="object_inventory.md",
    ),
    PreGenAgent(
        id="spatial_layout",
        name="conjure-spatial-layout",
        label="Spatial Layout",
        port=8103,
        seed="conjure-spatial-layout-v1",
        description=(
            "Post-gen agent. I produce a rough floorplan / room graph from "
            "the overhead capture — room count, adjacencies, approximate "
            "footprint. Shot List and Hazard Audit lean on this."
        ),
        readme_filename="spatial_layout.md",
    ),

    # Tier 1 — Real-world grounding
    PreGenAgent(
        id="geolocator",
        name="conjure-geolocator",
        label="Geolocator",
        port=8104,
        seed="conjure-geolocator-v1",
        description=(
            "Post-gen agent. Given a scene description, I propose top-3 "
            "candidate real-world regions where this place could plausibly "
            "exist, with reasoning and confidence scores."
        ),
        readme_filename="geolocator.md",
    ),
    PreGenAgent(
        id="filming_scout",
        name="conjure-filming-scout",
        label="Filming Location Scout",
        port=8105,
        seed="conjure-filming-scout-v1",
        description=(
            "Post-gen agent. I find 3-5 real-world filming locations that "
            "match the world's vibe — Peerspace/Giggster-style listings with "
            "addresses and rough day rates."
        ),
        readme_filename="filming_scout.md",
    ),
    PreGenAgent(
        id="era_estimator",
        name="conjure-era-estimator",
        label="Era Estimator",
        port=8106,
        seed="conjure-era-estimator-v1",
        description=(
            "Post-gen agent. I estimate when this scene is set — decade, "
            "century, or geological epoch — based on visible architecture, "
            "tech, materials, and decor."
        ),
        readme_filename="era_estimator.md",
    ),
    PreGenAgent(
        id="architectural_style",
        name="conjure-architectural-style",
        label="Architectural Style",
        port=8107,
        seed="conjure-architectural-style-v1",
        description=(
            "Post-gen agent. I classify the architectural style — Brutalist, "
            "Victorian, Mid-Century Modern, etc. — and call out the specific "
            "features that drove the call."
        ),
        readme_filename="architectural_style.md",
    ),

    # Tier 2 — Creative / production
    PreGenAgent(
        id="shot_list",
        name="conjure-shot-list",
        label="Shot List",
        port=8108,
        seed="conjure-shot-list-v1",
        description=(
            "Post-gen agent. I plan a 5-8 shot cinematographer's shot list "
            "for filming this world: lens choice, camera position, framing, "
            "and the story beat each shot serves."
        ),
        readme_filename="shot_list.md",
    ),
    PreGenAgent(
        id="mood_palette",
        name="conjure-mood-palette",
        label="Mood & Palette",
        port=8109,
        seed="conjure-mood-palette-v1",
        description=(
            "Post-gen agent. I pull a 5-color palette out of the scene plus "
            "LUT/film stock suggestions — the color-grade starting point for "
            "anyone using this world in post."
        ),
        readme_filename="mood_palette.md",
    ),
    PreGenAgent(
        id="soundscape",
        name="conjure-soundscape",
        label="Soundscape",
        port=8110,
        seed="conjure-soundscape-v1",
        description=(
            "Post-gen agent. I design the ambient soundscape and Foley list "
            "for this world — what you'd hear standing inside it, with rough "
            "volume mix suggestions."
        ),
        readme_filename="soundscape.md",
    ),
    PreGenAgent(
        id="prop_shopping",
        name="conjure-prop-shopping",
        label="Prop Shopping",
        port=8111,
        seed="conjure-prop-shopping-v1",
        description=(
            "Post-gen agent. From the object inventory I produce a real "
            "shopping list with Amazon/Wayfair/IKEA-style links so a set "
            "decorator could actually build this room."
        ),
        readme_filename="prop_shopping.md",
    ),
    PreGenAgent(
        id="set_dressing",
        name="conjure-set-dressing",
        label="Set Dressing",
        port=8112,
        seed="conjure-set-dressing-v1",
        description=(
            "Post-gen agent. I suggest 5-10 specific set-dressing additions "
            "or changes that would push the scene further in its intended "
            "direction without breaking continuity."
        ),
        readme_filename="set_dressing.md",
    ),

    # Tier 3 — Narrative
    PreGenAgent(
        id="story_seed",
        name="conjure-story-seed",
        label="Story Seeds",
        port=8113,
        seed="conjure-story-seed-v1",
        description=(
            "Post-gen agent. I write 3 short story or film premises set in "
            "this world — different genres, different tones, all grounded in "
            "the actual scene and era."
        ),
        readme_filename="story_seed.md",
    ),
    PreGenAgent(
        id="character_suggester",
        name="conjure-character-suggester",
        label="Characters",
        port=8114,
        seed="conjure-character-suggester-v1",
        description=(
            "Post-gen agent. I propose 3-5 character cards — who lives or "
            "works in this place, what they want, what tension they bring "
            "into the room."
        ),
        readme_filename="character_suggester.md",
    ),
    PreGenAgent(
        id="npc_dialogue",
        name="conjure-npc-dialogue",
        label="NPC Dialogue",
        port=8115,
        seed="conjure-npc-dialogue-v1",
        description=(
            "Post-gen agent. I write sample NPC dialogue lines for the "
            "characters in this world — useful as a starting pack for game "
            "writers or improv-style scene work."
        ),
        readme_filename="npc_dialogue.md",
    ),

    # Tier 4 — Practical
    PreGenAgent(
        id="real_estate",
        name="conjure-real-estate",
        label="Real Estate Appraisal",
        port=8116,
        seed="conjure-real-estate-v1",
        description=(
            "Post-gen agent. Given the inferred location and floorplan I "
            "estimate what this place would rent or sell for in its "
            "real-world market."
        ),
        readme_filename="real_estate.md",
    ),
    PreGenAgent(
        id="hazard_audit",
        name="conjure-hazard-audit",
        label="Hazard Audit",
        port=8117,
        seed="conjure-hazard-audit-v1",
        description=(
            "Post-gen agent. I flag fire exits, trip hazards, and obvious "
            "code violations — the kind of pass a building inspector or "
            "location manager would do on a real set."
        ),
        readme_filename="hazard_audit.md",
    ),
    PreGenAgent(
        id="accessibility",
        name="conjure-accessibility",
        label="Accessibility",
        port=8118,
        seed="conjure-accessibility-v1",
        description=(
            "Post-gen agent. I audit the scene for wheelchair access, "
            "lighting for low vision, hearing-loop friendliness, and other "
            "accessibility concerns."
        ),
        readme_filename="accessibility.md",
    ),
    PreGenAgent(
        id="carbon_score",
        name="conjure-carbon-score",
        label="Carbon Score",
        port=8119,
        seed="conjure-carbon-score-v1",
        description=(
            "Post-gen agent. I estimate the embodied-carbon footprint of "
            "the materials and objects visible in the scene and produce a "
            "1-10 sustainability score with reasoning."
        ),
        readme_filename="carbon_score.md",
    ),
]


# All agents in pipeline order (Coordinator first as the public entry point).
ALL: list[PreGenAgent] = [COORDINATOR] + WORKERS + POST_GEN_WORKERS
BY_ID: dict[str, PreGenAgent] = {a.id: a for a in ALL}
WORKERS_BY_ID: dict[str, PreGenAgent] = {a.id: a for a in WORKERS}
POST_GEN_BY_ID: dict[str, PreGenAgent] = {a.id: a for a in POST_GEN_WORKERS}
ALL_WORKERS_BY_ID: dict[str, PreGenAgent] = {**WORKERS_BY_ID, **POST_GEN_BY_ID}
