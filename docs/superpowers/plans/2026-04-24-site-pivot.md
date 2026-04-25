# Site Pivot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Repivot World Build from "styled cabin with curated products" to "whole building on a 100×100m grass plot, walk inside and outside through a real entrance."

**Architecture:** Add a `Site` model (plot + buildingFootprint + buildingAnchor + entrance) above the existing `Blueprint`. The pipeline produces ground/exterior_wall/roof primitives in plot-world coordinates. `furniture_planner` becomes a pure-code lookup against a `room_type → template` table. `product_scout` and `style_matcher` are unwired from the orchestrator (the agent files stay so the 14-uAgent count for Fetch.ai is preserved). The `Product` model, image proxy endpoints, and `FurniturePanel` are deleted.

**Tech Stack:** FastAPI, Pydantic v2, Gemini structured output, Next.js 14 + React Three Fiber, pytest.

**Spec:** `docs/superpowers/specs/2026-04-24-site-pivot-design.md`

---

## File Structure

**Backend — new:**
- `backend/core/site.py` — pure helpers: `derive_site_from_intent`, plot/footprint defaults
- `backend/core/room_templates.py` — `ROOM_FURNITURE` dict + `apply_template` function
- `backend/core/site_validators.py` — `check_site_constraints(spec)` for the new compliance checks

**Backend — modified:**
- `backend/core/world_spec.py` — add `Plot`, `Entrance`, `Site`; add `site` field to `WorldSpec`; remove `Product` and `selectedProductId`/`alternates`/`subtype`/`tint` from `FurnitureItem`; remove `products` from `WorldSpec`; extend `GeometryPrimitive.type` literal
- `backend/core/geometry.py` — add ground/exterior_wall/roof primitives; offset everything by `buildingAnchor`
- `backend/core/pricing.py` — switch to `cost_per_sqm × area`
- `backend/core/navigation.py` — spawn on grass facing entrance
- `backend/core/prompts/blueprint_architect.py` — office-building examples + footprint constraint
- `backend/agents/intent_parser.py` — also derive `Site`
- `backend/agents/blueprint_architect.py` — pass footprint into prompt
- `backend/agents/compliance_critic.py` — call new site validators
- `backend/agents/geometry_builder.py` — pass `site` into `build_geometry`
- `backend/agents/furniture_planner.py` — pure code, uses `apply_template`
- `backend/agents/pricing_estimator.py` — new signature
- `backend/agents/navigation_planner.py` — pass `spec` to `compute_navigation`
- `backend/agents/orchestrator.py` — remove `product_scout` and `style_matcher` from `POST_STEPS`
- `backend/bridge/main.py` — delete `/api/img`, `/api/img-color`, `/api/select-product` and helpers
- `backend/requirements.txt` — drop `Pillow`, drop `httpx`

**Backend — deleted:**
- `backend/tests/e2e/test_product_urls_live.py`

**Backend — kept (unwired):**
- `backend/agents/product_scout.py` (still imported by `uagent_runner`)
- `backend/agents/style_matcher.py` (still imported by `uagent_runner`)

**Frontend — new:**
- `frontend/components/Plot.tsx`
- `frontend/components/Roof.tsx`
- `frontend/components/Furniture/Desk.tsx`
- `frontend/components/Furniture/OfficeChair.tsx`
- `frontend/components/Furniture/ConferenceTable.tsx`
- `frontend/components/Furniture/ReceptionDesk.tsx`
- `frontend/components/Furniture/Whiteboard.tsx`
- `frontend/components/Furniture/FilingCabinet.tsx`
- `frontend/lib/wallSegments.ts` — shared segmentation between `Wall.tsx` and the collider

**Frontend — modified:**
- `frontend/lib/worldSpec.ts` — mirror Pydantic changes
- `frontend/lib/api.ts` — drop `proxiedImage`, `fetchProductColor`, `selectProduct`
- `frontend/components/World3D.tsx` — render ground/exterior/roof; remove FurniturePanel/state; collider includes both wall types via segmenter
- `frontend/components/Wall.tsx` — use the shared segmenter
- `frontend/components/Furniture/index.tsx` — register new components

**Frontend — deleted:**
- `frontend/components/FurniturePanel.tsx`

**Tests — new (unit):**
- `backend/tests/unit/test_site.py`
- `backend/tests/unit/test_room_templates.py`
- `backend/tests/unit/test_geometry_envelope.py`
- `backend/tests/unit/test_navigation_site.py`
- `backend/tests/unit/test_pricing_sqm.py`

**Tests — modified:**
- `backend/tests/e2e/test_full_pipeline.py`
- `backend/tests/e2e/test_multistory.py`
- Existing unit tests that touched `products`/`selectedProductId` (find via grep)

**Tests — deleted:**
- `backend/tests/e2e/test_product_urls_live.py`

---

## Order of attack

1. **Phase A — schema + pure logic** (Tasks 1–7). All backend/core. No agent or frontend changes. Each task is TDD-able without LLM.
2. **Phase B — agents** (Tasks 8–13). Wire the new logic into agents, update the orchestrator.
3. **Phase C — bridge + frontend cleanup** (Tasks 14–16). Delete the legacy product path.
4. **Phase D — frontend rendering** (Tasks 17–22). New components, simplified `World3D`.
5. **Phase E — verification** (Tasks 23–24). E2E + manual demo.

Each phase ends with the system in a coherent (even if temporarily incomplete) state.

---

## Phase A — Schema + pure logic

### Task 1: Add `Site`, `Plot`, `Entrance` models

**Files:**
- Modify: `backend/core/world_spec.py`
- Test: `backend/tests/unit/test_site.py` (new)

- [ ] **Step 1: Write the failing test**

Create `backend/tests/unit/test_site.py`:

```python
import pytest
from pydantic import ValidationError
from core.world_spec import Plot, Entrance, Site


def test_plot_defaults():
    p = Plot()
    assert p.width == 100.0
    assert p.depth == 100.0
    assert p.groundColor == "#5a7c3a"


def test_entrance_validates_positive_dimensions():
    with pytest.raises(ValidationError):
        Entrance(wall="south", offset=10, width=0, height=2.2)
    with pytest.raises(ValidationError):
        Entrance(wall="south", offset=-1, width=1.6, height=2.2)


def test_site_construction():
    s = Site(
        buildingFootprint=[40.0, 25.0],
        buildingAnchor=[30.0, 37.0],
        entrance=Entrance(wall="south", offset=20.0),
    )
    assert s.plot.width == 100.0
    assert s.buildingFootprint == [40.0, 25.0]
    assert s.entrance.width == 1.6  # default
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && pytest tests/unit/test_site.py -v
```

Expected: FAIL with `ImportError` (Plot/Entrance/Site not defined).

- [ ] **Step 3: Add the models**

In `backend/core/world_spec.py`, after the `Wall = Literal[...]` line, add:

```python
class Plot(BaseModel):
    width: float = Field(default=100.0, gt=0)
    depth: float = Field(default=100.0, gt=0)
    groundColor: str = "#5a7c3a"


class Entrance(BaseModel):
    wall: Wall
    offset: float = Field(ge=0)
    width: float = Field(default=1.6, gt=0)
    height: float = Field(default=2.2, gt=0)


class Site(BaseModel):
    plot: Plot = Field(default_factory=Plot)
    buildingFootprint: list[float]
    buildingAnchor: list[float]
    entrance: Entrance
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd backend && pytest tests/unit/test_site.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/core/world_spec.py backend/tests/unit/test_site.py
git commit -m "feat(site): add Plot, Entrance, Site Pydantic models"
```

---

### Task 2: Add `site` field to `WorldSpec`, remove `products` and Product fields

**Files:**
- Modify: `backend/core/world_spec.py`
- Test: `backend/tests/unit/test_world_spec.py` (existing)

- [ ] **Step 1: Find existing tests that reference removed fields**

```bash
cd backend && grep -rn "selectedProductId\|alternates\|\.products\|\.tint\|subtype" tests/ --include="*.py"
```

Note the lines for fixup later.

- [ ] **Step 2: Write the failing test**

Add to `backend/tests/unit/test_world_spec.py`:

```python
from core.world_spec import WorldSpec, FurnitureItem


def test_world_spec_has_site_field():
    spec = WorldSpec(worldId="x", prompt="test")
    assert spec.site is None
    assert not hasattr(spec, "products")


def test_furniture_item_no_product_fields():
    f = FurnitureItem(id="f1", roomId="r1", type="desk",
                     position=[0, 0, 0], size=[1, 1, 1])
    assert not hasattr(f, "selectedProductId")
    assert not hasattr(f, "alternates")
    assert not hasattr(f, "subtype")
    assert not hasattr(f, "tint")
```

- [ ] **Step 3: Run test to verify it fails**

```bash
cd backend && pytest tests/unit/test_world_spec.py::test_world_spec_has_site_field tests/unit/test_world_spec.py::test_furniture_item_no_product_fields -v
```

Expected: FAIL.

- [ ] **Step 4: Update the models**

In `backend/core/world_spec.py`:

Replace the `FurnitureItem` class with:

```python
class FurnitureItem(BaseModel):
    id: str
    roomId: str
    type: str
    position: list[float]
    rotation: float = 0.0
    size: list[float]
```

Delete the `Product` class entirely.

Replace `WorldSpec` with:

```python
class WorldSpec(BaseModel):
    worldId: str
    prompt: str
    intent: Optional[Intent] = None
    site: Optional[Site] = None
    blueprint: Optional[Blueprint] = None
    geometry: Optional[Geometry] = None
    lighting: Optional[Lighting] = None
    materials: Optional[Materials] = None
    furniture: list[FurnitureItem] = Field(default_factory=list)
    navigation: Optional[Navigation] = None
    cost: Optional[Cost] = None
```

Extend `GeometryPrimitive.type`:

```python
class GeometryPrimitive(BaseModel):
    type: Literal["floor", "wall", "ceiling", "stair", "exterior_wall", "roof", "ground"]
    # ... rest unchanged
```

- [ ] **Step 5: Fix referenced tests**

For each grep hit from Step 1, remove the reference. Specifically expect:
- `test_pricing.py` — currently passes Products dict; will be replaced in Task 6
- `test_world_spec.py` — remove any `selectedProductId`/`alternates` assertions
- `test_examples_load.py` — likely fine

Run full unit suite:

```bash
cd backend && pytest tests/unit -v
```

Fix anything that fails *because of removed fields* (not other reasons).

- [ ] **Step 6: Run new tests to verify they pass**

```bash
cd backend && pytest tests/unit/test_world_spec.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/core/world_spec.py backend/tests/unit/
git commit -m "feat(site): add WorldSpec.site, remove Product and product-related fields"
```

---

### Task 3: `derive_site_from_intent` helper

**Files:**
- Create: `backend/core/site.py`
- Test: `backend/tests/unit/test_site.py` (existing)

- [ ] **Step 1: Write the failing test**

Append to `backend/tests/unit/test_site.py`:

```python
from core.world_spec import Intent
from core.site import derive_site_from_intent


def test_derive_site_centers_building_on_plot():
    intent = Intent(buildingType="office", style="modern", floors=3,
                    vibe=["minimal"], sizeHint="medium")
    site = derive_site_from_intent(intent)
    assert site.plot.width == 100.0
    assert site.plot.depth == 100.0
    fw, fd = site.buildingFootprint
    ax, ay = site.buildingAnchor
    assert ax == (100 - fw) / 2
    assert ay == (100 - fd) / 2


def test_derive_site_size_hint_scales_footprint():
    small = derive_site_from_intent(Intent(buildingType="office", style="modern",
                                           floors=1, vibe=[], sizeHint="small"))
    large = derive_site_from_intent(Intent(buildingType="office", style="modern",
                                           floors=1, vibe=[], sizeHint="large"))
    assert large.buildingFootprint[0] > small.buildingFootprint[0]


def test_derive_site_entrance_on_south_wall():
    site = derive_site_from_intent(Intent(buildingType="office", style="modern",
                                          floors=1, vibe=[], sizeHint="medium"))
    assert site.entrance.wall == "south"
    assert 0 < site.entrance.offset < site.buildingFootprint[0]


def test_derive_site_leaves_grass_margin():
    site = derive_site_from_intent(Intent(buildingType="office", style="modern",
                                          floors=1, vibe=[], sizeHint="large"))
    fw, fd = site.buildingFootprint
    ax, ay = site.buildingAnchor
    assert ax >= 10  # 10m margin
    assert ay >= 10
    assert ax + fw <= 90
    assert ay + fd <= 90
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && pytest tests/unit/test_site.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'core.site'`.

- [ ] **Step 3: Implement `derive_site_from_intent`**

Create `backend/core/site.py`:

```python
from .world_spec import Intent, Site, Plot, Entrance

PLOT_SIZE = 100.0
MARGIN = 10.0


def derive_site_from_intent(intent: Intent) -> Site:
    """Pure-code Site computation from Intent.

    Building is centered on a fixed 100x100m plot. Footprint scales with
    sizeHint; clamped so 10m of grass remains on every side. Entrance is
    on the south wall, centered.
    """
    bonus = {"small": 0, "medium": 10, "large": 20}.get(intent.sizeHint, 10)
    fw = min(20.0 + bonus, PLOT_SIZE - 2 * MARGIN)
    fd = min(15.0 + bonus, PLOT_SIZE - 2 * MARGIN)

    ax = (PLOT_SIZE - fw) / 2
    ay = (PLOT_SIZE - fd) / 2

    return Site(
        plot=Plot(),
        buildingFootprint=[fw, fd],
        buildingAnchor=[ax, ay],
        entrance=Entrance(wall="south", offset=fw / 2),
    )
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd backend && pytest tests/unit/test_site.py -v
```

Expected: PASS (all four `derive_site_*` tests).

- [ ] **Step 5: Commit**

```bash
git add backend/core/site.py backend/tests/unit/test_site.py
git commit -m "feat(site): derive_site_from_intent — center building, south entrance"
```

---

### Task 4: Site validators (footprint + entrance landing)

**Files:**
- Create: `backend/core/site_validators.py`
- Test: `backend/tests/unit/test_site.py` (existing)

- [ ] **Step 1: Write the failing test**

Append to `backend/tests/unit/test_site.py`:

```python
from core.world_spec import (Blueprint, Floor, Room, Door, WorldSpec)
from core.site_validators import check_site_constraints


def _spec_with(site, floors):
    return WorldSpec(worldId="x", prompt="t", site=site,
                     blueprint=Blueprint(floors=floors))


def _good_site():
    return derive_site_from_intent(
        Intent(buildingType="office", style="modern", floors=1,
               vibe=[], sizeHint="medium"))


def test_site_validator_accepts_room_inside_footprint():
    site = _good_site()
    fw, fd = site.buildingFootprint
    floor = Floor(level=0, ceilingHeight=3.0, rooms=[
        Room(id="lobby", type="lobby", x=0, y=0, width=fw, depth=fd,
             doors=[Door(wall="south", offset=site.entrance.offset, width=1.6)])
    ])
    spec = _spec_with(site, [floor])
    errors = check_site_constraints(spec)
    assert errors == []


def test_site_validator_rejects_room_outside_footprint():
    site = _good_site()
    fw, fd = site.buildingFootprint
    floor = Floor(level=0, ceilingHeight=3.0, rooms=[
        Room(id="lobby", type="lobby", x=0, y=0, width=fw + 5, depth=fd,
             doors=[Door(wall="south", offset=site.entrance.offset, width=1.6)])
    ])
    spec = _spec_with(site, [floor])
    errors = check_site_constraints(spec)
    assert any("outside building footprint" in e for e in errors)


def test_site_validator_rejects_missing_entrance_door():
    site = _good_site()
    fw, fd = site.buildingFootprint
    floor = Floor(level=0, ceilingHeight=3.0, rooms=[
        Room(id="lobby", type="lobby", x=0, y=0, width=fw, depth=fd,
             doors=[Door(wall="north", offset=2, width=1.6)])
    ])
    spec = _spec_with(site, [floor])
    errors = check_site_constraints(spec)
    assert any("entrance" in e.lower() for e in errors)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && pytest tests/unit/test_site.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'core.site_validators'`.

- [ ] **Step 3: Implement `check_site_constraints`**

Create `backend/core/site_validators.py`:

```python
from .world_spec import WorldSpec


def check_site_constraints(spec: WorldSpec) -> list[str]:
    """Validate Site-level invariants: rooms inside footprint, entrance landing."""
    errors: list[str] = []
    if spec.site is None or spec.blueprint is None:
        return errors

    fw, fd = spec.site.buildingFootprint
    for fl in spec.blueprint.floors:
        for r in fl.rooms:
            if r.x < 0 or r.y < 0 or r.x + r.width > fw + 1e-6 or r.y + r.depth > fd + 1e-6:
                errors.append(
                    f"room {r.id} (level {fl.level}) is outside building footprint "
                    f"{fw}x{fd}"
                )

    ground = next((f for f in spec.blueprint.floors if f.level == 0), None)
    if ground is None:
        errors.append("no ground floor (level 0)")
        return errors

    e = spec.site.entrance
    matched = False
    for r in ground.rooms:
        for d in r.doors:
            if d.wall != e.wall:
                continue
            door_min = d.offset
            door_max = d.offset + d.width
            ent_min = e.offset - e.width / 2
            ent_max = e.offset + e.width / 2
            # door must overlap entrance opening
            if door_max >= ent_min and door_min <= ent_max:
                if e.wall == "south" and abs(r.y) < 1e-6:
                    matched = True
                elif e.wall == "north" and abs((r.y + r.depth) - fd) < 1e-6:
                    matched = True
                elif e.wall == "west" and abs(r.x) < 1e-6:
                    matched = True
                elif e.wall == "east" and abs((r.x + r.width) - fw) < 1e-6:
                    matched = True
    if not matched:
        errors.append(
            f"no ground-floor room has a {e.wall} door overlapping entrance "
            f"at offset {e.offset}"
        )

    return errors
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd backend && pytest tests/unit/test_site.py -v
```

Expected: PASS (all site validator tests).

- [ ] **Step 5: Commit**

```bash
git add backend/core/site_validators.py backend/tests/unit/test_site.py
git commit -m "feat(site): site_validators — footprint + entrance landing checks"
```

---

### Task 5: Geometry — ground, exterior_wall, roof + anchor offset

**Files:**
- Modify: `backend/core/geometry.py`
- Test: `backend/tests/unit/test_geometry_envelope.py` (new)

- [ ] **Step 1: Write the failing test**

Create `backend/tests/unit/test_geometry_envelope.py`:

```python
from core.world_spec import (
    Blueprint, Floor, Room, Door, Site, Plot, Entrance, Intent
)
from core.site import derive_site_from_intent
from core.geometry import build_geometry


def _setup():
    intent = Intent(buildingType="office", style="modern", floors=2,
                    vibe=[], sizeHint="medium")
    site = derive_site_from_intent(intent)
    fw, fd = site.buildingFootprint
    floors = [
        Floor(level=0, ceilingHeight=3.0, rooms=[
            Room(id="lobby", type="lobby", x=0, y=0, width=fw, depth=fd,
                 doors=[Door(wall="south", offset=site.entrance.offset, width=1.6)])
        ]),
        Floor(level=1, ceilingHeight=3.0, rooms=[
            Room(id="offices", type="office", x=0, y=0, width=fw, depth=fd,
                 doors=[Door(wall="south", offset=2.0, width=1.0)])
        ]),
    ]
    bp = Blueprint(floors=floors)
    return site, bp


def test_geometry_includes_ground_primitive():
    site, bp = _setup()
    geo = build_geometry(bp, site)
    grounds = [p for p in geo.primitives if p.type == "ground"]
    assert len(grounds) == 1
    assert grounds[0].size[0] == site.plot.width
    assert grounds[0].size[2] == site.plot.depth


def test_exterior_walls_one_perimeter_per_floor():
    site, bp = _setup()
    geo = build_geometry(bp, site)
    ext = [p for p in geo.primitives if p.type == "exterior_wall"]
    # 4 walls × 2 floors
    assert len(ext) == 8
    walls_by_dir = {"north": 0, "south": 0, "east": 0, "west": 0}
    for p in ext:
        walls_by_dir[p.wall] += 1
    assert walls_by_dir == {"north": 2, "south": 2, "east": 2, "west": 2}


def test_ground_floor_south_wall_has_entrance_hole():
    site, bp = _setup()
    geo = build_geometry(bp, site)
    south_walls = [p for p in geo.primitives if p.type == "exterior_wall" and p.wall == "south"]
    ground_south = [p for p in south_walls if abs(p.position[1] - 1.5) < 0.5]
    assert len(ground_south) == 1
    assert len(ground_south[0].holes) == 1
    hole = ground_south[0].holes[0]
    assert abs(hole["width"] - site.entrance.width) < 1e-6


def test_upper_floor_south_wall_has_no_entrance_hole():
    site, bp = _setup()
    geo = build_geometry(bp, site)
    south_walls = [p for p in geo.primitives if p.type == "exterior_wall" and p.wall == "south"]
    upper = [p for p in south_walls if p.position[1] > 3.0]
    assert len(upper) == 1
    assert upper[0].holes == []


def test_roof_exists_above_top_floor():
    site, bp = _setup()
    geo = build_geometry(bp, site)
    roofs = [p for p in geo.primitives if p.type == "roof"]
    assert len(roofs) == 1
    # Above level 1 (top of 2 floors at 3m each = 6m)
    assert roofs[0].position[1] >= 6.0


def test_existing_primitives_offset_by_anchor():
    site, bp = _setup()
    geo = build_geometry(bp, site)
    floors = [p for p in geo.primitives if p.type == "floor"]
    assert floors
    # First floor's first room is at building-local (0,0); plot-world should be anchor
    expected_x = site.buildingAnchor[0] + bp.floors[0].rooms[0].width / 2
    assert abs(floors[0].position[0] - expected_x) < 1e-6
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && pytest tests/unit/test_geometry_envelope.py -v
```

Expected: FAIL with `TypeError: build_geometry() takes 1 positional argument but 2 were given`.

- [ ] **Step 3: Update `build_geometry`**

Replace the contents of `backend/core/geometry.py` with:

```python
"""Convert validated Blueprint + Site into 3D geometry primitives.

Coord mapping: blueprint (x, y) building-local -> plot-world by adding the
buildingAnchor; then plot-world -> scene (x, height_y, -y_p).
"""
from .world_spec import (
    Blueprint, Room, Stairs, Site, Geometry, GeometryPrimitive
)

WALL_THICKNESS = 0.1
EXTERIOR_WALL_THICKNESS = 0.2
ROOF_THICKNESS = 0.2


def _floor_y_offset(level: int, ceiling_height: float) -> float:
    return level * ceiling_height


def _floor_primitive(room: Room, level_y: float, ax: float, ay: float) -> GeometryPrimitive:
    cx = ax + room.x + room.width / 2
    cy = ay + room.y + room.depth / 2
    return GeometryPrimitive(
        type="floor",
        roomId=room.id,
        position=[cx, level_y, -cy],
        size=[room.width, 0.05, room.depth],
    )


def _ceiling_primitive(room: Room, level_y: float, ceiling_height: float,
                       ax: float, ay: float) -> GeometryPrimitive:
    cx = ax + room.x + room.width / 2
    cy = ay + room.y + room.depth / 2
    return GeometryPrimitive(
        type="ceiling",
        roomId=room.id,
        position=[cx, level_y + ceiling_height - 0.025, -cy],
        size=[room.width, 0.05, room.depth],
    )


def _wall_primitive(room: Room, wall: str, level_y: float, ceiling_height: float,
                    ax: float, ay: float) -> GeometryPrimitive:
    holes: list[dict] = []
    for d in room.doors:
        if d.wall == wall:
            holes.append({"offset": d.offset, "width": d.width, "height": 2.1, "bottom": 0.0})
    for w in room.windows:
        if w.wall == wall:
            holes.append({"offset": w.offset, "width": w.width, "height": w.height, "bottom": w.sill})

    if wall == "north":
        cx = ax + room.x + room.width / 2
        cz = -(ay + room.y + room.depth)
        size = [room.width, ceiling_height, WALL_THICKNESS]
    elif wall == "south":
        cx = ax + room.x + room.width / 2
        cz = -(ay + room.y)
        size = [room.width, ceiling_height, WALL_THICKNESS]
    elif wall == "west":
        cx = ax + room.x
        cz = -(ay + room.y + room.depth / 2)
        size = [WALL_THICKNESS, ceiling_height, room.depth]
    elif wall == "east":
        cx = ax + room.x + room.width
        cz = -(ay + room.y + room.depth / 2)
        size = [WALL_THICKNESS, ceiling_height, room.depth]
    else:
        raise ValueError(f"unknown wall {wall}")

    return GeometryPrimitive(
        type="wall",
        roomId=room.id,
        wall=wall,
        position=[cx, level_y + ceiling_height / 2, cz],
        size=size,
        rotation=0.0,
        holes=holes,
    )


def _stair_primitive(s: Stairs, level_y: float, ceiling_height: float,
                     ax: float, ay: float) -> GeometryPrimitive:
    cx = ax + s.x + s.width / 2
    cy = ay + s.y + s.depth / 2
    rot_map = {"north": 0.0, "south": 3.14159, "east": 1.5708, "west": -1.5708}
    return GeometryPrimitive(
        type="stair",
        roomId=s.id,
        position=[cx, level_y, -cy],
        size=[s.width, ceiling_height, s.depth],
        rotation=rot_map[s.direction],
    )


def _ground_primitive(site: Site) -> GeometryPrimitive:
    p = site.plot
    return GeometryPrimitive(
        type="ground",
        position=[p.width / 2, -0.025, -p.depth / 2],
        size=[p.width, 0.05, p.depth],
    )


def _exterior_walls_for_floor(site: Site, level: int, level_y: float,
                              ceiling_height: float) -> list[GeometryPrimitive]:
    fw, fd = site.buildingFootprint
    ax, ay = site.buildingAnchor
    e = site.entrance

    def hole_for(wall: str) -> list[dict]:
        if level != 0 or wall != e.wall:
            return []
        return [{
            "offset": e.offset,
            "width": e.width,
            "height": e.height,
            "bottom": 0.0,
        }]

    walls: list[GeometryPrimitive] = []
    # south
    walls.append(GeometryPrimitive(
        type="exterior_wall", wall="south",
        position=[ax + fw / 2, level_y + ceiling_height / 2, -ay],
        size=[fw, ceiling_height, EXTERIOR_WALL_THICKNESS],
        holes=hole_for("south"),
    ))
    # north
    walls.append(GeometryPrimitive(
        type="exterior_wall", wall="north",
        position=[ax + fw / 2, level_y + ceiling_height / 2, -(ay + fd)],
        size=[fw, ceiling_height, EXTERIOR_WALL_THICKNESS],
        holes=hole_for("north"),
    ))
    # west
    walls.append(GeometryPrimitive(
        type="exterior_wall", wall="west",
        position=[ax, level_y + ceiling_height / 2, -(ay + fd / 2)],
        size=[EXTERIOR_WALL_THICKNESS, ceiling_height, fd],
        holes=hole_for("west"),
    ))
    # east
    walls.append(GeometryPrimitive(
        type="exterior_wall", wall="east",
        position=[ax + fw, level_y + ceiling_height / 2, -(ay + fd / 2)],
        size=[EXTERIOR_WALL_THICKNESS, ceiling_height, fd],
        holes=hole_for("east"),
    ))
    return walls


def _roof_primitive(site: Site, top_y: float) -> GeometryPrimitive:
    fw, fd = site.buildingFootprint
    ax, ay = site.buildingAnchor
    return GeometryPrimitive(
        type="roof",
        position=[ax + fw / 2, top_y + ROOF_THICKNESS / 2, -(ay + fd / 2)],
        size=[fw + 0.2, ROOF_THICKNESS, fd + 0.2],
    )


def build_geometry(bp: Blueprint, site: Site) -> Geometry:
    prims: list[GeometryPrimitive] = []
    ax, ay = site.buildingAnchor

    prims.append(_ground_primitive(site))

    top_y = 0.0
    for fl in bp.floors:
        level_y = _floor_y_offset(fl.level, fl.ceilingHeight)
        top_y = max(top_y, level_y + fl.ceilingHeight)
        for r in fl.rooms:
            prims.append(_floor_primitive(r, level_y, ax, ay))
            prims.append(_ceiling_primitive(r, level_y, fl.ceilingHeight, ax, ay))
            for w in ("north", "south", "east", "west"):
                prims.append(_wall_primitive(r, w, level_y, fl.ceilingHeight, ax, ay))
        for s in fl.stairs:
            prims.append(_stair_primitive(s, level_y, fl.ceilingHeight, ax, ay))
        prims.extend(_exterior_walls_for_floor(site, fl.level, level_y, fl.ceilingHeight))

    prims.append(_roof_primitive(site, top_y))

    return Geometry(primitives=prims)
```

- [ ] **Step 4: Run new test to verify it passes**

```bash
cd backend && pytest tests/unit/test_geometry_envelope.py -v
```

Expected: PASS (all six tests).

- [ ] **Step 5: Run existing geometry test suite — expect failures**

```bash
cd backend && pytest tests/unit/test_geometry.py -v
```

Likely FAILS because `build_geometry(bp)` calls now need a site argument. **Update existing tests:** for each call to `build_geometry(bp)`, change to `build_geometry(bp, derive_site_from_intent(Intent(...)))` or construct a minimal `Site` directly. Add this import: `from core.site import derive_site_from_intent` and `from core.world_spec import Intent`.

Re-run:

```bash
cd backend && pytest tests/unit/test_geometry.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/core/geometry.py backend/tests/unit/test_geometry_envelope.py backend/tests/unit/test_geometry.py
git commit -m "feat(geometry): ground/exterior_wall/roof primitives + anchor offset"
```

---

### Task 6: Pricing — flat $/sqm

**Files:**
- Modify: `backend/core/pricing.py`
- Test: `backend/tests/unit/test_pricing_sqm.py` (new)
- Test: `backend/tests/unit/test_pricing.py` (existing — update or replace)

- [ ] **Step 1: Write the failing test**

Create `backend/tests/unit/test_pricing_sqm.py`:

```python
from core.world_spec import WorldSpec, Blueprint, Floor, Room, Door
from core.pricing import compute_cost, COST_PER_SQM


def _spec(rooms_per_floor):
    floors = []
    for level, rooms in enumerate(rooms_per_floor):
        floors.append(Floor(level=level, ceilingHeight=3.0, rooms=rooms))
    return WorldSpec(worldId="x", prompt="t", blueprint=Blueprint(floors=floors))


def test_pricing_single_room_one_floor():
    rooms = [Room(id="r1", type="office", x=0, y=0, width=10, depth=5,
                  doors=[Door(wall="south", offset=2, width=1)])]
    spec = _spec([rooms])
    cost = compute_cost(spec)
    assert cost.total == 10 * 5 * COST_PER_SQM
    assert cost.byRoom == {"r1": 10 * 5 * COST_PER_SQM}


def test_pricing_multiroom_multifloor():
    rooms_lvl0 = [Room(id="lobby", type="lobby", x=0, y=0, width=8, depth=4,
                       doors=[Door(wall="south", offset=2, width=1)])]
    rooms_lvl1 = [Room(id="off1", type="office", x=0, y=0, width=4, depth=4,
                       doors=[Door(wall="north", offset=1, width=1)]),
                  Room(id="off2", type="office", x=4, y=0, width=4, depth=4,
                       doors=[Door(wall="north", offset=1, width=1)])]
    spec = _spec([rooms_lvl0, rooms_lvl1])
    cost = compute_cost(spec)
    assert cost.total == (8*4 + 4*4 + 4*4) * COST_PER_SQM
    assert len(cost.byRoom) == 3


def test_pricing_no_blueprint_returns_zero():
    spec = WorldSpec(worldId="x", prompt="t")
    cost = compute_cost(spec)
    assert cost.total == 0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && pytest tests/unit/test_pricing_sqm.py -v
```

Expected: FAIL with `ImportError` on `COST_PER_SQM` or signature mismatch.

- [ ] **Step 3: Replace `compute_cost`**

Replace the entire contents of `backend/core/pricing.py` with:

```python
from .world_spec import WorldSpec, Cost

COST_PER_SQM = 1500.0


def compute_cost(spec: WorldSpec) -> Cost:
    by_room: dict[str, float] = {}
    total = 0.0
    if spec.blueprint:
        for fl in spec.blueprint.floors:
            for r in fl.rooms:
                area = r.width * r.depth
                cost = area * COST_PER_SQM
                by_room[r.id] = cost
                total += cost
    return Cost(total=total, byRoom=by_room)
```

- [ ] **Step 4: Delete or rewrite the old pricing test**

```bash
cd backend && rm tests/unit/test_pricing.py
```

(All the per-product price logic it tested is gone.)

- [ ] **Step 5: Run test to verify it passes**

```bash
cd backend && pytest tests/unit/test_pricing_sqm.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/core/pricing.py backend/tests/unit/test_pricing_sqm.py
git rm backend/tests/unit/test_pricing.py
git commit -m "feat(pricing): flat \$1500/sqm cost model"
```

---

### Task 7: Room templates + `apply_template`

**Files:**
- Create: `backend/core/room_templates.py`
- Test: `backend/tests/unit/test_room_templates.py` (new)

- [ ] **Step 1: Write the failing test**

Create `backend/tests/unit/test_room_templates.py`:

```python
from core.world_spec import Room, Door
from core.room_templates import (
    ROOM_FURNITURE, FurnitureTemplate, apply_template
)


def test_every_known_room_type_has_template():
    expected = {"office", "conference_room", "lobby", "breakroom",
                "corridor", "restroom", "stairwell", "reception",
                "bedroom", "kitchen", "living_room", "bathroom", "default"}
    assert expected.issubset(set(ROOM_FURNITURE.keys()))


def test_office_template_produces_desk_and_chair():
    room = Room(id="o1", type="office", x=0, y=0, width=4, depth=4,
                doors=[Door(wall="south", offset=2, width=1)])
    items = apply_template(room, level_y=0.0, anchor=(30.0, 30.0))
    types = [i.type for i in items]
    assert "desk" in types
    assert "office_chair" in types


def test_apply_template_skips_oversized_furniture():
    # tiny room: should skip a desk that needs >1m
    room = Room(id="tiny", type="office", x=0, y=0, width=0.5, depth=0.5,
                doors=[Door(wall="south", offset=0.1, width=0.3)])
    items = apply_template(room, level_y=0.0, anchor=(0.0, 0.0))
    assert items == []


def test_apply_template_offsets_by_anchor():
    room = Room(id="o1", type="office", x=2.0, y=3.0, width=4, depth=4,
                doors=[Door(wall="south", offset=2, width=1)])
    items = apply_template(room, level_y=0.0, anchor=(30.0, 50.0))
    desks = [i for i in items if i.type == "desk"]
    assert desks
    # desk position x should include anchor + room.x
    assert desks[0].position[0] > 32.0


def test_apply_template_unknown_type_returns_empty():
    room = Room(id="weird", type="alien_lab", x=0, y=0, width=4, depth=4,
                doors=[Door(wall="south", offset=2, width=1)])
    items = apply_template(room, level_y=0.0, anchor=(0.0, 0.0))
    assert items == []
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && pytest tests/unit/test_room_templates.py -v
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement `room_templates.py`**

Create `backend/core/room_templates.py`:

```python
from pydantic import BaseModel
from .world_spec import Room, FurnitureItem


class FurnitureTemplate(BaseModel):
    type: str
    room_offset: list[float]   # [x, y] in meters from room SW corner
    size: list[float]          # [w, h, d]
    rotation: float = 0.0


ROOM_FURNITURE: dict[str, list[FurnitureTemplate]] = {
    "office": [
        FurnitureTemplate(type="desk", room_offset=[1.0, 1.0],
                          size=[1.4, 0.75, 0.7]),
        FurnitureTemplate(type="office_chair", room_offset=[1.7, 2.0],
                          size=[0.6, 1.1, 0.6], rotation=3.14159),
    ],
    "conference_room": [
        FurnitureTemplate(type="conference_table", room_offset=[1.5, 1.5],
                          size=[2.4, 0.75, 1.0]),
        FurnitureTemplate(type="office_chair", room_offset=[1.0, 1.0],
                          size=[0.6, 1.1, 0.6]),
        FurnitureTemplate(type="office_chair", room_offset=[1.0, 2.5],
                          size=[0.6, 1.1, 0.6]),
        FurnitureTemplate(type="office_chair", room_offset=[3.5, 1.0],
                          size=[0.6, 1.1, 0.6], rotation=3.14159),
        FurnitureTemplate(type="office_chair", room_offset=[3.5, 2.5],
                          size=[0.6, 1.1, 0.6], rotation=3.14159),
    ],
    "lobby": [
        FurnitureTemplate(type="reception_desk", room_offset=[2.0, 2.0],
                          size=[2.5, 1.0, 0.8]),
        FurnitureTemplate(type="couch", room_offset=[1.0, 4.0],
                          size=[2.2, 0.8, 0.9]),
    ],
    "reception": [
        FurnitureTemplate(type="reception_desk", room_offset=[1.5, 1.5],
                          size=[2.5, 1.0, 0.8]),
    ],
    "breakroom": [
        FurnitureTemplate(type="table", room_offset=[1.5, 1.5],
                          size=[1.5, 0.75, 1.0]),
        FurnitureTemplate(type="chair", room_offset=[1.5, 0.6],
                          size=[0.5, 1.0, 0.5]),
        FurnitureTemplate(type="chair", room_offset=[1.5, 3.1],
                          size=[0.5, 1.0, 0.5], rotation=3.14159),
    ],
    "corridor": [],
    "restroom": [],
    "stairwell": [],
    "bedroom": [
        FurnitureTemplate(type="bed", room_offset=[1.0, 1.0],
                          size=[2.0, 0.5, 1.5]),
    ],
    "kitchen": [
        FurnitureTemplate(type="table", room_offset=[1.5, 1.5],
                          size=[1.2, 0.75, 0.8]),
    ],
    "living_room": [
        FurnitureTemplate(type="couch", room_offset=[1.0, 1.0],
                          size=[2.2, 0.8, 0.9]),
    ],
    "bathroom": [],
    "default": [],
}


def apply_template(room: Room, level_y: float,
                   anchor: tuple[float, float]) -> list[FurnitureItem]:
    """Pure-code: produce FurnitureItems for a room from its type template.

    `anchor` is buildingAnchor (plot-world offset). Room positions are
    building-local. Output positions are plot-world. Items whose template
    offset+size would exceed room dimensions are skipped.
    """
    template = ROOM_FURNITURE.get(room.type, [])
    items: list[FurnitureItem] = []
    ax, ay = anchor
    for i, t in enumerate(template):
        ox, oy = t.room_offset
        w, _, d = t.size
        if ox + w > room.width or oy + d > room.depth:
            continue
        # plot-world center of the item
        px = ax + room.x + ox + w / 2
        py = ay + room.y + oy + d / 2
        items.append(FurnitureItem(
            id=f"{room.id}-{t.type}-{i}",
            roomId=room.id,
            type=t.type,
            position=[px, level_y, -py],
            rotation=t.rotation,
            size=t.size,
        ))
    return items
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd backend && pytest tests/unit/test_room_templates.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/core/room_templates.py backend/tests/unit/test_room_templates.py
git commit -m "feat(templates): room_type -> furniture template lookup (pure code)"
```

---

## Phase B — Agents

### Task 8: `intent_parser` — also derive Site

**Files:**
- Modify: `backend/agents/intent_parser.py`
- Test: `backend/tests/unit/test_intent_parser.py` (existing — extend)

- [ ] **Step 1: Write the failing test**

Append to `backend/tests/unit/test_intent_parser.py` (create if needed):

```python
def test_intent_parser_writes_site_from_intent(monkeypatch):
    from agents import intent_parser
    from core.world_spec import WorldSpec, Intent
    fake_intent = Intent(buildingType="office", style="modern", floors=2,
                         vibe=[], sizeHint="medium")
    monkeypatch.setattr("agents.intent_parser.structured",
                        lambda *a, **kw: fake_intent)
    spec = WorldSpec(worldId="x", prompt="an office")
    out = intent_parser.run(spec)
    assert out.site is not None
    assert out.site.entrance.wall == "south"
    assert out.site.plot.width == 100.0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && pytest tests/unit/test_intent_parser.py::test_intent_parser_writes_site_from_intent -v
```

Expected: FAIL — `out.site` is None.

- [ ] **Step 3: Update `intent_parser.run`**

Replace `backend/agents/intent_parser.py` with:

```python
from core.world_spec import WorldSpec, Intent
from core.gemini_client import structured
from core.prompts.intent_parser import SYSTEM, USER_TMPL
from core.site import derive_site_from_intent


def run(spec: WorldSpec) -> WorldSpec:
    intent = structured(USER_TMPL.format(prompt=spec.prompt), Intent, system=SYSTEM)
    spec.intent = intent
    spec.site = derive_site_from_intent(intent)
    return spec
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd backend && pytest tests/unit/test_intent_parser.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/agents/intent_parser.py backend/tests/unit/test_intent_parser.py
git commit -m "feat(intent): derive Site after picking Intent"
```

---

### Task 9: `blueprint_architect` prompt — footprint constraint + office examples

**Files:**
- Modify: `backend/core/prompts/blueprint_architect.py`
- Modify: `backend/agents/blueprint_architect.py`

- [ ] **Step 1: Read the current prompt**

```bash
cat backend/core/prompts/blueprint_architect.py
```

Note current `SYSTEM` and `USER_TMPL` placeholders.

- [ ] **Step 2: Update `USER_TMPL` to take footprint**

In `backend/core/prompts/blueprint_architect.py`, modify `USER_TMPL` so it includes:

```
The building footprint is {footprint_w} m × {footprint_d} m.
ALL rooms (on every floor) MUST fit inside this footprint.
The ground floor MUST contain a room with a SOUTH-facing door at offset {entrance_offset} m
(width {entrance_width} m). This is the building entrance.
```

And update `SYSTEM` to mention office room types: `lobby, corridor, office, conference_room, breakroom, restroom, stairwell, reception` along with the existing residential types.

Add one example near the end of `SYSTEM` (or in `core/prompts/examples/`) showing a 3-floor office:

```
Example for "a 3-story tech startup office" (footprint 40×25):
{
  "gridSize": 0.5,
  "floors": [
    {"level": 0, "ceilingHeight": 3.0, "rooms": [
      {"id": "lobby", "type": "lobby", "x": 0, "y": 0, "width": 40, "depth": 8,
       "doors": [{"wall": "south", "offset": 20, "width": 1.6},
                 {"wall": "north", "offset": 20, "width": 1.5}]},
      {"id": "corr0", "type": "corridor", "x": 0, "y": 8, "width": 40, "depth": 2,
       "doors": [{"wall": "south", "offset": 20, "width": 1.5},
                 {"wall": "north", "offset": 5, "width": 1},
                 {"wall": "north", "offset": 35, "width": 1}]},
      {"id": "off0a", "type": "office", "x": 0, "y": 10, "width": 10, "depth": 15,
       "doors": [{"wall": "south", "offset": 5, "width": 1}]},
      {"id": "conf0", "type": "conference_room", "x": 10, "y": 10, "width": 20, "depth": 15,
       "doors": [{"wall": "south", "offset": 10, "width": 1}]},
      {"id": "off0b", "type": "office", "x": 30, "y": 10, "width": 10, "depth": 15,
       "doors": [{"wall": "south", "offset": 5, "width": 1}]}
    ], "stairs": [{"id": "stair", "x": 18, "y": 0.5, "width": 2, "depth": 4,
                   "direction": "north", "toLevel": 1}]},
    {"level": 1, "ceilingHeight": 3.0, "rooms": [...similar layout...],
     "stairs": [{"id": "stair", "x": 18, "y": 0.5, "width": 2, "depth": 4,
                 "direction": "north", "toLevel": 0}]},
    {"level": 2, "ceilingHeight": 3.0, "rooms": [...]}
  ]
}
```

- [ ] **Step 3: Update `blueprint_architect.run`**

Modify `backend/agents/blueprint_architect.py`:

```python
import json
from core.world_spec import WorldSpec, Blueprint
from core.gemini_client import structured
from core.prompts.blueprint_architect import SYSTEM, USER_TMPL


def run(spec: WorldSpec) -> WorldSpec:
    assert spec.intent is not None
    assert spec.site is not None
    fw, fd = spec.site.buildingFootprint
    user = USER_TMPL.format(
        prompt=spec.prompt,
        building_type=spec.intent.buildingType,
        style=spec.intent.style,
        floors=spec.intent.floors,
        size_hint=spec.intent.sizeHint,
        footprint_w=fw,
        footprint_d=fd,
        entrance_offset=spec.site.entrance.offset,
        entrance_width=spec.site.entrance.width,
    )
    spec.blueprint = structured(user, Blueprint, system=SYSTEM)
    return spec
```

(Adapt the `format(...)` keys to match the actual placeholder names in `USER_TMPL`.)

- [ ] **Step 4: Run blueprint architect unit test**

```bash
cd backend && pytest tests/unit/test_blueprint_architect.py -v
```

Expected: PASS (the unit test mocks Gemini and just checks the call shape; if it fails because of new format keys, update the test mocks accordingly).

- [ ] **Step 5: Commit**

```bash
git add backend/core/prompts/blueprint_architect.py backend/agents/blueprint_architect.py backend/tests/unit/test_blueprint_architect.py
git commit -m "feat(blueprint): footprint constraint + office room types in prompt"
```

---

### Task 10: `compliance_critic` — call site validators

**Files:**
- Modify: `backend/agents/compliance_critic.py`
- Test: `backend/tests/unit/test_validators.py` (existing) or new

- [ ] **Step 1: Write the failing test**

Add to `backend/tests/unit/test_validators.py`:

```python
import pytest
from core.world_spec import (WorldSpec, Blueprint, Floor, Room, Door, Intent)
from core.site import derive_site_from_intent
from agents.compliance_critic import run as critic_run, ComplianceError


def test_critic_rejects_room_outside_footprint():
    intent = Intent(buildingType="office", style="modern", floors=1,
                    vibe=[], sizeHint="medium")
    site = derive_site_from_intent(intent)
    fw, fd = site.buildingFootprint
    bp = Blueprint(floors=[Floor(level=0, ceilingHeight=3.0, rooms=[
        Room(id="big", type="office", x=0, y=0, width=fw + 50, depth=fd,
             doors=[Door(wall="south", offset=1, width=1)])])])
    spec = WorldSpec(worldId="x", prompt="t", intent=intent, site=site, blueprint=bp)
    with pytest.raises(ComplianceError):
        critic_run(spec)


def test_critic_passes_with_valid_site():
    intent = Intent(buildingType="office", style="modern", floors=1,
                    vibe=[], sizeHint="medium")
    site = derive_site_from_intent(intent)
    fw, fd = site.buildingFootprint
    bp = Blueprint(floors=[Floor(level=0, ceilingHeight=3.0, rooms=[
        Room(id="lobby", type="lobby", x=0, y=0, width=fw, depth=fd,
             doors=[Door(wall="south", offset=site.entrance.offset, width=1.6)])])])
    spec = WorldSpec(worldId="x", prompt="t", intent=intent, site=site, blueprint=bp)
    out = critic_run(spec)
    assert out is spec
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && pytest tests/unit/test_validators.py::test_critic_rejects_room_outside_footprint -v
```

Expected: FAIL — current critic doesn't check site constraints.

- [ ] **Step 3: Update `compliance_critic`**

Replace `backend/agents/compliance_critic.py` with:

```python
from core.world_spec import WorldSpec
from core.validators import validate_blueprint
from core.site_validators import check_site_constraints


class ComplianceError(RuntimeError):
    pass


def run(spec: WorldSpec) -> WorldSpec:
    if spec.blueprint is None:
        raise ValueError("compliance_critic requires blueprint")
    report = validate_blueprint(spec.blueprint)
    errors = list(report.errors)
    if spec.site is not None:
        errors.extend(check_site_constraints(spec))
    if errors:
        raise ComplianceError("; ".join(errors))
    return spec
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend && pytest tests/unit/test_validators.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/agents/compliance_critic.py backend/tests/unit/test_validators.py
git commit -m "feat(critic): include site constraint checks"
```

---

### Task 11: `geometry_builder`, `pricing_estimator`, `navigation_planner` — new signatures

**Files:**
- Modify: `backend/agents/geometry_builder.py`
- Modify: `backend/agents/pricing_estimator.py`
- Modify: `backend/agents/navigation_planner.py`
- Modify: `backend/core/navigation.py`
- Test: `backend/tests/unit/test_navigation_site.py` (new)

- [ ] **Step 1: Write the failing test for navigation**

Create `backend/tests/unit/test_navigation_site.py`:

```python
from core.world_spec import WorldSpec, Intent, Blueprint, Floor, Room, Door
from core.site import derive_site_from_intent
from core.navigation import compute_navigation


def test_spawn_is_on_grass_in_front_of_entrance():
    intent = Intent(buildingType="office", style="modern", floors=1,
                    vibe=[], sizeHint="medium")
    site = derive_site_from_intent(intent)
    spec = WorldSpec(worldId="x", prompt="t", intent=intent, site=site)
    nav = compute_navigation(spec)
    sx, sy_height, sz = nav.spawnPoint
    # spawn is in plot coords; should be 3m south of entrance, on grass
    expected_x = site.buildingAnchor[0] + site.entrance.offset
    expected_z = -(site.buildingAnchor[1] - 3.0)
    assert abs(sx - expected_x) < 1e-6
    assert abs(sz - expected_z) < 1e-6
    assert sy_height == 1.7
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && pytest tests/unit/test_navigation_site.py -v
```

Expected: FAIL — `compute_navigation` takes a `Blueprint`, not a `WorldSpec`.

- [ ] **Step 3: Update `core/navigation.py`**

Replace contents:

```python
from .world_spec import WorldSpec, Navigation


def compute_navigation(spec: WorldSpec) -> Navigation:
    """Spawn 3m south of the building entrance, on the grass, looking north."""
    if spec.site is None:
        return Navigation(spawnPoint=[50.0, 1.7, -50.0])
    s = spec.site
    spawn_x = s.buildingAnchor[0] + s.entrance.offset
    spawn_y_plot = s.buildingAnchor[1] - 3.0
    return Navigation(
        spawnPoint=[spawn_x, 1.7, -spawn_y_plot],
        walkableMeshIds=[],
        stairColliders=[],
    )
```

- [ ] **Step 4: Update `agents/navigation_planner.py`**

Replace contents:

```python
from core.world_spec import WorldSpec
from core.navigation import compute_navigation


def run(spec: WorldSpec) -> WorldSpec:
    spec.navigation = compute_navigation(spec)
    return spec
```

- [ ] **Step 5: Update `agents/geometry_builder.py`**

```python
from core.world_spec import WorldSpec
from core.geometry import build_geometry


def run(spec: WorldSpec) -> WorldSpec:
    assert spec.blueprint is not None and spec.site is not None
    spec.geometry = build_geometry(spec.blueprint, spec.site)
    return spec
```

- [ ] **Step 6: Update `agents/pricing_estimator.py`**

```python
from core.world_spec import WorldSpec
from core.pricing import compute_cost


def run(spec: WorldSpec) -> WorldSpec:
    spec.cost = compute_cost(spec)
    return spec
```

- [ ] **Step 7: Run all unit tests — fix any callers**

```bash
cd backend && pytest tests/unit -v
```

Update any failing tests that use old signatures (`compute_navigation(bp)` → `compute_navigation(spec)`, etc.).

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add backend/agents/geometry_builder.py backend/agents/pricing_estimator.py backend/agents/navigation_planner.py backend/core/navigation.py backend/tests/unit/test_navigation_site.py backend/tests/unit/test_navigation.py
git commit -m "feat(agents): geometry/pricing/navigation use Site-aware signatures"
```

---

### Task 12: `furniture_planner` — pure code via templates

**Files:**
- Modify: `backend/agents/furniture_planner.py`
- Test: `backend/tests/unit/test_furniture_planner.py` (new)

- [ ] **Step 1: Write the failing test**

Create `backend/tests/unit/test_furniture_planner.py`:

```python
from core.world_spec import (WorldSpec, Intent, Blueprint, Floor, Room, Door)
from core.site import derive_site_from_intent
from agents.furniture_planner import run as planner_run


def _spec_with_offices():
    intent = Intent(buildingType="office", style="modern", floors=1,
                    vibe=[], sizeHint="medium")
    site = derive_site_from_intent(intent)
    fw, fd = site.buildingFootprint
    bp = Blueprint(floors=[Floor(level=0, ceilingHeight=3.0, rooms=[
        Room(id="off1", type="office", x=0, y=0, width=4, depth=4,
             doors=[Door(wall="south", offset=2, width=1)]),
        Room(id="conf1", type="conference_room", x=4, y=0, width=6, depth=5,
             doors=[Door(wall="south", offset=2, width=1)]),
    ])])
    return WorldSpec(worldId="x", prompt="t", intent=intent,
                     site=site, blueprint=bp)


def test_furniture_planner_produces_items_per_room():
    spec = _spec_with_offices()
    out = planner_run(spec)
    assert any(f.type == "desk" and f.roomId == "off1" for f in out.furniture)
    assert any(f.type == "conference_table" and f.roomId == "conf1" for f in out.furniture)


def test_furniture_planner_no_llm_call_required():
    # If furniture_planner.run still tried to call structured(), this would
    # fail because we haven't mocked the gemini client. The test should pass
    # without any gemini env vars set.
    spec = _spec_with_offices()
    planner_run(spec)  # must not raise


def test_furniture_planner_positions_in_plot_world():
    spec = _spec_with_offices()
    out = planner_run(spec)
    desk = next(f for f in out.furniture if f.type == "desk")
    # building anchor offsets desk position by anchor[0] (>= 30 for medium plot)
    assert desk.position[0] > 20
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && pytest tests/unit/test_furniture_planner.py -v
```

Expected: FAIL — current planner makes Gemini calls.

- [ ] **Step 3: Replace `furniture_planner.run`**

Replace `backend/agents/furniture_planner.py` with:

```python
from core.world_spec import WorldSpec, FurnitureItem
from core.room_templates import apply_template


def run(spec: WorldSpec) -> WorldSpec:
    assert spec.blueprint is not None and spec.site is not None
    items: list[FurnitureItem] = []
    anchor = (spec.site.buildingAnchor[0], spec.site.buildingAnchor[1])
    for fl in spec.blueprint.floors:
        level_y = fl.level * fl.ceilingHeight
        for room in fl.rooms:
            items.extend(apply_template(room, level_y, anchor))
    spec.furniture = items
    return spec
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd backend && pytest tests/unit/test_furniture_planner.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/agents/furniture_planner.py backend/tests/unit/test_furniture_planner.py
git commit -m "feat(planner): pure-code furniture via room templates (no LLM)"
```

---

### Task 13: Orchestrator — drop `product_scout` and `style_matcher`

**Files:**
- Modify: `backend/agents/orchestrator.py`

- [ ] **Step 1: Read the current orchestrator**

Confirm `POST_STEPS` includes both `product_scout` and `style_matcher`.

- [ ] **Step 2: Edit `POST_STEPS`**

In `backend/agents/orchestrator.py`, change:

```python
POST_STEPS: list[tuple[str, Callable[[WorldSpec], WorldSpec]]] = [
    ("furniture_planner", furniture_planner.run),
    ("placement_validator", placement_validator.run),
    ("product_scout", product_scout.run),
    ("style_matcher", style_matcher.run),
    ("pricing_estimator", pricing_estimator.run),
    ("navigation_planner", navigation_planner.run),
]
```

to:

```python
POST_STEPS: list[tuple[str, Callable[[WorldSpec], WorldSpec]]] = [
    ("furniture_planner", furniture_planner.run),
    ("placement_validator", placement_validator.run),
    ("pricing_estimator", pricing_estimator.run),
    ("navigation_planner", navigation_planner.run),
]
```

Also remove `product_scout, style_matcher` from the import line at the top.

- [ ] **Step 3: Verify orchestrator still imports**

```bash
cd backend && python -c "from agents import orchestrator; print('ok')"
```

Expected: `ok`.

- [ ] **Step 4: Run the unit suite**

```bash
cd backend && pytest tests/unit -v
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/agents/orchestrator.py
git commit -m "feat(orchestrator): drop product_scout/style_matcher from pipeline"
```

---

## Phase C — Bridge cleanup

### Task 14: Delete image proxy and product endpoints

**Files:**
- Modify: `backend/bridge/main.py`
- Modify: `backend/requirements.txt`

- [ ] **Step 1: Open `backend/bridge/main.py` and delete:**

  - `class SelectProductReq` (~ line 55–58)
  - `_OG_RE`, `_OG_RE_REV`, `_TWITTER_RE`, `_image_cache`, `_image_ct_cache`, `_color_cache`
  - `_dominant_color`, `_browser_headers`, `_fetch_og_image` functions
  - `@app.post("/api/select-product")` and its handler `select_product`
  - `@app.get("/api/img")` and its handler `proxy_image`
  - `@app.get("/api/img-color")` and its handler `image_color`
  - `import re`, `from urllib.parse import urlparse`, `import httpx` if no longer used
  - `from fastapi.responses import Response` if no longer used
  - `from fastapi import ... Query` if `Query` no longer used (it isn't after the deletions)

- [ ] **Step 2: Verify the file compiles**

```bash
cd backend && python -c "from bridge import main; print('ok')"
```

Expected: `ok`. Fix any unused-import lints.

- [ ] **Step 3: Drop `Pillow` and `httpx` from requirements**

In `backend/requirements.txt`, remove the lines:

```
httpx>=0.27
Pillow>=10.0
```

- [ ] **Step 4: Smoke-test the bridge**

```bash
cd backend && WORLD_BUILD_DISABLE_UAGENTS=1 .venv/bin/uvicorn bridge.main:app --port 8000 &
sleep 3
curl -sf http://localhost:8000/docs > /dev/null && echo "bridge ok" || echo "bridge broken"
pkill -f "uvicorn bridge.main"
```

Expected: `bridge ok`.

- [ ] **Step 5: Commit**

```bash
git add backend/bridge/main.py backend/requirements.txt
git commit -m "feat(bridge): delete /api/img, /api/img-color, /api/select-product"
```

---

### Task 15: Delete legacy e2e test

**Files:**
- Delete: `backend/tests/e2e/test_product_urls_live.py`

- [ ] **Step 1: Delete the test**

```bash
git rm backend/tests/e2e/test_product_urls_live.py
```

- [ ] **Step 2: Commit**

```bash
git commit -m "test: remove product-URL liveness test (no more products)"
```

---

### Task 16: Frontend — drop product types and image helpers

**Files:**
- Modify: `frontend/lib/worldSpec.ts`
- Modify: `frontend/lib/api.ts`
- Delete: `frontend/components/FurniturePanel.tsx`

- [ ] **Step 1: Replace `frontend/lib/worldSpec.ts` contents**

```typescript
export type Wall = "north" | "south" | "east" | "west";

export interface Door { wall: Wall; offset: number; width: number; }
export interface Window { wall: Wall; offset: number; width: number; height: number; sill: number; }

export interface Room {
  id: string; type: string;
  x: number; y: number; width: number; depth: number;
  doors: Door[]; windows: Window[];
}

export interface Stairs { id: string; x: number; y: number; width: number; depth: number; direction: Wall; toLevel: number; }
export interface Floor { level: number; ceilingHeight: number; rooms: Room[]; stairs: Stairs[]; }
export interface Blueprint { gridSize: number; floors: Floor[]; }

export interface Plot { width: number; depth: number; groundColor: string; }
export interface Entrance { wall: Wall; offset: number; width: number; height: number; }
export interface Site { plot: Plot; buildingFootprint: [number, number]; buildingAnchor: [number, number]; entrance: Entrance; }

export interface GeometryPrimitive {
  type: "floor" | "wall" | "ceiling" | "stair" | "exterior_wall" | "roof" | "ground";
  roomId?: string;
  wall?: Wall;
  position: [number, number, number];
  size: [number, number, number];
  rotation?: number;
  holes?: { offset: number; width: number; height: number; bottom: number }[];
}
export interface Geometry { primitives: GeometryPrimitive[]; }

export interface Light { type: "ceiling" | "lamp" | "ambient"; position: [number, number, number]; color: string; intensity: number; }
export interface Lighting { byRoom: Record<string, Light[]>; }

export interface RoomMaterial { wall: string; floor: string; ceiling: string; }
export interface Materials { byRoom: Record<string, RoomMaterial>; }

export interface FurnitureItem {
  id: string; roomId: string; type: string;
  position: [number, number, number]; rotation: number; size: [number, number, number];
}

export interface Navigation { spawnPoint: [number, number, number]; walkableMeshIds: string[]; stairColliders: string[]; }
export interface Cost { total: number; byRoom: Record<string, number>; }

export interface Intent { buildingType: string; style: string; floors: number; vibe: string[]; sizeHint: string; }

export interface WorldSpec {
  worldId: string;
  prompt: string;
  intent?: Intent;
  site?: Site;
  blueprint?: Blueprint;
  geometry?: Geometry;
  lighting?: Lighting;
  materials?: Materials;
  furniture: FurnitureItem[];
  navigation?: Navigation;
  cost?: Cost;
}
```

- [ ] **Step 2: Strip `frontend/lib/api.ts`**

Remove `selectProduct`, `proxiedImage`, `fetchProductColor`. The file should keep: `generate`, `edit`, `getWorld`, `openStatusSocket`, `StatusEvent`. Final shape:

```typescript
import type { WorldSpec } from "./worldSpec";

const BRIDGE = process.env.NEXT_PUBLIC_BRIDGE_URL ?? "http://localhost:8000";

export async function generate(prompt: string): Promise<{ worldId: string }> {
  const r = await fetch(`${BRIDGE}/api/generate`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ prompt }),
  });
  if (!r.ok) throw new Error(`generate: ${r.status}`);
  return r.json();
}

export async function edit(worldId: string, edit: string): Promise<{ worldId: string }> {
  const r = await fetch(`${BRIDGE}/api/edit`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ worldId, edit }),
  });
  if (!r.ok) throw new Error(`edit: ${r.status}`);
  return r.json();
}

export async function getWorld(worldId: string): Promise<WorldSpec> {
  const r = await fetch(`${BRIDGE}/api/world/${worldId}`);
  if (!r.ok) throw new Error(`world: ${r.status}`);
  return r.json();
}

export type StatusEvent = { agent: string; state: "running" | "done" | "error"; message: string; data?: any };

export function openStatusSocket(worldId: string, onEvent: (e: StatusEvent) => void, onClose?: () => void): () => void {
  const wsUrl = BRIDGE.replace(/^http/, "ws") + `/ws/build/${worldId}`;
  let ws: WebSocket | null = new WebSocket(wsUrl);
  let closed = false;
  ws.onmessage = (m) => {
    try { onEvent(JSON.parse(m.data)); } catch {}
  };
  ws.onclose = () => { if (!closed) onClose?.(); };
  ws.onerror = () => { if (!closed) onClose?.(); };
  return () => { closed = true; ws?.close(); ws = null; };
}
```

- [ ] **Step 3: Delete `FurniturePanel.tsx`**

```bash
git rm frontend/components/FurniturePanel.tsx
```

- [ ] **Step 4: TypeScript compile check**

```bash
cd frontend && npx tsc --noEmit
```

Will likely fail because `World3D.tsx` still imports `FurniturePanel` and uses removed types. **Don't fix here** — Task 17 rewrites `World3D.tsx`. For now, accept the broken build and proceed.

- [ ] **Step 5: Commit (with broken build OK; Task 17 fixes)**

```bash
git add frontend/lib/worldSpec.ts frontend/lib/api.ts
git commit -m "feat(frontend): mirror new schema, drop product types/api helpers"
```

---

## Phase D — Frontend rendering

### Task 17: Plot, Roof, and shared wall-segment helper

**Files:**
- Create: `frontend/components/Plot.tsx`
- Create: `frontend/components/Roof.tsx`
- Create: `frontend/lib/wallSegments.ts`
- Modify: `frontend/components/Wall.tsx`

- [ ] **Step 1: Create `Plot.tsx`**

```typescript
"use client";

interface Props { size: [number, number]; color: string }

export default function Plot({ size, color }: Props) {
  return (
    <mesh position={[size[0] / 2, -0.025, -size[1] / 2]}>
      <boxGeometry args={[size[0], 0.05, size[1]]} />
      <meshStandardMaterial color={color} />
    </mesh>
  );
}
```

- [ ] **Step 2: Create `Roof.tsx`**

```typescript
"use client";
import type { GeometryPrimitive } from "@/lib/worldSpec";

export default function Roof({ prim, color }: { prim: GeometryPrimitive; color: string }) {
  return (
    <mesh position={prim.position}>
      <boxGeometry args={prim.size} />
      <meshStandardMaterial color={color} />
    </mesh>
  );
}
```

- [ ] **Step 3: Create `wallSegments.ts`**

```typescript
import type { GeometryPrimitive } from "./worldSpec";

export interface WallSegment {
  position: [number, number, number];
  size: [number, number, number];
}

/** Run the same hole-aware segmentation as Wall.tsx, but emit AABB
 *  primitives suitable for collision (and for rendering). The original
 *  `prim` is the unsegmented wall; the result is the list of solid sub-boxes. */
export function expandWallSegments(prim: GeometryPrimitive): GeometryPrimitive[] {
  const [w, h, d] = prim.size;
  const isXAxis = w >= d;
  const length = isXAxis ? w : d;
  const thickness = isXAxis ? d : w;
  const holes = (prim.holes ?? []).slice().sort((a, b) => a.offset - b.offset);

  const raw: { offset: number; len: number; bottom: number; height: number }[] = [];
  let cursor = 0;
  for (const hole of holes) {
    const holeStart = hole.offset - hole.width / 2;
    const holeEnd = hole.offset + hole.width / 2;
    if (holeStart > cursor) raw.push({ offset: cursor, len: holeStart - cursor, bottom: 0, height: h });
    if (hole.bottom > 0) raw.push({ offset: holeStart, len: hole.width, bottom: 0, height: hole.bottom });
    const topOfHole = hole.bottom + hole.height;
    if (topOfHole < h) raw.push({ offset: holeStart, len: hole.width, bottom: topOfHole, height: h - topOfHole });
    cursor = Math.max(cursor, holeEnd);
  }
  if (cursor < length) raw.push({ offset: cursor, len: length - cursor, bottom: 0, height: h });
  if (raw.length === 0) raw.push({ offset: 0, len: length, bottom: 0, height: h });

  const [cx, cy, cz] = prim.position;
  return raw.map(s => {
    const sxLocal = isXAxis ? s.offset - length / 2 + s.len / 2 : 0;
    const szLocal = isXAxis ? 0 : s.offset - length / 2 + s.len / 2;
    const syLocal = -h / 2 + s.bottom + s.height / 2;
    const sizeX = isXAxis ? s.len : thickness;
    const sizeY = s.height;
    const sizeZ = isXAxis ? thickness : s.len;
    return {
      ...prim,
      position: [cx + sxLocal, cy + syLocal, cz + szLocal] as [number, number, number],
      size: [sizeX, sizeY, sizeZ] as [number, number, number],
      holes: [],
    };
  });
}
```

- [ ] **Step 4: Update `Wall.tsx` to delegate to the shared helper**

```typescript
"use client";
import type { GeometryPrimitive } from "@/lib/worldSpec";
import { expandWallSegments } from "@/lib/wallSegments";

export default function Wall({ prim, color }: { prim: GeometryPrimitive; color: string }) {
  const segments = expandWallSegments(prim);
  return (
    <>
      {segments.map((s, idx) => (
        <mesh key={idx} position={s.position}>
          <boxGeometry args={s.size} />
          <meshStandardMaterial color={color} />
        </mesh>
      ))}
    </>
  );
}
```

- [ ] **Step 5: TypeScript compile check**

```bash
cd frontend && npx tsc --noEmit
```

Expected: still fails on `World3D.tsx` (next task). Other files clean.

- [ ] **Step 6: Commit**

```bash
git add frontend/components/Plot.tsx frontend/components/Roof.tsx frontend/lib/wallSegments.ts frontend/components/Wall.tsx
git commit -m "feat(frontend): Plot, Roof, shared wall-segment helper"
```

---

### Task 18: New office furniture components

**Files:**
- Create: `frontend/components/Furniture/Desk.tsx`
- Create: `frontend/components/Furniture/OfficeChair.tsx`
- Create: `frontend/components/Furniture/ConferenceTable.tsx`
- Create: `frontend/components/Furniture/ReceptionDesk.tsx`
- Create: `frontend/components/Furniture/Whiteboard.tsx`
- Create: `frontend/components/Furniture/FilingCabinet.tsx`
- Modify: `frontend/components/Furniture/index.tsx`

- [ ] **Step 1: Create `Desk.tsx`**

```typescript
"use client";

interface Props { size: [number, number, number]; color: string }

export default function Desk({ size, color }: Props) {
  const [w, h, d] = size;
  const topThickness = 0.04;
  const legSize = 0.06;
  const legY = (h - topThickness) / 2;
  return (
    <group>
      <mesh position={[0, h - topThickness / 2, 0]}>
        <boxGeometry args={[w, topThickness, d]} />
        <meshStandardMaterial color={color} />
      </mesh>
      {[
        [-w / 2 + legSize, legY, -d / 2 + legSize],
        [w / 2 - legSize, legY, -d / 2 + legSize],
        [-w / 2 + legSize, legY, d / 2 - legSize],
        [w / 2 - legSize, legY, d / 2 - legSize],
      ].map((p, i) => (
        <mesh key={i} position={p as [number, number, number]}>
          <boxGeometry args={[legSize, h - topThickness, legSize]} />
          <meshStandardMaterial color="#3a3a3a" />
        </mesh>
      ))}
    </group>
  );
}
```

- [ ] **Step 2: Create `OfficeChair.tsx`**

```typescript
"use client";

interface Props { size: [number, number, number]; color: string }

export default function OfficeChair({ size, color }: Props) {
  const [w, h, d] = size;
  return (
    <group>
      {/* wheel base */}
      <mesh position={[0, 0.05, 0]}>
        <cylinderGeometry args={[w * 0.5, w * 0.5, 0.1, 12]} />
        <meshStandardMaterial color="#1a1a1a" />
      </mesh>
      {/* post */}
      <mesh position={[0, h * 0.32, 0]}>
        <cylinderGeometry args={[0.04, 0.04, h * 0.45, 8]} />
        <meshStandardMaterial color="#2a2a2a" />
      </mesh>
      {/* seat */}
      <mesh position={[0, h * 0.55, 0]}>
        <boxGeometry args={[w * 0.85, 0.08, d * 0.85]} />
        <meshStandardMaterial color={color} />
      </mesh>
      {/* backrest */}
      <mesh position={[0, h * 0.85, -d * 0.4]}>
        <boxGeometry args={[w * 0.85, h * 0.4, 0.08]} />
        <meshStandardMaterial color={color} />
      </mesh>
    </group>
  );
}
```

- [ ] **Step 3: Create `ConferenceTable.tsx`**

```typescript
"use client";

interface Props { size: [number, number, number]; color: string }

export default function ConferenceTable({ size, color }: Props) {
  const [w, h, d] = size;
  const topThickness = 0.05;
  const legSize = 0.08;
  const legY = (h - topThickness) / 2;
  return (
    <group>
      <mesh position={[0, h - topThickness / 2, 0]}>
        <boxGeometry args={[w, topThickness, d]} />
        <meshStandardMaterial color={color} />
      </mesh>
      {[
        [-w / 2 + legSize, legY, -d / 2 + legSize],
        [w / 2 - legSize, legY, -d / 2 + legSize],
        [-w / 2 + legSize, legY, d / 2 - legSize],
        [w / 2 - legSize, legY, d / 2 - legSize],
      ].map((p, i) => (
        <mesh key={i} position={p as [number, number, number]}>
          <boxGeometry args={[legSize, h - topThickness, legSize]} />
          <meshStandardMaterial color="#222" />
        </mesh>
      ))}
    </group>
  );
}
```

- [ ] **Step 4: Create `ReceptionDesk.tsx`**

```typescript
"use client";

interface Props { size: [number, number, number]; color: string }

export default function ReceptionDesk({ size, color }: Props) {
  const [w, h, d] = size;
  return (
    <group>
      {/* main counter */}
      <mesh position={[0, h / 2, 0]}>
        <boxGeometry args={[w, h, d * 0.7]} />
        <meshStandardMaterial color={color} />
      </mesh>
      {/* high front rail */}
      <mesh position={[0, h * 0.55, d * 0.4]}>
        <boxGeometry args={[w, h * 0.2, 0.08]} />
        <meshStandardMaterial color="#222" />
      </mesh>
    </group>
  );
}
```

- [ ] **Step 5: Create `Whiteboard.tsx`**

```typescript
"use client";

interface Props { size: [number, number, number]; color: string }

export default function Whiteboard({ size, color: _color }: Props) {
  const [w, h, d] = size;
  return (
    <group>
      <mesh position={[0, h / 2, 0]}>
        <boxGeometry args={[w, h, d]} />
        <meshStandardMaterial color="#f5f5f0" />
      </mesh>
      {/* frame */}
      <mesh position={[0, h / 2, d / 2 + 0.005]}>
        <boxGeometry args={[w + 0.04, h + 0.04, 0.01]} />
        <meshStandardMaterial color="#a0a0a0" />
      </mesh>
    </group>
  );
}
```

- [ ] **Step 6: Create `FilingCabinet.tsx`**

```typescript
"use client";

interface Props { size: [number, number, number]; color: string }

export default function FilingCabinet({ size, color }: Props) {
  const [w, h, d] = size;
  return (
    <group>
      <mesh position={[0, h / 2, 0]}>
        <boxGeometry args={[w, h, d]} />
        <meshStandardMaterial color={color} />
      </mesh>
      {/* drawer lines */}
      {[0.25, 0.5, 0.75].map((frac, i) => (
        <mesh key={i} position={[0, h * frac, d / 2 + 0.001]}>
          <boxGeometry args={[w * 0.9, 0.01, 0.005]} />
          <meshStandardMaterial color="#1a1a1a" />
        </mesh>
      ))}
    </group>
  );
}
```

- [ ] **Step 7: Update `Furniture/index.tsx` registry**

Replace the registry with:

```typescript
"use client";
import type { FurnitureItem } from "@/lib/worldSpec";
import Couch from "./Couch";
import Bed from "./Bed";
import Table from "./Table";
import Chair from "./Chair";
import Lamp from "./Lamp";
import Rug from "./Rug";
import Bookshelf from "./Bookshelf";
import Plant from "./Plant";
import Desk from "./Desk";
import OfficeChair from "./OfficeChair";
import ConferenceTable from "./ConferenceTable";
import ReceptionDesk from "./ReceptionDesk";
import Whiteboard from "./Whiteboard";
import FilingCabinet from "./FilingCabinet";

interface Props { item: FurnitureItem; tint?: string }

const REGISTRY: Record<string, React.ComponentType<any>> = {
  couch: Couch, sofa: Couch, bed: Bed,
  table: Table, nightstand: Table, tv: Table,
  chair: Chair, lamp: Lamp, rug: Rug,
  bookshelf: Bookshelf, wardrobe: Bookshelf, plant: Plant,
  desk: Desk,
  office_chair: OfficeChair,
  conference_table: ConferenceTable,
  reception_desk: ReceptionDesk,
  whiteboard: Whiteboard,
  filing_cabinet: FilingCabinet,
};

export default function Furniture({ item, tint }: Props) {
  const Comp = REGISTRY[item.type] ?? Table;
  const finalTint = tint ?? defaultTint(item.type);
  return (
    <group position={item.position} rotation={[0, item.rotation ?? 0, 0]}>
      <Comp size={item.size} color={finalTint} />
    </group>
  );
}

function defaultTint(type: string): string {
  switch (type) {
    case "couch": case "sofa": return "#6b7280";
    case "bed": return "#9ca3af";
    case "table": case "desk": case "nightstand": case "tv": return "#a16207";
    case "chair": return "#4b5563";
    case "office_chair": return "#1f2937";
    case "conference_table": return "#3a2e1d";
    case "reception_desk": return "#5e3a1e";
    case "whiteboard": return "#f5f5f0";
    case "filing_cabinet": return "#374151";
    case "lamp": return "#fef3c7";
    case "rug": return "#92400e";
    case "bookshelf": case "wardrobe": return "#451a03";
    case "plant": return "#16a34a";
    default: return "#6b7280";
  }
}
```

(Note: `onClick` removed; no more click-to-open panel.)

- [ ] **Step 8: TypeScript compile check**

```bash
cd frontend && npx tsc --noEmit
```

Expected: still fails on `World3D.tsx` only (next task).

- [ ] **Step 9: Commit**

```bash
git add frontend/components/Furniture/
git commit -m "feat(furniture): office components (desk, office chair, conference table, …)"
```

---

### Task 19: Rewrite `World3D.tsx`

**Files:**
- Modify: `frontend/components/World3D.tsx`

- [ ] **Step 1: Replace `World3D.tsx`**

```typescript
"use client";
import { Suspense, useEffect, useState } from "react";
import { Canvas } from "@react-three/fiber";
import type { WorldSpec } from "@/lib/worldSpec";
import { expandWallSegments } from "@/lib/wallSegments";
import Plot from "./Plot";
import Roof from "./Roof";
import Wall from "./Wall";
import Furniture from "./Furniture";
import PlayerControls from "./PlayerControls";
import CrosshairHUD from "./CrosshairHUD";
import StatusBar from "./StatusBar";
import ChatPanel from "./ChatPanel";

export default function World3D({ spec }: { spec: WorldSpec }) {
  const [chatOpen, setChatOpen] = useState(false);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.code === "KeyT") setChatOpen((v) => !v);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const prims = spec.geometry?.primitives ?? [];
  const ground   = prims.filter((p) => p.type === "ground");
  const exterior = prims.filter((p) => p.type === "exterior_wall");
  const roof     = prims.filter((p) => p.type === "roof");
  const walls    = prims.filter((p) => p.type === "wall");
  const floors   = prims.filter((p) => p.type === "floor");
  const ceilings = prims.filter((p) => p.type === "ceiling");
  const stairs   = prims.filter((p) => p.type === "stair");

  const colliders = [
    ...exterior.flatMap(expandWallSegments),
    ...walls.flatMap(expandWallSegments),
  ];

  const matFloor = (rid?: string) => spec.materials?.byRoom?.[rid ?? ""]?.floor;
  const matWall  = (rid?: string) => spec.materials?.byRoom?.[rid ?? ""]?.wall ?? "#e7e1d5";
  const matCeil  = (rid?: string) => spec.materials?.byRoom?.[rid ?? ""]?.ceiling ?? "#ffffff";

  const spawn = spec.navigation?.spawnPoint ?? [50, 1.7, -47];
  const groundColor = spec.site?.plot?.groundColor ?? "#5a7c3a";

  return (
    <div className="fixed inset-0">
      <Canvas camera={{ fov: 70, position: spawn as any, near: 0.05, far: 300 }}>
        <color attach="background" args={["#a8c8e8"]} />
        <ambientLight intensity={0.7} />
        <directionalLight position={[60, 80, 40]} intensity={0.9} />

        {Object.entries(spec.lighting?.byRoom ?? {}).flatMap(([rid, lights]) =>
          lights.map((l, i) => (
            <pointLight key={`${rid}-${i}`} position={l.position as any}
                        color={l.color} intensity={l.intensity} distance={12} />
          ))
        )}

        <Suspense fallback={null}>
          {ground.map((p, i) => (
            <Plot key={`g${i}`} size={[p.size[0], p.size[2]]} color={groundColor} />
          ))}
          {floors.map((p, i) => (
            <mesh key={`f${i}`} position={p.position as any}>
              <boxGeometry args={p.size as any} />
              <meshStandardMaterial color={floorColor(matFloor(p.roomId))} />
            </mesh>
          ))}
          {ceilings.map((p, i) => (
            <mesh key={`c${i}`} position={p.position as any}>
              <boxGeometry args={p.size as any} />
              <meshStandardMaterial color={matCeil(p.roomId)} />
            </mesh>
          ))}
          {walls.map((p, i)    => <Wall key={`w${i}`} prim={p} color={matWall(p.roomId)} />)}
          {exterior.map((p, i) => <Wall key={`e${i}`} prim={p} color="#d8d4c6" />)}
          {roof.map((p, i)     => <Roof key={`r${i}`} prim={p} color="#3a3a3a" />)}
          {stairs.map((p, i) => (
            <mesh key={`s${i}`} position={p.position as any}
                  rotation={[0, p.rotation ?? 0, 0]}>
              <boxGeometry args={[p.size[0], 0.2, p.size[2]]} />
              <meshStandardMaterial color="#7c5a3a" />
            </mesh>
          ))}
          {spec.furniture.map((f) => (
            <Furniture key={f.id} item={f} />
          ))}
        </Suspense>

        <PlayerControls walls={colliders} spawn={spawn as any} />
      </Canvas>

      <CrosshairHUD />
      <StatusBar spec={spec} />
      <ChatPanel open={chatOpen} onClose={() => setChatOpen(false)} worldId={spec.worldId} />
    </div>
  );
}

function floorColor(token?: string): string {
  const map: Record<string, string> = {
    oak_planks: "#a47a4f",
    marble_tile: "#e9e6df",
    concrete: "#9a9a9a",
    carpet_grey: "#7d7d7d",
    carpet_beige: "#c8b89c",
    tile_white: "#f1efe7",
    dark_wood: "#4b2e1a",
  };
  return map[token ?? ""] ?? "#9b8466";
}
```

- [ ] **Step 2: TypeScript compile check**

```bash
cd frontend && npx tsc --noEmit
```

Expected: clean (no errors).

- [ ] **Step 3: Commit**

```bash
git add frontend/components/World3D.tsx
git commit -m "feat(world3d): render Plot/exterior/Roof + collider includes wall segments"
```

---

### Task 20: Smoke test — frontend boots

**Files:** none (verification step)

- [ ] **Step 1: Build frontend**

```bash
cd frontend && npm run build
```

Expected: build succeeds. Fix any TypeScript or module errors.

- [ ] **Step 2: Run dev mode**

```bash
cd frontend && npm run dev &
sleep 5
curl -sf http://localhost:3000 > /dev/null && echo "frontend ok" || echo "frontend broken"
pkill -f "next dev"
```

Expected: `frontend ok`.

- [ ] **Step 3: No commit needed (verification only)**

---

## Phase E — Verification

### Task 21: Update e2e tests

**Files:**
- Modify: `backend/tests/e2e/test_full_pipeline.py`
- Modify: `backend/tests/e2e/test_multistory.py`

- [ ] **Step 1: Read and update `test_full_pipeline.py`**

Add these assertions after the pipeline runs:

```python
assert spec.site is not None
assert spec.site.plot.width == 100.0
assert any(p.type == "ground" for p in spec.geometry.primitives)
assert any(p.type == "exterior_wall" for p in spec.geometry.primitives)
assert any(p.type == "roof" for p in spec.geometry.primitives)
assert not hasattr(spec, "products")  # field removed
```

Remove any assertions about `spec.products`, `selectedProductId`, etc.

- [ ] **Step 2: Update `test_multistory.py`**

Add:

```python
ext_walls = [p for p in spec.geometry.primitives if p.type == "exterior_wall"]
assert len(ext_walls) >= 4 * spec.intent.floors  # 4 walls per floor
ground_south = [p for p in ext_walls if p.wall == "south" and p.position[1] < 3]
assert len(ground_south) == 1
assert len(ground_south[0].holes) == 1  # entrance
```

- [ ] **Step 3: Run e2e tests**

```bash
cd backend && pytest tests/e2e -v
```

Expected: PASS. (These are slow — 5–10 minutes each. Plan accordingly.)

- [ ] **Step 4: Commit**

```bash
git add backend/tests/e2e/
git commit -m "test(e2e): assert site/exterior walls, drop product assertions"
```

---

### Task 22: Manual demo run

**Files:** none (manual verification)

- [ ] **Step 1: Start backend**

```bash
cd backend && WORLD_BUILD_DISABLE_UAGENTS=1 .venv/bin/uvicorn bridge.main:app --port 8000 &
```

Wait for `Application startup complete`.

- [ ] **Step 2: Start frontend**

```bash
cd frontend && npm run dev &
```

- [ ] **Step 3: Generate the demo prompt**

Open http://localhost:3000. Type: **"a 3-story tech startup office"**. Submit.

- [ ] **Step 4: Watch the build**

Status panel should stream:
- intent_parser → done
- blueprint_architect → done
- compliance_critic → done
- geometry_builder, lighting_designer, material_stylist (parallel) → done
- furniture_planner → done (fast — no LLM)
- placement_validator → done
- pricing_estimator → done
- navigation_planner → done

**No** product_scout, **no** style_matcher in the activity stream.

- [ ] **Step 5: Walk the demo**

When the 3D scene appears:

1. You should be on grass, facing a 3-story building with a visible front door.
2. WASD forward → walk across grass to the entrance.
3. Walk through the entrance into the lobby.
4. Visible: reception desk, maybe a couch.
5. Walk through corridor; offices have desk + chair, conference room has long table + chairs.
6. Find stairs, climb to floor 2.
7. Walk back outside through the south entrance.

**Pass criteria:** loop completes without falling through walls, no JS errors in browser console, no 404s in network tab.

- [ ] **Step 6: Stop servers**

```bash
pkill -f "uvicorn bridge.main"
pkill -f "next dev"
```

- [ ] **Step 7: No commit (manual test only)**

---

### Task 23: Update `docs/ARCHITECTURE.md` and `docs/ROADMAP.md`

**Files:**
- Modify: `docs/ARCHITECTURE.md`
- Modify: `docs/ROADMAP.md`

- [ ] **Step 1: ARCHITECTURE.md updates**

In the "mental model" section, add `site` to the WorldSpec field list with "written by intent_parser (pure code)".

In the "pipeline" section, replace the table row for `product_scout` and `style_matcher` with: "removed from POST_STEPS as of site pivot; agents still registered as uAgents."

In the "common changes" table, add:
- "Add a new room template" → `backend/core/room_templates.py`
- "Change plot size / entrance side" → `backend/core/site.py` (`derive_site_from_intent`)
- "Change building cost rate" → `backend/core/pricing.py` (`COST_PER_SQM`)

- [ ] **Step 2: ROADMAP.md updates**

Mark items 1, 2 (style tokens still TODO), 3 (office primitives partially done), 4 (multi-floor working) as done/in-progress. Add a new "What's next after site pivot" section listing: style tokens, exterior windows, parking lot, multiple buildings on one plot.

- [ ] **Step 3: Commit**

```bash
git add docs/ARCHITECTURE.md docs/ROADMAP.md
git commit -m "docs: update architecture + roadmap for site-pivot completion"
```

---

### Task 24: Final push

- [ ] **Step 1: Run full test suite one more time**

```bash
cd backend && pytest tests/unit -v
```

Expected: all PASS.

- [ ] **Step 2: Push**

```bash
git push origin main
```

- [ ] **Step 3: Verify on GitHub**

Open https://github.com/pauligwe/WorldEdit/commits/main — confirm the site-pivot commits are there.

---

## Self-review

**Spec coverage:**
- ✓ §1 Site model — Tasks 1–2
- ✓ §1 Coordinate convention — Task 5 (geometry_builder is the single conversion site)
- ✓ §2 intent_parser writes Site — Task 8
- ✓ §2 blueprint_architect footprint constraint — Task 9
- ✓ §2 compliance_critic adds checks — Tasks 4, 10
- ✓ §2 geometry_builder ground/exterior_wall/roof — Task 5
- ✓ §2 furniture_planner pure code — Tasks 7, 12
- ✓ §2 pricing $/sqm — Task 6
- ✓ §2 navigation spawns on grass — Task 11
- ✓ §2 product_scout / style_matcher unwired but registered — Task 13
- ✓ §3 bridge endpoint deletions — Task 14
- ✓ §3 Pillow / httpx removed — Task 14
- ✓ §4 frontend deletions and additions — Tasks 16–19
- ✓ §4 collider includes wall segments — Tasks 17, 19
- ✓ §5 unit tests — Tasks 1, 3, 4, 5, 6, 7, 11, 12
- ✓ §5 e2e tests updated — Task 21
- ✓ §5 product URL test deleted — Task 15
- ✓ §6 visual targets — Task 22 manual demo
- ✓ §7 things kept — implicit (we only modify the listed files)
- ✓ §8 demo prompt run — Task 22

**Placeholder scan:** none. Every step has either complete code, a complete command, or a concrete file edit description.

**Type consistency:**
- `Site` fields used the same way across Tasks 1, 3, 5, 8, 9, 11, 12 ✓
- `apply_template(room, level_y, anchor)` signature consistent across Tasks 7 and 12 ✓
- `compute_navigation(spec)` consistent across Tasks 11 and the test in Task 11 ✓
- `compute_cost(spec)` consistent ✓
- `expandWallSegments(prim)` consistent across Tasks 17 and 19 ✓
- `GeometryPrimitive.type` literal extensions match between backend (Task 2) and frontend (Task 16) ✓

No gaps. Plan complete.
