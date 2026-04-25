from pydantic import BaseModel
from core.world_spec import WorldSpec
from core.gemini_client import structured
from core.prompts.chat_edit_coordinator import SYSTEM, USER_TMPL


class _NewPrompt(BaseModel):
    prompt: str


def run(spec: WorldSpec, edit: str) -> WorldSpec:
    out = structured(USER_TMPL.format(prompt=spec.prompt, edit=edit), _NewPrompt, system=SYSTEM)
    spec.prompt = out.prompt
    return spec
