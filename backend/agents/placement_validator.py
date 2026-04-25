from core.world_spec import WorldSpec
from core.placement import validate_and_fix_placements


def run(spec: WorldSpec) -> WorldSpec:
    assert spec.blueprint is not None
    spec.furniture = validate_and_fix_placements(spec.furniture, spec.blueprint)
    return spec
