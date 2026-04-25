# Configure

Type a prompt like *"a small cozy cabin"* or *"a two-story modern house"* and get a walkable 3D building rendered in your browser. A pipeline of Gemini-backed agents turns the prompt into a structured building spec — rooms, walls, lighting, materials, furniture — and the frontend renders it with React Three Fiber so you can spawn inside and walk around.

Built for **LA Hacks 2026 (Fetch.ai Agentverse track)**. 14 agents are registered on Agentverse with the Chat Protocol; the actual generation runs through them as a sequential + parallel pipeline orchestrated by FastAPI.

> **Where this is heading:** the next phase pivots away from real-product matching (Walmart/Amazon scraping was unreliable) toward **bigger buildings** — office buildings, multi-floor commercial spaces — using base procedural meshes for furniture instead of real-product alternates. See `docs/ROADMAP.md` for the pivot plan.

---

## Quick start

### Prereqs

- Python 3.11+
- Node 20+
- A `GOOGLE_API_KEY` for Gemini (https://aistudio.google.com/app/apikey)
- Optional: `AGENTVERSE_API_KEY` if you want the 14 uAgents to register on Agentverse

### Setup

```bash
# clone
git clone https://github.com/pauligwe/WorldEdit.git
cd WorldEdit

# backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env   # fill in GOOGLE_API_KEY
cd ..

# frontend
cd frontend
npm install
cd ..
```

### Run

Two terminals:

```bash
# Terminal 1 — backend (FastAPI on :8000)
cd backend
source .venv/bin/activate
WORLD_BUILD_DISABLE_UAGENTS=1 uvicorn bridge.main:app --port 8000
# drop WORLD_BUILD_DISABLE_UAGENTS=1 to also register the 14 uAgents on Agentverse
```

```bash
# Terminal 2 — frontend (Next.js on :3000)
cd frontend
npm run dev
```

Open http://localhost:3000, type a prompt, watch the agent pipeline run, then walk around the result.

### Controls

- **WASD** — walk
- **Mouse** — look (click canvas to capture pointer)
- **Click furniture** — open product panel, browse alternates
- **T** — toggle chat (edit the world with natural language)
- **Esc** — release pointer

---

## What it builds

Each generated world is a `WorldSpec` (see `backend/core/world_spec.py`):

- **Blueprint**: floors → rooms (axis-aligned rectangles on a grid) with doors/windows/stairs
- **Geometry**: flattened primitives — boxes for floors/ceilings/stairs, walls (with door/window holes)
- **Lighting**: per-room point lights
- **Materials**: per-room wall/floor/ceiling material tokens (e.g. `oak_planks`, `marble_tile`)
- **Furniture**: typed items (chair, table, lamp, bed, plant, …) with position/size/rotation
- **Products** *(legacy — being phased out)*: per-furniture product alternates pulled from real vendors via Gemini grounded search
- **Navigation**: spawn point + walkable mesh ids
- **Cost**: `byRoom` + total

---

## Architecture in 30 seconds

```
prompt
  │
  ▼
┌──────────────────── orchestrator ─────────────────────┐
│ intent_parser → blueprint_architect → compliance_critic│  (sequential)
│        ↓                                                │
│ ┌─ geometry_builder ┐                                  │
│ ├─ lighting_designer├── parallel, merged back into spec│
│ └─ material_stylist ┘                                  │
│        ↓                                                │
│ furniture_planner → placement_validator → product_scout│
│ → style_matcher → pricing_estimator → navigation_planner│ (sequential)
└────────────────────────────────────────────────────────┘
  │
  ▼
WorldSpec → saved to backend/worlds/<id>.json → streamed to frontend over WS
```

- **`backend/agents/`** — 14 single-responsibility agents. Each reads/writes a slice of `WorldSpec`. Pure functions in/out; LLM calls are inside the agent.
- **`backend/agents/orchestrator.py`** — runs them in the right order; LLM calls in parallel where there are no data dependencies.
- **`backend/bridge/main.py`** — FastAPI: `POST /api/generate`, `POST /api/edit`, `POST /api/select-product`, `GET /api/world/{id}`, `WS /ws/build/{id}`, plus `/api/img` (image proxy with og:image fallback) and `/api/img-color` (Pillow dominant-color extraction).
- **`backend/agents/uagent_runner.py`** — registers 14 uAgents on Agentverse with the Chat Protocol (Fetch.ai track requirement). The actual pipeline runs in-process; uAgents are echo handlers.
- **`backend/core/`** — pure logic: `WorldSpec` (Pydantic), grid validators, geometry flattening, navigation, placement, pricing.
- **`frontend/`** — Next.js 14 App Router + React Three Fiber. The 3D scene is `components/World3D.tsx`; furniture meshes are in `components/Furniture/`; movement is `components/PlayerControls.tsx`.

For a deeper pass through the code, read **`docs/ARCHITECTURE.md`**. For where this is going, read **`docs/ROADMAP.md`**.

---

## Tests

```bash
cd backend
source .venv/bin/activate

# unit tests (fast, no network)
pytest tests/unit -v

# end-to-end (hits Gemini + real vendor sites — needs GOOGLE_API_KEY, slow ~10 min)
pytest tests/e2e -v
```

The e2e suite generates real worlds and asserts the WorldSpec is structurally valid, multi-story works, and product URLs are live.

---

## Layout

```
backend/
  agents/        14 pipeline agents + uagent_runner + orchestrator + chat_edit_coordinator
  bridge/        FastAPI server (HTTP + WS + image proxy)
  core/          WorldSpec, prompts, pure helpers (geometry, placement, pricing, …)
  tests/         unit + e2e
  worlds/        generated WorldSpec JSON (gitignored)
frontend/
  app/           Next.js routes (/ form, /build/[worldId] viewer)
  components/    World3D, Furniture/*, PlayerControls, ChatPanel, FurniturePanel, …
  lib/           api client + WorldSpec types (mirrors backend Pydantic)
docs/
  ARCHITECTURE.md   how the pieces fit; where to make changes
  ROADMAP.md        next steps (office-building pivot)
  superpowers/      original design spec + implementation plan
```

---

## Environment variables

| Var | Required | Notes |
|---|---|---|
| `GOOGLE_API_KEY` | yes | Gemini grounded-search and structured outputs |
| `AGENTVERSE_API_KEY` | optional | needed only if you want uAgents to register on Agentverse |
| `WORLD_BUILD_DISABLE_UAGENTS` | optional | set to `1` to skip the uAgent thread (faster local dev) |
| `NEXT_PUBLIC_BRIDGE_URL` | optional | frontend → backend URL, defaults to `http://localhost:8000` |
