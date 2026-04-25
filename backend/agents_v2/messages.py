"""uagents.Model message types for the agent swarm.

Two transport types route data through the swarm:
- AgentRequest: sent from orchestrator to each agent
- AgentResponse: sent back from each agent to orchestrator

Per-agent output types (SceneDescription, GeolocationResult, etc.) are
nested into AgentResponse.output as plain dicts. We keep them as Pydantic
models for validation when the agents themselves construct results, but
on the wire everything flows as dicts to avoid a combinatorial number of
typed message subclasses.
"""
from typing import Literal, Optional
from uagents import Model
from pydantic import BaseModel


# ---- Transport (uagents.Model — used over Chat Protocol) ----

class PerceptionInput(Model):
    """Initial input to any agent — captured frames + prompt."""
    world_id: str
    prompt: str
    view_paths: list[str]


class AgentRequest(Model):
    """Orchestrator → agent. Contains everything the agent needs to run."""
    world_id: str
    agent_id: str
    prompt: str
    view_paths: list[str]
    upstream: dict = {}


class AgentResponse(Model):
    """Agent → orchestrator. status='done' carries output, 'error' carries error_message."""
    world_id: str
    agent_id: str
    status: Literal["done", "error"]
    duration_ms: int
    output: Optional[dict] = None
    error_message: Optional[str] = None


# ---- Per-agent output schemas (Pydantic — used internally for Gemini structured output) ----

class SceneDescription(BaseModel):
    summary: str
    tags: list[str]


class ObjectInventory(BaseModel):
    objects: list[dict]


class SpatialLayout(BaseModel):
    rooms: list[dict]
    entrances: list[str]
    sightlines: list[str]
    total_sqft_estimate: int


class GeolocationResult(BaseModel):
    candidates: list[dict]


class FilmingScoutResult(BaseModel):
    locations: list[dict]


class EraEstimate(BaseModel):
    period: str
    confidence: float
    reasoning: str


class ArchitecturalStyle(BaseModel):
    style: str
    confidence: float
    reasoning: str


class ShotList(BaseModel):
    shots: list[dict]


class MoodPalette(BaseModel):
    palette: list[str]
    luts: list[str]
    film_stocks: list[str]


class Soundscape(BaseModel):
    ambient: list[str]
    foley: list[str]


class PropShopping(BaseModel):
    items: list[dict]


class SetDressing(BaseModel):
    suggestions: list[dict]


class StorySeed(BaseModel):
    premises: list[dict]


class Characters(BaseModel):
    characters: list[dict]


class NPCDialogue(BaseModel):
    lines: list[dict]


class RealEstate(BaseModel):
    estimated_monthly_rent_usd: int
    market: str
    reasoning: str


class HazardAudit(BaseModel):
    hazards: list[dict]


class Accessibility(BaseModel):
    issues: list[dict]
    suggestions: list[str]


class CarbonScore(BaseModel):
    embodied_carbon_kg_co2e: int
    breakdown: list[dict]
    reasoning: str
