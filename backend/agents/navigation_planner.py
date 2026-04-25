from core.world_spec import WorldSpec
from core.navigation import compute_navigation


def run(spec: WorldSpec) -> WorldSpec:
    spec.navigation = compute_navigation(spec)
    return spec
