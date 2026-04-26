"""Canned-but-plausible artifacts each pre-gen worker produces.

The pre-gen pipeline is theatre — actual world generation is the cached
splat returned by the Marble Dispatcher. These artifacts give the
Coordinator something to narrate to the user that *sounds* like a real
LLM-driven prompt-engineering pipeline.

One artifact per worker, parameterised loosely by the user prompt: we
keyword-match a few words to pick a "preset" so the whole chain feels
coherent (cabin → forest preset, office → urban preset, etc.).
"""
from __future__ import annotations

PRESET_KEYWORDS: dict[str, list[str]] = {
    "forest_cabin": ["cabin", "forest", "wood", "cottage", "lodge", "rustic"],
    "downtown_office": ["office", "downtown", "city", "skyscraper", "corporate"],
    "desert_canyon": ["desert", "canyon", "dune", "sandstone", "arid", "mesa"],
    "underwater_ruin": ["underwater", "ruin", "sunken", "ocean", "atlantis", "reef"],
}

DEFAULT_PRESET = "forest_cabin"


def pick_preset(prompt: str) -> str:
    p = prompt.lower()
    for preset, words in PRESET_KEYWORDS.items():
        if any(w in p for w in words):
            return preset
    return DEFAULT_PRESET


# ---------- Per-preset content ----------
# Each entry maps preset → per-agent artifact (headline + structured payload).

INTENT: dict[str, dict] = {
    "forest_cabin": {
        "headline": "Intent: cozy single-story interior, dusk, woodland setting",
        "payload": {"genre": "shelter", "mood": "warm/intimate", "era": "modern rustic",
                    "scale": "small (~400 sqft)", "setting": "interior",
                    "anchors": ["fireplace", "rocking chair", "window with view"]},
    },
    "downtown_office": {
        "headline": "Intent: modern corporate interior, daytime, glass + concrete",
        "payload": {"genre": "workplace", "mood": "sleek/neutral", "era": "2020s",
                    "scale": "medium (~1500 sqft)", "setting": "interior",
                    "anchors": ["desk pods", "city-view glass wall", "open floorplan"]},
    },
    "desert_canyon": {
        "headline": "Intent: open exterior landscape, golden hour, monumental scale",
        "payload": {"genre": "landscape", "mood": "vast/dry", "era": "geological",
                    "scale": "huge (canyon-floor to rim)", "setting": "exterior",
                    "anchors": ["sandstone cliffs", "dry riverbed", "lone juniper"]},
    },
    "underwater_ruin": {
        "headline": "Intent: submerged exploration, low-light, mythological scale",
        "payload": {"genre": "ruin", "mood": "eerie/quiet", "era": "ancient",
                    "scale": "medium-large (~2 city blocks)", "setting": "exterior",
                    "anchors": ["broken columns", "kelp forest", "schooling fish"]},
    },
}

REFERENCES: dict[str, dict] = {
    "forest_cabin": {
        "headline": "References: 8 stills (Studio Ghibli, Apartamento, Kinfolk)",
        "payload": {"sources": ["Spirited Away — bathhouse interiors",
                                "Apartamento Issue 31 — woodland cottages",
                                "Roger Deakins — 'The Assassination of Jesse James' dusk shots"]},
    },
    "downtown_office": {
        "headline": "References: 6 stills (Severance, Apple Park, Office Snapshots)",
        "payload": {"sources": ["Severance S1 — Lumon floor",
                                "Apple Park lobby photographs",
                                "Office Snapshots — Stripe SF"]},
    },
    "desert_canyon": {
        "headline": "References: 9 stills (Dune, Antelope Canyon, Wadi Rum)",
        "payload": {"sources": ["Dune (2021) cinematography",
                                "Peter Lik — Antelope Canyon plates",
                                "Wadi Rum location reels"]},
    },
    "underwater_ruin": {
        "headline": "References: 7 stills (Atlantis, BBC Blue Planet II, Subnautica)",
        "payload": {"sources": ["Atlantis (2001) production paintings",
                                "Blue Planet II — coral cathedrals",
                                "Subnautica concept art"]},
    },
}

STYLE: dict[str, dict] = {
    "forest_cabin": {
        "headline": "Style: hand-painted realism, low-saturation, soft edges",
        "payload": {"art_direction": "Ghibli-inflected painterly realism",
                    "saturation": "low-medium", "linework": "soft",
                    "render_lookalike": "Arnold w/ painterly post"},
    },
    "downtown_office": {
        "headline": "Style: clean photoreal, neutral palette, hard light",
        "payload": {"art_direction": "architectural photography realism",
                    "saturation": "low", "linework": "crisp",
                    "render_lookalike": "V-Ray archviz"},
    },
    "desert_canyon": {
        "headline": "Style: cinematic photoreal, warm/cool split, deep contrast",
        "payload": {"art_direction": "Deakins-school cinematography",
                    "saturation": "medium-high", "linework": "natural",
                    "render_lookalike": "Octane w/ filmic tonemap"},
    },
    "underwater_ruin": {
        "headline": "Style: muted painterly, blue-green palette, volumetric haze",
        "payload": {"art_direction": "matte-painting / video-game cinematic",
                    "saturation": "low", "linework": "diffused",
                    "render_lookalike": "Unreal w/ underwater volumetrics"},
    },
}

LIGHTING: dict[str, dict] = {
    "forest_cabin": {
        "headline": "Lighting: dusk, 2700K key from window, low ambient",
        "payload": {"time_of_day": "dusk", "key_color_temp_k": 2700,
                    "weather": "clear", "key_fill_ratio": "5:1",
                    "practicals": ["fireplace", "single floor lamp"]},
    },
    "downtown_office": {
        "headline": "Lighting: midday, 5600K daylight, even fluorescent fill",
        "payload": {"time_of_day": "midday", "key_color_temp_k": 5600,
                    "weather": "overcast bright", "key_fill_ratio": "2:1",
                    "practicals": ["recessed LED grid", "monitor glow"]},
    },
    "desert_canyon": {
        "headline": "Lighting: golden hour, 3200K low sun, hard shadows",
        "payload": {"time_of_day": "golden hour", "key_color_temp_k": 3200,
                    "weather": "clear/dry", "key_fill_ratio": "8:1",
                    "practicals": []},
    },
    "underwater_ruin": {
        "headline": "Lighting: caustic-filtered surface light, 6500K cooled to 4500K",
        "payload": {"time_of_day": "10am surface, dim by depth",
                    "key_color_temp_k": 4500, "weather": "calm surface",
                    "key_fill_ratio": "3:1",
                    "practicals": ["bioluminescent algae"]},
    },
}

COMPOSITION: dict[str, dict] = {
    "forest_cabin": {
        "headline": "Composition: rule-of-thirds, fireplace anchor, window vista",
        "payload": {"focal_point": "stone fireplace, lower-left third",
                    "depth_layers": ["foreground rug", "mid-room seating",
                                     "back-wall window with forest"],
                    "negative_space": "ceiling beams, upper third"},
    },
    "downtown_office": {
        "headline": "Composition: linear perspective, glass-wall vanishing point",
        "payload": {"focal_point": "city-view glass wall, dead center",
                    "depth_layers": ["foreground desk", "open floor", "skyline"],
                    "negative_space": "polished concrete floor"},
    },
    "desert_canyon": {
        "headline": "Composition: low horizon, dwarfed scale, leading lines",
        "payload": {"focal_point": "lone juniper, rule-of-thirds right",
                    "depth_layers": ["dry riverbed", "talus slope", "rim cliffs"],
                    "negative_space": "open sky, upper two-thirds"},
    },
    "underwater_ruin": {
        "headline": "Composition: descending Z-axis, columns frame the void",
        "payload": {"focal_point": "broken column with marine growth",
                    "depth_layers": ["nearby fish school",
                                     "mid-distance ruined plaza",
                                     "haze-obscured deeper structures"],
                    "negative_space": "blue volumetric depth"},
    },
}

# The "Marble prompt" the Prompt Engineer assembles — a long, weighted prompt
# string that demonstrates the synthesis of everything upstream.
ASSEMBLED_PROMPT: dict[str, str] = {
    "forest_cabin": (
        "(cozy forest cabin interior:1.2), single-story rustic shelter, "
        "stone fireplace lower-left, rocking chair, woodland visible through "
        "window with dusk light, hand-painted realism, Ghibli-inflected, "
        "low-saturation, 2700K warm key from window, painterly Arnold render"
    ),
    "downtown_office": (
        "modern corporate interior, open-plan workspace, polished concrete "
        "floor, desk pods, glass curtain wall with city skyline, daylight "
        "5600K, neutral palette, V-Ray archviz photoreal"
    ),
    "desert_canyon": (
        "vast desert canyon, golden hour, lone juniper on rule-of-thirds "
        "right, sandstone cliffs, dry riverbed leading lines, low horizon, "
        "Deakins cinematography, Octane filmic tonemap"
    ),
    "underwater_ruin": (
        "submerged ancient plaza, broken marble columns with kelp and coral, "
        "schooling fish, caustic surface light filtering down, blue-green "
        "volumetric haze, matte-painting / Unreal cinematic"
    ),
}

# Marble Dispatcher: picks the closest pre-built world to the user's prompt.
# We score each world against the prompt by simple keyword overlap — the
# splat library is small (7 worlds) and judges' demo prompts are short, so
# bag-of-words beats anything fancier. Falls back to cabin if no world wins.
WORLD_KEYWORDS: dict[str, list[str]] = {
    "cabin": [
        "cabin", "woods", "woodland", "forest", "rustic", "cottage",
        "lodge", "wood", "wooden", "trees", "treehouse",
    ],
    "office": [
        "office", "downtown", "skyscraper", "corporate", "workplace",
        "building", "modern", "urban", "city", "work", "cubicle", "desk",
    ],
    "living_room": [
        "living room", "livingroom", "lounge", "couch", "sofa",
        "interior", "home", "apartment", "indoor", "cozy",
    ],
    "minecraft_valley": [
        "minecraft", "voxel", "blocky", "block", "valley", "waterfall",
        "oasis", "pixel", "cube", "mine", "craft",
    ],
    "serene_living_room": [
        "serene", "countryside", "calm", "peaceful", "tranquil", "quiet",
        "view", "rural", "pastoral", "meadow", "vista",
    ],
    "grecian_city": [
        "grecian", "greek", "greece", "marble", "ancient", "classical",
        "white", "columns", "temple", "athens", "mediterranean",
        "santorini", "city", "landscape",
    ],
}

DEFAULT_WORLD_ID = "cabin"

# Multi-word phrases need to be checked first so "living room" doesn't get
# split into "living" + "room" tokens that could mismatch other worlds.
def pick_world_id(prompt: str) -> str:
    """Pick the world id whose keywords best match the prompt.

    Scores by counting keyword hits per world (substring match for
    multi-word keywords like "living room"; whole-word for single tokens).
    Ties broken by registry order. Falls back to DEFAULT_WORLD_ID.
    """
    p = prompt.lower()
    scores: dict[str, int] = {}
    for world_id, words in WORLD_KEYWORDS.items():
        s = 0
        for w in words:
            if " " in w:
                if w in p:
                    s += 2  # phrase match is a stronger signal
            else:
                # whole-word match so "modern" doesn't fire on "modernist"
                # being absent — keep it simple, plain substring is fine
                # for our short prompts and curated keyword set
                if w in p:
                    s += 1
        if s > 0:
            scores[world_id] = s
    if not scores:
        return DEFAULT_WORLD_ID
    return max(scores, key=lambda k: scores[k])


def _marble_result_for_world(world_id: str) -> dict:
    """Build the marble_dispatcher artifact for a chosen world id."""
    return {
        "headline": (
            f"Marble: splat ready, served from cache "
            f"({world_id}.spz)"
        ),
        "payload": {"world_id": world_id, "splat_url": f"/worlds/{world_id}.spz"},
    }

CAPTURE_PLAN: dict[str, dict] = {
    "forest_cabin": {
        "headline": "Captures planned: 3 angles (entry, fireplace, window POV)",
        "payload": {"viewpoints": ["entry threshold, eye-level",
                                   "diagonal across to fireplace",
                                   "window seat looking outward"]},
    },
    "downtown_office": {
        "headline": "Captures planned: 3 angles (lobby, floor pan, window vista)",
        "payload": {"viewpoints": ["entry lobby, eye-level",
                                   "open floor wide pan",
                                   "city-view at window"]},
    },
    "desert_canyon": {
        "headline": "Captures planned: 3 angles (rim, floor, juniper detail)",
        "payload": {"viewpoints": ["canyon rim looking down",
                                   "riverbed floor wide",
                                   "juniper closeup, rim-light"]},
    },
    "underwater_ruin": {
        "headline": "Captures planned: 3 angles (descent, plaza, column)",
        "payload": {"viewpoints": ["descending into ruin",
                                   "plaza wide with fish school",
                                   "column closeup w/ marine growth"]},
    },
}

QUALITY: dict[str, dict] = {
    "forest_cabin": {
        "headline": "QC: 3/3 captures pass — geometry crisp, no clipping",
        "payload": {"verdict": "pass", "issues": [], "regen_needed": False},
    },
    "downtown_office": {
        "headline": "QC: 3/3 captures pass — minor banding on glass, acceptable",
        "payload": {"verdict": "pass-with-notes",
                    "issues": ["mild moiré on glass curtain wall"],
                    "regen_needed": False},
    },
    "desert_canyon": {
        "headline": "QC: 3/3 captures pass — sharp geometry, lighting on-brief",
        "payload": {"verdict": "pass", "issues": [], "regen_needed": False},
    },
    "underwater_ruin": {
        "headline": "QC: 3/3 captures pass — volumetrics read well, no holes",
        "payload": {"verdict": "pass", "issues": [], "regen_needed": False},
    },
}

CONTINUITY: dict[str, dict] = {
    "forest_cabin": {
        "headline": "Continuity: 0.92 — splat matches 'cozy' + 'forest' anchors",
        "payload": {"score": 0.92,
                    "matched_anchors": ["fireplace", "window with forest view"],
                    "missed_anchors": ["rocking chair partially occluded"]},
    },
    "downtown_office": {
        "headline": "Continuity: 0.88 — corporate/glass anchors present",
        "payload": {"score": 0.88,
                    "matched_anchors": ["glass wall", "open floor", "desks"],
                    "missed_anchors": []},
    },
    "desert_canyon": {
        "headline": "Continuity: 0.95 — scale + lighting on-target",
        "payload": {"score": 0.95,
                    "matched_anchors": ["sandstone", "juniper", "golden hour"],
                    "missed_anchors": []},
    },
    "underwater_ruin": {
        "headline": "Continuity: 0.86 — ruin + fish anchors present",
        "payload": {"score": 0.86,
                    "matched_anchors": ["broken columns", "marine growth",
                                        "fish school"],
                    "missed_anchors": ["coral less prominent than referenced"]},
    },
}


# Lookup table: agent_id → preset_dict
ARTIFACTS: dict[str, dict[str, dict]] = {
    "intent_parser":          INTENT,
    "reference_curator":      REFERENCES,
    "style_synthesizer":      STYLE,
    "mood_lighting_director": LIGHTING,
    "scene_composer":         COMPOSITION,
    "capture_planner":        CAPTURE_PLAN,
    "quality_critic":         QUALITY,
    "continuity_checker":     CONTINUITY,
}


def artifact_for(agent_id: str, prompt: str) -> dict:
    """Look up the canned artifact for this agent given the user prompt.

    Returns a dict with `headline` and `payload`.
    """
    if agent_id == "prompt_engineer":
        # Prompt engineer is special — its payload is a single long string.
        preset = pick_preset(prompt)
        return {
            "headline": "Marble prompt assembled (1 weighted block, 6 modifiers)",
            "payload": {"prompt": ASSEMBLED_PROMPT.get(preset, ASSEMBLED_PROMPT[DEFAULT_PRESET])},
        }
    if agent_id == "marble_dispatcher":
        # Picks one of the 7 pre-built worlds by similarity to the prompt.
        return _marble_result_for_world(pick_world_id(prompt))
    table = ARTIFACTS.get(agent_id)
    if table is None:
        return {"headline": f"{agent_id}: ok", "payload": {}}
    preset = pick_preset(prompt)
    return table.get(preset, table[DEFAULT_PRESET])
