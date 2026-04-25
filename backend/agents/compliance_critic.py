from core.world_spec import WorldSpec
from core.validators import validate_blueprint
from core.site_validators import check_site_constraints
from core.floor_connectivity import validate_floor_connectivity


class ComplianceError(RuntimeError):
    pass


def run(spec: WorldSpec) -> WorldSpec:
    if spec.blueprint is None:
        raise ValueError("compliance_critic requires blueprint")
    report = validate_blueprint(spec.blueprint)
    errors = list(report.errors)
    if spec.site is not None:
        errors.extend(check_site_constraints(spec))
        errors.extend(validate_floor_connectivity(spec.blueprint, spec.site))
    if errors:
        raise ComplianceError("; ".join(errors))
    return spec
