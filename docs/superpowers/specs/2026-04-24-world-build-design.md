# World Build — Design Spec

**Date:** 2026-04-24
**Event:** LA Hacks 2026 — Fetch.ai track (Agentverse - Search & Discovery of Agents)
**Goal:** Generate a 3D walkable building from a natural language prompt, populated with real-product furniture options, editable via persistent chat.

---

## 1. Architecture Overview

Three-layer system:

1. **Frontend** — Next.js + React Three Fiber (R3F) + drei. One web app handling: prompt input, agent activity panel, 3D walkthrough, chat panel, click-to-swap furniture overlay. Talks to backend over HTTP + WebSocket.
2. **Orchestration bridge** — FastAPI server. Receives prompts, drives the orchestrator uAgent, streams agent status events back to the frontend, returns final scene JSON.
3. **Agent layer** — Fetch.ai uAgents (orchestrator + 13 worker agents) running locally in one Python process. All registered on Agentverse with Chat Protocol implemented.

### Data flow — initial generation

1. User submits prompt → frontend `POST /api/generate` and opens WebSocket `/ws/build/[worldId]`.
2. FastAPI sends `BuildRequest` to orchestrator uAgent (in-process asyncio queue).
3. Orchestrator runs the agent DAG. After each agent completes, orchestrator pushes an `AgentStatus` event to the bridge, which forwards to the frontend WebSocket.
4. On completion, orchestrator returns final `WorldSpec` to bridge → final WebSocket message.
5. Frontend renders 3D world from `WorldSpec`.

### Data flow — chat edit

User toggles chat (T key), sends edit message → Chat Edit Coordinator agent rewrites prompt with prior `WorldSpec` context → orchestrator re-runs full pipeline → frontend fade-to-black, swap, fade-in at spawn point.

---

## 2. WorldSpec — Data Model

The single JSON object that flows through the pipeline. Every agent reads it and writes to its own designated top-level field.

```jsonc
{
  "worldId": "uuid",
  "prompt": "original user prompt",

  "intent": {
    "buildingType": "house",
    "style": "modern beach",
    "floors": 2,
    "vibe": ["airy", "minimal"],
    "sizeHint": "medium"
  },

  "blueprint": {
    "gridSize": 0.5,
    "floors": [
      {
        "level": 0,
        "ceilingHeight": 3.0,
        "rooms": [
          {
            "id": "living-room",
            "type": "living_room",
            "x": 0, "y": 0,
            "width": 8, "depth": 6,
            "doors":   [{ "wall": "south", "offset": 4, "width": 1.0 }],
            "windows": [{ "wall": "north", "offset": 4, "width": 1.5, "height": 1.2, "sill": 1.0 }]
          }
        ],
        "stairs": [
          { "id": "s1", "x": 2, "y": 0, "width": 2, "depth": 3, "direction": "north", "toLevel": 1 }
        ]
      }
    ]
  },

  "geometry": [
    { "type": "floor", "roomId": "living-room", "position": [0,0,0], "size": [8,0.1,6] },
    { "type": "wall",  "roomId": "living-room", "wall": "north", "position": [...], "size": [...], "holes": [{...}] }
  ],

  "lighting":  { "byRoom": { "living-room": [{ "type": "ceiling", "position": [4,2.8,3], "color": "#ffeacc", "intensity": 1.2 }] } },
  "materials": { "byRoom": { "living-room": { "wall": "#f5efe6", "floor": "oak_planks", "ceiling": "#ffffff" } } },

  "furniture": [
    {
      "id": "couch-1",
      "roomId": "living-room",
      "type": "couch",
      "subtype": "sectional",
      "position": [4, 0, 3],
      "rotation": 0,
      "size":     [2.4, 0.9, 1.0],
      "selectedProductId": "p_AB12",
      "alternates": ["p_AB12", "p_CD34"]
    }
  ],

  "products": {
    "p_AB12": {
      "name": "Mid-century 3-seat sectional",
      "price": 899,
      "imageUrl": "https://...",
      "vendor": "Amazon",
      "url": "https://...",
      "fitsTypes": ["couch"]
    }
  },

  "navigation": {
    "spawnPoint": [4, 1.7, 1],
    "walkableMeshIds": ["floor-0", "floor-1"],
    "stairColliders":  ["s1"]
  },

  "cost": { "total": 12480, "byRoom": { "living-room": 4200 } }
}
```

### Schema rules

- All dimensions in **meters**.
- All positions/sizes snap to **0.5m grid**.
- Rooms are **axis-aligned rectangles** (not arbitrary polygons). LLM reliability is the reason.
- Doors/windows positioned by named wall (`north`/`south`/`east`/`west`) + offset along that wall. Doors require `width`. Windows require `width`, `height`, `sill`.
- Stairs are rectangles with `direction` (which compass direction you face going up) and `toLevel`.
- `furniture[].position` and `furniture[].size` are in **scene coords** (3 components, y is up; `position[1]=0` means item rests on floor of its room). `lighting[].position` likewise in scene coords. Geometry uses scene coords. Only `blueprint.*` uses 2D top-down coords.
- Coordinate convention in **blueprint** (2D, top-down): `+x = east`, `+y = north`. In **3D scene** (Three.js): `+x = east`, `+y = up`, `+z = south` (Three.js right-handed y-up). Geometry Builder maps blueprint `(x, y)` → scene `(x, 0, -y)` so the blueprint's north (+y) renders into the scene's -z direction. Heights/`ceilingHeight` map to scene y.

### Few-shot examples

The Blueprint Architect's prompt includes **3 hand-written WorldSpec examples** as few-shot context:

1. Tiny 1-floor apartment (3 rooms, no stairs).
2. Standard 1-floor 4-bedroom house.
3. 2-floor modern house with stairs.

These are stored in `backend/core/prompts/examples/`.

---

## 3. Agents

14 agents total (1 orchestrator + 13 workers). All implemented as Fetch.ai uAgents in one Python process, all registered on Agentverse with Chat Protocol.

### Pipeline DAG

```
1. Intent Parser
        ↓
2. Blueprint Architect
        ↓
3. Code Compliance Critic
        ↓
        ┌──────────────────────┬──────────────────────┐
        ↓                      ↓                      ↓
4. 3D Geometry Builder   5. Lighting Designer   6. Material/Texture Stylist
        ↓                      ↓                      ↓
        └──────────────────────┴──────────────────────┘
                               ↓
                      7. Furniture Planner
                               ↓
                  8. Furniture Placement Validator
                               ↓
                      9. Real Product Scout
                               ↓
                       10. Style Matcher
                               ↓
                    11. Pricing Estimator
                               ↓
                    12. Navigation Planner

(13. Chat Edit Coordinator runs separately on user edit messages)
```

### Agent specs

| # | Name | Input | What it does | Output (WorldSpec field) |
|---|------|-------|--------------|--------------------------|
| 1 | Intent Parser | `prompt` | Gemini structured output extracts buildingType, style, floors, vibe, sizeHint. | `intent` |
| 2 | Blueprint Architect | `intent` | Gemini with few-shot examples generates rectangle-based floors/rooms/doors/windows/stairs. | `blueprint` |
| 3 | Code Compliance Critic | `blueprint` | Pure Python validation. Each room ≥1 door; no overlapping room rectangles per floor; stairs connect different floors and align spatially; entrance exists; all rooms reachable. On fail, errors fed back to Blueprint Architect for one retry. | validated `blueprint` |
| 4 | 3D Geometry Builder | `blueprint` | Pure Python. Generates floor/wall/ceiling primitives with door/window holes. | `geometry` |
| 5 | Lighting Designer | `blueprint` + `intent.vibe` | Rule-based defaults (kitchen→bright, bedroom→warm) plus Gemini for color temperature/intensity tweaks. | `lighting.byRoom` |
| 6 | Material/Texture Stylist | `blueprint` + `intent.style` | Gemini picks color palettes; floor textures map to fixed library (`oak_planks`, `marble_tile`, `concrete`, `carpet_grey`, etc.). | `materials.byRoom` |
| 7 | Furniture Planner | `blueprint` | Per room, Gemini returns furniture list with positions/rotations in room-local meters. | preliminary `furniture` |
| 8 | Furniture Placement Validator | `furniture` + `blueprint` | Pure Python. No overlaps, no doorway intrusion, fits in room. Nudge or remove invalid items. | validated `furniture` |
| 9 | Real Product Scout | `furniture` + `intent.style` | Per furniture type, Gemini with Google Search grounding returns 5 real products `{name, price, imageUrl, vendor, url}`. Each URL HEAD-checked for 200; dead ones dropped. One retry with broader query if <3 valid. | `products`, `furniture[].alternates`, `furniture[].selectedProductId` |
| 10 | Style Matcher | `furniture` + `products` | Re-rank/filter Scout results to span style variants per slot. Doesn't fetch new products. | refined `furniture[].alternates` |
| 11 | Pricing Estimator | `furniture` + `products` | Python sum per-room and total. | `cost` |
| 12 | Navigation Planner | `blueprint` + `furniture` | Pure Python. Spawn point inside front door; walkable mesh IDs; stair colliders. | `navigation` |
| 13 | Chat Edit Coordinator | prior `WorldSpec` + edit message | Gemini interprets edit and rewrites prompt for a full re-run. | new `prompt` |

### Parallel execution

Only **agents 4, 5, 6 run concurrently** after Compliance Critic — they all only need the validated blueprint. Everything else is strictly sequential.

### Deferred agents (not built in v1)

- Tour Guide / Narrator (voiceover via GCP TTS)
- Accessibility Auditor (doorway widths, hallway clearance flags)
- Sustainability Reporter (eco-score for furniture choices)

---

## 4. Frontend / UX

### Pages

- **`/`** — landing. Full-screen hero, prompt textarea, "Generate" button. Fetch.ai/Agentverse badge.
- **`/build/[worldId]`** — build view. Two phases:
  - **Phase A: Generation.** Full-screen `AgentActivityPanel` showing all 14 agents in DAG layout. States: idle (grey) → running (pulsing blue) → done (green check) → error (red). Each card shows a 1-line status string.
  - **Phase B: Walkthrough.** Full-screen 3D canvas. WASD + mouse look (PointerLockControls). Crosshair HUD. Click furniture → overlay. Press T → chat panel.

### Components

- **AgentActivityPanel** — DAG layout with sequential rows + 3-card parallel row.
- **CrosshairHUD** — center dot + "click to interact" hint when looking at furniture.
- **FurniturePanel** — slides in from right on furniture click. Carousel of real-product cards (image, name, price, vendor, "View" link). Selecting re-tints the in-scene mesh.
- **ChatPanel** — toggled with T. Slides in from left. Persistent history. Send → fade-to-black → re-run → fade in at spawn.
- **StatusBar** — bottom. Current room name, current floor, total cost.

### Controls

- WASD: walk. Shift: sprint. Mouse: look.
- E or click: interact with furniture.
- T: toggle chat panel.
- Stairs: walk-up by collision (no manual climbing).

### Style

- Dark mode UI, neon accent (cyan or violet) for activity panel and chat.
- 3D world uses naturalistic lighting per agent output.
- Smooth fades; no jarring transitions.

### Mobile

Not supported. Desktop-only. README states this.

---

## 5. Backend / Infrastructure

### Repo layout

```
world-build/
├── frontend/                 # Next.js + R3F app
├── backend/
│   ├── bridge/               # FastAPI (HTTP + WebSocket)
│   │   └── main.py
│   ├── agents/               # 14 uAgent files
│   │   ├── orchestrator.py
│   │   ├── intent_parser.py
│   │   ├── blueprint_architect.py
│   │   ├── compliance_critic.py
│   │   ├── geometry_builder.py
│   │   ├── lighting_designer.py
│   │   ├── material_stylist.py
│   │   ├── furniture_planner.py
│   │   ├── placement_validator.py
│   │   ├── product_scout.py
│   │   ├── style_matcher.py
│   │   ├── pricing_estimator.py
│   │   ├── navigation_planner.py
│   │   └── chat_edit_coordinator.py
│   ├── core/
│   │   ├── world_spec.py     # Pydantic models
│   │   ├── gemini_client.py
│   │   ├── prompts/
│   │   │   ├── system/
│   │   │   └── examples/     # WorldSpec few-shot examples
│   │   └── validators.py
│   ├── tests/                # end-to-end + unit
│   └── requirements.txt
├── reference-brown/          # already present
└── docs/superpowers/specs/
```

### Communication

- **Frontend ↔ FastAPI**: HTTP `POST /api/generate`, `POST /api/edit`, `POST /api/select-product`. WebSocket `/ws/build/[worldId]` for status events + final WorldSpec.
- **FastAPI ↔ Orchestrator uAgent**: in-process. Bridge owns the uAgent runtime; `BuildRequest` Pydantic message in, `AgentStatus` events streamed via asyncio queue, final `WorldSpec` in.
- **Orchestrator ↔ Workers**: standard uAgent messaging on local addresses, all in same process.

### Agentverse registration

All 14 uAgents register on Agentverse using the saved `AGENTVERSE_API_KEY`. Each implements Chat Protocol per Fetch.ai requirement. We do not depend on ASI:One UI; our own frontend is the user interface.

### Environment

`.env` in `backend/`:

- `GOOGLE_API_KEY` — Gemini.
- `AGENTVERSE_API_KEY` — uAgent registration.
- Per-agent seed phrases (auto-generated on first run, persisted).

Frontend: `NEXT_PUBLIC_BRIDGE_URL` defaults to `http://localhost:8000`.

### External services

- **GCP Gemini 2.0 Flash** — Intent Parser, Blueprint Architect, Lighting Designer (mood tweaks), Material Stylist, Furniture Planner, Chat Edit Coordinator. Structured output mode where possible.
- **Gemini with Google Search grounding** — Real Product Scout only.
- **Agentverse** — registration + Chat Protocol.

### Persistence

No database. WorldSpecs kept in memory keyed by `worldId` in FastAPI. Restart loses state — fine for hackathon. Each WorldSpec also written to `backend/worlds/<worldId>.json` for replay/debug.

### Assets

- **Textures**: 8-10 CC0 textures from Poly Haven in `frontend/public/textures/`.
- **Furniture meshes**: procedural primitives as React components (couch, bed, table, chair, lamp, etc.). Each takes a `tint` prop so product selection re-tints the mesh. No external GLTF loading in v1.

### Logging / debug

- FastAPI logs every agent message, timing, and error to stdout.
- `GET /api/debug/[worldId]` returns full WorldSpec for inspection.

### Deployment

Demo runs locally on the demo laptop. No cloud deploy required. Optional: Vercel (frontend) + Cloud Run (FastAPI) at the very end if there's time.

---

## 6. Risks and Mitigations

1. **Blueprint Architect produces invalid geometry.** Mitigations: rectangle-only schema + 0.5m grid + 3 few-shot examples + validation+1-retry loop. If still invalid, error surfaces to UI ("couldn't generate valid floorplan, try rephrasing"). No silent fallback.
2. **Real Product Scout returns hallucinated URLs.** Mitigations: one retry with broader query + live URL HEAD-check + drop dead URLs. If a slot has 0 valid products, slot empty in UI. No curated fallback.
3. **First-person collision is buggy.** Bounding-box collision against walls only. Furniture non-collidable.
4. **WebSocket drops mid-generation.** Auto-reconnect; status events also in final HTTP response.
5. **GCP rate limits / auth failures.** Real error surfaces to UI. No pre-baked WorldSpec substitution.
6. **Chat edits take too long.** Fade-to-black masks pipeline timing.
7. **3D performance.** Cap ~6 furniture/room, procedural primitives, simple per-room point lights, no shadows on furniture.

If demo flakiness emerges near submission time, we can add a fallback layer then. Not now.

### Out of scope (deliberately not building)

Multiplayer, persistence across sessions, authentication, mobile support, audio, physics/jumping, drag-edit in 3D world, ASI:One UI integration, fallback content.

---

## 7. Demo Plan

90-120 second flow:

1. Open landing page.
2. Type prompt: *"A 2-story modern beach house with an open kitchen, three bedrooms, and a reading nook"*.
3. Click Generate. Agent activity panel lights up sequentially. Parallel branch (4/5/6) lights up together. ~30-45s total.
4. Drop into first-person at the front door. Walk inside.
5. Click a couch → overlay shows 5 real Amazon products with prices and links.
6. Press T → type *"make the kitchen bigger and add a fireplace"*. Fade-to-black. Re-run. Fade-in.
7. Walk upstairs. Show second floor.
8. End on aerial cinematic shot.

---

## 8. Testing Strategy

End-to-end testing is the primary quality bar. Unit tests are secondary.

### Unit tests (`backend/tests/unit/`)
- WorldSpec Pydantic models accept valid examples and reject invalid ones.
- Compliance Critic validators flag the right errors on hand-crafted broken blueprints.
- Geometry Builder produces correct primitives for a known blueprint.
- Placement Validator removes overlapping furniture.
- Pricing Estimator sums correctly.

### End-to-end tests (`backend/tests/e2e/`)

These are the load-bearing tests. They actually run the full pipeline against live Gemini and verify the output is a *functional building*.

- **`test_full_pipeline_generates_valid_house`** — submit a prompt, run all 13 worker agents end-to-end, assert: WorldSpec validates, blueprint passes Compliance Critic, geometry has walls for every room, every room has at least one piece of furniture with a real product URL that returns 200, navigation has a spawn point inside the entrance room.
- **`test_multistory_house_has_aligned_stairs`** — submit a multi-story prompt, assert: blueprint has ≥2 floors, stairs connect them, stairs occupy the same x/y on both floors, navigation lists stair colliders.
- **`test_chat_edit_changes_blueprint`** — generate a house, send edit message ("add a fireplace"), assert: new WorldSpec differs in furniture (or blueprint), pipeline ran successfully.
- **`test_product_urls_are_live`** — generate a house, assert: every `selectedProductId` in furniture maps to a product whose URL HEAD-checks 200.

### Frontend smoke

- `frontend/tests/smoke.spec.ts` — Playwright. Open `/`, type prompt, submit, wait for build view, assert agent panel renders, assert canvas appears, assert WASD movement updates camera position.

### Test execution gates

- Unit tests must pass locally before commit.
- End-to-end tests must pass before declaring the project complete.
- Frontend smoke must pass on a fresh `npm run build && npm run start`.

---

## 9. Implementation Order

Build a vertical slice first. Don't build 14 great agents on a non-functional pipeline.

1. WorldSpec Pydantic models + 3 hand-written example fixtures.
2. FastAPI scaffold with `/api/generate` returning a static example WorldSpec.
3. Next.js + R3F scaffold. Render a hardcoded house from the example WorldSpec. WASD + mouse look working.
4. Wire up the WebSocket. Status events flow from backend (faked) to frontend agent panel.
5. Implement Intent Parser + Blueprint Architect + Compliance Critic against Gemini. Get one real generated blueprint flowing through.
6. 3D Geometry Builder, Lighting Designer, Material Stylist (parallel branch).
7. Furniture Planner + Placement Validator. Render furniture meshes.
8. Real Product Scout + Style Matcher. Wire up FurniturePanel overlay.
9. Pricing Estimator + Navigation Planner. Wire up StatusBar.
10. Chat Edit Coordinator + ChatPanel. Wire up edit flow and fade-to-black.
11. Agentverse registration for all 14 uAgents.
12. End-to-end tests. Verify. Polish.

---

## Appendix: Confirmed decisions log

- Stack: Next.js + React Three Fiber + drei. FastAPI bridge. Fetch.ai uAgents (in-process, all 14 registered to Agentverse).
- Generation runtime: ~30-45s sequential with one parallel branch (geometry/lighting/materials).
- Building scope: multi-story houses/apartments only.
- Edits: full structural edits via chat. Pipeline re-runs on every edit.
- Schema: axis-aligned rectangles, 0.5m grid, dimensions in meters.
- Products: Gemini grounded search live, URL HEAD-verified, no curated fallback.
- Failure handling: real errors surface; no silent fallbacks.
- Demo: 90-120s scripted flow. Pre-generation safety net deferred.
