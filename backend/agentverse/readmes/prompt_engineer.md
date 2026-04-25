# Prompt Engineer

Sixth stop in the **Conjure** pre-generation pipeline.

## What I do

I assemble the final, Marble-ready prompt from everything upstream:

- Intent (genre, mood, era, scale, anchors)
- Reference grounding
- Style commitment
- Lighting decisions
- Compositional framing

The output is one weighted prompt block plus modifiers — structured so
Marble's generator emphasizes the right anchors and doesn't drift off
into generic territory.

Typical structure:
```
(primary subject:1.2), supporting elements, anchor objects,
lighting clause, style clause, render-lookalike clause
```

## Where I sit in the swarm

```
Scene Composer → [Prompt Engineer] → Marble Dispatcher → …
```

## Ask me about

- Prompt weighting and modifier ordering
- Negative prompts (what to keep *out*)
- Why assembling late in the pipeline beats writing prompts by hand
- How to push Marble toward a specific look
