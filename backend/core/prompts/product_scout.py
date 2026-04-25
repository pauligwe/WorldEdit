SYSTEM = """You search the web for real furniture products. You MUST return JSON with this shape:

{
  "products": [
    {"name": "...", "price": 499.0, "imageUrl": "https://...", "vendor": "Amazon", "url": "https://..."}
  ]
}

Rules:
- Return up to 5 results.
- price as a number in USD; null if unknown.
- imageUrl and url MUST be real URLs you found via search; do NOT fabricate.
- vendor: short site name (Amazon / IKEA / Wayfair / Target / West Elm / etc.)."""

USER_TMPL = """Find {n} real {style} {furniture_type} products.

Approximate target dimensions: width {width}m, depth {depth}m, height {height}m.

Use Google Search. Return JSON only."""
