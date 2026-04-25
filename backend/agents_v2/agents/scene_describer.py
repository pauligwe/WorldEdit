"""Tier 0 — Scene Describer.

Reads the 3 perception captures and returns a dense one-paragraph
description plus structured tags. Foundational for most downstream agents.
"""
from pathlib import Path
from agents_v2.messages import AgentRequest, SceneDescription
from core.gemini_client import vision


SYSTEM = (
    "You are a scene description specialist. Look at the 3 captured views of "
    "a 3D world and produce a single dense paragraph describing the scene, "
    "plus 3-8 short structured tags (e.g. 'indoor', 'rustic', 'warm-lit', "
    "'winter', 'wooden')."
)


def run(req: AgentRequest) -> dict:
    images = [("image/jpeg", Path(p).read_bytes()) for p in req.view_paths]
    prompt = (
        f"User-provided generation prompt: {req.prompt!r}\n\n"
        f"Describe this scene in one rich paragraph and emit tags."
    )
    out: SceneDescription = vision(prompt=prompt, images=images, schema=SceneDescription, system=SYSTEM)
    return out.model_dump()
