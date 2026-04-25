from core.world_spec import WorldSpec
from core.pricing import compute_cost


def run(spec: WorldSpec) -> WorldSpec:
    spec.cost = compute_cost(spec.furniture, spec.products)
    return spec
