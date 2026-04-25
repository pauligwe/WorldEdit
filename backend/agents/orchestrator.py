import asyncio
from typing import Callable
from core.world_spec import WorldSpec
from core.status_bus import StatusBus, AgentStatus

from agents import (
    intent_parser, blueprint_architect, compliance_critic, geometry_builder,
    lighting_designer, material_stylist, furniture_planner, placement_validator,
    product_scout, style_matcher, pricing_estimator, navigation_planner,
)


SEQUENTIAL_STEPS: list[tuple[str, Callable[[WorldSpec], WorldSpec]]] = [
    ("intent_parser", intent_parser.run),
    ("blueprint_architect", blueprint_architect.run),
    ("compliance_critic", compliance_critic.run),
]

PARALLEL_STEP: list[tuple[str, Callable[[WorldSpec], WorldSpec]]] = [
    ("geometry_builder", geometry_builder.run),
    ("lighting_designer", lighting_designer.run),
    ("material_stylist", material_stylist.run),
]

POST_STEPS: list[tuple[str, Callable[[WorldSpec], WorldSpec]]] = [
    ("furniture_planner", furniture_planner.run),
    ("placement_validator", placement_validator.run),
    ("product_scout", product_scout.run),
    ("style_matcher", style_matcher.run),
    ("pricing_estimator", pricing_estimator.run),
    ("navigation_planner", navigation_planner.run),
]


async def _run_step(name: str, fn: Callable[[WorldSpec], WorldSpec], spec: WorldSpec, bus: StatusBus, world_id: str) -> WorldSpec:
    await bus.publish(world_id, AgentStatus(agent=name, state="running"))
    try:
        out = await asyncio.to_thread(fn, spec)
    except Exception as e:
        await bus.publish(world_id, AgentStatus(agent=name, state="error", message=str(e)))
        raise
    await bus.publish(world_id, AgentStatus(agent=name, state="done"))
    return out


async def run_pipeline(spec: WorldSpec, bus: StatusBus) -> WorldSpec:
    world_id = spec.worldId

    for name, fn in SEQUENTIAL_STEPS:
        spec = await _run_step(name, fn, spec, bus, world_id)

    parallel_results: list[WorldSpec] = await asyncio.gather(*[
        _run_step(name, fn, spec.model_copy(deep=True), bus, world_id)
        for name, fn in PARALLEL_STEP
    ])
    for branch in parallel_results:
        if branch.geometry is not None:
            spec.geometry = branch.geometry
        if branch.lighting is not None:
            spec.lighting = branch.lighting
        if branch.materials is not None:
            spec.materials = branch.materials

    for name, fn in POST_STEPS:
        spec = await _run_step(name, fn, spec, bus, world_id)

    return spec
