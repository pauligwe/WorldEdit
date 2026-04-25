from core.world_spec import WorldSpec, Blueprint
from core.floor_packer import (
    BuildingTemplateSelection, pack_floor_plan
)
from core.room_library import ROOM_LIBRARY
from core.gemini_client import structured
from core.prompts.blueprint_architect import SYSTEM, USER_TMPL


def run(spec: WorldSpec) -> WorldSpec:
    if spec.intent is None:
        raise ValueError("blueprint_architect requires intent")
    if spec.site is None:
        raise ValueError("blueprint_architect requires site")

    # 1. LLM picks template names per floor.
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

    # 2. Pack each floor deterministically.
    floors = []
    for fl_sel in selection.floors:
        floor = pack_floor_plan(
            fl_sel.template_names,
            (fw, fd),
            level=fl_sel.level,
            ceiling_height=3.0,
        )
        floors.append(floor)

    spec.blueprint = Blueprint(gridSize=0.5, floors=floors)
    return spec
