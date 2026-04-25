"""We don't actually start uagents in tests (would bind ports). We test the
factory that builds agent instances from the manifest."""
from unittest.mock import patch
from agents_v2 import runner
from agents_v2.manifest import AGENTS


def test_builds_one_agent_per_manifest_entry():
    """build_agents returns one Agent object per manifest row, on the right port."""
    with patch.object(runner, "Agent") as MockAgent, \
         patch.object(runner, "Protocol") as MockProto:
        agents = runner.build_agents()
    assert len(agents) == 19
    seen_ports = sorted([call.kwargs["port"] for call in MockAgent.call_args_list])
    assert seen_ports == sorted([a.port for a in AGENTS])


def test_agent_names_are_namespaced():
    """We use 'conjure_<id>' so old + new agents don't collide on Agentverse."""
    with patch.object(runner, "Agent") as MockAgent, \
         patch.object(runner, "Protocol"):
        runner.build_agents()
    seen_names = {call.kwargs["name"] for call in MockAgent.call_args_list}
    assert "conjure_scene_describer" in seen_names
    assert "conjure_carbon_score" in seen_names
