from .world_spec import WorldSpec, Cost

COST_PER_SQM = 1500.0


def compute_cost(spec: WorldSpec) -> Cost:
    by_room: dict[str, float] = {}
    total = 0.0
    if spec.blueprint:
        for fl in spec.blueprint.floors:
            for r in fl.rooms:
                area = r.width * r.depth
                cost = area * COST_PER_SQM
                by_room[r.id] = cost
                total += cost
    return Cost(total=total, byRoom=by_room)
