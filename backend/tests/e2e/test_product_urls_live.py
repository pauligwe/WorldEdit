import os
import asyncio
import httpx
import pytest
from core.world_spec import WorldSpec
from core.status_bus import StatusBus
from agents.orchestrator import run_pipeline

pytestmark = pytest.mark.skipif(not os.environ.get("GOOGLE_API_KEY"), reason="no Gemini key")


async def test_product_urls_are_live():
    spec = WorldSpec(worldId="urls1", prompt="A small modern cabin with a bedroom and a living room")
    bus = StatusBus()
    out = await run_pipeline(spec, bus)
    urls = [p.url for p in out.products.values() if p.url]
    assert len(urls) >= 3, f"expected >=3 product URLs, got {len(urls)}"
    async with httpx.AsyncClient(follow_redirects=True, timeout=8.0) as client:
        statuses = await asyncio.gather(*[client.head(u) for u in urls], return_exceptions=True)
    ok = sum(1 for s in statuses if not isinstance(s, Exception) and s.status_code == 200)
    assert ok >= max(1, len(urls) // 2), f"too many dead URLs: {ok}/{len(urls)}"
