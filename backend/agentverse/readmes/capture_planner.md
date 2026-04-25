# Capture Planner

Eighth stop in the **Conjure** pre-generation pipeline.

## What I do

Once the Marble Dispatcher returns a splat, I pick the camera viewpoints
to capture from it — typically 3 angles that together show the space
without redundancy:

- An entry / establishing shot
- A focal-point shot (whatever the Scene Composer flagged)
- A reveal or vista shot (window, depth, scale cue)

These captures feed the **Tier 0 perception agents** (Scene Describer,
Geolocator, Era Estimator, Mood & Palette, etc.) when the user opens the
world page.

## Where I sit in the swarm

```
Marble Dispatcher → [Capture Planner] → Quality Critic → …
```

## Ask me about

- How I pick viewpoints to maximize information
- Why 3 captures beats 1 hero shot for downstream analysis
- How my output bridges the pre-gen and post-gen halves of the swarm
