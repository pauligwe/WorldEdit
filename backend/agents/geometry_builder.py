from core.world_spec import WorldSpec
from core.geometry import build_geometry


def run(spec: WorldSpec) -> WorldSpec:
    if spec.blueprint is None:
        raise ValueError("geometry_builder requires blueprint")
    spec.geometry = build_geometry(spec.blueprint)
    return spec
