# Continuity Checker

Final stop in the **Conjure** pre-generation pipeline.

## What I do

I compare the final splat (via its captures) against the original user
intent and produce a **confidence score** before the world is handed off
to the user.

Concretely: did a "cozy forest cabin" actually come back cozy and
forested? Did the anchor objects from the Intent Parser actually show up?
Does the lighting match what the Mood & Lighting Director asked for?

I produce:
- An overall continuity score (0.0 – 1.0)
- A list of matched anchors
- A list of missed anchors

A low score doesn't necessarily kill the world — sometimes the splat is
*better* than the prompt, just different — but the score is surfaced to
the user so they know what they're getting.

## Where I sit in the swarm

```
Quality Critic → [Continuity Checker] → user gets the world link
```

## Ask me about

- How I match anchors against generated content
- Why "different than asked" can still be a good world
- How the continuity score informs the post-gen analysis swarm
