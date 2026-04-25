"""Sanity-check that the agentverse registry covers every post-gen agent
in the v2 manifest. The manifest drives orchestration; the registry drives
mailbox/Agentverse presence — they need to stay in lockstep.
"""
from agents_v2.manifest import AGENTS
from agentverse.registry import POST_GEN_BY_ID, POST_GEN_WORKERS


def test_registry_covers_every_manifest_agent():
    """Every v2-orchestrator agent has a matching mailbox-backed wrapper."""
    manifest_ids = {a.id for a in AGENTS}
    registry_ids = set(POST_GEN_BY_ID)
    missing = manifest_ids - registry_ids
    extra = registry_ids - manifest_ids
    assert not missing, f"manifest agents missing from registry: {missing}"
    assert not extra, f"registry agents not in manifest: {extra}"


def test_post_gen_ports_are_unique_and_in_band():
    """Ports 8101-8119 are reserved for post-gen mailbox wrappers."""
    ports = [a.port for a in POST_GEN_WORKERS]
    assert len(set(ports)) == len(ports), "duplicate ports"
    for p in ports:
        assert 8100 <= p <= 8199, f"post-gen port {p} outside 81xx band"


def test_post_gen_seeds_are_unique():
    """Distinct seeds → distinct on-network addresses."""
    seeds = [a.seed for a in POST_GEN_WORKERS]
    assert len(set(seeds)) == len(seeds), "duplicate seeds would collide on Agentverse"
