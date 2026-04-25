from core.world_spec import WorldSpec, Intent
from core.gemini_client import structured
from core.prompts.intent_parser import SYSTEM, USER_TMPL
from core.site import derive_site_from_intent


def run(spec: WorldSpec) -> WorldSpec:
    intent = structured(USER_TMPL.format(prompt=spec.prompt), Intent, system=SYSTEM)
    spec.intent = intent
    spec.site = derive_site_from_intent(intent)
    return spec
