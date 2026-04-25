"""Procedural floor-plan generator. No LLM call.

Picks a hand-tuned room program per (building_type, level) and feeds it to the
maze packer. Stair (x, y) is threaded across floors so they align vertically.
World ID is mixed into the seed so identical inputs still yield different
layouts per generation.
"""

from core.maze_packer import maze_pack_floor
from core.world_spec import Blueprint, WorldSpec


# Hand-tuned room programs per (building_type, level). Floor 0 always starts
# with an entry-style template so the entrance lands on the south edge.
_OFFICE_GROUND = [
    "lobby_modern",
    "office_open_bullpen",
    "conference_small",
    "office_private_small",
    "office_private_small",
    "breakroom",
    "restroom",
]
_OFFICE_UPPER = [
    "office_open_bullpen",
    "conference_large",
    "conference_small",
    "office_private_small",
    "office_private_small",
    "breakroom",
    "restroom",
    "server_room",
]
_HOUSE_GROUND = [
    "house_foyer",
    "living_room",
    "kitchen",
    "dining_room",
    "bathroom",
]
_HOUSE_UPPER = [
    "bedroom",
    "bedroom",
    "bedroom",
    "bathroom",
]
_GENERIC_GROUND = [
    "lobby_modern",
    "office_open_bullpen",
    "conference_small",
    "breakroom",
    "restroom",
]
_GENERIC_UPPER = [
    "office_open_bullpen",
    "conference_small",
    "office_private_small",
    "breakroom",
    "restroom",
]


_RESIDENTIAL_KEYWORDS = (
    "house", "home", "cabin", "cottage", "apartment", "studio",
    "loft", "condo", "mansion", "villa", "bungalow", "townhouse",
    "duplex", "ranch", "colonial",
)
_OFFICE_KEYWORDS = (
    "office", "startup", "workplace", "company", "corporate", "lab",
)


def _classify(spec: WorldSpec) -> str:
    """Returns one of 'house', 'office', 'generic'."""
    bt = (spec.intent.buildingType or "").lower() if spec.intent else ""
    prompt = (spec.prompt or "").lower()
    haystack = f"{bt} {prompt}"
    if any(kw in haystack for kw in _OFFICE_KEYWORDS):
        return "office"
    if any(kw in haystack for kw in _RESIDENTIAL_KEYWORDS):
        return "house"
    return "generic"


def _room_program(category: str, level: int) -> list[str]:
    if category == "office":
        return list(_OFFICE_GROUND if level == 0 else _OFFICE_UPPER)
    if category == "house":
        return list(_HOUSE_GROUND if level == 0 else _HOUSE_UPPER)
    return list(_GENERIC_GROUND if level == 0 else _GENERIC_UPPER)


def run(spec: WorldSpec) -> WorldSpec:
    if spec.intent is None:
        raise ValueError("blueprint_architect requires intent")
    if spec.site is None:
        raise ValueError("blueprint_architect requires site")

    fw, fd = spec.site.buildingFootprint
    target_floors = spec.intent.floors
    entrance_offset = spec.site.entrance.offset
    category = _classify(spec)

    # Mix the worldId into the seed so identical inputs still yield different
    # layouts per generation.
    world_seed = abs(hash(spec.worldId)) % (2**31)

    floors = []
    next_stair_seed: tuple[float, float, float, float] | None = None
    multi_floor = target_floors > 1

    for level in range(target_floors):
        is_last_level = level == target_floors - 1
        templates = _room_program(category, level)

        stair_position = next_stair_seed
        if multi_floor and not is_last_level and stair_position is None:
            # Sentinel so maze_pack_floor knows it should place stairs.
            stair_position = ((fw - 3.0) / 2, (fd - 4.0) / 2, 3.0, 4.0)

        floor, stair_xy = maze_pack_floor(
            templates,
            (fw, fd),
            level=level,
            ceiling_height=3.0,
            stair_position=stair_position,
            entrance_offset=entrance_offset if level == 0 else None,
            seed=world_seed + level + 1,
            is_top_floor=is_last_level,
        )
        floors.append(floor)

        if stair_xy is not None and not is_last_level:
            next_stair_seed = (stair_xy[0], stair_xy[1], 3.0, 4.0)
        else:
            next_stair_seed = None

    spec.blueprint = Blueprint(gridSize=0.5, floors=floors)
    return spec
