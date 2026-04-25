from agents_v2.manifest import AGENTS, AgentDef


def test_exactly_19_agents():
    assert len(AGENTS) == 19


def test_unique_ids_and_ports():
    ids = [a.id for a in AGENTS]
    ports = [a.port for a in AGENTS]
    assert len(set(ids)) == 19
    assert len(set(ports)) == 19


def test_ports_in_expected_range():
    for a in AGENTS:
        assert 8100 <= a.port <= 8118


def test_dependencies_reference_known_ids():
    ids = {a.id for a in AGENTS}
    for a in AGENTS:
        for dep in a.dependencies:
            assert dep in ids, f"{a.id} depends on unknown {dep}"


def test_no_dependency_cycles():
    by_id = {a.id: a for a in AGENTS}
    visited = set()
    stack = set()

    def visit(node_id: str):
        if node_id in stack:
            raise AssertionError(f"cycle through {node_id}")
        if node_id in visited:
            return
        stack.add(node_id)
        for dep in by_id[node_id].dependencies:
            visit(dep)
        stack.remove(node_id)
        visited.add(node_id)

    for a in AGENTS:
        visit(a.id)


def test_tier_0_has_no_deps():
    tier0 = [a for a in AGENTS if a.tier == 0]
    assert len(tier0) == 3
    for a in tier0:
        assert a.dependencies == []


def test_known_agent_ids_present():
    ids = {a.id for a in AGENTS}
    expected = {
        "scene_describer", "object_inventory", "spatial_layout",
        "geolocator", "filming_scout", "era_estimator", "architectural_style",
        "shot_list", "mood_palette", "soundscape", "prop_shopping", "set_dressing",
        "story_seed", "character_suggester", "npc_dialogue",
        "real_estate", "hazard_audit", "accessibility", "carbon_score",
    }
    assert ids == expected
