from core.world_spec import WorldSpec, FurnitureItem
from core.room_templates import apply_template


def run(spec: WorldSpec) -> WorldSpec:
    assert spec.blueprint is not None and spec.site is not None
    items: list[FurnitureItem] = []
    anchor = (spec.site.buildingAnchor[0], spec.site.buildingAnchor[1])
    for fl in spec.blueprint.floors:
        level_y = fl.level * fl.ceilingHeight
        for room in fl.rooms:
            items.extend(apply_template(room, level_y, anchor))
    spec.furniture = items
    return spec
