from core.world_spec import WorldSpec
from core.geometry import build_geometry


def run(spec: WorldSpec) -> WorldSpec:
    assert spec.blueprint is not None and spec.site is not None
    spec.geometry = build_geometry(spec.blueprint, spec.site)
    return spec
