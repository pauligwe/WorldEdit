# Roadmap

This is the forward-looking plan. The current state of the repo is described in `ARCHITECTURE.md`.

---

## The pivot: bigger buildings, no real products

**What we're moving away from.** The original spec had us scraping Walmart / Amazon / Wayfair for real product alternates per furniture item, then letting the user click a chair to swap it for a real $X chair on a real vendor page. We built it; it half-worked. Walmart's "HEAD-returns-200, GET-returns-404 for delisted items" behavior, Gemini hallucinating CDN image URLs, and CORS-blocked vendor images all conspired to make the experience flaky.

**What we're moving toward.** Procedural meshes only. Each furniture type has one (eventually a few) good base mesh in `frontend/components/Furniture/`. The pipeline picks a *type* and a *style*, not a product. With that complexity gone, we redirect the saved effort into **scaling up the buildings** — multi-story office buildings, schools, hospitals, retail.

### Why this is the right move

- The fun part of the product is "I typed a thing and walked around it." Real products were a feature in service of a demo, not in service of users.
- Office buildings are a way better stress test of the pipeline (dozens of rooms, repeating floors, elevators, hallways) than a 4-room cabin.
- Procedural meshes are fast, deterministic, and CORS-free. We control the look.

---

## Concrete next steps

### 1. Strip the legacy product path *(small, safe, do first)*

These pieces are dead weight once we commit to the pivot. Removing them unblocks everything else:

- **Backend agents to delete/gut**
  - `agents/product_scout.py` — Gemini grounded search for vendor URLs
  - `agents/style_matcher.py` — picks `selectedProductId`
  - References to both in `agents/orchestrator.py` (remove from `POST_STEPS`)
- **Backend bridge endpoints to delete**
  - `POST /api/select-product`
  - `GET /api/img` (image proxy)
  - `GET /api/img-color` (dominant color)
  - The `_OG_RE`, `_image_cache`, `_color_cache`, `_dominant_color`, `_fetch_og_image` helpers in `bridge/main.py`
- **Schema**
  - Drop `Product` model and `WorldSpec.products`
  - Drop `FurnitureItem.selectedProductId` and `alternates`
  - Drop `Pillow` from `requirements.txt`
- **Frontend**
  - Delete `components/FurniturePanel.tsx` (the side panel for swapping products)
  - Delete `proxiedImage` and `fetchProductColor` in `lib/api.ts`
  - Simplify `World3D.tsx` — `tintForProduct` becomes pure style-based, no async fetch

The `pricing_estimator` should stay, but switch from "sum product prices" to "estimate from furniture type + size" (rough $/sqft model is fine).

### 2. Rich style system (replaces products as the visual variety)

Without products, the way furniture varies is via **style tokens** the agents already pick. Today these are loose strings (`"modern"`, `"rustic"`). Make them first-class:

- Define a `StyleToken` enum in `core/world_spec.py`: `modern | industrial | corporate | scandinavian | midcentury | classical | tech_office | medical | retail`.
- `material_stylist` writes a style token per room.
- Procedural furniture components in `components/Furniture/*` accept `style` as a prop and switch colors/proportions based on it. E.g. `Chair` in `corporate` style is a black mesh-back office chair; in `midcentury` it's tapered wood legs + walnut.
- This is the primary visual surface area going forward — invest in it.

### 3. Office-building primitives

New room types and structural pieces the current model doesn't know about:

- **Room types**: `office`, `cubicle_farm`, `conference_room`, `breakroom`, `lobby`, `corridor`, `restroom`, `server_room`, `reception`.
- **Structural**: `corridor` as a first-class rectangle (long, narrow, doors on both sides). `elevator_shaft` as a vertical column that lines up across floors.
- **Furniture types**: `desk`, `office_chair`, `cubicle_partition`, `whiteboard`, `conference_table`, `monitor`, `printer`, `water_cooler`, `reception_desk`, `filing_cabinet`.

Each new room/furniture type is a ~30-line PR: add to the Pydantic model (or just use a string), add an example to the prompt, add a procedural component.

### 4. Multi-floor at scale

The current `Blueprint.floors: list[Floor]` already supports multi-story, but in practice we've only tested 1–2 floors. For an office building:

- Make `blueprint_architect` reason about **stacked floor plates** — a typical office has a repeating floor (3–20 copies) with a unique ground floor (lobby) and top floor (executive). Prompt should encourage this pattern instead of unique floors.
- Stairs need to align floor-to-floor. Add a validator in `compliance_critic` that checks every stair on level N has a corresponding stair / opening at the same `(x, y)` on level N+1.
- Elevators: a vertical box at consistent `(x, y)` across all floors. Render as a closed shaft with a door per floor. (Functional elevator transport is post-MVP — for now the user uses stairs.)

### 5. Hallway/corridor layout algorithm

The current `blueprint_architect` packs rooms naively. Office buildings are dominated by corridors. Two options:

- **Easy**: tell the LLM "include a central corridor running north-south, with rooms opening off it." Let it do the spatial reasoning. Probably good enough for the demo.
- **Hard**: split the floor plate into "core" (elevators, stairs, restrooms — center), "ring" (corridor), "shell" (rooms along the perimeter). This is how real offices are designed.

Start with easy, fall back to hard if outputs are bad.

### 6. Performance

A 10-floor office with 200 rooms is ~5000 geometry primitives. The frontend currently renders every box as its own `<mesh>`. At that scale we'll need:

- Instanced meshes for repeated furniture (every cubicle has the same desk).
- Frustum culling per room (already free in three.js, but worth verifying).
- Possibly LOD: render distant floors as silhouettes.

Don't optimize until you actually see frame drops. The cabin runs at 60fps with no effort.

---

## Suggested order of attack

1. **Day 1** — Strip the product path. ~half day of deletion, zero new code. Push.
2. **Day 1–2** — Wire `StyleToken` end-to-end. Pick 3 styles, make every furniture component honor them. This is the biggest user-visible quality jump.
3. **Day 2–3** — Add office room types + furniture types. ~10 small PRs.
4. **Day 3–4** — Push `blueprint_architect` toward office layouts (prompt engineering + a few examples in `core/prompts/examples/`).
5. **Day 4–5** — Multi-floor stress test: generate a 5-story office, walk through it, fix what's broken.
6. **Day 5+** — Performance only if needed; otherwise polish.

---

## Things to keep

- The 14-agent uAgent registration. It's the Fetch.ai track requirement and it's already working. Don't touch.
- The status bus + WebSocket activity feed. It's the most fun part of the demo to watch.
- `chat_edit_coordinator` natural-language editing. Becomes more valuable for big buildings ("add a conference room to the third floor") than it ever was for cabins.
- Disk hydration of `worlds/<id>.json`. Generations take 5+ minutes; we cannot lose them on restart.
- The pure-logic split (`core/` is LLM-free). Every time we've broken this, we've regretted it.

---

## Things to throw out without regret

- `Pillow` and the dominant-color path
- `httpx` calls to scrape vendor pages
- The `og:image` regexes
- The "live URL" e2e test (`tests/e2e/test_product_urls_live.py`) — it tests something we're no longer doing
- `frontend/components/FurniturePanel.tsx`
