# Site Pivot — Design Spec

**Date:** 2026-04-24
**Status:** approved (autonomous brainstorm with user)
**Scope:** repivot World Build from "single-room interior with curated products" to "whole building on a plot of grass, walk inside and outside."

---

## Goal

Type a prompt like *"a 3-story tech startup office"* and get:

- A 100×100m grass plot
- A whole multi-floor building centered on the plot
- A working entrance (door cutout in the south exterior wall on the ground floor)
- Walkable interior (corridors, rooms with generic furniture)
- Player spawns on the grass facing the entrance, walks across grass, through the door, into the building

The interior is **generic** — every room type has a hardcoded furniture template. We do not search for products. We do not let the user swap furniture. The building shell is the headline.

---

## Non-goals

- **Real products / vendor URLs / image proxy.** Gone. The `Product` model, `product_scout`, `style_matcher`, `/api/img`, `/api/img-color`, `Pillow`, the og:image regexes, the `FurniturePanel` component — all removed.
- **Style tokens / per-room style variation.** Out of scope for this spec; furniture meshes still use simple style hashing for now. Future work.
- **Functional elevators.** Stairs only.
- **Multiple buildings on one plot.** One building per world.
- **Outdoor furniture / landscaping.** Just grass.
- **Plot size as user input.** Fixed 100×100m.

---

## The new shape (at a glance)

```
WorldSpec
├── prompt           "a 3-story tech startup office"
├── intent           {buildingType: "office", floors: 3, ...}
├── site             ← NEW
│   ├── plot         {width: 100, depth: 100, groundColor: "#5a7c3a"}
│   ├── buildingFootprint  (40, 25)
│   ├── buildingAnchor     (30, 37)        # SW corner on plot
│   └── entrance     {wall: "south", offset: 20, width: 1.6, height: 2.2}
├── blueprint        # rooms in BUILDING-LOCAL coords (existing)
├── geometry         # primitives in PLOT-WORLD coords (offset by anchor)
│   primitives: [
│     {type: "ground", ...},                   ← NEW (one per world)
│     {type: "exterior_wall", ...} × N,        ← NEW (4 walls × N floors)
│     {type: "roof", ...},                     ← NEW (one per building)
│     {type: "floor" | "ceiling" | "wall" | "stair", ...}   ← existing
│   ]
├── lighting         (existing)
├── materials        (existing)
├── furniture        # populated from room templates (existing field, new producer)
├── navigation       {spawnPoint: ON THE GRASS facing entrance}
└── cost             {total: ~ floor_area_sqm × $1500}
# products field: REMOVED
```

---

## Section 1 — Site model

### Pydantic additions (`backend/core/world_spec.py`)

```python
class Plot(BaseModel):
    width: float = 100.0      # meters
    depth: float = 100.0
    groundColor: str = "#5a7c3a"   # grass green

class Entrance(BaseModel):
    wall: Wall                # "south" | "north" | "east" | "west"
    offset: float = Field(ge=0)   # along the wall, in meters
    width: float = Field(default=1.6, gt=0)
    height: float = Field(default=2.2, gt=0)

class Site(BaseModel):
    plot: Plot = Field(default_factory=Plot)
    buildingFootprint: list[float]   # [width, depth], both > 0
    buildingAnchor: list[float]      # [x, y], SW corner on plot
    entrance: Entrance
```

### `WorldSpec` changes

```python
class WorldSpec(BaseModel):
    worldId: str
    prompt: str
    intent: Optional[Intent] = None
    site: Optional[Site] = None             # NEW
    blueprint: Optional[Blueprint] = None
    geometry: Optional[Geometry] = None
    lighting: Optional[Lighting] = None
    materials: Optional[Materials] = None
    furniture: list[FurnitureItem] = Field(default_factory=list)
    # products: dict[str, Product] = ...  ← REMOVED
    navigation: Optional[Navigation] = None
    cost: Optional[Cost] = None
```

### `FurnitureItem` simplified

```python
class FurnitureItem(BaseModel):
    id: str
    roomId: str
    type: str
    position: list[float]      # plot-world coords
    rotation: float = 0.0
    size: list[float]
    # selectedProductId, alternates, subtype, tint: REMOVED
```

### `Product` model

**Deleted.**

### Coordinate convention

- **Building-local**: `(x_b, y_b)` in meters, origin at building SW corner. This is what `Blueprint.rooms` use.
- **Plot-world**: `(x_p, y_p)` in meters, origin at plot SW corner. `x_p = x_b + buildingAnchor[0]`, `y_p = y_b + buildingAnchor[1]`.
- **Scene** (three.js): `(x_p, height_y, -y_p)`. Right-handed y-up. Existing convention; do not change.

`geometry_builder` is the single place that does the building-local → plot-world conversion.

---

## Section 2 — Pipeline changes

### Orchestrator (`backend/agents/orchestrator.py`)

```python
SEQUENTIAL_STEPS = [
    ("intent_parser", intent_parser.run),       # now also writes Site
    ("blueprint_architect", blueprint_architect.run),  # constrained to footprint
    ("compliance_critic", compliance_critic.run),      # checks footprint + entrance
]

PARALLEL_STEP = [
    ("geometry_builder", geometry_builder.run),  # adds ground/exterior_wall/roof
    ("lighting_designer", lighting_designer.run),
    ("material_stylist", material_stylist.run),
]

POST_STEPS = [
    ("furniture_planner", furniture_planner.run),     # now pure code, looks up templates
    ("placement_validator", placement_validator.run),
    # product_scout: REMOVED
    # style_matcher: REMOVED
    ("pricing_estimator", pricing_estimator.run),     # now $/sqm
    ("navigation_planner", navigation_planner.run),   # spawns on grass
]
```

### `intent_parser`
After picking `Intent`, also pick a `Site`:
- `plot`: default 100×100
- `buildingFootprint`: derived from `intent.sizeHint` and `intent.floors`. Heuristic: `(20 + sizeBonus, 15 + sizeBonus)` where sizeBonus = 0/10/20 for small/medium/large. Capped so the building leaves ≥ 10m of grass on every side.
- `buildingAnchor`: centered → `((100 - footprint_w) / 2, (100 - footprint_d) / 2)`
- `entrance.wall`: always `"south"` for v1
- `entrance.offset`: `footprint_w / 2`

This is a **pure-code** computation in `intent_parser.run` after the LLM call. The LLM picks `Intent`; we derive `Site` deterministically.

### `blueprint_architect`
Prompt updated:
- Tell the LLM the footprint dimensions and that rooms must fit within them
- Encourage office-style room types: `lobby`, `corridor`, `office`, `conference_room`, `breakroom`, `restroom`, `reception`, `stairwell`
- For multi-floor: a corridor on every floor; stairs align across floors
- Ground floor must contain a room with a south door at `entrance.offset` (the lobby/reception)

Existing examples in `core/prompts/examples/` updated; one new example added: a 3-floor office.

### `compliance_critic`
Adds three checks:
1. Every room on every floor fits inside `buildingFootprint`
2. Ground floor has at least one room with a `south` door whose offset overlaps `entrance.offset ± entrance.width/2`
3. Stairs on level N have matching footprint on level N+1 (existing partial check, formalized)

### `geometry_builder`
Existing logic preserved, with three additions:

**1. Ground primitive** (one per world):
```python
GeometryPrimitive(
    type="ground",
    position=[plot.width / 2, -0.025, -plot.depth / 2],
    size=[plot.width, 0.05, plot.depth],
)
```

**2. Building anchor offset:** every existing primitive's `(x, z)` is shifted by `(+anchor[0], -anchor[1])` (because scene z = -plot_y).

**3. Exterior walls + roof:** for each floor level, four primitives wrapping the building footprint. The south wall on level 0 carries a `holes` entry for the entrance:
```python
GeometryPrimitive(
    type="exterior_wall",
    wall="south",
    position=[anchor_x + footprint_w/2, level_y + ceiling_h/2, -anchor_y],
    size=[footprint_w, ceiling_h, EXTERIOR_WALL_THICKNESS],   # 0.2 m
    holes=[{"offset": entrance.offset, "width": entrance.width,
            "height": entrance.height, "bottom": 0.0}] if (level == 0 and wall == "south") else [],
)
```

Plus a flat roof on top:
```python
GeometryPrimitive(
    type="roof",
    position=[anchor_x + footprint_w/2, top_y + 0.1, -(anchor_y + footprint_d/2)],
    size=[footprint_w + 0.2, 0.2, footprint_d + 0.2],
)
```

### `furniture_planner` — replaced with pure code

Old: per-room Gemini call that hallucinates furniture. Slow, variable.
New: lookup table.

```python
# core/room_templates.py
class FurnitureTemplate(BaseModel):
    type: str
    room_offset: list[float]   # [x, y] in meters from room SW corner
    size: list[float]          # [w, h, d]
    rotation: float = 0.0

ROOM_FURNITURE: dict[str, list[FurnitureTemplate]] = {
    "office": [
        FurnitureTemplate(type="desk",         room_offset=[1.0, 1.0], size=[1.4, 0.75, 0.7]),
        FurnitureTemplate(type="office_chair", room_offset=[1.7, 2.0], size=[0.6, 1.1, 0.6], rotation=3.14),
    ],
    "conference_room": [
        FurnitureTemplate(type="conference_table", room_offset=[1.5, 1.5], size=[2.4, 0.75, 1.0]),
        # 6 chairs around it (positions in template)
    ],
    "lobby":     [FurnitureTemplate(type="reception_desk", room_offset=[2.0, 2.0], size=[2.0, 1.0, 0.6])],
    "breakroom": [FurnitureTemplate(type="table", room_offset=[1.5, 1.5], size=[1.5, 0.75, 1.0]),
                  FurnitureTemplate(type="chair", room_offset=[1.5, 0.5], size=[0.5, 1.0, 0.5], rotation=0.0),
                  FurnitureTemplate(type="chair", room_offset=[1.5, 3.0], size=[0.5, 1.0, 0.5], rotation=3.14)],
    "corridor":  [],
    "restroom":  [],
    "stairwell": [],
    "reception": [FurnitureTemplate(type="reception_desk", room_offset=[2.0, 2.0], size=[2.0, 1.0, 0.6])],
    # Existing residential types still work for non-office prompts:
    "bedroom":   [FurnitureTemplate(type="bed", room_offset=[1.0, 1.0], size=[2.0, 0.5, 1.5])],
    "kitchen":   [FurnitureTemplate(type="table", room_offset=[1.5, 1.5], size=[1.2, 0.75, 0.8])],
    "living_room": [FurnitureTemplate(type="couch", room_offset=[1.5, 1.5], size=[2.2, 0.8, 0.9])],
    "bathroom":  [],
    "default":   [],   # any room type without a template
}
```

`furniture_planner.run` becomes:

```python
def run(spec: WorldSpec) -> WorldSpec:
    assert spec.blueprint and spec.site
    items: list[FurnitureItem] = []
    anchor = spec.site.buildingAnchor
    for fl in spec.blueprint.floors:
        level_y = fl.level * fl.ceilingHeight
        for room in fl.rooms:
            template = ROOM_FURNITURE.get(room.type, ROOM_FURNITURE["default"])
            for i, t in enumerate(template):
                # skip if template doesn't fit in this room
                if t.room_offset[0] + t.size[0] > room.width: continue
                if t.room_offset[1] + t.size[2] > room.depth: continue
                px = anchor[0] + room.x + t.room_offset[0] + t.size[0] / 2
                py = anchor[1] + room.y + t.room_offset[1] + t.size[2] / 2
                items.append(FurnitureItem(
                    id=f"{room.id}-{t.type}-{i}",
                    roomId=room.id,
                    type=t.type,
                    position=[px, level_y, -py],
                    rotation=t.rotation,
                    size=t.size,
                ))
    spec.furniture = items
    return spec
```

No LLM. Deterministic. Skips templates that wouldn't fit.

### `pricing_estimator`
```python
COST_PER_SQM = 1500.0  # USD

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

Old `compute_cost(furniture, products)` signature is gone. Simpler.

### `navigation_planner`
```python
def compute_navigation(spec: WorldSpec) -> Navigation:
    assert spec.site
    s = spec.site
    # Spawn 3m south of the entrance, on the grass, facing north
    spawn_x = s.buildingAnchor[0] + s.entrance.offset
    spawn_y_plot = s.buildingAnchor[1] - 3.0
    return Navigation(
        spawnPoint=[spawn_x, 1.7, -spawn_y_plot],
        walkableMeshIds=[],
        stairColliders=[],
    )
```

### Untouched
`lighting_designer`, `material_stylist`, `placement_validator`, `chat_edit_coordinator`, `intent_parser` Gemini-call portion.

### uAgents
**Untouched.** Still 14 agents in `uagent_runner.py`. The two unwired-from-orchestrator agents (`product_scout`, `style_matcher`) remain registered as Chat Protocol echo handlers. Fetch.ai track count preserved.

---

## Section 3 — Bridge changes (`backend/bridge/main.py`)

**Removed:**
- `POST /api/select-product` and `SelectProductReq`
- `GET /api/img` and `proxy_image` and helpers
- `GET /api/img-color` and `image_color`
- `_OG_RE`, `_OG_RE_REV`, `_TWITTER_RE`, `_image_cache`, `_image_ct_cache`, `_color_cache`
- `_dominant_color`, `_browser_headers`, `_fetch_og_image`
- `httpx`, `Pillow` imports

**Kept:** `/api/generate`, `/api/edit`, `/api/world/{id}`, `/ws/build/{id}`. Disk hydration via `_load_world`.

`requirements.txt`: drop `Pillow`, drop `httpx`.

---

## Section 4 — Frontend changes

### Removed
- `frontend/components/FurniturePanel.tsx` (entire file)
- `proxiedImage`, `fetchProductColor` in `lib/api.ts`
- `selectProduct` in `lib/api.ts`
- `Product` type, `selectedProductId`, `alternates`, `subtype`, `tint`, `products` in `lib/worldSpec.ts`
- `selected`, `setSelected`, `productColors`, `setProductColors` state in `World3D.tsx`
- `tintForProduct`, `floorColor` (move floorColor to a shared util — actually keep, just inline)

### Added

**`frontend/components/Plot.tsx`** — green ground plane:
```tsx
export default function Plot({ size, color }: { size: [number, number]; color: string }) {
  return (
    <mesh position={[size[0]/2, -0.025, -size[1]/2]} receiveShadow>
      <boxGeometry args={[size[0], 0.05, size[1]]} />
      <meshStandardMaterial color={color} />
    </mesh>
  );
}
```

**`frontend/components/Roof.tsx`** — flat building roof, just a `<mesh>` with the primitive's size.

**Furniture components** (new procedural meshes in `frontend/components/Furniture/`):
- `Desk.tsx` — flat box with 4 leg cylinders
- `OfficeChair.tsx` — wheel base + post + seat + backrest
- `ConferenceTable.tsx` — long box with 4 leg cylinders
- `ReceptionDesk.tsx` — L-shaped composite of two boxes
- `Whiteboard.tsx` — wall-mounted thin white box (positioned against a wall)
- `FilingCabinet.tsx` — vertical box with 4 horizontal lines for drawers

`components/Furniture/index.tsx` adds these to the type→component map.

### Changed

**`World3D.tsx`** — major simplification:

```tsx
export default function World3D({ spec }: { spec: WorldSpec }) {
  const [chatOpen, setChatOpen] = useState(false);
  // T toggles chat (existing)

  const prims = spec.geometry?.primitives ?? [];
  const ground   = prims.filter(p => p.type === "ground");
  const exterior = prims.filter(p => p.type === "exterior_wall");
  const roof     = prims.filter(p => p.type === "roof");
  const walls    = prims.filter(p => p.type === "wall");
  const floors   = prims.filter(p => p.type === "floor");
  const ceilings = prims.filter(p => p.type === "ceiling");
  const stairs   = prims.filter(p => p.type === "stair");
  // collisions: exterior walls AND interior walls
  const colliders = [...exterior, ...walls];

  const spawn = spec.navigation?.spawnPoint ?? [50, 1.7, -50];

  return (
    <div className="fixed inset-0">
      <Canvas camera={{ fov: 70, position: spawn, near: 0.05, far: 300 }}>
        <ambientLight intensity={0.7} />
        <directionalLight position={[60, 80, 40]} intensity={0.9} />
        {/* sky color */}
        <color attach="background" args={["#a8c8e8"]} />

        <Suspense fallback={null}>
          {ground.map((p, i) => <Plot key={i} size={[p.size[0], p.size[2]]} color="#5a7c3a" />)}
          {floors.map((p, i)   => <mesh key={`f${i}`} position={p.position}><boxGeometry args={p.size}/><meshStandardMaterial color={floorColor(matFloor(p.roomId))}/></mesh>)}
          {ceilings.map((p, i) => <mesh key={`c${i}`} position={p.position}><boxGeometry args={p.size}/><meshStandardMaterial color={matCeil(p.roomId)}/></mesh>)}
          {walls.map((p, i)    => <Wall key={`w${i}`} prim={p} color={matWall(p.roomId)}/>)}
          {exterior.map((p, i) => <Wall key={`e${i}`} prim={p} color="#d8d4c6"/>)}
          {roof.map((p, i)     => <mesh key={`r${i}`} position={p.position}><boxGeometry args={p.size}/><meshStandardMaterial color="#3a3a3a"/></mesh>)}
          {stairs.map((p, i)   => <mesh key={`s${i}`} position={p.position} rotation={[0, p.rotation ?? 0, 0]}><boxGeometry args={[p.size[0], 0.2, p.size[2]]}/><meshStandardMaterial color="#7c5a3a"/></mesh>)}
          {spec.furniture.map(f => <Furniture key={f.id} item={f} tint={hashTint(f.id)} />)}
        </Suspense>

        <PlayerControls walls={colliders} spawn={spawn} />
      </Canvas>

      <CrosshairHUD />
      <StatusBar spec={spec} />
      <ChatPanel open={chatOpen} onClose={() => setChatOpen(false)} worldId={spec.worldId} />
    </div>
  );
}
```

**Click-to-open-furniture-panel removed.** No more `selected` state, no `onClick` on `<Furniture>`, no `<FurniturePanel>`.

**`PlayerControls.tsx`** — collision now handles both exterior and interior walls. **No code change needed**: the `walls` prop already takes `GeometryPrimitive[]` and does AABB checks. We just pass both lists in.

`Wall.tsx` already supports `holes` — entrance hole renders correctly and produces no collider where the door is (because `Wall.tsx` builds segments around the hole, and we'd need to feed those segments — not the unsegmented prim — to the collider). **Decision:** add a small helper `expandWallSegments(prim)` that runs the same segment logic as `Wall.tsx` but returns AABB primitives suitable for collision. Both `Wall.tsx` and the collider import it.

```ts
// frontend/lib/wallSegments.ts
export function expandWallSegments(prim: GeometryPrimitive): GeometryPrimitive[] {
  // same segmentation as Wall.tsx, but returns full prim objects
  // with adjusted position/size per segment
}
```

`World3D.tsx` flattens before passing to `PlayerControls`:
```ts
const colliders = [...exterior.flatMap(expandWallSegments), ...walls.flatMap(expandWallSegments)];
```

This way the player can walk through the entrance hole.

### `lib/worldSpec.ts`
Mirror the Pydantic changes: add `Site`, `Plot`, `Entrance`; remove `Product`, `selectedProductId`, `alternates`, `subtype`, `tint`, `products`.

---

## Section 5 — Tests

### Removed
- `backend/tests/e2e/test_product_urls_live.py` (entire file)
- Any test that asserts `Product` or `selectedProductId` fields exist

### Added (unit)
- `tests/unit/test_site.py`
  - building stays inside plot bounds
  - entrance offset is on the entrance wall
  - default Site computation from Intent
- `tests/unit/test_room_templates.py`
  - every known room type has a template (or `default`)
  - templates produce valid `FurnitureItem` objects
  - templates that don't fit are skipped (no overflow)
- `tests/unit/test_geometry_envelope.py`
  - exterior walls form a closed perimeter (4 walls per floor)
  - ground floor south wall has exactly one entrance hole
  - upper floors' south walls have no entrance hole
  - roof exists and is positioned above the top floor
  - ground primitive exists and matches plot size
- `tests/unit/test_navigation_site.py`
  - spawn point is on the grass (outside building footprint, within plot)
  - spawn faces the entrance (in front of, not behind)
- `tests/unit/test_pricing_sqm.py`
  - cost = sum(room areas) × $1500/sqm
  - byRoom totals match individual rooms

### Updated (e2e)
- `tests/e2e/test_full_pipeline.py`
  - assert `spec.site` is populated
  - assert exterior walls + ground + roof primitives exist
  - assert no `products` field
- `tests/e2e/test_multistory.py`
  - assert exterior walls per floor
  - assert entrance hole only on level 0

---

## Section 6 — Frontend visual targets

The demo should look like this (roughly):

```
                           sky (#a8c8e8)
        ┌────────────────────────────────────┐
        │     ┌──────────────┐               │
        │     │   building   │               │
        │     │              │               │
        │     │   ┌──┐       │               │   ← roof (#3a3a3a)
        │     │   │  │       │               │   ← walls (#d8d4c6)
        │     │   └──┘       │               │
        │     ├──────┴───────┤               │
        │           ↑                        │
        │       entrance                     │
        │      (south wall)                  │   ← grass (#5a7c3a)
        │                                    │
        │           ●  ← spawn               │
        │       (3m south of entrance)       │
        │                                    │
        └────────────────────────────────────┘
                  100m × 100m plot
```

Player spawn: on the grass, 3m south of entrance, looking north toward the door.

---

## Section 7 — What stays the same

- `WorldSpec` as the single source of truth flowing through `f(spec) → spec` agents
- 14 uAgents on Agentverse with Chat Protocol (Fetch.ai track requirement)
- StatusBus + WebSocket activity feed
- Disk hydration of `worlds/<id>.json` for restart safety
- `chat_edit_coordinator` — still produces a new spec from a natural-language edit
- `lighting_designer` and `material_stylist` — same prompts, output applies to interior rooms
- `placement_validator` — validates furniture doesn't overlap walls
- The Gemini structured-output infrastructure (`core/gemini_client.py`)
- Pure-logic separation: `core/` has zero LLM calls

---

## Section 8 — Demo script

Single demo prompt: **"a 3-story tech startup office"**

Expected behavior:
1. User types prompt, hits enter
2. Pipeline runs (status panel streams agent activity)
3. Camera fades up on grass plot, building visible ahead
4. WASD + mouse — player walks across grass to the south entrance
5. Walks through entrance into a lobby (reception desk visible)
6. Walks through corridor; sees offices (desk + chair), conference room (long table), breakroom
7. Stairs to floor 2 — same layout above
8. Walks back outside through the same entrance

Quality bar: it looks like a building, not a maze. The player can complete the loop above without falling through walls or getting stuck.

---

## Section 9 — Open questions / deferred

- **Multiple buildings on a plot.** Easy extension; not in v1.
- **Outdoor furniture** (benches, parking lot). Not in v1.
- **Style tokens.** Mentioned in roadmap; explicitly not in this spec.
- **Functional elevators.** Not in v1; render as solid columns.
- **Window cutouts on exterior walls.** Not in v1; exterior walls are solid except for the entrance.
- **Performance at 10+ floors.** Defer until we see frame drops.
- **Variable plot size.** Defer.
- **Sky / sun / weather.** Out of scope; flat sky color is fine.

---

## Self-review

- [x] No "TBD" / "TODO" placeholders
- [x] Section 2's pipeline reflects Section 1's schema
- [x] `Product` removal called out in schema, bridge, frontend, tests
- [x] Frontend changes match backend output (`ground`, `exterior_wall`, `roof` primitive types)
- [x] Coordinate convention defined once and referenced consistently
- [x] Furniture template path doesn't depend on LLM, matches "generic interior" goal
- [x] uAgent count preserved (Fetch.ai track requirement honored)
- [x] Single demo prompt named in §8 — clear ship target
