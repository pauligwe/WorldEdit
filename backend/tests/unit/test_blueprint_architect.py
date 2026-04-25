import pytest

from agents.blueprint_architect import run
from core.site import derive_site_from_intent
from core.world_spec import Intent, WorldSpec


def _make_spec(world_id: str, prompt: str, intent: Intent) -> WorldSpec:
    return WorldSpec(
        worldId=world_id,
        prompt=prompt,
        intent=intent,
        site=derive_site_from_intent(intent),
    )


def test_run_raises_without_site():
    intent = Intent(
        buildingType="house", style="modern", floors=1, vibe=[],
        sizeHint="small",
    )
    spec = WorldSpec(
        worldId="no-site",
        prompt="A house",
        intent=intent,
        site=None,
    )
    with pytest.raises(ValueError, match="site"):
        run(spec)


def test_house_routes_through_maze_with_residential_rooms():
    intent = Intent(
        buildingType="house", style="modern", floors=1, vibe=[],
        sizeHint="medium",
    )
    spec = _make_spec("t-house", "A cozy modern home with a kitchen", intent)
    out = run(spec)

    assert out.blueprint is not None
    assert len(out.blueprint.floors) == 1
    rooms = out.blueprint.floors[0].rooms
    assert rooms, "house should produce at least one room"
    types = {r.type for r in rooms}
    # The seed should be the residential foyer, and the program should produce
    # at least one of the core residential rooms.
    assert "foyer" in types, f"expected foyer in {types}"
    assert types & {"living_room", "kitchen", "dining_room", "bedroom", "bathroom"}, (
        f"no residential rooms found in {types}"
    )


def test_office_routes_through_maze_with_office_rooms():
    intent = Intent(
        buildingType="office", style="modern", floors=1, vibe=[],
        sizeHint="medium",
    )
    spec = _make_spec("t-office", "A startup office", intent)
    out = run(spec)

    assert out.blueprint is not None
    rooms = out.blueprint.floors[0].rooms
    types = {r.type for r in rooms}
    assert "lobby" in types, f"expected lobby seed in {types}"
    assert types & {"office", "conference_room", "breakroom"}, (
        f"expected office-like rooms in {types}"
    )


def test_two_story_house_aligns_stairs():
    intent = Intent(
        buildingType="house", style="traditional", floors=2, vibe=[],
        sizeHint="medium",
    )
    spec = _make_spec("t-2story", "A two-story family home", intent)
    out = run(spec)

    assert out.blueprint is not None
    assert len(out.blueprint.floors) == 2
    s0 = out.blueprint.floors[0].stairs
    s1 = out.blueprint.floors[1].stairs
    assert s0 and s1
    assert (s0[0].x, s0[0].y) == (s1[0].x, s1[0].y)
