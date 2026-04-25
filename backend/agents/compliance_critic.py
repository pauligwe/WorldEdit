from core.world_spec import WorldSpec
from core.validators import validate_blueprint


class ComplianceError(RuntimeError):
    pass


def run(spec: WorldSpec) -> WorldSpec:
    if spec.blueprint is None:
        raise ValueError("compliance_critic requires blueprint")
    report = validate_blueprint(spec.blueprint)
    if not report.ok:
        raise ComplianceError("; ".join(report.errors))
    return spec
