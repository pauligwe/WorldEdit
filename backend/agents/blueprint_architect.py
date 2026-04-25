from core.world_spec import WorldSpec, Blueprint
from core.floor_packer import BuildingTemplateSelection
from core.maze_packer import maze_pack_floor
from core.archetype_packer import RESIDENTIAL_ARCHETYPES, archetype_pack_floor
from core.room_library import ROOM_LIBRARY
from core.gemini_client import structured
from core.prompts.blueprint_architect import SYSTEM, USER_TMPL


_RESIDENTIAL_TYPES = {
    "house", "home", "cabin", "cottage", "apartment", "studio",
    "loft", "condo", "mansion", "villa", "bungalow", "townhouse",
    "duplex", "ranch", "colonial",
}

_COMMERCIAL_PROMPT_OVERRIDES = (
    "office", "startup", "workplace", "company", "corporate",
    "school", "classroom", "university", "library", "hospital",
    "clinic", "hotel", "mall", "store", "shop", "restaurant",
    "museum", "warehouse", "lab", "factory",
)


def _is_residential(spec: WorldSpec) -> bool:
    prompt = (spec.prompt or "").lower()
    if any(kw in prompt for kw in _COMMERCIAL_PROMPT_OVERRIDES):
        return False
    bt = (spec.intent.buildingType or "").lower() if spec.intent else ""
    return bt in _RESIDENTIAL_TYPES


def _pick_archetype(spec: WorldSpec) -> str:
    floors = spec.intent.floors if spec.intent else 1
    bt = (spec.intent.buildingType or "").lower() if spec.intent else ""
    prompt = (spec.prompt or "").lower()

    if "studio" in bt or "studio" in prompt:
        return "studio"
    if "loft" in bt or "loft" in prompt:
        return "loft"
    if "colonial" in bt or "colonial" in prompt or floors >= 2:
        return "two_story_colonial"
    return "ranch"


def _run_residential(spec: WorldSpec) -> WorldSpec:
    archetype = _pick_archetype(spec)
    arch_spec = RESIDENTIAL_ARCHETYPES[archetype]
    num_floors = len(arch_spec.floors)

    floors = [
        archetype_pack_floor(archetype, level=lvl, ceiling_height=3.0)
        for lvl in range(num_floors)
    ]

    fw, fd = arch_spec.footprint
    spec.site.buildingFootprint = (fw, fd)
    spec.intent.floors = num_floors

    spec.blueprint = Blueprint(gridSize=0.5, floors=floors)
    return spec


def _run_grid_maze(spec: WorldSpec) -> WorldSpec:
    catalog = "\n".join(
        f"- {name}: {t.description} ({t.width}m x {t.depth}m, type={t.type})"
        for name, t in ROOM_LIBRARY.items()
    )
    fw, fd = spec.site.buildingFootprint
    user_prompt = USER_TMPL.format(
        prompt=spec.prompt,
        building_type=spec.intent.buildingType,
        style=spec.intent.style,
        floors=spec.intent.floors,
        footprint_w=fw,
        footprint_d=fd,
        catalog=catalog,
    )
    selection = structured(user_prompt, BuildingTemplateSelection, system=SYSTEM)

    entrance_offset = spec.site.entrance.offset

    floors = []
    # Stair from level N becomes the seed/landing position on level N+1.
    next_stair_seed: tuple[float, float, float, float] | None = None
    multi_floor = spec.intent.floors > 1

    for fl_sel in sorted(selection.floors, key=lambda f: f.level):
        is_last_level = fl_sel.level == spec.intent.floors - 1
        # Multi-floor: every level except the topmost emits stairs upward.
        stair_position = next_stair_seed
        if multi_floor and not is_last_level and stair_position is None:
            # Sentinel so maze_pack_floor knows it should place stairs.
            stair_position = ((fw - 3.0) / 2, (fd - 4.0) / 2, 3.0, 4.0)

        floor, stair_xy = maze_pack_floor(
            fl_sel.template_names,
            (fw, fd),
            level=fl_sel.level,
            ceiling_height=3.0,
            stair_position=stair_position,
            entrance_offset=entrance_offset if fl_sel.level == 0 else None,
            seed=fl_sel.level + 1,
        )
        floors.append(floor)

        if stair_xy is not None and not is_last_level:
            next_stair_seed = (stair_xy[0], stair_xy[1], 3.0, 4.0)
        else:
            next_stair_seed = None

    spec.blueprint = Blueprint(gridSize=0.5, floors=floors)
    return spec


def run(spec: WorldSpec) -> WorldSpec:
    if spec.intent is None:
        raise ValueError("blueprint_architect requires intent")
    if spec.site is None:
        raise ValueError("blueprint_architect requires site")

    if _is_residential(spec):
        return _run_residential(spec)
    return _run_grid_maze(spec)
