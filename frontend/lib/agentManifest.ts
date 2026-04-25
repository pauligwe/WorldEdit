/**
 * Mirror of backend/agents_v2/manifest.py — kept in sync by hand.
 * Adding/renaming/removing an agent: update both files.
 *
 * Frontend manifest adds graph layout coordinates (col, row) for the
 * Circuit Board visual. These are NOT in the backend manifest because
 * the backend doesn't care where nodes are drawn.
 */

export type AgentTier = 0 | 1 | 2 | 3 | 4;
export type AgentDisplayType = "text" | "list" | "swatches" | "map" | "products" | "thumbnails";

export interface AgentDef {
  id: string;
  label: string;
  tier: AgentTier;
  category: string;
  dependencies: string[];
  display: AgentDisplayType;
  col: number;
  row: number;
}

export const AGENTS: AgentDef[] = [
  // Tier 0 — Perception (row 1)
  { id: "scene_describer",     label: "Scene Describer",      tier: 0, category: "Perception", dependencies: [],                                  display: "text",       col: 0, row: 1 },
  { id: "object_inventory",    label: "Object Inventory",     tier: 0, category: "Perception", dependencies: [],                                  display: "list",       col: 2, row: 1 },
  { id: "spatial_layout",      label: "Spatial Layout",       tier: 0, category: "Perception", dependencies: [],                                  display: "text",       col: 4, row: 1 },

  // Tier 1 — Real-world (row 2)
  { id: "geolocator",          label: "Geolocator",           tier: 1, category: "Real-world",  dependencies: ["scene_describer"],                 display: "list",       col: 0, row: 2 },
  { id: "filming_scout",       label: "Filming Scout",        tier: 1, category: "Real-world",  dependencies: ["geolocator"],                      display: "list",       col: 1, row: 2 },
  { id: "era_estimator",       label: "Era",                  tier: 1, category: "Real-world",  dependencies: ["scene_describer"],                 display: "text",       col: 2, row: 2 },
  { id: "architectural_style", label: "Architectural Style",  tier: 1, category: "Real-world",  dependencies: ["scene_describer"],                 display: "text",       col: 3, row: 2 },

  // Tier 2 — Creative (row 3)
  { id: "shot_list",           label: "Shot List",            tier: 2, category: "Creative",    dependencies: ["spatial_layout","scene_describer"], display: "list",       col: 0, row: 3 },
  { id: "mood_palette",        label: "Mood & Palette",       tier: 2, category: "Creative",    dependencies: ["scene_describer"],                 display: "swatches",   col: 1, row: 3 },
  { id: "soundscape",          label: "Soundscape",           tier: 2, category: "Creative",    dependencies: ["scene_describer"],                 display: "list",       col: 2, row: 3 },
  { id: "prop_shopping",       label: "Prop Shopping",        tier: 2, category: "Creative",    dependencies: ["object_inventory"],                display: "products",   col: 3, row: 3 },
  { id: "set_dressing",        label: "Set Dressing",         tier: 2, category: "Creative",    dependencies: ["scene_describer","object_inventory"], display: "list",     col: 4, row: 3 },

  // Tier 3 — Narrative (row 4)
  { id: "story_seed",          label: "Story Seeds",          tier: 3, category: "Narrative",   dependencies: ["scene_describer","era_estimator"], display: "list",       col: 0, row: 4 },
  { id: "character_suggester", label: "Characters",           tier: 3, category: "Narrative",   dependencies: ["scene_describer"],                 display: "list",       col: 2, row: 4 },
  { id: "npc_dialogue",        label: "NPC Dialogue",         tier: 3, category: "Narrative",   dependencies: ["character_suggester"],             display: "list",       col: 3, row: 4 },

  // Tier 4 — Practical (row 5)
  { id: "real_estate",         label: "Real Estate",          tier: 4, category: "Practical",   dependencies: ["geolocator","spatial_layout"],     display: "text",       col: 0, row: 5 },
  { id: "hazard_audit",        label: "Hazards",              tier: 4, category: "Practical",   dependencies: ["object_inventory","spatial_layout"], display: "list",     col: 1, row: 5 },
  { id: "accessibility",       label: "Accessibility",        tier: 4, category: "Practical",   dependencies: ["spatial_layout"],                  display: "list",       col: 2, row: 5 },
  { id: "carbon_score",        label: "Carbon Score",         tier: 4, category: "Practical",   dependencies: ["object_inventory","scene_describer"], display: "text",    col: 4, row: 5 },
];

export const AGENTS_BY_ID: Record<string, AgentDef> = Object.fromEntries(
  AGENTS.map((a) => [a.id, a]),
);

export const CATEGORIES: { name: string; tier: AgentTier }[] = [
  { name: "Perception",  tier: 0 },
  { name: "Real-world",  tier: 1 },
  { name: "Creative",    tier: 2 },
  { name: "Narrative",   tier: 3 },
  { name: "Practical",   tier: 4 },
];
