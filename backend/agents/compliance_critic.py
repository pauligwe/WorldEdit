from core.world_spec import WorldSpec
from core.validators import validate_blueprint
from core.site_validators import check_site_constraints
from core.floor_connectivity import validate_floor_connectivity


class ComplianceError(RuntimeError):
    pass


def _snap_entrance_to_blueprint(spec: WorldSpec) -> None:
    """If the blueprint has any south-facing door on a ground-floor room that
    sits on the south edge, override spec.site.entrance to match that door.

    This makes the pipeline robust to LLM blueprints that don't honor the
    pre-computed entrance offset — we accept whatever door the architect drew.
    """
    if spec.site is None or spec.blueprint is None:
        return
    ground = next((f for f in spec.blueprint.floors if f.level == 0), None)
    if ground is None:
        return
    e = spec.site.entrance
    for r in ground.rooms:
        # only consider rooms whose `wall`-side touches the relevant edge
        if e.wall == "south" and abs(r.y) > 1e-6:
            continue
        for d in r.doors:
            if d.wall != e.wall:
                continue
            spec.site.entrance.offset = r.x + d.offset + d.width / 2
            spec.site.entrance.width = d.width
            return


def run(spec: WorldSpec) -> WorldSpec:
    if spec.blueprint is None:
        raise ValueError("compliance_critic requires blueprint")
    _snap_entrance_to_blueprint(spec)
    report = validate_blueprint(spec.blueprint)
    errors = list(report.errors)
    if spec.site is not None:
        errors.extend(check_site_constraints(spec))
    if spec.site is not None:
        errors.extend(validate_floor_connectivity(spec.blueprint, spec.site))
    if errors:
        raise ComplianceError("; ".join(errors))
    return spec
