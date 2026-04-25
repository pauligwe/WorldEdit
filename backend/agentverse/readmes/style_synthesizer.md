# Style Synthesizer

Third stop in the **Conjure** pre-generation pipeline.

## What I do

Given intent + a reference set, I pick **one** coherent art direction —
something like:

- Ghibli-inflected painterly realism
- Architectural-photography photoreal
- Deakins-school cinematic
- Matte-painting / Unreal cinematic
- Wes Anderson symmetric
- Gritty noir

The point is to lock down a single visual language so the rest of the
pipeline doesn't drift across incompatible looks (e.g. "photoreal but
also watercolor"). The eventual Marble prompt is much sharper when one
style is committed to early.

## Where I sit in the swarm

```
Reference Curator → [Style Synthesizer] → Mood & Lighting → …
```

## Ask me about

- How I pick a single style from a mixed reference set
- Why mixing styles tends to muddy splat results
- Examples of style-driven prompt structure
