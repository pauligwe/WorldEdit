from unittest.mock import patch
from agents_v2.agents import prop_shopping
from agents_v2.messages import AgentRequest, PropShopping


def test_returns_items_using_inventory():
    fake = PropShopping(items=[
        {"name": "leather couch", "vendor": "Wayfair", "url": "https://wayfair.com/x", "price_estimate_usd": 1200},
    ])
    with patch.object(prop_shopping, "structured", return_value=fake) as m:
        out = prop_shopping.run(AgentRequest(
            world_id="cabin", agent_id="prop_shopping", prompt="cabin", view_paths=[],
            upstream={"object_inventory": {"objects": [{"name": "leather couch", "position": "center"}]}},
        ))
    assert out["items"][0]["price_estimate_usd"] == 1200
    args, kwargs = m.call_args
    body = kwargs.get("prompt") or (args and args[0]) or ""
    assert "leather couch" in body
