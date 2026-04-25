# Architecture

This is a hand-off document for someone picking up the project. It explains *why* things are where they are, not just *what* they are. If you're going to add a feature or fix a bug, read this first.

---

## The mental model

There is exactly one shared object that flows through the system: **`WorldSpec`** (`backend/core/world_spec.py`). Everything else is a function `WorldSpec → WorldSpec` that fills in one slice.

```
prompt           ─┐
intent           ─┤ written by intent_parser
site             ─┤ written by intent_parser (pure code)
blueprint        ─┤ written by blueprint_architect, validated by compliance_critic
geometry         ─┤ written by geometry_builder       ┐
lighting         ─┤ written by lighting_designer      │ run in parallel
materials        ─┤ written by material_stylist       ┘
furniture        ─┤ written by furniture_planner, validated by placement_validator
cost             ─┤ written by pricing_estimator
navigation       ─┘ written by navigation_planner
```

Every agent receives the whole spec and returns a (mutated) spec. They are dumb in isolation; the orchestrator gives them order.

If you understand `world_spec.py` and `orchestrator.py`, you understand the system.

---

## The pipeline (`backend/agents/orchestrator.py`)

Three phases:

1. **Sequential prefix** — `intent_parser` → `blueprint_architect` → `compliance_critic`. These build the structural skeleton; later steps assume rooms exist.
2. **Parallel middle** — `geometry_builder`, `lighting_designer`, `material_stylist` are launched concurrently because none reads the others' outputs. Each runs on a `model_copy(deep=True)` of the spec; their results are merged back by hand.
3. **Sequential suffix** — `furniture_planner` → `placement_validator` → `pricing_estimator` → `navigation_planner`. (`product_scout` and `style_matcher` removed from `POST_STEPS` as of site pivot; agents still registered as uAgents.)

Agents are registered as `(name, callable)` tuples in three lists. **To add a new agent, add it to the right list.** Don't be tempted to introduce a DAG framework — three lists are enough and they fit on one screen.

### Status streaming

`StatusBus` (`backend/core/status_bus.py`) is a tiny pub/sub. Every step publishes `running` / `done` / `error`. The frontend opens `WS /ws/build/{worldId}` and renders the activity feed in real time.

When the pipeline finishes, the orchestrator publishes a synthetic `__final__` event carrying the full spec. On error, `__pipeline__` with state `error`. The frontend uses these to know when to stop listening.

### Why some agents call Gemini and some don't

| Agent | LLM? | Why |
|---|---|---|
| `intent_parser` | yes | natural language → structured Intent |
| `blueprint_architect` | yes | spatial reasoning, hard to do procedurally |
| `compliance_critic` | yes | "does this make sense" judgement |
| `geometry_builder` | no | pure flattening of blueprint → primitives |
| `lighting_designer` | yes | aesthetic choice |
| `material_stylist` | yes | aesthetic choice |
| `furniture_planner` | yes | "what goes in a kitchen" + sizes |
| `placement_validator` | no | pure geometry: collisions, room fit |
| `product_scout` | yes (grounded search) | finds real vendor URLs *(legacy)* |
| `style_matcher` | yes | picks `selectedProductId` per item *(legacy)* |
| `pricing_estimator` | no | sums product prices |
| `navigation_planner` | no | picks spawn point inside first room |

Rule of thumb: aesthetic / linguistic = LLM. Geometric / arithmetic = pure code. **Resist adding LLM calls where pure code would do.** They're the slow part of the pipeline (~5–8 min total for a small house).

---

## The data model (`backend/core/world_spec.py`)

A few non-obvious things:

- **Grid alignment.** Blueprint validates that every room x/y/width/depth is on the `gridSize` grid (default 0.5m). This catches LLM drift early. If you change the gridSize, expect to re-tune the prompts.
- **Geometry primitives are flat.** `geometry_builder` flattens the hierarchical blueprint into a list of `{type, position, size, rotation, holes}` boxes. The frontend renders this list directly with `<boxGeometry>`. Walls get `holes` for doors/windows; `Wall.tsx` builds them out of multiple sub-meshes.
- **Furniture has both a procedural mesh and (legacy) a product.** `type` (e.g. `"chair"`) picks the procedural component in `frontend/components/Furniture/`. `selectedProductId` is the user's chosen alternate; if absent, the mesh uses a hash-derived tint.
- **`tint` on `FurnitureItem`.** Currently unused in the spec — the active tint is computed at render time in `World3D.tsx`. We may want to bake it into the spec eventually.

---

## The bridge (`backend/bridge/main.py`)

Endpoints:

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/generate` | start a new world from prompt; returns `worldId`, drives pipeline async |
| POST | `/api/edit` | natural-language edit; clones the spec, runs `chat_edit_coordinator`, kicks off the pipeline again with a new `worldId` |
| POST | `/api/select-product` | pin a product to a furniture item *(legacy)* |
| GET | `/api/world/{id}` | hydrate from in-memory cache or `worlds/<id>.json` |
| WS | `/ws/build/{id}` | stream `AgentStatus` events |
| GET | `/api/img` | proxy image fetches; spoofs Referer; falls back to `og:image` from product page |
| GET | `/api/img-color` | Pillow dominant-color extraction *(legacy — used to tint furniture from product image)* |

### Why the image proxy exists

Vendor CDNs (Walmart, Wayfair, …) often block hotlinking. Direct `<img src=>` from the browser fails CORS or returns 403. The proxy:

1. Tries the image URL with browser-like headers + a `Referer` from the product page.
2. If that fails, scrapes `og:image` / `twitter:image` from the product page HTML and tries that.
3. Caches body and content-type per `(product_url || image_url)` key.

`/api/img-color` reuses the cached bytes so we don't double-fetch.

### Why worlds get hydrated from disk

Pipeline output is saved to `backend/worlds/<id>.json` (in `_drive`). On backend restart, the in-memory `worlds` dict is empty, so `/api/world/{id}` falls back to disk read via `_load_world`. **Without this, every restart breaks live URLs.**

---

## The frontend (`frontend/`)

### Routes

- `/` — `app/page.tsx` — prompt form. POSTs `/api/generate`, redirects to `/build/[worldId]`.
- `/build/[worldId]` — `app/build/[worldId]/page.tsx` — viewer. Tries `getWorld` first; if the world is already complete (has `cost` + `navigation`), renders immediately. Otherwise opens `WS /ws/build/{id}` and shows the activity panel until `__final__` arrives.

### The 3D scene

`components/World3D.tsx` is the entry point. It:

1. Reads `geometry.primitives` and partitions by type (wall / floor / ceiling / stair).
2. Renders walls via `<Wall>` (multi-mesh with holes), everything else as `<boxGeometry>`.
3. Renders furniture by mapping `spec.furniture` → `<Furniture>` (which dispatches on `item.type` to the procedural component in `components/Furniture/`).
4. Mounts `<PlayerControls>` (pointer-lock + WASD + AABB collision against walls).
5. Layers HUD: crosshair, status bar, optional furniture/chat panels.

The procedural furniture meshes are in `components/Furniture/{Chair,Table,Bed,Lamp,Couch,Bookshelf,Plant,Rug}.tsx`. Each is a small `<group>` of boxes/cylinders parameterized by `{size, color}`. **This is where the office-building pivot work lands** — see `ROADMAP.md`.

### Movement

`PlayerControls.tsx` does pointer-lock, WASD on the camera, and AABB collision against the wall list passed in. There's no ceiling check yet. Stairs are walkable as flat ramps.

### Why the editor lives in a side panel

`ChatPanel.tsx` posts to `/api/edit`. The backend creates a new `worldId` for each edit (forks the spec), so undo is free: navigate back. We don't try to mutate in place.

---

## Tests

- **`tests/unit/`** — mostly pure-logic tests on `core/`. No network. Run constantly.
- **`tests/e2e/`** — hit Gemini and real vendor sites. Slow (5–10 min each). Run before releases. They generate a real world end-to-end and assert structural shape.

There's no frontend test suite yet. Manual testing in browser is the workflow — the worlds are visual.

---

## Common changes, where to make them

| Want to… | Touch |
|---|---|
| Add a new room type (e.g. `"office"`) | prompt examples in `core/prompts/blueprint_architect.py` + `furniture_planner.py` |
| Add a new furniture type | `world_spec.py` (no enum — type is a string) + new component in `frontend/components/Furniture/` + entry in `components/Furniture/index.tsx` + add to `furniture_planner` prompt |
| Add a new agent | `backend/agents/<name>.py` exposing `def run(spec) -> spec`, then add a tuple to the right list in `orchestrator.py` |
| Change pipeline order / parallelism | only `orchestrator.py` |
| Change spawn point logic | `core/navigation.py` + `agents/navigation_planner.py` |
| Change movement | `frontend/components/PlayerControls.tsx` |
| Change a Gemini prompt | `backend/core/prompts/<agent>.py` — these are pure strings; restart not always needed |
| Add a new HTTP endpoint | `backend/bridge/main.py` |
| Add a new uAgent | `agents/uagent_runner.py` — append to `AGENT_NAMES` |
| Add a new room template | `backend/core/room_templates.py` |
| Change plot size / entrance side | `backend/core/site.py` (`derive_site_from_intent`) |
| Change building cost rate | `backend/core/pricing.py` (`COST_PER_SQM`) |

---

## Things I'd do differently next time

- The `products` / `selectedProductId` / image-proxy / dominant-color path is ~40% of the backend code and contributes ~10% of the user value. Walmart's HEAD-200/GET-404 anomaly for delisted items burned hours. **The pivot away from real products is the right call.**
- The `chat_edit_coordinator` re-runs the whole pipeline. For small edits (move a chair) this is overkill — should diff and re-run only affected agents.
- Frontend WorldSpec types are hand-mirrored from the Pydantic models. A code-gen step would prevent drift.
- No caching of LLM calls. The same prompt regenerates from scratch every time. A simple disk cache keyed on `(agent_name, hash(input_spec))` would make iteration much faster.
