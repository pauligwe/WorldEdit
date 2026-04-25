"""Procedural floor-plan generator. No LLM call.

Picks a hand-tuned room program per (building_type, level) and feeds it to the
maze packer. Stair (x, y) is threaded across floors so they align vertically.
World ID is mixed into the seed so identical inputs still yield different
layouts per generation.
"""

from core.maze_packer import maze_pack_floor
from core.world_spec import Blueprint, Door, Entrance, Site, WorldSpec


_GRID = 0.5
_FOYER_DOOR_WIDTH = 1.6


def _snap(v: float) -> float:
    return round(v / _GRID) * _GRID


def _shrink_site_to_rooms(spec: WorldSpec) -> None:
    """Tighten the building footprint to the bounding box of placed rooms,
    shift all rooms+stairs so the bbox starts at (0, 0), recenter the building
    on the plot, and add a south-wall door to the foyer matching the entrance.

    Without this, the maze packer leaves large unused regions inside the
    building's exterior walls; doorways into those regions appear to "lead to
    grass" because no room floor covers the gap.
    """
    bp = spec.blueprint
    if bp is None or not bp.floors:
        return

    xs0, ys0, xs1, ys1 = [], [], [], []
    for fl in bp.floors:
        for r in fl.rooms:
            xs0.append(r.x); ys0.append(r.y)
            xs1.append(r.x + r.width); ys1.append(r.y + r.depth)
    if not xs0:
        return

    min_x = _snap(min(xs0))
    min_y = _snap(min(ys0))
    max_x = _snap(max(xs1))
    max_y = _snap(max(ys1))
    new_w = max_x - min_x
    new_d = max_y - min_y

    for fl in bp.floors:
        for r in fl.rooms:
            r.x = _snap(r.x - min_x)
            r.y = _snap(r.y - min_y)
        for s in fl.stairs:
            s.x = _snap(s.x - min_x)
            s.y = _snap(s.y - min_y)

    site = spec.site
    plot_w = site.plot.width
    plot_d = site.plot.depth
    ax = (plot_w - new_w) / 2
    ay = (plot_d - new_d) / 2
    spec.site = Site(
        plot=site.plot,
        buildingFootprint=[new_w, new_d],
        buildingAnchor=[ax, ay],
        entrance=site.entrance,
    )

    # Pick the foyer (or any room flush against the south wall at y=0) and
    # align the entrance to its south face, then punch a matching door.
    ground = bp.floors[0]
    south_rooms = [r for r in ground.rooms if abs(r.y) < 1e-6]
    if not south_rooms:
        return
    south_rooms.sort(key=lambda r: 0 if r.type in ("foyer", "lobby", "entry") else 1)
    foyer = south_rooms[0]

    door_w = min(_FOYER_DOOR_WIDTH, foyer.width - 0.4)
    if door_w < 0.6:
        return
    foyer.doors.append(Door(wall="south", offset=foyer.width / 2, width=door_w))

    entrance_offset = foyer.x + foyer.width / 2
    spec.site.entrance = Entrance(
        wall="south",
        offset=entrance_offset,
        width=door_w,
        height=site.entrance.height,
    )


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
    _shrink_site_to_rooms(spec)
    return spec
