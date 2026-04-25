from core.world_spec import WorldSpec, Blueprint
from core.gemini_client import structured
from core.validators import validate_blueprint
from core.prompts.blueprint_architect import SYSTEM, make_user_prompt, REPAIR_TMPL


def run(spec: WorldSpec) -> WorldSpec:
    if spec.intent is None:
        raise ValueError("blueprint_architect requires intent")
    intent_json = spec.intent.model_dump_json(indent=2)
    bp = structured(make_user_prompt(intent_json, spec.prompt), Blueprint, system=SYSTEM)

    report = validate_blueprint(bp)
    if not report.ok:
        repair = REPAIR_TMPL.format(
            errors="\n".join(f"- {e}" for e in report.errors),
            previous=bp.model_dump_json(indent=2),
        )
        bp = structured(repair, Blueprint, system=SYSTEM)

    spec.blueprint = bp
    return spec
