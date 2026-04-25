from core.world_spec import WorldSpec
from core.validators import validate_blueprint
from core.site_validators import check_site_constraints


class ComplianceError(RuntimeError):
    pass


def run(spec: WorldSpec) -> WorldSpec:
    if spec.blueprint is None:
        raise ValueError("compliance_critic requires blueprint")
    report = validate_blueprint(spec.blueprint)
    errors = list(report.errors)
    if spec.site is not None:
        errors.extend(check_site_constraints(spec))
    if errors:
        raise ComplianceError("; ".join(errors))
    return spec
