from core.world_spec import WorldSpec, Intent
from core.gemini_client import structured
from core.prompts.intent_parser import SYSTEM, USER_TMPL


def run(spec: WorldSpec) -> WorldSpec:
    intent = structured(USER_TMPL.format(prompt=spec.prompt), Intent, system=SYSTEM)
    spec.intent = intent
    return spec
