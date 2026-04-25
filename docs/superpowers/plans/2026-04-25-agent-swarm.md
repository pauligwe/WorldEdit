# Conjure Agent Swarm Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a 19-agent multi-agent analysis pipeline to Conjure that produces structured insights for each world (perception, geolocation, shot list, props, narrative, audits) renderable in a sidebar drawer alongside a scripted Circuit Board network graph animation.

**Architecture:** New `backend/agents_v2/` package with 19 `uagents.Agent` processes (Fetch.ai Agentverse), a DAG orchestrator that fans out via Chat Protocol message-passing, results written as static JSON to `frontend/public/worlds/<id>.agents.json`. Frontend captures 3 yaw-rotated perception views automatically on first world visit, triggers analysis, then renders sidebar from the static JSON. The network graph animation is fully scripted theater — identical visual sequence every run, decoupled from real agent timing.

**Tech Stack:** Python 3.11 (uagents 0.24, google-genai, FastAPI, Pydantic), Next.js 14 / React 18 / TypeScript, three.js + @react-three/fiber, SVG for the network graph.

**Spec:** `docs/superpowers/specs/2026-04-25-agent-swarm-design.md`

---

## File Structure

### Backend — new

- `backend/agents_v2/__init__.py` — package marker
- `backend/agents_v2/messages.py` — all `uagents.Model` message types (one input/output type per agent)
- `backend/agents_v2/manifest.py` — single source of truth: list of 19 agents with `id`, `port`, `tier`, `dependencies`, `display_type`
- `backend/agents_v2/registry.py` — instantiates one `Agent` per manifest entry, registers Chat Protocol handlers, holds the in-process dispatch table
- `backend/agents_v2/orchestrator.py` — DAG executor: takes `PerceptionInput`, walks dependency graph, dispatches messages, collects results into final JSON dict
- `backend/agents_v2/runner.py` — replacement for the old `uagent_runner.py`: spins up 19 agents on ports 8100-8118 in a daemon thread
- `backend/agents_v2/agents/__init__.py` — package marker
- `backend/agents_v2/agents/scene_describer.py` — Tier 0 perception agent
- `backend/agents_v2/agents/object_inventory.py`
- `backend/agents_v2/agents/spatial_layout.py`
- `backend/agents_v2/agents/geolocator.py` — Tier 1
- `backend/agents_v2/agents/filming_scout.py`
- `backend/agents_v2/agents/era_estimator.py`
- `backend/agents_v2/agents/architectural_style.py`
- `backend/agents_v2/agents/shot_list.py` — Tier 2
- `backend/agents_v2/agents/mood_palette.py`
- `backend/agents_v2/agents/soundscape.py`
- `backend/agents_v2/agents/prop_shopping.py`
- `backend/agents_v2/agents/set_dressing.py`
- `backend/agents_v2/agents/story_seed.py` — Tier 3
- `backend/agents_v2/agents/character_suggester.py`
- `backend/agents_v2/agents/npc_dialogue.py`
- `backend/agents_v2/agents/real_estate.py` — Tier 4
- `backend/agents_v2/agents/hazard_audit.py`
- `backend/agents_v2/agents/accessibility.py`
- `backend/agents_v2/agents/carbon_score.py`

### Backend — modified

- `backend/bridge/main.py` — add 3 endpoints (`POST /api/perception-frames`, `POST /api/analyze/{id}`, `GET /api/analyze/{id}/status`); replace `uagent_runner` import with `agents_v2.runner`
- `backend/core/gemini_client.py` — add `vision()` helper for multi-image vision calls (existing `text`/`structured`/`grounded_search` stay)

### Backend — tests

- `backend/tests/unit/test_agent_manifest.py`
- `backend/tests/unit/test_agent_messages.py`
- `backend/tests/unit/test_agent_orchestrator.py`
- `backend/tests/unit/test_perception_endpoint.py`
- `backend/tests/unit/test_analyze_endpoint.py`
- `backend/tests/unit/test_agents/test_scene_describer.py` (one per agent — same shape, mocked Gemini)

### Frontend — new

- `frontend/lib/agentManifest.ts` — mirror of backend manifest (id, label, category, position on graph, display type)
- `frontend/lib/agentResults.ts` — types + fetch helper for `<id>.agents.json`
- `frontend/components/AgentSidebar.tsx` — slide-out drawer
- `frontend/components/AgentNetworkGraph.tsx` — scripted SVG Circuit Board animation
- `frontend/components/agent-cards/TextCard.tsx`
- `frontend/components/agent-cards/ListCard.tsx`
- `frontend/components/agent-cards/index.ts` — selector by display type, defaulting to TextCard

### Frontend — modified

- `frontend/components/SplatScene.tsx` — extend capture flow: also capture 3 yaw-rotated views, POST to `/api/perception-frames`, trigger `/api/analyze/{id}`, poll for completion, mount `AgentSidebar` overlay
- `frontend/app/world/[id]/page.tsx` — pass world id through (already does)

### Frontend — tests

We don't have frontend tests in this repo today. Plan adds none — manual testing per the spec's "Live demo dry-run".

---

## Pre-flight

### Task 0: Worktree + branch setup

This work spans backend + frontend and is large. Do it on a worktree branch.

- [ ] **Step 1: Verify clean working tree**

```bash
cd /Users/tomalmog/projects/world-build
git status
```

Expected: `nothing to commit, working tree clean` OR a list of pending world-asset/work changes that should be committed first. If unclean, pause and resolve before continuing.

- [ ] **Step 2: Create worktree branch**

```bash
cd /Users/tomalmog/projects/world-build
git worktree add ../world-build-agents -b agent-swarm
cd ../world-build-agents
```

Expected: new directory created, on branch `agent-swarm`.

- [ ] **Step 3: Verify Python deps installed**

```bash
cd backend
source .venv/bin/activate
python -c "import uagents, google.genai, fastapi; print('ok')"
```

Expected: `ok`. If ImportError, `pip install -r requirements.txt`.

- [ ] **Step 4: Verify env vars**

```bash
grep -E "GOOGLE_API_KEY|AGENTVERSE_API_KEY" /Users/tomalmog/projects/world-build/backend/.env | sed 's/=.*/=<set>/'
```

Expected: both keys listed (values redacted by sed). If `GOOGLE_API_KEY` missing, ask user before continuing (Gemini calls won't work without it). `AGENTVERSE_API_KEY` is optional but should be present for the demo.

---

## Phase 1 — Backend foundation (manifest, messages, orchestrator skeleton)

### Task 1: Agent manifest

**Files:**
- Create: `backend/agents_v2/__init__.py`
- Create: `backend/agents_v2/manifest.py`
- Test: `backend/tests/unit/test_agent_manifest.py`

- [ ] **Step 1: Create empty package marker**

```bash
mkdir -p /Users/tomalmog/projects/world-build-agents/backend/agents_v2
touch /Users/tomalmog/projects/world-build-agents/backend/agents_v2/__init__.py
```

- [ ] **Step 2: Write the failing test**

Create `backend/tests/unit/test_agent_manifest.py`:

```python
from agents_v2.manifest import AGENTS, AgentDef


def test_exactly_19_agents():
    assert len(AGENTS) == 19


def test_unique_ids_and_ports():
    ids = [a.id for a in AGENTS]
    ports = [a.port for a in AGENTS]
    assert len(set(ids)) == 19
    assert len(set(ports)) == 19


def test_ports_in_expected_range():
    for a in AGENTS:
        assert 8100 <= a.port <= 8118


def test_dependencies_reference_known_ids():
    ids = {a.id for a in AGENTS}
    for a in AGENTS:
        for dep in a.dependencies:
            assert dep in ids, f"{a.id} depends on unknown {dep}"


def test_no_dependency_cycles():
    # Topological sort must succeed
    by_id = {a.id: a for a in AGENTS}
    visited = set()
    stack = set()

    def visit(node_id: str):
        if node_id in stack:
            raise AssertionError(f"cycle through {node_id}")
        if node_id in visited:
            return
        stack.add(node_id)
        for dep in by_id[node_id].dependencies:
            visit(dep)
        stack.remove(node_id)
        visited.add(node_id)

    for a in AGENTS:
        visit(a.id)


def test_tier_0_has_no_deps():
    tier0 = [a for a in AGENTS if a.tier == 0]
    assert len(tier0) == 3
    for a in tier0:
        assert a.dependencies == []


def test_known_agent_ids_present():
    ids = {a.id for a in AGENTS}
    expected = {
        "scene_describer", "object_inventory", "spatial_layout",
        "geolocator", "filming_scout", "era_estimator", "architectural_style",
        "shot_list", "mood_palette", "soundscape", "prop_shopping", "set_dressing",
        "story_seed", "character_suggester", "npc_dialogue",
        "real_estate", "hazard_audit", "accessibility", "carbon_score",
    }
    assert ids == expected
```

- [ ] **Step 3: Run test to verify it fails**

```bash
cd /Users/tomalmog/projects/world-build-agents/backend
pytest tests/unit/test_agent_manifest.py -v
```

Expected: ImportError on `agents_v2.manifest`.

- [ ] **Step 4: Implement manifest**

Create `backend/agents_v2/manifest.py`:

```python
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
    label: str            # human-readable, shown in sidebar/graph
    tier: Tier
    port: int             # local uagent listen port
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
```

- [ ] **Step 5: Run test to verify it passes**

```bash
cd /Users/tomalmog/projects/world-build-agents/backend
pytest tests/unit/test_agent_manifest.py -v
```

Expected: 7 tests pass.

- [ ] **Step 6: Commit**

```bash
cd /Users/tomalmog/projects/world-build-agents
git add backend/agents_v2/__init__.py backend/agents_v2/manifest.py backend/tests/unit/test_agent_manifest.py
git commit -m "feat(agents_v2): add 19-agent manifest with tiers and dependencies"
```

---

### Task 2: Shared message types

**Files:**
- Create: `backend/agents_v2/messages.py`
- Test: `backend/tests/unit/test_agent_messages.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/unit/test_agent_messages.py`:

```python
from agents_v2.messages import (
    PerceptionInput, AgentRequest, AgentResponse,
    SceneDescription, ObjectInventory, SpatialLayout,
    GeolocationResult, FilmingScoutResult,
    EraEstimate, ArchitecturalStyle,
    ShotList, MoodPalette, Soundscape, PropShopping, SetDressing,
    StorySeed, Characters, NPCDialogue,
    RealEstate, HazardAudit, Accessibility, CarbonScore,
)


def test_perception_input_roundtrip():
    p = PerceptionInput(
        world_id="cabin", prompt="rustic cabin",
        view_paths=["/a.jpg", "/b.jpg", "/c.jpg"],
    )
    assert p.world_id == "cabin"
    assert len(p.view_paths) == 3


def test_agent_request_carries_upstream_outputs():
    req = AgentRequest(
        world_id="cabin",
        agent_id="filming_scout",
        prompt="rustic cabin",
        view_paths=["/a.jpg"],
        upstream={"geolocator": {"candidates": [{"region": "PNW", "confidence": 0.7}]}},
    )
    assert req.upstream["geolocator"]["candidates"][0]["region"] == "PNW"


def test_agent_response_done_shape():
    r = AgentResponse(
        world_id="cabin",
        agent_id="scene_describer",
        status="done",
        output={"summary": "x", "tags": []},
        duration_ms=1234,
    )
    assert r.status == "done"
    assert r.error_message is None


def test_agent_response_error_shape():
    r = AgentResponse(
        world_id="cabin",
        agent_id="scene_describer",
        status="error",
        error_message="boom",
        duration_ms=42,
    )
    assert r.output is None


def test_scene_description_fields():
    s = SceneDescription(summary="A rustic cabin", tags=["rustic", "warm"])
    assert s.summary
    assert "rustic" in s.tags


def test_geolocation_candidate_shape():
    g = GeolocationResult(candidates=[
        {"region": "PNW", "confidence": 0.7, "reasoning": "conifers"},
    ])
    assert g.candidates[0]["confidence"] == 0.7
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_agent_messages.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement messages**

Create `backend/agents_v2/messages.py`:

```python
"""uagents.Model message types for the agent swarm.

Two transport types route data through the swarm:
- AgentRequest: sent from orchestrator to each agent
- AgentResponse: sent back from each agent to orchestrator

Per-agent output types (SceneDescription, GeolocationResult, etc.) are
nested into AgentResponse.output as plain dicts. We keep them as Pydantic
models for validation when the agents themselves construct results, but
on the wire everything flows as dicts to avoid a combinatorial number of
typed message subclasses.
"""
from typing import Literal, Optional
from uagents import Model
from pydantic import BaseModel


# ---- Transport (uagents.Model — used over Chat Protocol) ----

class PerceptionInput(Model):
    """Initial input to any agent — captured frames + prompt."""
    world_id: str
    prompt: str
    view_paths: list[str]  # absolute paths to view_0/120/240.jpg


class AgentRequest(Model):
    """Orchestrator → agent. Contains everything the agent needs to run."""
    world_id: str
    agent_id: str
    prompt: str
    view_paths: list[str]
    upstream: dict = {}  # agent_id -> output dict


class AgentResponse(Model):
    """Agent → orchestrator. status='done' carries output, 'error' carries error_message."""
    world_id: str
    agent_id: str
    status: Literal["done", "error"]
    duration_ms: int
    output: Optional[dict] = None
    error_message: Optional[str] = None


# ---- Per-agent output schemas (Pydantic — used internally for Gemini structured output) ----

class SceneDescription(BaseModel):
    summary: str
    tags: list[str]


class ObjectInventory(BaseModel):
    objects: list[dict]  # {"name": str, "position": str}


class SpatialLayout(BaseModel):
    rooms: list[dict]  # {"name": str, "approx_sqft": int}
    entrances: list[str]
    sightlines: list[str]
    total_sqft_estimate: int


class GeolocationResult(BaseModel):
    candidates: list[dict]  # {"region": str, "confidence": float, "reasoning": str}


class FilmingScoutResult(BaseModel):
    locations: list[dict]  # {"name": str, "address": str, "match_reason": str}


class EraEstimate(BaseModel):
    period: str
    confidence: float
    reasoning: str


class ArchitecturalStyle(BaseModel):
    style: str
    confidence: float
    reasoning: str


class ShotList(BaseModel):
    shots: list[dict]  # {"name": str, "angle": str, "lens_mm": int, "time_of_day": str, "notes": str}


class MoodPalette(BaseModel):
    palette: list[str]    # 5 hex colors
    luts: list[str]
    film_stocks: list[str]


class Soundscape(BaseModel):
    ambient: list[str]
    foley: list[str]


class PropShopping(BaseModel):
    items: list[dict]  # {"name": str, "vendor": str, "url": str, "price_estimate_usd": float}


class SetDressing(BaseModel):
    suggestions: list[dict]  # {"theme": str, "additions": list[str]}


class StorySeed(BaseModel):
    premises: list[dict]  # {"title": str, "logline": str, "genre": str}


class Characters(BaseModel):
    characters: list[dict]  # {"name": str, "role": str, "bio": str}


class NPCDialogue(BaseModel):
    lines: list[dict]  # {"character": str, "line": str}


class RealEstate(BaseModel):
    estimated_monthly_rent_usd: int
    market: str
    reasoning: str


class HazardAudit(BaseModel):
    hazards: list[dict]  # {"type": str, "severity": str, "description": str}


class Accessibility(BaseModel):
    issues: list[dict]      # {"category": str, "description": str}
    suggestions: list[str]


class CarbonScore(BaseModel):
    embodied_carbon_kg_co2e: int
    breakdown: list[dict]   # {"material": str, "kg_co2e": int}
    reasoning: str
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/unit/test_agent_messages.py -v
```

Expected: 6 tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/agents_v2/messages.py backend/tests/unit/test_agent_messages.py
git commit -m "feat(agents_v2): add transport + per-agent output message types"
```

---

### Task 3: Vision-aware Gemini client helper

**Files:**
- Modify: `backend/core/gemini_client.py`
- Test: `backend/tests/unit/test_gemini_vision.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/unit/test_gemini_vision.py`:

```python
from unittest.mock import patch, MagicMock
from pydantic import BaseModel
from core import gemini_client


class _Out(BaseModel):
    summary: str


def test_vision_calls_with_inline_image_parts():
    """vision() builds a request with one text prompt + N image parts and parses
    structured response."""
    mock_resp = MagicMock()
    mock_resp.parsed = _Out(summary="hi")
    mock_resp.text = '{"summary": "hi"}'

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_resp

    with patch.object(gemini_client, "_client", mock_client):
        # Two tiny synthetic images (1x1 PNGs)
        img_bytes = bytes.fromhex(
            "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
            "890000000d49444154789c63000100000005000100"
            "5d8a0a3a0000000049454e44ae426082"
        )
        out = gemini_client.vision(
            prompt="describe",
            images=[("image/png", img_bytes), ("image/png", img_bytes)],
            schema=_Out,
        )
        assert out.summary == "hi"

    # Exactly one generate_content call
    assert mock_client.models.generate_content.call_count == 1


def test_vision_raises_when_no_api_key():
    with patch.object(gemini_client, "_client", None):
        try:
            gemini_client.vision(prompt="x", images=[], schema=_Out)
        except gemini_client.GeminiError as e:
            assert "GOOGLE_API_KEY" in str(e)
        else:
            raise AssertionError("expected GeminiError")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_gemini_vision.py -v
```

Expected: AttributeError on `gemini_client.vision`.

- [ ] **Step 3: Add `vision()` to `core/gemini_client.py`**

Append to `backend/core/gemini_client.py`:

```python
def vision(
    prompt: str,
    images: list[tuple[str, bytes]],
    schema: Type[T],
    system: str | None = None,
    model: str = DEFAULT_MODEL,
) -> T:
    """Send a multimodal prompt with N inline images, expecting JSON matching schema.

    images: list of (mime_type, raw_bytes) tuples — typically 'image/jpeg'.
    """
    client = _require_client()
    parts: list = [gtypes.Part.from_text(text=prompt)]
    for mime, data in images:
        parts.append(gtypes.Part.from_bytes(data=data, mime_type=mime))
    contents = [gtypes.Content(role="user", parts=parts)]
    cfg = gtypes.GenerateContentConfig(
        system_instruction=system,
        response_mime_type="application/json",
        response_schema=schema,
    )
    resp = client.models.generate_content(model=model, contents=contents, config=cfg)
    parsed = resp.parsed
    if isinstance(parsed, schema):
        return parsed
    raw = (resp.text or "").strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise GeminiError(f"Gemini returned non-JSON: {raw[:500]}") from e
    try:
        return schema(**data)
    except ValidationError as e:
        raise GeminiError(f"Gemini JSON failed schema validation: {e}\nRaw: {raw[:500]}") from e
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/unit/test_gemini_vision.py -v
```

Expected: 2 tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/core/gemini_client.py backend/tests/unit/test_gemini_vision.py
git commit -m "feat(gemini): add vision() helper for multi-image structured calls"
```

---

## Phase 2 — Implement the 19 agents

Each agent follows the same template:
- A `run()` function (sync) that takes `AgentRequest` and returns `dict` (the output)
- Calls `gemini_client.vision()` for perception agents (which need images), `gemini_client.structured()` for everything else
- Uses upstream agent outputs from `req.upstream` to compose its prompt

**Build order:** Tier 0 (3 agents) → Tier 1 (4) → Tier 2 (5) → Tier 3 (3) → Tier 4 (4). This matches dependency order so each task can use already-built upstream agents in its own integration test.

For brevity in this plan, Task 4 spells out the full TDD loop in detail. Tasks 5–22 follow the same five-step pattern (test, fail, implement, pass, commit). The full code blocks for each subsequent agent are inline with the task — no "similar to" pointers.

### Task 4: Agent — `scene_describer`

**Files:**
- Create: `backend/agents_v2/agents/__init__.py`
- Create: `backend/agents_v2/agents/scene_describer.py`
- Test: `backend/tests/unit/test_agents/__init__.py`
- Test: `backend/tests/unit/test_agents/test_scene_describer.py`

- [ ] **Step 1: Create package markers**

```bash
mkdir -p /Users/tomalmog/projects/world-build-agents/backend/agents_v2/agents
mkdir -p /Users/tomalmog/projects/world-build-agents/backend/tests/unit/test_agents
touch /Users/tomalmog/projects/world-build-agents/backend/agents_v2/agents/__init__.py
touch /Users/tomalmog/projects/world-build-agents/backend/tests/unit/test_agents/__init__.py
```

- [ ] **Step 2: Write the failing test**

Create `backend/tests/unit/test_agents/test_scene_describer.py`:

```python
from unittest.mock import patch, MagicMock
from agents_v2.agents import scene_describer
from agents_v2.messages import AgentRequest, SceneDescription


def _request(tmp_path):
    # Minimal jpeg file
    (tmp_path / "v0.jpg").write_bytes(b"\xff\xd8\xff\xe0")
    (tmp_path / "v1.jpg").write_bytes(b"\xff\xd8\xff\xe0")
    (tmp_path / "v2.jpg").write_bytes(b"\xff\xd8\xff\xe0")
    return AgentRequest(
        world_id="cabin", agent_id="scene_describer",
        prompt="rustic cabin",
        view_paths=[str(tmp_path / "v0.jpg"), str(tmp_path / "v1.jpg"), str(tmp_path / "v2.jpg")],
        upstream={},
    )


def test_returns_summary_and_tags(tmp_path):
    fake = SceneDescription(summary="A rustic log cabin", tags=["rustic", "warm"])
    with patch.object(scene_describer, "vision", return_value=fake) as m:
        out = scene_describer.run(_request(tmp_path))
    assert out["summary"].startswith("A rustic")
    assert "rustic" in out["tags"]
    # Verify vision() was called with 3 images
    args, kwargs = m.call_args
    assert len(kwargs["images"]) == 3
    # All inline images should be image/jpeg
    for mime, _ in kwargs["images"]:
        assert mime == "image/jpeg"
    assert kwargs["schema"] is SceneDescription
```

- [ ] **Step 3: Run test to verify it fails**

```bash
pytest tests/unit/test_agents/test_scene_describer.py -v
```

Expected: ImportError on `agents_v2.agents.scene_describer`.

- [ ] **Step 4: Implement the agent**

Create `backend/agents_v2/agents/scene_describer.py`:

```python
"""Tier 0 — Scene Describer.

Reads the 3 perception captures and returns a dense one-paragraph
description plus structured tags. Foundational for most downstream agents.
"""
from pathlib import Path
from agents_v2.messages import AgentRequest, SceneDescription
from core.gemini_client import vision


SYSTEM = (
    "You are a scene description specialist. Look at the 3 captured views of "
    "a 3D world and produce a single dense paragraph describing the scene, "
    "plus 3-8 short structured tags (e.g. 'indoor', 'rustic', 'warm-lit', "
    "'winter', 'wooden')."
)


def run(req: AgentRequest) -> dict:
    images = [("image/jpeg", Path(p).read_bytes()) for p in req.view_paths]
    prompt = (
        f"User-provided generation prompt: {req.prompt!r}\n\n"
        f"Describe this scene in one rich paragraph and emit tags."
    )
    out: SceneDescription = vision(prompt=prompt, images=images, schema=SceneDescription, system=SYSTEM)
    return out.model_dump()
```

- [ ] **Step 5: Run test to verify it passes**

```bash
pytest tests/unit/test_agents/test_scene_describer.py -v
```

Expected: 1 test passes.

- [ ] **Step 6: Commit**

```bash
git add backend/agents_v2/agents/__init__.py backend/agents_v2/agents/scene_describer.py backend/tests/unit/test_agents/
git commit -m "feat(agents_v2): scene_describer agent (Tier 0)"
```

---

### Task 5: Agent — `object_inventory`

**Files:**
- Create: `backend/agents_v2/agents/object_inventory.py`
- Test: `backend/tests/unit/test_agents/test_object_inventory.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/unit/test_agents/test_object_inventory.py`:

```python
from unittest.mock import patch
from pathlib import Path
from agents_v2.agents import object_inventory
from agents_v2.messages import AgentRequest, ObjectInventory


def _req(tmp_path):
    for i in range(3):
        (tmp_path / f"v{i}.jpg").write_bytes(b"\xff\xd8\xff\xe0")
    return AgentRequest(
        world_id="cabin", agent_id="object_inventory",
        prompt="cabin", view_paths=[str(tmp_path / f"v{i}.jpg") for i in range(3)],
        upstream={},
    )


def test_returns_object_list(tmp_path):
    fake = ObjectInventory(objects=[
        {"name": "leather couch", "position": "center-left"},
        {"name": "fireplace", "position": "back wall"},
    ])
    with patch.object(object_inventory, "vision", return_value=fake):
        out = object_inventory.run(_req(tmp_path))
    assert len(out["objects"]) == 2
    assert out["objects"][0]["name"] == "leather couch"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_agents/test_object_inventory.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement**

Create `backend/agents_v2/agents/object_inventory.py`:

```python
"""Tier 0 — Object Inventory.

Lists every visible object across the 3 captures with rough position labels.
Feeds prop_shopping, set_dressing, hazard_audit, carbon_score.
"""
from pathlib import Path
from agents_v2.messages import AgentRequest, ObjectInventory
from core.gemini_client import vision


SYSTEM = (
    "You catalog visible objects in a 3D scene. Look at the 3 captures and "
    "list every distinct object you can identify, with a short position "
    "phrase (e.g. 'center-left', 'far wall', 'on the table near window')."
)


def run(req: AgentRequest) -> dict:
    images = [("image/jpeg", Path(p).read_bytes()) for p in req.view_paths]
    prompt = (
        f"Generation prompt: {req.prompt!r}\n\n"
        f"Enumerate every visible object as {{name, position}}."
    )
    out: ObjectInventory = vision(prompt=prompt, images=images, schema=ObjectInventory, system=SYSTEM)
    return out.model_dump()
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/unit/test_agents/test_object_inventory.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/agents_v2/agents/object_inventory.py backend/tests/unit/test_agents/test_object_inventory.py
git commit -m "feat(agents_v2): object_inventory agent (Tier 0)"
```

---

### Task 6: Agent — `spatial_layout`

**Files:**
- Create: `backend/agents_v2/agents/spatial_layout.py`
- Test: `backend/tests/unit/test_agents/test_spatial_layout.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/unit/test_agents/test_spatial_layout.py`:

```python
from unittest.mock import patch
from agents_v2.agents import spatial_layout
from agents_v2.messages import AgentRequest, SpatialLayout


def _req(tmp_path):
    for i in range(3):
        (tmp_path / f"v{i}.jpg").write_bytes(b"\xff\xd8\xff\xe0")
    return AgentRequest(
        world_id="cabin", agent_id="spatial_layout",
        prompt="cabin", view_paths=[str(tmp_path / f"v{i}.jpg") for i in range(3)],
        upstream={},
    )


def test_returns_layout(tmp_path):
    fake = SpatialLayout(
        rooms=[{"name": "living room", "approx_sqft": 300}],
        entrances=["front door (south wall)"],
        sightlines=["from couch to fireplace"],
        total_sqft_estimate=300,
    )
    with patch.object(spatial_layout, "vision", return_value=fake):
        out = spatial_layout.run(_req(tmp_path))
    assert out["total_sqft_estimate"] == 300
    assert out["rooms"][0]["name"] == "living room"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_agents/test_spatial_layout.py -v
```

- [ ] **Step 3: Implement**

Create `backend/agents_v2/agents/spatial_layout.py`:

```python
"""Tier 0 — Spatial Layout.

Infers the rough floorplan from the 3 captures: room count, entrances,
sightlines, total square footage estimate. Feeds shot_list, real_estate,
hazard_audit, accessibility.
"""
from pathlib import Path
from agents_v2.messages import AgentRequest, SpatialLayout
from core.gemini_client import vision


SYSTEM = (
    "You are an architectural surveyor. From 3 views of a 3D space, infer "
    "the floor plan: list rooms with rough square footage, list visible "
    "entrances, list notable sightlines, and estimate total square footage."
)


def run(req: AgentRequest) -> dict:
    images = [("image/jpeg", Path(p).read_bytes()) for p in req.view_paths]
    prompt = (
        f"Generation prompt: {req.prompt!r}\n\n"
        f"Infer the floor plan as JSON with rooms, entrances, sightlines, total_sqft_estimate."
    )
    out: SpatialLayout = vision(prompt=prompt, images=images, schema=SpatialLayout, system=SYSTEM)
    return out.model_dump()
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/unit/test_agents/test_spatial_layout.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/agents_v2/agents/spatial_layout.py backend/tests/unit/test_agents/test_spatial_layout.py
git commit -m "feat(agents_v2): spatial_layout agent (Tier 0)"
```

---

### Task 7: Agent — `geolocator`

**Files:**
- Create: `backend/agents_v2/agents/geolocator.py`
- Test: `backend/tests/unit/test_agents/test_geolocator.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/unit/test_agents/test_geolocator.py`:

```python
from unittest.mock import patch
from agents_v2.agents import geolocator
from agents_v2.messages import AgentRequest, GeolocationResult


def test_uses_scene_summary_in_prompt():
    fake = GeolocationResult(candidates=[
        {"region": "Pacific Northwest, USA", "confidence": 0.7, "reasoning": "conifers"}
    ])
    with patch.object(geolocator, "structured", return_value=fake) as m:
        req = AgentRequest(
            world_id="cabin", agent_id="geolocator", prompt="cabin",
            view_paths=[],
            upstream={"scene_describer": {"summary": "Log cabin in dense conifer forest", "tags": ["pnw"]}},
        )
        out = geolocator.run(req)
    assert out["candidates"][0]["region"].startswith("Pacific Northwest")
    args, kwargs = m.call_args
    assert "Log cabin" in kwargs["prompt"] or "Log cabin" in args[0]
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_agents/test_geolocator.py -v
```

- [ ] **Step 3: Implement**

Create `backend/agents_v2/agents/geolocator.py`:

```python
"""Tier 1 — Geolocator.

Given the scene description, guesses the top-3 real-world regions the place
could be. Reads only text (cheap), not images. Feeds filming_scout,
real_estate.
"""
from agents_v2.messages import AgentRequest, GeolocationResult
from core.gemini_client import structured


SYSTEM = (
    "You are a geolocation analyst. Given a scene description, return the "
    "top-3 most plausible real-world regions where the scene could exist, "
    "each with a confidence (0-1) and short reasoning."
)


def run(req: AgentRequest) -> dict:
    scene = req.upstream.get("scene_describer", {})
    summary = scene.get("summary", "")
    tags = scene.get("tags", [])
    prompt = (
        f"Scene description: {summary}\n"
        f"Tags: {', '.join(tags)}\n"
        f"User generation prompt: {req.prompt!r}\n\n"
        "Return up to 3 candidate regions, ordered by confidence."
    )
    out: GeolocationResult = structured(prompt=prompt, schema=GeolocationResult, system=SYSTEM)
    return out.model_dump()
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/unit/test_agents/test_geolocator.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/agents_v2/agents/geolocator.py backend/tests/unit/test_agents/test_geolocator.py
git commit -m "feat(agents_v2): geolocator agent (Tier 1)"
```

---

### Task 8: Agent — `filming_scout`

**Files:**
- Create: `backend/agents_v2/agents/filming_scout.py`
- Test: `backend/tests/unit/test_agents/test_filming_scout.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/unit/test_agents/test_filming_scout.py`:

```python
from unittest.mock import patch
from agents_v2.agents import filming_scout
from agents_v2.messages import AgentRequest, FilmingScoutResult


def test_uses_geolocator_top_region():
    fake = FilmingScoutResult(locations=[
        {"name": "Mt. Hood Cabin Rentals", "address": "Welches, OR", "match_reason": "log cabin in PNW conifer forest"},
    ])
    with patch.object(filming_scout, "structured", return_value=fake) as m:
        req = AgentRequest(
            world_id="cabin", agent_id="filming_scout", prompt="cabin",
            view_paths=[],
            upstream={
                "geolocator": {"candidates": [{"region": "Pacific Northwest, USA", "confidence": 0.7}]},
            },
        )
        out = filming_scout.run(req)
    assert out["locations"][0]["name"]
    args, kwargs = m.call_args
    body = kwargs.get("prompt") or (args and args[0]) or ""
    assert "Pacific Northwest" in body
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_agents/test_filming_scout.py -v
```

- [ ] **Step 3: Implement**

Create `backend/agents_v2/agents/filming_scout.py`:

```python
"""Tier 1 — Filming Location Scout.

Given a geolocated region, suggests 3-5 real-world filming locations
matching the scene's vibe. Uses Google Search grounding for richer results
when available.
"""
from agents_v2.messages import AgentRequest, FilmingScoutResult
from core.gemini_client import structured


SYSTEM = (
    "You are a film location scout. Given a target region and scene "
    "description, suggest 3-5 specific real-world locations a director "
    "could book or visit, each with name, rough address, and why it matches."
)


def run(req: AgentRequest) -> dict:
    geo = req.upstream.get("geolocator", {})
    region = ""
    cands = geo.get("candidates", [])
    if cands:
        region = cands[0].get("region", "")
    scene = req.upstream.get("scene_describer", {})
    summary = scene.get("summary", "")

    prompt = (
        f"Target region: {region or 'unspecified'}\n"
        f"Scene: {summary or req.prompt}\n\n"
        "Return 3-5 plausible filming locations within this region."
    )
    out: FilmingScoutResult = structured(prompt=prompt, schema=FilmingScoutResult, system=SYSTEM)
    return out.model_dump()
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/unit/test_agents/test_filming_scout.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/agents_v2/agents/filming_scout.py backend/tests/unit/test_agents/test_filming_scout.py
git commit -m "feat(agents_v2): filming_scout agent (Tier 1)"
```

---

### Task 9: Agent — `era_estimator`

**Files:**
- Create: `backend/agents_v2/agents/era_estimator.py`
- Test: `backend/tests/unit/test_agents/test_era_estimator.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/unit/test_agents/test_era_estimator.py`:

```python
from unittest.mock import patch
from agents_v2.agents import era_estimator
from agents_v2.messages import AgentRequest, EraEstimate


def test_returns_period():
    fake = EraEstimate(period="1970s rustic Americana", confidence=0.6, reasoning="x")
    with patch.object(era_estimator, "structured", return_value=fake):
        out = era_estimator.run(AgentRequest(
            world_id="cabin", agent_id="era_estimator", prompt="cabin", view_paths=[],
            upstream={"scene_describer": {"summary": "log cabin", "tags": []}},
        ))
    assert out["period"] == "1970s rustic Americana"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_agents/test_era_estimator.py -v
```

- [ ] **Step 3: Implement**

Create `backend/agents_v2/agents/era_estimator.py`:

```python
"""Tier 1 — Era / Period Estimator."""
from agents_v2.messages import AgentRequest, EraEstimate
from core.gemini_client import structured


SYSTEM = "Estimate the historical period or design era a scene evokes (e.g. '1970s Scandinavian modern', 'Edwardian')."


def run(req: AgentRequest) -> dict:
    scene = req.upstream.get("scene_describer", {})
    prompt = f"Scene: {scene.get('summary','')}\nTags: {', '.join(scene.get('tags',[]))}"
    out: EraEstimate = structured(prompt=prompt, schema=EraEstimate, system=SYSTEM)
    return out.model_dump()
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/unit/test_agents/test_era_estimator.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/agents_v2/agents/era_estimator.py backend/tests/unit/test_agents/test_era_estimator.py
git commit -m "feat(agents_v2): era_estimator agent (Tier 1)"
```

---

### Task 10: Agent — `architectural_style`

**Files:**
- Create: `backend/agents_v2/agents/architectural_style.py`
- Test: `backend/tests/unit/test_agents/test_architectural_style.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/unit/test_agents/test_architectural_style.py`:

```python
from unittest.mock import patch
from agents_v2.agents import architectural_style
from agents_v2.messages import AgentRequest, ArchitecturalStyle


def test_returns_style():
    fake = ArchitecturalStyle(style="Craftsman log cabin", confidence=0.8, reasoning="exposed log walls")
    with patch.object(architectural_style, "structured", return_value=fake):
        out = architectural_style.run(AgentRequest(
            world_id="cabin", agent_id="architectural_style", prompt="cabin", view_paths=[],
            upstream={"scene_describer": {"summary": "log cabin", "tags": []}},
        ))
    assert out["style"] == "Craftsman log cabin"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_agents/test_architectural_style.py -v
```

- [ ] **Step 3: Implement**

Create `backend/agents_v2/agents/architectural_style.py`:

```python
"""Tier 1 — Architectural Style Classifier."""
from agents_v2.messages import AgentRequest, ArchitecturalStyle
from core.gemini_client import structured


SYSTEM = "Classify the architectural style of a scene (Craftsman, mid-century modern, brutalist, etc)."


def run(req: AgentRequest) -> dict:
    scene = req.upstream.get("scene_describer", {})
    prompt = f"Scene: {scene.get('summary','')}\nTags: {', '.join(scene.get('tags',[]))}"
    out: ArchitecturalStyle = structured(prompt=prompt, schema=ArchitecturalStyle, system=SYSTEM)
    return out.model_dump()
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/unit/test_agents/test_architectural_style.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/agents_v2/agents/architectural_style.py backend/tests/unit/test_agents/test_architectural_style.py
git commit -m "feat(agents_v2): architectural_style agent (Tier 1)"
```

---

### Task 11: Agent — `shot_list`

**Files:**
- Create: `backend/agents_v2/agents/shot_list.py`
- Test: `backend/tests/unit/test_agents/test_shot_list.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/unit/test_agents/test_shot_list.py`:

```python
from unittest.mock import patch
from agents_v2.agents import shot_list
from agents_v2.messages import AgentRequest, ShotList


def test_returns_shots():
    fake = ShotList(shots=[
        {"name": "low-angle dolly through doorway", "angle": "low", "lens_mm": 35,
         "time_of_day": "golden hour", "notes": ""},
    ])
    with patch.object(shot_list, "structured", return_value=fake):
        out = shot_list.run(AgentRequest(
            world_id="cabin", agent_id="shot_list", prompt="cabin", view_paths=[],
            upstream={
                "scene_describer": {"summary": "cabin", "tags": []},
                "spatial_layout": {"rooms": [], "entrances": [], "sightlines": [], "total_sqft_estimate": 300},
            },
        ))
    assert len(out["shots"]) == 1
    assert out["shots"][0]["lens_mm"] == 35
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_agents/test_shot_list.py -v
```

- [ ] **Step 3: Implement**

Create `backend/agents_v2/agents/shot_list.py`:

```python
"""Tier 2 — Cinematographer's Shot List."""
from agents_v2.messages import AgentRequest, ShotList
from core.gemini_client import structured


SYSTEM = (
    "You are a cinematographer. Propose 5-8 specific shots a director should "
    "capture in this space — name, angle, lens (mm), time of day, brief notes."
)


def run(req: AgentRequest) -> dict:
    scene = req.upstream.get("scene_describer", {})
    layout = req.upstream.get("spatial_layout", {})
    prompt = (
        f"Scene: {scene.get('summary','')}\n"
        f"Layout: {layout}\n\n"
        "Propose 5-8 distinct shots."
    )
    out: ShotList = structured(prompt=prompt, schema=ShotList, system=SYSTEM)
    return out.model_dump()
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/unit/test_agents/test_shot_list.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/agents_v2/agents/shot_list.py backend/tests/unit/test_agents/test_shot_list.py
git commit -m "feat(agents_v2): shot_list agent (Tier 2)"
```

---

### Task 12: Agent — `mood_palette`

**Files:**
- Create: `backend/agents_v2/agents/mood_palette.py`
- Test: `backend/tests/unit/test_agents/test_mood_palette.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/unit/test_agents/test_mood_palette.py`:

```python
from unittest.mock import patch
from agents_v2.agents import mood_palette
from agents_v2.messages import AgentRequest, MoodPalette


def test_returns_palette():
    fake = MoodPalette(palette=["#3a2a1a","#5e4630","#8a7256","#c2a98c","#e8dcc6"],
                       luts=["FilmConvert Tungsten"], film_stocks=["Kodak Portra 400"])
    with patch.object(mood_palette, "structured", return_value=fake):
        out = mood_palette.run(AgentRequest(
            world_id="cabin", agent_id="mood_palette", prompt="cabin", view_paths=[],
            upstream={"scene_describer": {"summary": "warm cabin", "tags": ["warm"]}},
        ))
    assert len(out["palette"]) == 5
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_agents/test_mood_palette.py -v
```

- [ ] **Step 3: Implement**

Create `backend/agents_v2/agents/mood_palette.py`:

```python
"""Tier 2 — Mood & Palette."""
from agents_v2.messages import AgentRequest, MoodPalette
from core.gemini_client import structured


SYSTEM = (
    "Pick a 5-color palette (hex strings starting with '#') that captures "
    "the mood, plus 2-3 LUTs and 2-3 film stocks that would suit this scene."
)


def run(req: AgentRequest) -> dict:
    scene = req.upstream.get("scene_describer", {})
    prompt = f"Scene: {scene.get('summary','')}\nTags: {', '.join(scene.get('tags',[]))}"
    out: MoodPalette = structured(prompt=prompt, schema=MoodPalette, system=SYSTEM)
    return out.model_dump()
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/unit/test_agents/test_mood_palette.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/agents_v2/agents/mood_palette.py backend/tests/unit/test_agents/test_mood_palette.py
git commit -m "feat(agents_v2): mood_palette agent (Tier 2)"
```

---

### Task 13: Agent — `soundscape`

**Files:**
- Create: `backend/agents_v2/agents/soundscape.py`
- Test: `backend/tests/unit/test_agents/test_soundscape.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/unit/test_agents/test_soundscape.py`:

```python
from unittest.mock import patch
from agents_v2.agents import soundscape
from agents_v2.messages import AgentRequest, Soundscape


def test_returns_audio_design():
    fake = Soundscape(ambient=["wind through pines"], foley=["floorboard creaks", "fire crackle"])
    with patch.object(soundscape, "structured", return_value=fake):
        out = soundscape.run(AgentRequest(
            world_id="cabin", agent_id="soundscape", prompt="cabin", view_paths=[],
            upstream={"scene_describer": {"summary": "cabin in forest", "tags": []}},
        ))
    assert "wind through pines" in out["ambient"]
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_agents/test_soundscape.py -v
```

- [ ] **Step 3: Implement**

Create `backend/agents_v2/agents/soundscape.py`:

```python
"""Tier 2 — Soundscape Designer."""
from agents_v2.messages import AgentRequest, Soundscape
from core.gemini_client import structured


SYSTEM = (
    "Design the audio for this scene: 3-5 ambient layers (continuous bed) "
    "plus 5-10 specific Foley sounds."
)


def run(req: AgentRequest) -> dict:
    scene = req.upstream.get("scene_describer", {})
    prompt = f"Scene: {scene.get('summary','')}"
    out: Soundscape = structured(prompt=prompt, schema=Soundscape, system=SYSTEM)
    return out.model_dump()
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/unit/test_agents/test_soundscape.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/agents_v2/agents/soundscape.py backend/tests/unit/test_agents/test_soundscape.py
git commit -m "feat(agents_v2): soundscape agent (Tier 2)"
```

---

### Task 14: Agent — `prop_shopping`

**Files:**
- Create: `backend/agents_v2/agents/prop_shopping.py`
- Test: `backend/tests/unit/test_agents/test_prop_shopping.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/unit/test_agents/test_prop_shopping.py`:

```python
from unittest.mock import patch
from agents_v2.agents import prop_shopping
from agents_v2.messages import AgentRequest, PropShopping


def test_returns_items_using_inventory():
    fake = PropShopping(items=[
        {"name": "leather couch", "vendor": "Wayfair", "url": "https://wayfair.com/x", "price_estimate_usd": 1200},
    ])
    with patch.object(prop_shopping, "structured", return_value=fake) as m:
        out = prop_shopping.run(AgentRequest(
            world_id="cabin", agent_id="prop_shopping", prompt="cabin", view_paths=[],
            upstream={"object_inventory": {"objects": [{"name": "leather couch", "position": "center"}]}},
        ))
    assert out["items"][0]["price_estimate_usd"] == 1200
    args, kwargs = m.call_args
    body = kwargs.get("prompt") or (args and args[0]) or ""
    assert "leather couch" in body
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_agents/test_prop_shopping.py -v
```

- [ ] **Step 3: Implement**

Create `backend/agents_v2/agents/prop_shopping.py`:

```python
"""Tier 2 — Prop Shopping List."""
from agents_v2.messages import AgentRequest, PropShopping
from core.gemini_client import structured


SYSTEM = (
    "Given an object inventory, suggest plausible store products that would "
    "match each item. Vendors: Amazon, Wayfair, IKEA, West Elm, Target. "
    "URLs may be search URLs (e.g. https://www.wayfair.com/keyword/sb0/leather-couch.html). "
    "Estimate price in USD."
)


def run(req: AgentRequest) -> dict:
    inventory = req.upstream.get("object_inventory", {})
    objects = inventory.get("objects", [])
    items_text = "\n".join(f"- {o.get('name')} ({o.get('position','')})" for o in objects)
    prompt = f"Objects to shop for:\n{items_text}\n\nReturn one product per object."
    out: PropShopping = structured(prompt=prompt, schema=PropShopping, system=SYSTEM)
    return out.model_dump()
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/unit/test_agents/test_prop_shopping.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/agents_v2/agents/prop_shopping.py backend/tests/unit/test_agents/test_prop_shopping.py
git commit -m "feat(agents_v2): prop_shopping agent (Tier 2)"
```

---

### Task 15: Agent — `set_dressing`

**Files:**
- Create: `backend/agents_v2/agents/set_dressing.py`
- Test: `backend/tests/unit/test_agents/test_set_dressing.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/unit/test_agents/test_set_dressing.py`:

```python
from unittest.mock import patch
from agents_v2.agents import set_dressing
from agents_v2.messages import AgentRequest, SetDressing


def test_returns_suggestions():
    fake = SetDressing(suggestions=[
        {"theme": "more lived-in", "additions": ["scattered books", "knit throw"]},
    ])
    with patch.object(set_dressing, "structured", return_value=fake):
        out = set_dressing.run(AgentRequest(
            world_id="cabin", agent_id="set_dressing", prompt="cabin", view_paths=[],
            upstream={
                "scene_describer": {"summary": "minimal cabin", "tags": []},
                "object_inventory": {"objects": [{"name": "couch", "position": ""}]},
            },
        ))
    assert out["suggestions"][0]["theme"]
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_agents/test_set_dressing.py -v
```

- [ ] **Step 3: Implement**

Create `backend/agents_v2/agents/set_dressing.py`:

```python
"""Tier 2 — Set Dressing Improvements."""
from agents_v2.messages import AgentRequest, SetDressing
from core.gemini_client import structured


SYSTEM = (
    "Propose 3-5 'to make this scene more X, add Y' suggestions. Each "
    "suggestion has a theme (e.g. 'more lived-in', 'more dramatic') and "
    "specific additions."
)


def run(req: AgentRequest) -> dict:
    scene = req.upstream.get("scene_describer", {})
    inv = req.upstream.get("object_inventory", {})
    prompt = (
        f"Scene: {scene.get('summary','')}\n"
        f"Existing objects: {[o.get('name') for o in inv.get('objects',[])]}\n\n"
        "Propose 3-5 themed set dressing additions."
    )
    out: SetDressing = structured(prompt=prompt, schema=SetDressing, system=SYSTEM)
    return out.model_dump()
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/unit/test_agents/test_set_dressing.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/agents_v2/agents/set_dressing.py backend/tests/unit/test_agents/test_set_dressing.py
git commit -m "feat(agents_v2): set_dressing agent (Tier 2)"
```

---

### Task 16: Agent — `story_seed`

**Files:**
- Create: `backend/agents_v2/agents/story_seed.py`
- Test: `backend/tests/unit/test_agents/test_story_seed.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/unit/test_agents/test_story_seed.py`:

```python
from unittest.mock import patch
from agents_v2.agents import story_seed
from agents_v2.messages import AgentRequest, StorySeed


def test_returns_premises():
    fake = StorySeed(premises=[
        {"title": "Snowed In", "logline": "Estranged siblings reunite for a funeral and get snowed into the family cabin.", "genre": "drama"}
    ])
    with patch.object(story_seed, "structured", return_value=fake):
        out = story_seed.run(AgentRequest(
            world_id="cabin", agent_id="story_seed", prompt="cabin", view_paths=[],
            upstream={
                "scene_describer": {"summary": "cabin", "tags": []},
                "era_estimator": {"period": "modern", "confidence": 0.5, "reasoning": ""},
            },
        ))
    assert len(out["premises"]) == 1
    assert "Snowed In" == out["premises"][0]["title"]
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_agents/test_story_seed.py -v
```

- [ ] **Step 3: Implement**

Create `backend/agents_v2/agents/story_seed.py`:

```python
"""Tier 3 — Story Seeds."""
from agents_v2.messages import AgentRequest, StorySeed
from core.gemini_client import structured


SYSTEM = (
    "You write loglines. Generate 3 short film/novel premises set in this "
    "scene. Each: title, one-sentence logline, genre."
)


def run(req: AgentRequest) -> dict:
    scene = req.upstream.get("scene_describer", {})
    era = req.upstream.get("era_estimator", {})
    prompt = (
        f"Scene: {scene.get('summary','')}\n"
        f"Era: {era.get('period','')}\n\n"
        "Generate 3 distinct premises."
    )
    out: StorySeed = structured(prompt=prompt, schema=StorySeed, system=SYSTEM)
    return out.model_dump()
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/unit/test_agents/test_story_seed.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/agents_v2/agents/story_seed.py backend/tests/unit/test_agents/test_story_seed.py
git commit -m "feat(agents_v2): story_seed agent (Tier 3)"
```

---

### Task 17: Agent — `character_suggester`

**Files:**
- Create: `backend/agents_v2/agents/character_suggester.py`
- Test: `backend/tests/unit/test_agents/test_character_suggester.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/unit/test_agents/test_character_suggester.py`:

```python
from unittest.mock import patch
from agents_v2.agents import character_suggester
from agents_v2.messages import AgentRequest, Characters


def test_returns_characters():
    fake = Characters(characters=[
        {"name": "Marta Lindquist", "role": "retired park ranger", "bio": "Solo dweller, knows every trail."}
    ])
    with patch.object(character_suggester, "structured", return_value=fake):
        out = character_suggester.run(AgentRequest(
            world_id="cabin", agent_id="character_suggester", prompt="cabin", view_paths=[],
            upstream={"scene_describer": {"summary": "cabin", "tags": []}},
        ))
    assert out["characters"][0]["name"] == "Marta Lindquist"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_agents/test_character_suggester.py -v
```

- [ ] **Step 3: Implement**

Create `backend/agents_v2/agents/character_suggester.py`:

```python
"""Tier 3 — Character Suggester."""
from agents_v2.messages import AgentRequest, Characters
from core.gemini_client import structured


SYSTEM = "Propose 3-5 plausible characters who might live or work in this scene. Each: name, role, 1-sentence bio."


def run(req: AgentRequest) -> dict:
    scene = req.upstream.get("scene_describer", {})
    prompt = f"Scene: {scene.get('summary','')}"
    out: Characters = structured(prompt=prompt, schema=Characters, system=SYSTEM)
    return out.model_dump()
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/unit/test_agents/test_character_suggester.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/agents_v2/agents/character_suggester.py backend/tests/unit/test_agents/test_character_suggester.py
git commit -m "feat(agents_v2): character_suggester agent (Tier 3)"
```

---

### Task 18: Agent — `npc_dialogue`

**Files:**
- Create: `backend/agents_v2/agents/npc_dialogue.py`
- Test: `backend/tests/unit/test_agents/test_npc_dialogue.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/unit/test_agents/test_npc_dialogue.py`:

```python
from unittest.mock import patch
from agents_v2.agents import npc_dialogue
from agents_v2.messages import AgentRequest, NPCDialogue


def test_returns_lines():
    fake = NPCDialogue(lines=[
        {"character": "Marta", "line": "Storm's coming. You should head down by sundown."}
    ])
    with patch.object(npc_dialogue, "structured", return_value=fake):
        out = npc_dialogue.run(AgentRequest(
            world_id="cabin", agent_id="npc_dialogue", prompt="cabin", view_paths=[],
            upstream={"character_suggester": {"characters": [{"name": "Marta", "role": "ranger", "bio": ""}]}},
        ))
    assert out["lines"][0]["character"] == "Marta"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_agents/test_npc_dialogue.py -v
```

- [ ] **Step 3: Implement**

Create `backend/agents_v2/agents/npc_dialogue.py`:

```python
"""Tier 3 — NPC Dialogue Pack."""
from agents_v2.messages import AgentRequest, NPCDialogue
from core.gemini_client import structured


SYSTEM = (
    "Given a list of characters, write 6-10 short dialogue lines a game NPC "
    "in this space might say. Each line tagged with the character's name."
)


def run(req: AgentRequest) -> dict:
    chars = req.upstream.get("character_suggester", {}).get("characters", [])
    char_text = "\n".join(f"- {c.get('name')}: {c.get('role')}" for c in chars)
    prompt = f"Characters:\n{char_text}\n\nWrite 6-10 dialogue lines."
    out: NPCDialogue = structured(prompt=prompt, schema=NPCDialogue, system=SYSTEM)
    return out.model_dump()
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/unit/test_agents/test_npc_dialogue.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/agents_v2/agents/npc_dialogue.py backend/tests/unit/test_agents/test_npc_dialogue.py
git commit -m "feat(agents_v2): npc_dialogue agent (Tier 3)"
```

---

### Task 19: Agent — `real_estate`

**Files:**
- Create: `backend/agents_v2/agents/real_estate.py`
- Test: `backend/tests/unit/test_agents/test_real_estate.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/unit/test_agents/test_real_estate.py`:

```python
from unittest.mock import patch
from agents_v2.agents import real_estate
from agents_v2.messages import AgentRequest, RealEstate


def test_returns_rent():
    fake = RealEstate(estimated_monthly_rent_usd=2200, market="Bend, OR", reasoning="cabin rentals 1500-3000")
    with patch.object(real_estate, "structured", return_value=fake):
        out = real_estate.run(AgentRequest(
            world_id="cabin", agent_id="real_estate", prompt="cabin", view_paths=[],
            upstream={
                "geolocator": {"candidates": [{"region": "Bend, OR", "confidence": 0.7}]},
                "spatial_layout": {"rooms": [], "entrances": [], "sightlines": [], "total_sqft_estimate": 1100},
            },
        ))
    assert out["estimated_monthly_rent_usd"] == 2200
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_agents/test_real_estate.py -v
```

- [ ] **Step 3: Implement**

Create `backend/agents_v2/agents/real_estate.py`:

```python
"""Tier 4 — Real Estate Appraisal."""
from agents_v2.messages import AgentRequest, RealEstate
from core.gemini_client import structured


SYSTEM = (
    "Given a likely market region and approximate square footage, estimate a "
    "plausible monthly rent in USD for an equivalent real-world property."
)


def run(req: AgentRequest) -> dict:
    geo = req.upstream.get("geolocator", {})
    cands = geo.get("candidates", [])
    region = cands[0].get("region", "unknown") if cands else "unknown"
    layout = req.upstream.get("spatial_layout", {})
    sqft = layout.get("total_sqft_estimate", 0)
    prompt = f"Region: {region}\nApprox sqft: {sqft}"
    out: RealEstate = structured(prompt=prompt, schema=RealEstate, system=SYSTEM)
    return out.model_dump()
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/unit/test_agents/test_real_estate.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/agents_v2/agents/real_estate.py backend/tests/unit/test_agents/test_real_estate.py
git commit -m "feat(agents_v2): real_estate agent (Tier 4)"
```

---

### Task 20: Agent — `hazard_audit`

**Files:**
- Create: `backend/agents_v2/agents/hazard_audit.py`
- Test: `backend/tests/unit/test_agents/test_hazard_audit.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/unit/test_agents/test_hazard_audit.py`:

```python
from unittest.mock import patch
from agents_v2.agents import hazard_audit
from agents_v2.messages import AgentRequest, HazardAudit


def test_returns_hazards():
    fake = HazardAudit(hazards=[
        {"type": "fire", "severity": "high", "description": "no smoke detector visible"}
    ])
    with patch.object(hazard_audit, "structured", return_value=fake):
        out = hazard_audit.run(AgentRequest(
            world_id="cabin", agent_id="hazard_audit", prompt="cabin", view_paths=[],
            upstream={
                "object_inventory": {"objects": []},
                "spatial_layout": {"rooms": [], "entrances": [], "sightlines": [], "total_sqft_estimate": 0},
            },
        ))
    assert out["hazards"][0]["severity"] == "high"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_agents/test_hazard_audit.py -v
```

- [ ] **Step 3: Implement**

Create `backend/agents_v2/agents/hazard_audit.py`:

```python
"""Tier 4 — Hazard Audit."""
from agents_v2.messages import AgentRequest, HazardAudit
from core.gemini_client import structured


SYSTEM = (
    "List 3-7 fire / trip / structural / code-related hazards a building "
    "inspector would flag in this space. Each: type, severity (low/medium/high), "
    "description."
)


def run(req: AgentRequest) -> dict:
    inv = req.upstream.get("object_inventory", {})
    layout = req.upstream.get("spatial_layout", {})
    prompt = (
        f"Objects: {[o.get('name') for o in inv.get('objects',[])]}\n"
        f"Layout: rooms={layout.get('rooms',[])} entrances={layout.get('entrances',[])}"
    )
    out: HazardAudit = structured(prompt=prompt, schema=HazardAudit, system=SYSTEM)
    return out.model_dump()
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/unit/test_agents/test_hazard_audit.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/agents_v2/agents/hazard_audit.py backend/tests/unit/test_agents/test_hazard_audit.py
git commit -m "feat(agents_v2): hazard_audit agent (Tier 4)"
```

---

### Task 21: Agent — `accessibility`

**Files:**
- Create: `backend/agents_v2/agents/accessibility.py`
- Test: `backend/tests/unit/test_agents/test_accessibility.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/unit/test_agents/test_accessibility.py`:

```python
from unittest.mock import patch
from agents_v2.agents import accessibility
from agents_v2.messages import AgentRequest, Accessibility


def test_returns_audit():
    fake = Accessibility(
        issues=[{"category": "mobility", "description": "narrow doorways"}],
        suggestions=["widen primary entry"],
    )
    with patch.object(accessibility, "structured", return_value=fake):
        out = accessibility.run(AgentRequest(
            world_id="cabin", agent_id="accessibility", prompt="cabin", view_paths=[],
            upstream={"spatial_layout": {"rooms": [], "entrances": [], "sightlines": [], "total_sqft_estimate": 0}},
        ))
    assert out["issues"][0]["category"] == "mobility"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_agents/test_accessibility.py -v
```

- [ ] **Step 3: Implement**

Create `backend/agents_v2/agents/accessibility.py`:

```python
"""Tier 4 — Accessibility Audit."""
from agents_v2.messages import AgentRequest, Accessibility
from core.gemini_client import structured


SYSTEM = (
    "Audit accessibility (mobility, vision, hearing, cognitive). List 3-5 "
    "issues with category + description, plus 3-5 actionable suggestions."
)


def run(req: AgentRequest) -> dict:
    layout = req.upstream.get("spatial_layout", {})
    prompt = f"Layout: {layout}"
    out: Accessibility = structured(prompt=prompt, schema=Accessibility, system=SYSTEM)
    return out.model_dump()
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/unit/test_agents/test_accessibility.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/agents_v2/agents/accessibility.py backend/tests/unit/test_agents/test_accessibility.py
git commit -m "feat(agents_v2): accessibility agent (Tier 4)"
```

---

### Task 22: Agent — `carbon_score`

**Files:**
- Create: `backend/agents_v2/agents/carbon_score.py`
- Test: `backend/tests/unit/test_agents/test_carbon_score.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/unit/test_agents/test_carbon_score.py`:

```python
from unittest.mock import patch
from agents_v2.agents import carbon_score
from agents_v2.messages import AgentRequest, CarbonScore


def test_returns_score():
    fake = CarbonScore(
        embodied_carbon_kg_co2e=12000,
        breakdown=[{"material": "logs", "kg_co2e": 4000}],
        reasoning="rough",
    )
    with patch.object(carbon_score, "structured", return_value=fake):
        out = carbon_score.run(AgentRequest(
            world_id="cabin", agent_id="carbon_score", prompt="cabin", view_paths=[],
            upstream={
                "object_inventory": {"objects": []},
                "scene_describer": {"summary": "log cabin", "tags": []},
            },
        ))
    assert out["embodied_carbon_kg_co2e"] == 12000
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_agents/test_carbon_score.py -v
```

- [ ] **Step 3: Implement**

Create `backend/agents_v2/agents/carbon_score.py`:

```python
"""Tier 4 — Carbon / Sustainability Score."""
from agents_v2.messages import AgentRequest, CarbonScore
from core.gemini_client import structured


SYSTEM = (
    "Estimate the embodied carbon (kg CO2e) of building this scene from its "
    "materials and contents. Return a total + breakdown by material + brief "
    "reasoning. Be conservative; this is a rough estimate."
)


def run(req: AgentRequest) -> dict:
    scene = req.upstream.get("scene_describer", {})
    inv = req.upstream.get("object_inventory", {})
    prompt = (
        f"Scene: {scene.get('summary','')}\n"
        f"Objects: {[o.get('name') for o in inv.get('objects',[])]}"
    )
    out: CarbonScore = structured(prompt=prompt, schema=CarbonScore, system=SYSTEM)
    return out.model_dump()
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/unit/test_agents/test_carbon_score.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/agents_v2/agents/carbon_score.py backend/tests/unit/test_agents/test_carbon_score.py
git commit -m "feat(agents_v2): carbon_score agent (Tier 4)"
```

---

## Phase 3 — Orchestrator + uAgent runner

### Task 23: DAG orchestrator

**Files:**
- Create: `backend/agents_v2/registry.py`
- Create: `backend/agents_v2/orchestrator.py`
- Test: `backend/tests/unit/test_agent_orchestrator.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/unit/test_agent_orchestrator.py`:

```python
import asyncio
from unittest.mock import patch
import pytest
from agents_v2.orchestrator import run_dag
from agents_v2.messages import PerceptionInput


def _stub_run(agent_id):
    """Returns a stub run() that produces a deterministic dict including its deps."""
    def _run(req):
        return {"agent": agent_id, "got_upstream": list(req.upstream.keys())}
    return _run


@pytest.mark.asyncio
async def test_dag_runs_all_19_agents_in_dependency_order():
    """Every agent runs exactly once. Dependent agents see their upstreams."""
    from agents_v2.manifest import AGENTS
    stubs = {a.id: _stub_run(a.id) for a in AGENTS}

    with patch("agents_v2.registry.AGENT_RUNS", stubs):
        result = await run_dag(PerceptionInput(
            world_id="t1", prompt="test", view_paths=[],
        ))

    assert len(result["agents"]) == 19
    # Every agent reports done
    for aid, entry in result["agents"].items():
        assert entry["status"] == "done"

    # Dependent agents got upstream outputs
    geo = result["agents"]["geolocator"]
    assert "scene_describer" in geo["output"]["got_upstream"]

    real = result["agents"]["real_estate"]
    assert "geolocator" in real["output"]["got_upstream"]
    assert "spatial_layout" in real["output"]["got_upstream"]


@pytest.mark.asyncio
async def test_failed_upstream_marks_downstream_skipped():
    from agents_v2.manifest import AGENTS

    def _failing_scene_describer(req):
        raise RuntimeError("boom")

    stubs = {a.id: _stub_run(a.id) for a in AGENTS}
    stubs["scene_describer"] = _failing_scene_describer

    with patch("agents_v2.registry.AGENT_RUNS", stubs):
        result = await run_dag(PerceptionInput(world_id="t2", prompt="x", view_paths=[]))

    assert result["agents"]["scene_describer"]["status"] == "error"
    # geolocator depends on scene_describer
    assert result["agents"]["geolocator"]["status"] == "skipped"
    assert result["agents"]["geolocator"]["reason"] == "upstream_failed"


@pytest.mark.asyncio
async def test_independent_agents_unaffected_by_other_failures():
    from agents_v2.manifest import AGENTS

    def _failing_object_inventory(req):
        raise RuntimeError("boom")

    stubs = {a.id: _stub_run(a.id) for a in AGENTS}
    stubs["object_inventory"] = _failing_object_inventory

    with patch("agents_v2.registry.AGENT_RUNS", stubs):
        result = await run_dag(PerceptionInput(world_id="t3", prompt="x", view_paths=[]))

    # scene_describer / spatial_layout / geolocator etc. should still run
    assert result["agents"]["scene_describer"]["status"] == "done"
    assert result["agents"]["spatial_layout"]["status"] == "done"
    assert result["agents"]["geolocator"]["status"] == "done"
    # prop_shopping depends on object_inventory
    assert result["agents"]["prop_shopping"]["status"] == "skipped"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_agent_orchestrator.py -v
```

Expected: ImportError on `agents_v2.orchestrator`.

- [ ] **Step 3: Implement registry**

Create `backend/agents_v2/registry.py`:

```python
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
```

- [ ] **Step 4: Implement orchestrator**

Create `backend/agents_v2/orchestrator.py`:

```python
"""DAG executor for the 19-agent swarm.

Walks the dependency graph in topological order. Each agent runs as soon as
all its upstream dependencies are done. Independent agents run in parallel
via asyncio.to_thread.

If an upstream agent errors, all downstream agents are marked 'skipped' with
reason='upstream_failed'. Independent agents continue.
"""
import asyncio
import time
from datetime import datetime, timezone
from agents_v2.manifest import AGENTS, by_id
from agents_v2.messages import PerceptionInput, AgentRequest
from agents_v2 import registry


async def _run_one(agent_id: str, req: AgentRequest) -> dict:
    fn = registry.AGENT_RUNS[agent_id]
    started = time.monotonic()
    try:
        output = await asyncio.to_thread(fn, req)
        duration_ms = int((time.monotonic() - started) * 1000)
        return {"status": "done", "duration_ms": duration_ms, "output": output}
    except Exception as e:
        duration_ms = int((time.monotonic() - started) * 1000)
        return {"status": "error", "duration_ms": duration_ms, "error_message": str(e)}


async def run_dag(perception: PerceptionInput) -> dict:
    """Run all 19 agents respecting dependency order. Returns the final JSON dict."""
    defs = list(AGENTS)
    by = by_id()
    results: dict[str, dict] = {}

    # Track which agent ids still need to be scheduled
    pending = {a.id for a in defs}
    in_flight: dict[str, asyncio.Task] = {}

    def _ready(agent_id: str) -> bool:
        deps = by[agent_id].dependencies
        return all(d in results for d in deps)

    def _any_dep_failed(agent_id: str) -> bool:
        return any(results.get(d, {}).get("status") in ("error", "skipped")
                   for d in by[agent_id].dependencies)

    def _start(agent_id: str):
        if _any_dep_failed(agent_id):
            results[agent_id] = {
                "status": "skipped",
                "duration_ms": 0,
                "reason": "upstream_failed",
            }
            return
        upstream = {dep: results[dep]["output"] for dep in by[agent_id].dependencies}
        req = AgentRequest(
            world_id=perception.world_id,
            agent_id=agent_id,
            prompt=perception.prompt,
            view_paths=perception.view_paths,
            upstream=upstream,
        )
        in_flight[agent_id] = asyncio.create_task(_run_one(agent_id, req))

    while pending or in_flight:
        # Schedule everything currently ready
        ready_now = [aid for aid in list(pending) if _ready(aid)]
        for aid in ready_now:
            pending.discard(aid)
            _start(aid)

        if not in_flight:
            # No tasks in flight and none ready — must be cycle or starvation
            if pending:
                raise RuntimeError(f"DAG starved with pending: {pending}")
            break

        done, _ = await asyncio.wait(in_flight.values(), return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            # Find which agent_id this task was for
            aid = next(k for k, v in in_flight.items() if v is task)
            results[aid] = task.result()
            del in_flight[aid]

    # Attach display type from manifest
    for aid, entry in results.items():
        entry.setdefault("display", by[aid].display)

    return {
        "world_id": perception.world_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "schema_version": 1,
        "agents": results,
    }
```

- [ ] **Step 5: Run test to verify it passes**

```bash
pytest tests/unit/test_agent_orchestrator.py -v
```

Expected: 3 tests pass.

- [ ] **Step 6: Commit**

```bash
git add backend/agents_v2/registry.py backend/agents_v2/orchestrator.py backend/tests/unit/test_agent_orchestrator.py
git commit -m "feat(agents_v2): DAG orchestrator with skip-on-upstream-failure"
```

---

### Task 24: uAgent runner (replaces old `uagent_runner.py`)

**Files:**
- Create: `backend/agents_v2/runner.py`
- Test: `backend/tests/unit/test_agent_runner.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/unit/test_agent_runner.py`:

```python
"""We don't actually start uagents in tests (would bind ports). We test the
factory that builds agent instances from the manifest."""
from unittest.mock import patch
from agents_v2 import runner
from agents_v2.manifest import AGENTS


def test_builds_one_agent_per_manifest_entry():
    """build_agents returns one Agent object per manifest row, on the right port."""
    with patch.object(runner, "Agent") as MockAgent, \
         patch.object(runner, "Protocol") as MockProto:
        agents = runner.build_agents()
    assert len(agents) == 19
    # ports passed correctly
    seen_ports = sorted([call.kwargs["port"] for call in MockAgent.call_args_list])
    assert seen_ports == sorted([a.port for a in AGENTS])


def test_agent_names_are_namespaced():
    """We use 'conjure_<id>' so old + new agents don't collide on Agentverse."""
    with patch.object(runner, "Agent") as MockAgent, \
         patch.object(runner, "Protocol"):
        runner.build_agents()
    seen_names = {call.kwargs["name"] for call in MockAgent.call_args_list}
    assert "conjure_scene_describer" in seen_names
    assert "conjure_carbon_score" in seen_names
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_agent_runner.py -v
```

- [ ] **Step 3: Implement runner**

Create `backend/agents_v2/runner.py`:

```python
"""Boot all 19 uagents.Agent processes on local ports.

These agents are real members of the Agentverse network when AGENTVERSE_API_KEY
is set: they register, accept Chat Protocol messages, and respond.

The orchestrator does NOT route work through these uagent instances — it
calls run() functions directly via the registry. The uagents are the
'on-network presence' that satisfies the Fetch.ai track requirement; the
orchestrator's in-process DAG is what produces results.

This separation is intentional: it keeps the in-process pipeline fast and
debuggable while still giving us 19 agents listed on Agentverse.
"""
import asyncio
import os
import threading
from dotenv import load_dotenv
from uagents import Agent, Context, Protocol, Model

from agents_v2.manifest import AGENTS

load_dotenv()
AV_KEY = os.environ.get("AGENTVERSE_API_KEY")


class ChatMessage(Model):
    content: str


def _make_agent(agent_id: str, label: str, port: int) -> Agent:
    name = f"conjure_{agent_id}"
    seed = f"conjure-{agent_id}-seed-2026"
    agent = Agent(
        name=name,
        seed=seed,
        port=port,
        endpoint=[f"http://127.0.0.1:{port}/submit"],
        mailbox=AV_KEY or "",
    )
    proto = Protocol(name="chat", version="0.1")

    @proto.on_message(model=ChatMessage)
    async def handle(ctx: Context, sender: str, msg: ChatMessage):
        await ctx.send(sender, ChatMessage(content=f"[{label}] received: {msg.content[:80]}"))

    agent.include(proto, publish_manifest=True)
    return agent


def build_agents() -> list[Agent]:
    return [_make_agent(a.id, a.label, a.port) for a in AGENTS]


def start_all_in_background() -> None:
    """Daemon thread runs all 19 uagents in their own asyncio loop."""
    def runner_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        agents = build_agents()
        for a in agents:
            loop.create_task(a.run_async())
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass

    t = threading.Thread(target=runner_thread, name="conjure-uagent-runner", daemon=True)
    t.start()
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/unit/test_agent_runner.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/agents_v2/runner.py backend/tests/unit/test_agent_runner.py
git commit -m "feat(agents_v2): uagent runner — 19 Agentverse-registered agents"
```

---

## Phase 4 — Bridge endpoints

### Task 25: `POST /api/perception-frames`

**Files:**
- Modify: `backend/bridge/main.py`
- Test: `backend/tests/unit/test_perception_endpoint.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/unit/test_perception_endpoint.py`:

```python
import base64
from pathlib import Path
from fastapi.testclient import TestClient
from bridge.main import app


def _data_url(payload_bytes: bytes) -> str:
    b64 = base64.b64encode(payload_bytes).decode()
    return f"data:image/jpeg;base64,{b64}"


def test_saves_three_frames_to_disk(tmp_path, monkeypatch):
    monkeypatch.setattr("bridge.main.WORLDS_DIR", tmp_path)
    client = TestClient(app)
    r = client.post("/api/perception-frames", json={
        "world_id": "cabin_test",
        "view_0": _data_url(b"\xff\xd8\xff\xe0_view0"),
        "view_120": _data_url(b"\xff\xd8\xff\xe0_view120"),
        "view_240": _data_url(b"\xff\xd8\xff\xe0_view240"),
    })
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    views_dir = tmp_path / "cabin_test" / "views"
    assert (views_dir / "view_0.jpg").exists()
    assert (views_dir / "view_120.jpg").exists()
    assert (views_dir / "view_240.jpg").exists()


def test_rejects_bad_id(monkeypatch, tmp_path):
    monkeypatch.setattr("bridge.main.WORLDS_DIR", tmp_path)
    client = TestClient(app)
    r = client.post("/api/perception-frames", json={
        "world_id": "../etc",
        "view_0": _data_url(b"x"),
        "view_120": _data_url(b"x"),
        "view_240": _data_url(b"x"),
    })
    assert r.status_code == 400


def test_rejects_non_data_url(monkeypatch, tmp_path):
    monkeypatch.setattr("bridge.main.WORLDS_DIR", tmp_path)
    client = TestClient(app)
    r = client.post("/api/perception-frames", json={
        "world_id": "cabin",
        "view_0": "https://example.com/x.jpg",
        "view_120": _data_url(b"x"),
        "view_240": _data_url(b"x"),
    })
    assert r.status_code == 400
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_perception_endpoint.py -v
```

Expected: 404 on `/api/perception-frames`.

- [ ] **Step 3: Add endpoint to `bridge/main.py`**

Append to `backend/bridge/main.py`:

```python
import base64
import re

PERCEPTION_ID_RE = re.compile(r"^[a-z0-9_-]+$", re.IGNORECASE)


class PerceptionFramesReq(BaseModel):
    world_id: str
    view_0: str
    view_120: str
    view_240: str


def _decode_data_url(data_url: str) -> bytes:
    if not data_url.startswith("data:image/"):
        raise HTTPException(status_code=400, detail="bad data URL")
    try:
        b64 = data_url.split(",", 1)[1]
    except IndexError:
        raise HTTPException(status_code=400, detail="bad data URL")
    return base64.b64decode(b64)


@app.post("/api/perception-frames")
def perception_frames(req: PerceptionFramesReq):
    if not PERCEPTION_ID_RE.match(req.world_id):
        raise HTTPException(status_code=400, detail="bad world_id")
    views_dir = WORLDS_DIR / req.world_id / "views"
    views_dir.mkdir(parents=True, exist_ok=True)
    (views_dir / "view_0.jpg").write_bytes(_decode_data_url(req.view_0))
    (views_dir / "view_120.jpg").write_bytes(_decode_data_url(req.view_120))
    (views_dir / "view_240.jpg").write_bytes(_decode_data_url(req.view_240))
    return {"ok": True, "path": str(views_dir)}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/unit/test_perception_endpoint.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/bridge/main.py backend/tests/unit/test_perception_endpoint.py
git commit -m "feat(bridge): POST /api/perception-frames saves 3 yaw-rotated views"
```

---

### Task 26: `POST /api/analyze/{id}` + `GET /api/analyze/{id}/status`

**Files:**
- Modify: `backend/bridge/main.py`
- Test: `backend/tests/unit/test_analyze_endpoint.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/unit/test_analyze_endpoint.py`:

```python
import json
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from bridge.main import app


def test_analyze_writes_json_and_returns_202(tmp_path, monkeypatch):
    monkeypatch.setattr("bridge.main.WORLDS_DIR", tmp_path / "backend_worlds")
    output_dir = tmp_path / "frontend_worlds"
    output_dir.mkdir()
    monkeypatch.setattr("bridge.main.FRONTEND_WORLDS_DIR", output_dir)

    # Pre-create the views dir
    views = (tmp_path / "backend_worlds" / "abc" / "views")
    views.mkdir(parents=True)
    for n in (0, 120, 240):
        (views / f"view_{n}.jpg").write_bytes(b"x")

    fake_result = {"world_id": "abc", "agents": {"scene_describer": {"status": "done"}}}

    async def fake_run_dag(p):
        return fake_result

    with patch("bridge.main.run_dag", side_effect=fake_run_dag):
        client = TestClient(app)
        r = client.post("/api/analyze/abc", json={"prompt": "test prompt"})
        assert r.status_code == 202
        # Poll status until done
        for _ in range(20):
            s = client.get("/api/analyze/abc/status").json()
            if s["state"] == "done":
                break
        assert (output_dir / "abc.agents.json").exists()
        loaded = json.loads((output_dir / "abc.agents.json").read_text())
        assert loaded["world_id"] == "abc"


def test_analyze_404_when_views_missing(tmp_path, monkeypatch):
    monkeypatch.setattr("bridge.main.WORLDS_DIR", tmp_path / "backend_worlds")
    monkeypatch.setattr("bridge.main.FRONTEND_WORLDS_DIR", tmp_path / "frontend_worlds")
    (tmp_path / "frontend_worlds").mkdir()
    client = TestClient(app)
    r = client.post("/api/analyze/missing", json={"prompt": "x"})
    assert r.status_code == 404


def test_analyze_409_when_already_running(tmp_path, monkeypatch):
    monkeypatch.setattr("bridge.main.WORLDS_DIR", tmp_path / "backend_worlds")
    monkeypatch.setattr("bridge.main.FRONTEND_WORLDS_DIR", tmp_path / "frontend_worlds")
    (tmp_path / "frontend_worlds").mkdir()
    views = (tmp_path / "backend_worlds" / "abc" / "views")
    views.mkdir(parents=True)
    for n in (0, 120, 240):
        (views / f"view_{n}.jpg").write_bytes(b"x")

    async def slow_run_dag(p):
        import asyncio
        await asyncio.sleep(0.5)
        return {"world_id": "abc", "agents": {}}

    with patch("bridge.main.run_dag", side_effect=slow_run_dag):
        client = TestClient(app)
        r1 = client.post("/api/analyze/abc", json={"prompt": "x"})
        assert r1.status_code == 202
        r2 = client.post("/api/analyze/abc", json={"prompt": "x"})
        assert r2.status_code == 409
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_analyze_endpoint.py -v
```

- [ ] **Step 3: Add endpoints + state to `bridge/main.py`**

Add near the top of `backend/bridge/main.py`, after existing imports:

```python
from agents_v2.orchestrator import run_dag
from agents_v2.messages import PerceptionInput

FRONTEND_WORLDS_DIR = Path(__file__).parent.parent.parent / "frontend" / "public" / "worlds"

# world_id -> "queued" | "running" | "done" | "error"
_analyze_state: dict[str, str] = {}
```

Append the endpoint code:

```python
class AnalyzeReq(BaseModel):
    prompt: str = ""


async def _drive_analyze(world_id: str, prompt: str) -> None:
    _analyze_state[world_id] = "running"
    try:
        views_dir = WORLDS_DIR / world_id / "views"
        view_paths = [str(views_dir / f"view_{n}.jpg") for n in (0, 120, 240)]
        result = await run_dag(PerceptionInput(
            world_id=world_id, prompt=prompt, view_paths=view_paths,
        ))
        FRONTEND_WORLDS_DIR.mkdir(parents=True, exist_ok=True)
        out_path = FRONTEND_WORLDS_DIR / f"{world_id}.agents.json"
        out_path.write_text(json.dumps(result, indent=2))
        _analyze_state[world_id] = "done"
    except Exception as e:
        _analyze_state[world_id] = "error"
        raise


@app.post("/api/analyze/{world_id}", status_code=202)
async def analyze(world_id: str, req: AnalyzeReq):
    if not PERCEPTION_ID_RE.match(world_id):
        raise HTTPException(status_code=400, detail="bad world_id")
    views_dir = WORLDS_DIR / world_id / "views"
    if not views_dir.exists():
        raise HTTPException(status_code=404, detail="perception frames not found")
    if _analyze_state.get(world_id) == "running":
        raise HTTPException(status_code=409, detail="already running")
    _analyze_state[world_id] = "queued"
    asyncio.create_task(_drive_analyze(world_id, req.prompt))
    return {"ok": True, "state": "queued"}


@app.get("/api/analyze/{world_id}/status")
def analyze_status(world_id: str):
    state = _analyze_state.get(world_id)
    if state is None:
        # Check if cached output exists
        out_path = FRONTEND_WORLDS_DIR / f"{world_id}.agents.json"
        if out_path.exists():
            return {"state": "done"}
        return {"state": "unknown"}
    return {"state": state}
```

Replace existing `_start_uagents` import to point at new runner:

```python
@app.on_event("startup")
def _start_uagents():
    if os.environ.get("WORLD_BUILD_DISABLE_UAGENTS") == "1":
        return
    from agents_v2.runner import start_all_in_background
    start_all_in_background()
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/unit/test_analyze_endpoint.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/bridge/main.py backend/tests/unit/test_analyze_endpoint.py
git commit -m "feat(bridge): POST /api/analyze + GET /api/analyze/status, swap runner"
```

---

### Task 27: Backend smoke test — full pipeline against fake world

**Files:**
- Test: `backend/tests/e2e/test_full_pipeline.py`

- [ ] **Step 1: Create the smoke test**

Create `backend/tests/e2e/test_full_pipeline.py`:

```python
"""End-to-end test: simulate a full analyze run with all 19 agents stubbed.
This catches integration regressions across manifest, orchestrator, registry,
and bridge."""
import base64
import json
from unittest.mock import patch
from fastapi.testclient import TestClient
from bridge.main import app
from agents_v2.manifest import AGENTS


def _data_url(b: bytes) -> str:
    return f"data:image/jpeg;base64,{base64.b64encode(b).decode()}"


def test_perception_then_analyze_writes_full_json(tmp_path, monkeypatch):
    backend_worlds = tmp_path / "backend_worlds"
    frontend_worlds = tmp_path / "frontend_worlds"
    frontend_worlds.mkdir()
    monkeypatch.setattr("bridge.main.WORLDS_DIR", backend_worlds)
    monkeypatch.setattr("bridge.main.FRONTEND_WORLDS_DIR", frontend_worlds)

    # Stub every agent run to emit a marker
    stubs = {a.id: (lambda req, _id=a.id: {"marker": _id, "got": list(req.upstream.keys())})
             for a in AGENTS}

    client = TestClient(app)

    # Step 1: upload perception frames
    r = client.post("/api/perception-frames", json={
        "world_id": "smoke",
        "view_0":   _data_url(b"\xff\xd8\xff\xe0v0"),
        "view_120": _data_url(b"\xff\xd8\xff\xe0v120"),
        "view_240": _data_url(b"\xff\xd8\xff\xe0v240"),
    })
    assert r.status_code == 200

    # Step 2: trigger analyze
    with patch("agents_v2.registry.AGENT_RUNS", stubs):
        r = client.post("/api/analyze/smoke", json={"prompt": "smoke prompt"})
        assert r.status_code == 202
        # Poll
        for _ in range(40):
            s = client.get("/api/analyze/smoke/status").json()
            if s["state"] == "done":
                break

    out = frontend_worlds / "smoke.agents.json"
    assert out.exists()
    data = json.loads(out.read_text())
    assert data["world_id"] == "smoke"
    assert len(data["agents"]) == 19
    for aid in (a.id for a in AGENTS):
        assert data["agents"][aid]["status"] == "done"
        assert data["agents"][aid]["output"]["marker"] == aid
```

- [ ] **Step 2: Run test to verify it passes**

```bash
pytest tests/e2e/test_full_pipeline.py -v
```

Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add backend/tests/e2e/test_full_pipeline.py
git commit -m "test: e2e smoke test for perception + analyze pipeline"
```

---

## Phase 5 — Frontend manifest + capture extension

### Task 28: Frontend agent manifest

**Files:**
- Create: `frontend/lib/agentManifest.ts`

- [ ] **Step 1: Create the file**

```typescript
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
  category: string;          // human label for sidebar grouping
  dependencies: string[];
  display: AgentDisplayType;
  // Circuit board grid position (col, row), 0-indexed. CAPTURE node is at (2, 0).
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
```

- [ ] **Step 2: Verify it type-checks**

```bash
cd /Users/tomalmog/projects/world-build-agents/frontend
npx tsc --noEmit
```

Expected: no errors. (If pre-existing errors, ignore those in unrelated files.)

- [ ] **Step 3: Commit**

```bash
git add frontend/lib/agentManifest.ts
git commit -m "feat(frontend): agent manifest mirrors backend, adds graph coords"
```

---

### Task 29: Frontend results loader

**Files:**
- Create: `frontend/lib/agentResults.ts`

- [ ] **Step 1: Create the file**

```typescript
export type AgentStatus = "done" | "error" | "skipped";

export interface AgentEntry {
  status: AgentStatus;
  duration_ms: number;
  display: "text" | "list" | "swatches" | "map" | "products" | "thumbnails";
  output?: any;
  error_message?: string;
  reason?: string;
}

export interface AgentResults {
  world_id: string;
  generated_at: string;
  schema_version: number;
  agents: Record<string, AgentEntry>;
}

export async function fetchAgentResults(worldId: string): Promise<AgentResults | null> {
  const url = `/worlds/${worldId}.agents.json`;
  const res = await fetch(url, { cache: "no-store" });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`agents.json fetch failed: ${res.status}`);
  return await res.json();
}

export async function pollAnalyzeStatus(
  worldId: string,
  apiBase: string = "http://localhost:8000",
): Promise<"queued" | "running" | "done" | "error" | "unknown"> {
  const res = await fetch(`${apiBase}/api/analyze/${worldId}/status`);
  if (!res.ok) return "unknown";
  const j = await res.json();
  return j.state;
}
```

- [ ] **Step 2: Verify it type-checks**

```bash
cd /Users/tomalmog/projects/world-build-agents/frontend
npx tsc --noEmit
```

- [ ] **Step 3: Commit**

```bash
git add frontend/lib/agentResults.ts
git commit -m "feat(frontend): typed loader + analyze status poller for agent results"
```

---

### Task 30: Capture 3 yaw-rotated frames + auto-trigger analyze

**Files:**
- Modify: `frontend/components/SplatScene.tsx`

- [ ] **Step 1: Read the current file**

```bash
cd /Users/tomalmog/projects/world-build-agents
cat frontend/components/SplatScene.tsx | wc -l
```

Note current line count. Confirm `CaptureBridge` is still defined inside Canvas children.

- [ ] **Step 2: Replace `CaptureBridge` with a 3-shot capture bridge**

Edit `frontend/components/SplatScene.tsx`. Find:

```typescript
function CaptureBridge({ captureRef }: { captureRef: React.MutableRefObject<(() => string | null) | null> }) {
  const { gl, scene, camera } = useThree();
  useEffect(() => {
    captureRef.current = () => {
      try {
        gl.render(scene, camera);
        return gl.domElement.toDataURL("image/jpeg", 0.85);
      } catch (err) {
        console.error("[capture] failed", err);
        return null;
      }
    };
    return () => { captureRef.current = null; };
  }, [gl, scene, camera, captureRef]);
  return null;
}
```

Replace with:

```typescript
type Capture3Fn = () => { thumbnail: string | null; views: [string, string, string] | null };

function CaptureBridge({ captureRef }: { captureRef: React.MutableRefObject<(() => string | null) | null> }) {
  const { gl, scene, camera } = useThree();
  useEffect(() => {
    captureRef.current = () => {
      try {
        gl.render(scene, camera);
        return gl.domElement.toDataURL("image/jpeg", 0.85);
      } catch (err) {
        console.error("[capture] failed", err);
        return null;
      }
    };
    return () => { captureRef.current = null; };
  }, [gl, scene, camera, captureRef]);
  return null;
}

function PerceptionCaptureBridge({
  captureRef,
}: { captureRef: React.MutableRefObject<Capture3Fn | null> }) {
  const { gl, scene, camera } = useThree();
  useEffect(() => {
    captureRef.current = () => {
      try {
        const originalYaw = camera.rotation.y;
        gl.render(scene, camera);
        const thumbnail = gl.domElement.toDataURL("image/jpeg", 0.85);

        const views: string[] = [];
        const yawOffsets = [0, (2 * Math.PI) / 3, (4 * Math.PI) / 3];
        for (const off of yawOffsets) {
          camera.rotation.y = originalYaw + off;
          camera.updateMatrixWorld(true);
          gl.render(scene, camera);
          views.push(gl.domElement.toDataURL("image/jpeg", 0.85));
        }
        camera.rotation.y = originalYaw;
        camera.updateMatrixWorld(true);
        gl.render(scene, camera);

        return { thumbnail, views: [views[0], views[1], views[2]] as [string, string, string] };
      } catch (err) {
        console.error("[perception capture] failed", err);
        return { thumbnail: null, views: null };
      }
    };
    return () => { captureRef.current = null; };
  }, [gl, scene, camera, captureRef]);
  return null;
}
```

- [ ] **Step 3: Replace the auto-capture effect with the 3-shot version**

In the same file, find the existing thumbnail auto-capture useEffect (the one around `runCapture` / `autoFiredRef`). Replace the auto-fire effect with this combined flow:

```typescript
// Auto-capture flow:
// 1. If world has no thumbnail yet (HEAD-check thumbnailUrl), use the
//    perception bridge to grab thumbnail + 3 yaw-rotated views in one go.
// 2. POST views to /api/perception-frames.
// 3. POST thumbnail to /api/thumbnail (existing).
// 4. POST /api/analyze/<id>.
// 5. Poll status; when done, the sidebar's own loader picks up the JSON.
const perceptionRef = useRef<Capture3Fn | null>(null);

useEffect(() => {
  if (!captureMode || !sparkReady) return;
  if (autoFiredRef.current) return;
  autoFiredRef.current = true;

  let cancelled = false;
  (async () => {
    if (!captureMode.force && thumbnailUrl) {
      try {
        const head = await fetch(thumbnailUrl, { method: "HEAD" });
        if (head.ok) return;
      } catch {}
    }
    await new Promise((r) => setTimeout(r, 1500));
    if (cancelled) return;

    const fn = perceptionRef.current;
    if (!fn) return;
    const { thumbnail, views } = fn();
    if (!thumbnail || !views) {
      setCaptureMsg("capture failed");
      return;
    }
    setCaptureMsg("saving thumbnail…");
    try {
      await fetch("/api/thumbnail", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: captureMode.id, dataUrl: thumbnail }),
      });
    } catch {}

    setCaptureMsg("saving perception frames…");
    try {
      const res = await fetch("http://localhost:8000/api/perception-frames", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          world_id: captureMode.id,
          view_0:   views[0],
          view_120: views[1],
          view_240: views[2],
        }),
      });
      if (!res.ok) {
        setCaptureMsg(`perception frames failed: ${res.status}`);
        return;
      }
    } catch (err) {
      setCaptureMsg(`perception frames error: ${String(err)}`);
      return;
    }

    setCaptureMsg("dispatching agents…");
    try {
      await fetch(`http://localhost:8000/api/analyze/${captureMode.id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: "" }),
      });
      setCaptureMsg("agents running…");
    } catch (err) {
      setCaptureMsg(`analyze trigger failed: ${String(err)}`);
      return;
    }

    setTimeout(() => setCaptureMsg(null), 4000);
  })();
  return () => {
    cancelled = true;
  };
}, [captureMode, sparkReady, thumbnailUrl]);
```

Then mount `PerceptionCaptureBridge` inside the Canvas alongside the existing `CaptureBridge`:

```typescript
{captureMode && <CaptureBridge captureRef={captureRef} />}
{captureMode && <PerceptionCaptureBridge captureRef={perceptionRef} />}
<PoseReadout onChange={onPoseChange} />
```

- [ ] **Step 4: Manual smoke test**

Open frontend in dev server, visit `/world/cabin?capture=1` (forces re-capture). Verify:
- HUD shows "saving thumbnail…" → "saving perception frames…" → "dispatching agents…" → "agents running…"
- `backend/worlds/cabin/views/view_0.jpg` etc. exist
- Backend log shows analyze starting
- After ~30-60s: `frontend/public/worlds/cabin.agents.json` exists with 19 entries

If backend isn't running, capture should still complete with the thumbnail; perception frame upload errors gracefully.

- [ ] **Step 5: Commit**

```bash
git add frontend/components/SplatScene.tsx
git commit -m "feat(frontend): capture 3 yaw-rotated perception views + auto-trigger analyze"
```

---

## Phase 6 — Sidebar UI

### Task 31: Default + List card renderers

**Files:**
- Create: `frontend/components/agent-cards/TextCard.tsx`
- Create: `frontend/components/agent-cards/ListCard.tsx`
- Create: `frontend/components/agent-cards/index.ts`

- [ ] **Step 1: TextCard**

Create `frontend/components/agent-cards/TextCard.tsx`:

```typescript
import type { AgentEntry } from "@/lib/agentResults";

export default function TextCard({ entry }: { entry: AgentEntry }) {
  if (entry.status !== "done") return <FallbackCard entry={entry} />;
  const out = entry.output ?? {};
  // Common shape: { summary, tags, reasoning, ... }
  if (typeof out.summary === "string") {
    return (
      <div className="space-y-2">
        <p className="text-sm leading-relaxed text-on-surface">{out.summary}</p>
        {Array.isArray(out.tags) && out.tags.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {out.tags.map((t: string) => (
              <span key={t} className="text-[10px] uppercase tracking-wider px-2 py-0.5 rounded bg-surface-container border border-outline-variant text-on-surface-variant">{t}</span>
            ))}
          </div>
        )}
      </div>
    );
  }
  return (
    <pre className="text-xs font-mono whitespace-pre-wrap break-words text-on-surface-variant">
      {JSON.stringify(out, null, 2)}
    </pre>
  );
}

export function FallbackCard({ entry }: { entry: AgentEntry }) {
  if (entry.status === "skipped") {
    return <p className="text-xs text-on-surface-variant italic">Skipped — {entry.reason ?? "upstream failed"}</p>;
  }
  return <p className="text-xs text-red-600">Error: {entry.error_message ?? "unknown"}</p>;
}
```

- [ ] **Step 2: ListCard**

Create `frontend/components/agent-cards/ListCard.tsx`:

```typescript
import type { AgentEntry } from "@/lib/agentResults";
import { FallbackCard } from "./TextCard";

export default function ListCard({ entry }: { entry: AgentEntry }) {
  if (entry.status !== "done") return <FallbackCard entry={entry} />;
  const out = entry.output ?? {};

  // Find the first array-valued key — most list-shaped outputs have one
  const arrayKey = Object.keys(out).find((k) => Array.isArray(out[k]));
  if (!arrayKey) {
    return (
      <pre className="text-xs font-mono whitespace-pre-wrap break-words text-on-surface-variant">
        {JSON.stringify(out, null, 2)}
      </pre>
    );
  }
  const items = out[arrayKey] as any[];

  return (
    <ul className="space-y-2">
      {items.map((item, i) => (
        <li key={i} className="text-sm text-on-surface">
          {typeof item === "string" ? (
            item
          ) : (
            <ItemRow item={item} />
          )}
        </li>
      ))}
    </ul>
  );
}

function ItemRow({ item }: { item: Record<string, any> }) {
  const keys = Object.keys(item);
  const primary = keys.find((k) => ["name", "title", "type", "region", "category"].includes(k)) ?? keys[0];
  const secondary = keys.find((k) => k !== primary && typeof item[k] === "string");
  return (
    <div>
      <div className="font-medium">{String(item[primary])}</div>
      {secondary && <div className="text-xs text-on-surface-variant">{String(item[secondary])}</div>}
    </div>
  );
}
```

- [ ] **Step 3: Index / selector**

Create `frontend/components/agent-cards/index.ts`:

```typescript
import TextCard from "./TextCard";
import ListCard from "./ListCard";
import type { AgentEntry } from "@/lib/agentResults";

export function renderAgentCard(entry: AgentEntry) {
  switch (entry.display) {
    case "list":
      return <ListCard entry={entry} />;
    case "swatches":
    case "map":
    case "products":
    case "thumbnails":
      // Custom renderers ship later; for v1 fall through to TextCard.
      return <TextCard entry={entry} />;
    case "text":
    default:
      return <TextCard entry={entry} />;
  }
}
```

- [ ] **Step 4: Verify type-check**

```bash
cd /Users/tomalmog/projects/world-build-agents/frontend
npx tsc --noEmit
```

- [ ] **Step 5: Commit**

```bash
git add frontend/components/agent-cards/
git commit -m "feat(frontend): TextCard + ListCard agent renderers (v1 fallback for others)"
```

---

### Task 32: AgentSidebar component

**Files:**
- Create: `frontend/components/AgentSidebar.tsx`
- Modify: `frontend/components/SplatScene.tsx` (mount the sidebar)

- [ ] **Step 1: Create AgentSidebar**

Create `frontend/components/AgentSidebar.tsx`:

```typescript
"use client";
import { useEffect, useState } from "react";
import { AGENTS, CATEGORIES, AGENTS_BY_ID } from "@/lib/agentManifest";
import { fetchAgentResults, pollAnalyzeStatus, type AgentResults } from "@/lib/agentResults";
import { renderAgentCard } from "./agent-cards";
import AgentNetworkGraph from "./AgentNetworkGraph";

export default function AgentSidebar({ worldId }: { worldId: string }) {
  const [open, setOpen] = useState(false);
  const [results, setResults] = useState<AgentResults | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    let interval: any;
    async function load() {
      setLoading(true);
      const r = await fetchAgentResults(worldId).catch(() => null);
      if (cancelled) return;
      if (r) {
        setResults(r);
        setLoading(false);
        return;
      }
      // Not ready yet — poll backend status
      interval = setInterval(async () => {
        const state = await pollAnalyzeStatus(worldId).catch(() => "unknown");
        if (state === "done") {
          const r2 = await fetchAgentResults(worldId).catch(() => null);
          if (r2) {
            setResults(r2);
            setLoading(false);
            clearInterval(interval);
          }
        }
      }, 2000);
    }
    load();
    return () => {
      cancelled = true;
      if (interval) clearInterval(interval);
    };
  }, [worldId]);

  return (
    <>
      <button
        onClick={() => setOpen((v) => !v)}
        className="fixed top-4 right-4 z-20 text-xs font-mono bg-white/90 text-on-surface px-3 py-1.5 rounded shadow-soft border border-outline-variant hover:bg-white"
      >
        {open ? "× close" : "agents"}
      </button>
      <div
        className={
          "fixed top-0 right-0 h-full w-[420px] bg-white/98 border-l border-outline-variant z-10 overflow-y-auto transition-transform duration-300 " +
          (open ? "translate-x-0" : "translate-x-full")
        }
      >
        <div className="p-6 space-y-6">
          <div>
            <h2 className="label-caps tracking-[0.18em] text-base">AGENT SWARM</h2>
            <div className="text-xs text-on-surface-variant mt-1 font-mono">
              {results ? `${Object.keys(results.agents).length} / 19` : loading ? "running…" : "queued"}
            </div>
          </div>

          {open && <AgentNetworkGraph results={results} />}

          {CATEGORIES.map((cat) => {
            const agentsInCat = AGENTS.filter((a) => a.category === cat.name);
            return (
              <section key={cat.name}>
                <h3 className="label-caps text-on-surface-variant text-xs mb-3">{cat.name}</h3>
                <div className="space-y-3">
                  {agentsInCat.map((a) => {
                    const entry = results?.agents[a.id];
                    return (
                      <div key={a.id} className="border border-outline-variant rounded p-3 bg-surface">
                        <div className="flex items-center justify-between mb-2">
                          <div className="text-sm font-medium">{a.label}</div>
                          <StatusBadge status={entry?.status ?? "pending"} />
                        </div>
                        {entry ? renderAgentCard(entry) : <PendingPlaceholder />}
                      </div>
                    );
                  })}
                </div>
              </section>
            );
          })}
        </div>
      </div>
    </>
  );
}

function StatusBadge({ status }: { status: string }) {
  const cls =
    status === "done" ? "bg-green-50 text-green-700 border-green-200" :
    status === "error" ? "bg-red-50 text-red-700 border-red-200" :
    status === "skipped" ? "bg-zinc-50 text-zinc-500 border-zinc-200" :
    "bg-zinc-100 text-zinc-500 border-zinc-200";
  return <span className={`text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded border ${cls}`}>{status}</span>;
}

function PendingPlaceholder() {
  return <div className="h-4 bg-surface-container rounded animate-pulse" />;
}
```

- [ ] **Step 2: Mount the sidebar in `SplatScene.tsx`**

In `frontend/components/SplatScene.tsx`, add at the top of the file:

```typescript
import AgentSidebar from "./AgentSidebar";
```

Inside the returned JSX, just before the final `</div>` of the scene wrapper:

```typescript
{captureMode && <AgentSidebar worldId={captureMode.id} />}
```

- [ ] **Step 3: Manual smoke test**

Visit `/world/cabin` (assuming `cabin.agents.json` exists from Task 30 smoke test). Click "agents" button top-right → drawer slides in → shows 19 cards under their categories. Status badges should reflect each agent's state.

If `cabin.agents.json` doesn't exist yet, sidebar will show "queued" / pending placeholders and poll until the backend writes it.

- [ ] **Step 4: Commit**

```bash
git add frontend/components/AgentSidebar.tsx frontend/components/SplatScene.tsx
git commit -m "feat(frontend): AgentSidebar drawer with 5 categories + 19 cards"
```

---

## Phase 7 — Network graph animation

### Task 33: Scripted Circuit Board network graph

**Files:**
- Create: `frontend/components/AgentNetworkGraph.tsx`

- [ ] **Step 1: Build the SVG component**

Create `frontend/components/AgentNetworkGraph.tsx`:

```typescript
"use client";
import { useEffect, useRef, useState } from "react";
import { AGENTS } from "@/lib/agentManifest";
import type { AgentResults } from "@/lib/agentResults";

const W = 380;
const H = 360;
const ROWS = 6;       // CAPTURE row + 5 tier rows
const COLS = 5;
const PADDING = 24;
const COL_W = (W - PADDING * 2) / (COLS - 1);
const ROW_H = (H - PADDING * 2) / (ROWS - 1);

const FETCH_BLUE = "#4a90ff";
const TRACE = "#333";
const NODE_BG = "#fff";

interface Node {
  id: string;
  label: string;
  x: number;
  y: number;
}

const CAPTURE_NODE: Node = {
  id: "__capture__",
  label: "CAPTURE",
  x: PADDING + 2 * COL_W,  // col 2
  y: PADDING + 0 * ROW_H,  // row 0
};

const NODES: Node[] = [
  CAPTURE_NODE,
  ...AGENTS.map((a) => ({
    id: a.id,
    label: a.label.toUpperCase(),
    x: PADDING + a.col * COL_W,
    y: PADDING + a.row * ROW_H,
  })),
];

const NODES_BY_ID = Object.fromEntries(NODES.map((n) => [n.id, n]));

interface Edge {
  from: string;
  to: string;
}

const EDGES: Edge[] = [
  // CAPTURE → all Tier 0 agents
  ...AGENTS.filter((a) => a.tier === 0).map((a) => ({ from: "__capture__", to: a.id })),
  // Each agent's declared dependencies
  ...AGENTS.flatMap((a) => a.dependencies.map((d) => ({ from: d, to: a.id }))),
];

// Build a right-angle path: go horizontally first, then vertically.
function tracePath(a: Node, b: Node): string {
  const midX = b.x;
  const midY = a.y;
  return `M ${a.x} ${a.y} L ${midX} ${midY} L ${b.x} ${b.y}`;
}

const SCRIPT_DURATION_MS = 12_000;
// Each node "lights up" at a deterministic time
function nodeLightTime(id: string): number {
  if (id === "__capture__") return 400;
  const a = AGENTS.find((x) => x.id === id)!;
  const tier = a.tier;
  const rowOrder = AGENTS.filter((x) => x.tier === tier).indexOf(a);
  return 1500 + tier * 1800 + rowOrder * 200;
}

function edgeLightTime(e: Edge): number {
  return Math.max(nodeLightTime(e.from), nodeLightTime(e.to));
}

export default function AgentNetworkGraph({ results }: { results: AgentResults | null }) {
  const [now, setNow] = useState(0);
  const startRef = useRef<number | null>(null);

  useEffect(() => {
    let raf: number;
    function tick(t: number) {
      if (startRef.current == null) startRef.current = t;
      setNow(t - startRef.current);
      if (t - startRef.current < SCRIPT_DURATION_MS + 500) {
        raf = requestAnimationFrame(tick);
      }
    }
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, []);

  const litNodes = new Set<string>();
  for (const n of NODES) {
    if (now >= nodeLightTime(n.id)) litNodes.add(n.id);
  }
  const activeEdges = EDGES.filter((e) => {
    const t = edgeLightTime(e);
    return now >= t - 600 && now <= t + 400;
  });

  return (
    <div className="border border-outline-variant rounded bg-[#fafafa] p-2">
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full">
        {/* grid */}
        <defs>
          <pattern id="grid-bg" width="20" height="20" patternUnits="userSpaceOnUse">
            <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#eee" strokeWidth="0.5" />
          </pattern>
          <filter id="glow"><feGaussianBlur stdDeviation="2" /></filter>
        </defs>
        <rect width={W} height={H} fill="url(#grid-bg)" />

        {/* edges */}
        {EDGES.map((e, i) => {
          const a = NODES_BY_ID[e.from];
          const b = NODES_BY_ID[e.to];
          const lit = litNodes.has(e.from) && litNodes.has(e.to);
          const active = activeEdges.includes(e);
          return (
            <g key={i}>
              <path d={tracePath(a, b)} fill="none"
                    stroke={active ? FETCH_BLUE : (lit ? TRACE : "#ccc")}
                    strokeWidth={active ? 2 : 1}
                    style={active ? { filter: "url(#glow)" } : undefined} />
              {active && (
                <circle r="2.5" fill={FETCH_BLUE}>
                  <animateMotion dur="0.6s" repeatCount="1" path={tracePath(a, b)} />
                </circle>
              )}
            </g>
          );
        })}

        {/* nodes */}
        {NODES.map((n) => {
          const lit = litNodes.has(n.id);
          const fill = lit ? (n.id === "__capture__" ? FETCH_BLUE : NODE_BG) : "#f0f0f0";
          const stroke = lit ? TRACE : "#ccc";
          return (
            <g key={n.id}>
              <rect x={n.x - 8} y={n.y - 8} width={16} height={16}
                    fill={fill} stroke={stroke} strokeWidth={1.5} />
              <text x={n.x} y={n.y - 12} textAnchor="middle"
                    fontFamily="monospace" fontSize="6.5" fill="#666">
                {n.label.slice(0, 14)}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
```

- [ ] **Step 2: Verify type-check**

```bash
cd /Users/tomalmog/projects/world-build-agents/frontend
npx tsc --noEmit
```

- [ ] **Step 3: Manual smoke test**

Open the sidebar on a world. You should see:
- Grid background
- CAPTURE node at top-center, lights up first (in Fetch blue)
- Tier 0 nodes light up next, traces appearing from CAPTURE to each
- Tier 1 → Tier 2 → Tier 3 → Tier 4 cascade
- Active edges briefly glow blue with traveling pulses
- After ~12s the animation settles

Animation plays once when sidebar opens. Re-open to replay.

- [ ] **Step 4: Commit**

```bash
git add frontend/components/AgentNetworkGraph.tsx
git commit -m "feat(frontend): scripted Circuit Board network graph (12s sequence)"
```

---

## Phase 8 — Dry run + cleanup

### Task 34: Live dry-run against the 3 existing worlds

**Files:**
- (No code; verification task)

- [ ] **Step 1: Start backend**

```bash
cd /Users/tomalmog/projects/world-build-agents/backend
source .venv/bin/activate
uvicorn bridge.main:app --port 8000
```

In another shell:

```bash
cd /Users/tomalmog/projects/world-build-agents/frontend
npm run dev
```

- [ ] **Step 2: Run pipeline against `cabin`**

In a browser, open `http://localhost:3000/world/cabin?capture=1`. Wait for the capture flow to complete and the sidebar to populate.

Expected:
- `frontend/public/worlds/cabin.agents.json` exists with all 19 agents
- Each agent's `status` is `done` (errors are acceptable for individual agents but the file should be present)
- Sidebar shows 5 categories with cards
- Network graph plays cleanly

- [ ] **Step 3: Repeat for `office` and `living_room`**

Visit `/world/office?capture=1` and `/world/living_room?capture=1`. Verify same outcomes.

- [ ] **Step 4: Sanity-check Agentverse registration**

Backend startup logs should show 19 agents on ports 8100-8118. With `AGENTVERSE_API_KEY` set, each should attempt registration. Any registration warnings (mailbox, etc.) are OK — the pipeline still runs.

- [ ] **Step 5: Commit any tweaks**

If the dry-run revealed bugs, fix them with TDD (test first), commit fixes individually. If clean, no commit needed.

---

### Task 35: Final cleanup + plan close-out

**Files:**
- (No code change required unless smoke test surfaced issues)

- [ ] **Step 1: Run the full backend test suite**

```bash
cd /Users/tomalmog/projects/world-build-agents/backend
pytest tests/ -v
```

Expected: all tests pass. Old (pre-pivot) tests should be untouched and still passing — this work doesn't modify `agents/` or `core/` (except for adding `vision()` to `gemini_client.py`).

- [ ] **Step 2: TypeScript check**

```bash
cd /Users/tomalmog/projects/world-build-agents/frontend
npx tsc --noEmit
```

Expected: no new errors introduced by this work.

- [ ] **Step 3: Verify no committed secrets**

```bash
cd /Users/tomalmog/projects/world-build-agents
git log --diff-filter=A --name-only agent-swarm | grep -E "\.env|secret|key" || echo "clean"
```

Expected: `clean`.

- [ ] **Step 4: Push branch**

```bash
git push -u origin agent-swarm
```

- [ ] **Step 5: Open PR (optional, can use superpowers:finishing-a-development-branch)**

Use the gh CLI if desired. Otherwise the branch is ready for review/merge.

---

## What's deliberately NOT in this plan

These are explicitly deferred per the spec:

- **Custom renderers for `swatches`, `map`, `products`, `thumbnails`** — they fall through to TextCard for now. v2 work.
- **Cleanup of old `backend/agents/` package** — left untouched. The bridge no longer imports `uagent_runner` from there but the agents themselves stay as dead code.
- **Marble API integration** — worlds are pre-built files. The capture-and-analyze flow would slot into Marble's post-generation hook when it lands.
- **Tier 5 agents (Critic, Variant Suggester)** — confirmed dropped.
- **Frontend automated tests** — no test infra in the repo today; not in scope for this plan.
- **Network graph live data binding** — animation is fully scripted. The `results` prop is passed but not consumed by the SVG. (We accept this as deliberate per the user's "the network thing honestly can just be a lie".)

## Self-review notes

This plan was self-reviewed against the spec. All major spec sections (architecture, 19 agents, data shapes, API surface, capture extension, sidebar, network graph, error handling) have corresponding tasks. No "TBD"/"similar to" placeholders. Type names (`AgentRequest`, `AgentResponse`, `AgentEntry`, `AgentDef`, `AgentResults`) are consistent across backend and frontend definitions. The `display` enum matches between `manifest.py`, `agentManifest.ts`, and `agentResults.ts`. Port range 8100-8118 used consistently (manifest, runner test, runner code).
