from unittest.mock import patch
from pathlib import Path
from agents_v2.agents import object_inventory
from agents_v2.messages import AgentRequest, ObjectInventory


def _req(tmp_path):
    for i in range(3):
        (tmp_path / f"v{i}.jpg").write_bytes(b"\xff\xd8\xff\xe0")
    return AgentRequest(
        world_id="cabin", agent_id="object_inventory",
        prompt="cabin", view_paths=[str(tmp_path / f"v{i}.jpg") for i in range(3)],
        upstream={},
    )


def test_returns_object_list(tmp_path):
    fake = ObjectInventory(objects=[
        {"name": "leather couch", "position": "center-left"},
        {"name": "fireplace", "position": "back wall"},
    ])
    with patch.object(object_inventory, "vision", return_value=fake):
        out = object_inventory.run(_req(tmp_path))
    assert len(out["objects"]) == 2
    assert out["objects"][0]["name"] == "leather couch"
