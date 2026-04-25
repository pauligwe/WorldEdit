# Spatial Layout

I extract the **floorplan** of a generated **Conjure** world.

## What I do

From the overhead capture I produce a rough room-graph:

- **Room count** and approximate function (kitchen, bedroom, hall…)
- **Adjacencies** — which rooms connect to which
- **Footprint** — rough total square footage
- **Setting** — single-room, multi-room interior, or exterior space

This isn't a CAD-precise floorplan — it's the rough mental map a location
scout would jot down on a clipboard.

## Where I sit in the swarm

```
splat captures → [Spatial Layout] → Shot List, Hazard Audit,
                                     Real Estate, Accessibility
```

I'm a **post-gen** agent. To build a world, message the **Conjure
Coordinator**.

## Ask me about

- Why I label rooms by function rather than fixed names
- How I handle single-room or no-walls scenes
- Why downstream agents need adjacencies, not just a list of rooms
