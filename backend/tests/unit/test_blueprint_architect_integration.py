"""End-to-end test for the procedural maze-pack path of blueprint_architect.

No mocking required — the floor program is hand-tuned per building type, so
this test runs without an API key and verifies the full output is structurally
walkable: every room reachable from the entrance, stairs aligned across all
floors, no connectivity errors.
"""

from agents.blueprint_architect import run
from core.floor_connectivity import validate_floor_connectivity
from core.site import derive_site_from_intent
from core.world_spec import Intent, WorldSpec


def _make_office_spec(world_id: str, floors: int) -> WorldSpec:
    intent = Intent(
        buildingType="office",
        style="modern",
        floors=floors,
        vibe=["collaborative"],
        sizeHint="medium",
    )
    return WorldSpec(
        worldId=world_id,
        prompt="A tech startup office",
        intent=intent,
        site=derive_site_from_intent(intent),
    )


def test_three_story_office_stairs_align_across_all_floors():
    out = run(_make_office_spec("t-3floor", floors=3))

    assert out.blueprint is not None
    assert len(out.blueprint.floors) == 3

    for fl in out.blueprint.floors:
        assert fl.stairs, f"floor {fl.level} has no stairs"

    coords = {(s.x, s.y) for fl in out.blueprint.floors for s in fl.stairs}
    assert len(coords) == 1, (
        f"stairs are not aligned: distinct positions {coords}"
    )

    floors_by_level = {fl.level: fl for fl in out.blueprint.floors}
    assert len(floors_by_level[0].stairs) == 1
    assert floors_by_level[0].stairs[0].direction == "north"

    assert len(floors_by_level[1].stairs) == 2
    dirs_l1 = sorted(s.direction for s in floors_by_level[1].stairs)
    assert dirs_l1 == ["north", "south"]

    assert len(floors_by_level[2].stairs) == 1
    assert floors_by_level[2].stairs[0].direction == "south"


def test_three_story_office_passes_floor_connectivity():
    out = run(_make_office_spec("t-3floor-conn", floors=3))
    errors = validate_floor_connectivity(out.blueprint, out.site)
    assert not errors, f"floor connectivity errors: {errors}"


def test_two_story_office_passes_floor_connectivity():
    out = run(_make_office_spec("t-2floor", floors=2))

    assert out.blueprint and len(out.blueprint.floors) == 2
    errors = validate_floor_connectivity(out.blueprint, out.site)
    assert not errors, f"floor connectivity errors: {errors}"

    s0 = out.blueprint.floors[0].stairs
    s1 = out.blueprint.floors[1].stairs
    assert s0 and s1
    assert (s0[0].x, s0[0].y) == (s1[0].x, s1[0].y)


def test_one_story_office_has_no_stairs():
    out = run(_make_office_spec("t-1floor", floors=1))
    assert out.blueprint and len(out.blueprint.floors) == 1
    assert out.blueprint.floors[0].stairs == []
    errors = validate_floor_connectivity(out.blueprint, out.site)
    assert not errors, f"floor connectivity errors: {errors}"


def test_different_world_ids_produce_different_layouts():
    """Verify the worldId-mixed seed actually varies layouts."""
    a = run(_make_office_spec("world-a", floors=2))
    b = run(_make_office_spec("world-b", floors=2))
    coords_a = [(r.x, r.y) for fl in a.blueprint.floors for r in fl.rooms]
    coords_b = [(r.x, r.y) for fl in b.blueprint.floors for r in fl.rooms]
    assert coords_a != coords_b, "two world IDs produced identical layouts"
