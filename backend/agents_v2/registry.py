"""Map agent_id -> run(req) -> dict.

The orchestrator looks up the run function by agent id. Tests can monkeypatch
AGENT_RUNS to swap real Gemini calls for stubs.
"""
from agents_v2.agents import (
    scene_describer, object_inventory, spatial_layout,
    geolocator, filming_scout, era_estimator, architectural_style,
    shot_list, mood_palette, soundscape, prop_shopping, set_dressing,
    story_seed, character_suggester, npc_dialogue,
    real_estate, hazard_audit, accessibility, carbon_score,
)


AGENT_RUNS = {
    "scene_describer":     scene_describer.run,
    "object_inventory":    object_inventory.run,
    "spatial_layout":      spatial_layout.run,
    "geolocator":          geolocator.run,
    "filming_scout":       filming_scout.run,
    "era_estimator":       era_estimator.run,
    "architectural_style": architectural_style.run,
    "shot_list":           shot_list.run,
    "mood_palette":        mood_palette.run,
    "soundscape":          soundscape.run,
    "prop_shopping":       prop_shopping.run,
    "set_dressing":        set_dressing.run,
    "story_seed":          story_seed.run,
    "character_suggester": character_suggester.run,
    "npc_dialogue":        npc_dialogue.run,
    "real_estate":         real_estate.run,
    "hazard_audit":        hazard_audit.run,
    "accessibility":       accessibility.run,
    "carbon_score":        carbon_score.run,
}
