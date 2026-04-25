# Conjure Agent Swarm — Design Spec

**Date:** 2026-04-25
**Status:** Approved for implementation planning

## Goal

Add a 19-agent multi-agent analysis pipeline to Conjure that runs once per world, producing structured insights (scene description, geolocation, shot list, prop shopping, story seeds, hazard audit, etc.) rendered in a sidebar drawer alongside a flashy "Circuit Board" network graph visualization.

The pipeline must satisfy the Fetch.ai Agentverse track: every agent is a real `uagents.Agent` registered on Agentverse with Chat Protocol, with declared message-passing dependencies forming a DAG.

## Architecture

### High-level flow

```
World creation (deferred — Marble API integration)
         ↓
First time a world is opened in browser:
  Frontend captures 3 yaw-rotated views (0°, 120°, 240°)
         ↓
  POST /api/perception-frames (frames saved to backend/worlds/<id>/views/)
         ↓
  POST /api/analyze/<id>
         ↓
  Backend orchestrator dispatches DAG of uAgent messages
         ↓
  Each uAgent: receives input → calls Gemini → publishes result → optional downstream subscribers fire
         ↓
  Orchestrator collects all 19 results, writes frontend/public/worlds/<id>.agents.json
         ↓
Subsequent visits: frontend fetches the static JSON, renders sidebar + plays scripted Circuit Board animation
```

The network graph animation is **scripted** — identical visual sequence every run, decoupled from real agent timing. Backend status events are **not** consumed by the visual; the visual is a baked performance played whenever the sidebar opens.

### Component map

**Backend (Python):**
- `backend/agents_v2/` — new package, one file per agent (19 files), each defining a `uagents.Agent` and its Chat Protocol message handler. Lives alongside the existing `backend/agents/` (which is dead pre-pivot code, left untouched for now).
- `backend/agents_v2/orchestrator.py` — DAG executor that dispatches messages, awaits responses, handles dependency edges
- `backend/agents_v2/uagent_runner.py` — boots all 19 agents on local ports, registers to Agentverse via `AGENTVERSE_API_KEY`
- `backend/agents_v2/messages.py` — shared `Model` types (PerceptionInput, ScenePerception, GeolocationResult, etc.)
- `backend/agents_v2/gemini_client.py` — thin wrapper around the existing `core/gemini_client.py` adding helpers for vision calls with structured JSON output
- `backend/bridge/main.py` — extended with new endpoints (existing FastAPI app, no replacement)

**Frontend (Next.js):**
- `components/AgentSidebar.tsx` — right-side slide-out drawer, toggle button, category-grouped cards
- `components/AgentNetworkGraph.tsx` — scripted SVG Circuit Board animation
- `components/agent-cards/` — one renderer per display type (`TextCard`, `ListCard` for v1; `SwatchCard`, `MapCard`, `ProductCard`, `ThumbnailCard` for v2)
- `lib/agentManifest.ts` — static metadata about the 19 agents (id, label, category, dependencies, expected display type) — used by sidebar grouping and graph layout
- Capture flow extension in `components/SplatScene.tsx`: when no perception frames exist for the world, capture 3 yaw-rotated frames and POST them, then trigger analyze.

### Why this split

The backend owns the agent computation and is intentionally heavy; the frontend is a dumb consumer of static JSON plus a scripted animation. This keeps demo-day risk low — even if the backend is down, cached worlds work perfectly. It also matches what production will look like once Marble is integrated: the pipeline runs server-side at world-creation time.

## The 19 agents (DAG)

Each agent is a `uagents.Agent` on its own port, registered on Agentverse, communicating via Chat Protocol. Dependencies listed below; agents with no dependencies start immediately on receipt of `PerceptionInput`.

### Tier 0 — Perception (no deps)
| Agent | Input | Output |
|---|---|---|
| `scene_describer` | PerceptionInput (3 captures + prompt) | dense paragraph + tags (indoor/outdoor, lighting, era, climate) |
| `object_inventory` | PerceptionInput | list of visible objects with rough position |
| `spatial_layout` | PerceptionInput | room graph: entrances, sightlines, est. square footage |

### Tier 1 — Real-world grounding
| Agent | Depends on | Output |
|---|---|---|
| `geolocator` | scene_describer | top-3 candidate regions with confidence + reasoning |
| `filming_scout` | geolocator | 3-5 mock real-world location matches with addresses |
| `era_estimator` | scene_describer | period (e.g., "1970s Scandinavian modern") |
| `architectural_style` | scene_describer | style classification (Craftsman, brutalist, etc.) |

### Tier 2 — Creative / production
| Agent | Depends on | Output |
|---|---|---|
| `shot_list` | spatial_layout, scene_describer | 5-8 specific camera shots (angle, lens, time of day) |
| `mood_palette` | scene_describer | 5-color palette + LUT/film stock suggestions |
| `soundscape` | scene_describer | ambient layer + Foley list |
| `prop_shopping` | object_inventory | product links (Amazon/Wayfair/IKEA — mocked URLs OK for hackathon) |
| `set_dressing` | scene_describer, object_inventory | "to make this scene more X, add Y" delta list |

### Tier 3 — Narrative
| Agent | Depends on | Output |
|---|---|---|
| `story_seed` | scene_describer, era_estimator | 3 short film/novel premises set here |
| `character_suggester` | scene_describer | 3-5 character cards (who lives/works here) |
| `npc_dialogue` | character_suggester | sample lines NPCs in this space might say |

### Tier 4 — Practical
| Agent | Depends on | Output |
|---|---|---|
| `real_estate_appraisal` | geolocator, spatial_layout | estimated rent in inferred market |
| `hazard_audit` | object_inventory, spatial_layout | fire exits, trip hazards, code violations |
| `accessibility_audit` | spatial_layout | wheelchair access, lighting concerns |
| `carbon_score` | object_inventory, scene_describer | embodied-carbon estimate from inferred materials |

**Total: 19 agents.** All run as `uagents.Agent` on ports 8100-8118 with seeded keys.

## Data contracts

### Backend: stored captures

```
backend/worlds/<id>/
  views/
    view_0.jpg     # at spawn yaw
    view_120.jpg   # +120°
    view_240.jpg   # +240°
  prompt.txt        # the original generation prompt (stub for now)
```

### Frontend: agents.json output

```json
{
  "world_id": "cabin",
  "generated_at": "2026-04-25T08:00:00Z",
  "schema_version": 1,
  "agents": {
    "scene_describer": {
      "status": "done",
      "duration_ms": 4200,
      "display": "text",
      "output": {
        "summary": "A rustic two-story log cabin nestled in...",
        "tags": ["indoor", "rustic", "warm-lit", "winter"]
      }
    },
    "geolocator": {
      "status": "done",
      "duration_ms": 3800,
      "display": "list",
      "output": {
        "candidates": [
          {"region": "Pacific Northwest, USA", "confidence": 0.72, "reasoning": "..."},
          {"region": "Norwegian fjords", "confidence": 0.18, "reasoning": "..."},
          {"region": "Swiss Alps", "confidence": 0.10, "reasoning": "..."}
        ]
      }
    }
  }
}
```

`status` ∈ `done | error`. Errored agents include `error_message` instead of `output`. Frontend renders error cards as gray "agent unavailable" cards rather than hiding them.

`display` ∈ `text | list | swatches | map | products | thumbnails`. v1 ships `text` and `list` renderers; others fall back to `text` (formatted JSON) until v2 cards land.

### uAgent message types

Defined in `backend/agents_v2/messages.py`. Examples:

```python
class PerceptionInput(Model):
    world_id: str
    prompt: str
    view_paths: list[str]  # absolute paths to view_0/120/240.jpg

class ScenePerception(Model):
    world_id: str
    summary: str
    tags: list[str]

class GeolocationResult(Model):
    world_id: str
    candidates: list[dict]  # {"region", "confidence", "reasoning"}
```

One message type per agent output. The orchestrator routes responses by `world_id` and collects them into the final JSON.

## API surface

New endpoints on the existing FastAPI bridge (`backend/bridge/main.py`):

| Endpoint | Purpose |
|---|---|
| `POST /api/perception-frames` | Body: `{world_id, view_0, view_120, view_240}` (data URLs). Saves all three to `backend/worlds/<id>/views/`. |
| `POST /api/analyze/<id>` | Triggers the DAG. Returns `202 Accepted` immediately; result is written to `frontend/public/worlds/<id>.agents.json` when complete. |
| `GET /api/analyze/<id>/status` | `{state: "queued"|"running"|"done"|"error"}` — used by frontend to know when to refresh `agents.json`. |

Existing `POST /api/thumbnail` endpoint stays as-is. `POST /api/perception-frames` is separate so we can iterate on perception capture without touching the thumbnail flow.

## Frontend behavior

### Capture flow extension

In `components/SplatScene.tsx`, after the existing auto-thumbnail logic:

1. On world load, HEAD-check `/worlds/<id>.agents.json`. If 200, render sidebar from it. If 404, proceed.
2. HEAD-check `/api/perception-frames/<id>` (or just attempt the analyze trigger; backend handles missing-frames case).
3. If frames missing: capture three frames from canvas — at the world's spawn yaw, +120°, +240° — by temporarily setting `camera.rotation.y` and calling `gl.render()` + `toDataURL()` for each. POST all three.
4. POST `/api/analyze/<id>` to start the DAG.
5. Poll `GET /api/analyze/<id>/status` every 2s; when `done`, fetch the static JSON and render.

The yaw-rotation captures must NOT permanently move the camera — save and restore the original rotation around the capture loop.

### Sidebar

- Right-side drawer, slides over the splat scene, splat stays visible (no replacement)
- Fixed toggle button top-right ("Agents" with a chevron icon)
- When opened: plays the scripted Circuit Board animation at the top, then renders the cards below as the animation progresses
- Cards grouped by tier with category headers (Perception, Real-world, Creative, Narrative, Practical)
- Each card: agent label, status badge, expand/collapse, output rendered via `display`-type renderer
- v1 renderers: `TextCard` (markdown summary + tag chips), `ListCard` (titled bullet list)
- Other display types fall through to `TextCard` with `JSON.stringify(output, null, 2)` until custom renderers ship

### Network graph animation

Scripted SVG, ~12 seconds total:

1. **0–1s**: blank circuit-board grid background fades in, "CAPTURE" node draws at center
2. **1–3s**: 3 perception nodes (Scene Describer, Object Inventory, Spatial Layout) draw, traces emerge from CAPTURE to each, pulses travel
3. **3–6s**: 4 grounding nodes draw (Geolocator, Filming Scout, Era, Style), traces grow, pulses travel from upstream perception nodes
4. **6–9s**: 5 creative nodes draw, then 3 narrative nodes
5. **9–11s**: 4 practical nodes draw
6. **11–12s**: every active edge gets one final pulse, then animation settles, all nodes glow steady, indicator shows "19 / 19 agents — done"

Implemented as a hand-authored SVG with `<animate>` / `<circle>` `<path>` elements, or a JS-driven sequence using `requestAnimationFrame` + GSAP-like keyframe timing (no GSAP dep — write minimal keyframe runner). Runs once per sidebar-open; replays on re-open.

Layout: hand-positioned grid, ~5 rows × ~5 cols, right-angle PCB traces, square chip-style nodes labeled with monospace agent IDs.

Color palette: `#fafafa` background, `#333` traces, `#fff` nodes with `#333` borders, **active edges and active node fills `#4a90ff` (Fetch blue)**.

## Error handling

- **Single agent errors:** orchestrator catches per-agent exceptions, marks that agent's entry as `status: "error"`, continues. Downstream agents that depend on a failed upstream get a `status: "skipped"` entry with `reason: "upstream_failed"`. Pipeline never aborts.
- **Gemini quota / rate limit:** retried 3 times with exponential backoff (1s, 4s, 16s) before marking `error`.
- **Frontend missing JSON:** sidebar shows "Analysis pending…" with a spinner; polls every 2s for up to 60s.
- **Analyze endpoint called twice for same world while running:** second call returns 409 with current status. Idempotent.
- **uAgent registration to Agentverse fails:** agents still run locally (uAgents framework permits no-mailbox mode). Logged as warning. Pipeline still produces output.

## What's explicitly out of scope

- **Marble API integration** — worlds are currently pre-built files. Pipeline runs against existing splats.
- **Live agent execution visible in browser** — animation is scripted theater. Real timing data is in the JSON but not consumed by the viz.
- **Tier 5 agents** (Critic, Variant Suggester) — confirmed deferred.
- **Custom card renderers** for swatches/maps/products/thumbnails — v1 ships text+list only.
- **Cleanup of old `backend/agents/` package** — left as dead code until after this ships.

## Open implementation considerations

These are flagged for the implementation plan, not unresolved design questions:

- **Gemini cost:** 19 agents × ~1 Gemini call each = ~19 calls per world. Many are text-only (cheap) but ~3-5 use vision (3 captures, more expensive). Per-world generation cost should be estimated in the plan and fit a hackathon budget. If too expensive, batch some non-vision agents into shared prompts.
- **uAgent Chat Protocol verbosity:** the existing `uagent_runner.py` defines a minimal `ChatMessage(content: str)`. Real DAG message passing wants typed messages — verify uAgents framework supports custom `Model` types per protocol or whether we route everything as JSON-stringified `ChatMessage.content`.
- **Capture-from-canvas yaw rotation:** test that `gl.render()` + `toDataURL()` works correctly when called repeatedly within the same frame for different camera rotations. May need to wait one frame between rotations.

## Testing approach

- **Backend:** unit tests per agent with mocked Gemini responses. Integration test: orchestrator runs DAG end-to-end with all-stubbed agents, verifies dependency ordering and JSON output shape.
- **Frontend:** sidebar rendering tested with hand-authored fixture JSONs (one per display type). Animation tested manually — no automated visual test.
- **Live demo dry-run:** run the full pipeline against `cabin`, `office`, `living_room` once each, confirm JSON outputs look reasonable, network graph plays cleanly.
