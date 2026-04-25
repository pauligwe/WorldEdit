"""Single source of truth for the 19 agents in the swarm.

Adding/removing/renaming an agent: edit this file. The orchestrator,
runner, registry, and frontend manifest mirror are all driven from this list.
"""
from dataclasses import dataclass, field
from typing import Literal

DisplayType = Literal["text", "list", "swatches", "map", "products", "thumbnails"]
Tier = Literal[0, 1, 2, 3, 4]


@dataclass(frozen=True)
class AgentDef:
    id: str
    label: str
    tier: Tier
    port: int
    dependencies: list[str] = field(default_factory=list)
    display: DisplayType = "text"


AGENTS: list[AgentDef] = [
    # Tier 0 — Perception
    AgentDef(id="scene_describer",     label="Scene Describer",      tier=0, port=8100),
    AgentDef(id="object_inventory",    label="Object Inventory",     tier=0, port=8101, display="list"),
    AgentDef(id="spatial_layout",      label="Spatial Layout",       tier=0, port=8102),

    # Tier 1 — Real-world grounding
    AgentDef(id="geolocator",          label="Geolocator",           tier=1, port=8103,
             dependencies=["scene_describer"], display="list"),
    AgentDef(id="filming_scout",       label="Filming Location Scout", tier=1, port=8104,
             dependencies=["geolocator"], display="list"),
    AgentDef(id="era_estimator",       label="Era Estimator",        tier=1, port=8105,
             dependencies=["scene_describer"]),
    AgentDef(id="architectural_style", label="Architectural Style",  tier=1, port=8106,
             dependencies=["scene_describer"]),

    # Tier 2 — Creative / production
    AgentDef(id="shot_list",           label="Shot List",            tier=2, port=8107,
             dependencies=["spatial_layout", "scene_describer"], display="list"),
    AgentDef(id="mood_palette",        label="Mood & Palette",       tier=2, port=8108,
             dependencies=["scene_describer"], display="swatches"),
    AgentDef(id="soundscape",          label="Soundscape",           tier=2, port=8109,
             dependencies=["scene_describer"], display="list"),
    AgentDef(id="prop_shopping",       label="Prop Shopping",        tier=2, port=8110,
             dependencies=["object_inventory"], display="products"),
    AgentDef(id="set_dressing",        label="Set Dressing",         tier=2, port=8111,
             dependencies=["scene_describer", "object_inventory"], display="list"),

    # Tier 3 — Narrative
    AgentDef(id="story_seed",          label="Story Seeds",          tier=3, port=8112,
             dependencies=["scene_describer", "era_estimator"], display="list"),
    AgentDef(id="character_suggester", label="Characters",           tier=3, port=8113,
             dependencies=["scene_describer"], display="list"),
    AgentDef(id="npc_dialogue",        label="NPC Dialogue",         tier=3, port=8114,
             dependencies=["character_suggester"], display="list"),

    # Tier 4 — Practical
    AgentDef(id="real_estate",         label="Real Estate Appraisal", tier=4, port=8115,
             dependencies=["geolocator", "spatial_layout"]),
    AgentDef(id="hazard_audit",        label="Hazard Audit",         tier=4, port=8116,
             dependencies=["object_inventory", "spatial_layout"], display="list"),
    AgentDef(id="accessibility",       label="Accessibility",        tier=4, port=8117,
             dependencies=["spatial_layout"], display="list"),
    AgentDef(id="carbon_score",        label="Carbon Score",         tier=4, port=8118,
             dependencies=["object_inventory", "scene_describer"]),
]


def by_id() -> dict[str, AgentDef]:
    return {a.id: a for a in AGENTS}
