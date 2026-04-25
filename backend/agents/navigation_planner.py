from core.world_spec import WorldSpec
from core.navigation import compute_navigation


def run(spec: WorldSpec) -> WorldSpec:
    assert spec.blueprint is not None
    spec.navigation = compute_navigation(spec.blueprint)
    return spec
