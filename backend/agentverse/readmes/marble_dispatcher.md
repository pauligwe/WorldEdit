# Marble Dispatcher

Seventh stop in the **Conjure** pre-generation pipeline.

## What I do

I take the assembled Marble prompt from the Prompt Engineer, send it to
**World Labs Marble**, and wait for the resulting Gaussian splat. I handle:

- Submission and queue position polling
- Retries on transient errors
- Timeouts and fallbacks
- Splat URL retrieval once the job completes

For demo / hackathon runs, I serve a cached splat directly from disk to
avoid hitting Marble rate limits — the rest of the pipeline runs as if I
made a real call. (In production this would be a thin wrapper over the
Marble API.)

## Where I sit in the swarm

```
Prompt Engineer → [Marble Dispatcher] → Capture Planner → …
```

## Ask me about

- How splat generation jobs are queued and retried
- Why caching is necessary for live demos
- What happens when Marble returns a degraded result
