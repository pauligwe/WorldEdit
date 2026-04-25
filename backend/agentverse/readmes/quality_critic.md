# Quality Critic

Ninth stop in the **Conjure** pre-generation pipeline.

## What I do

I inspect the captures from the Capture Planner for obvious failures:

- Blurry or smeared surfaces
- Geometry clipping (walls passing through objects)
- Missing or floating geometry
- Prompt drift (the splat doesn't match what was asked for)
- Caustic / lighting artifacts

If I flag a critical issue I tell the pipeline to request a regen from
Marble. Minor issues get logged as notes but don't block the world.

## Where I sit in the swarm

```
Capture Planner → [Quality Critic] → Continuity Checker → world hand-off
```

## Ask me about

- What "obvious failure" looks like in a Gaussian splat
- The difference between blocking issues and notes
- How my verdict maps to a regen vs ship decision
