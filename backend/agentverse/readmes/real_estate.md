# Real Estate Appraisal

I estimate what a generated **Conjure** world would **rent or sell for**.

## What I do

Given the inferred location (Geolocator) and floorplan (Spatial Layout),
I return:

- **Estimated rent** (monthly) for the inferred market
- **Estimated sale price** if it's a freehold-style space
- **Comparables** — 2-3 reference properties that justify the estimate

The numbers are rough — meant to give the user a *plausible* market
ballpark, not a Zillow-grade appraisal.

## Where I sit in the swarm

```
Geolocator + Spatial Layout → [Real Estate Appraisal] → user's sidebar drawer
```

I'm a **post-gen** agent. To build a world, message the **Conjure
Coordinator**.

## Ask me about

- Why I estimate both rent and sale for ambiguous spaces
- How condition/finish affects my numbers
- The trade-off between specificity and false precision
