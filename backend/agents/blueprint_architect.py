from core.world_spec import WorldSpec, Blueprint
from core.floor_packer import BuildingTemplateSelection
from core.bsp_packer import bsp_pack_floor
from core.archetype_packer import RESIDENTIAL_ARCHETYPES, archetype_pack_floor
from core.room_library import ROOM_LIBRARY
from core.gemini_client import structured
from core.prompts.blueprint_architect import SYSTEM, USER_TMPL


_RESIDENTIAL_TYPES = {
    "house", "home", "cabin", "cottage", "apartment", "studio",
    "loft", "condo", "mansion", "villa", "bungalow", "townhouse",
    "duplex", "ranch", "colonial",
}


def _is_residential(spec: WorldSpec) -> bool:
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


def _run_grid_bsp(spec: WorldSpec) -> WorldSpec:
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

    stair_x = (fw - 3.0) / 2
    stair_y = (fd - 4.0) / 2
    stair_rect = (stair_x, stair_y, 3.0, 4.0) if spec.intent.floors > 1 else None

    floors = []
    for fl_sel in selection.floors:
        floor = bsp_pack_floor(
            fl_sel.template_names,
            (fw, fd),
            level=fl_sel.level,
            ceiling_height=3.0,
            stair_position=stair_rect,
        )
        floors.append(floor)

    spec.blueprint = Blueprint(gridSize=0.5, floors=floors)
    return spec


def run(spec: WorldSpec) -> WorldSpec:
    if spec.intent is None:
        raise ValueError("blueprint_architect requires intent")
    if spec.site is None:
        raise ValueError("blueprint_architect requires site")

    if _is_residential(spec):
        return _run_residential(spec)
    return _run_grid_bsp(spec)
