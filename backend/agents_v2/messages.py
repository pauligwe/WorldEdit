"""uagents.Model message types for the agent swarm.

Two transport types route data through the swarm:
- AgentRequest: sent from orchestrator to each agent
- AgentResponse: sent back from each agent to orchestrator

Per-agent output types (SceneDescription, GeolocationResult, etc.) are
nested into AgentResponse.output as plain dicts. We keep them as Pydantic
models for validation when the agents themselves construct results, but
on the wire everything flows as dicts to avoid a combinatorial number of
typed message subclasses.

Why every nested type is explicit (not `list[dict]`): the Gemini API rejects
JSON schemas containing `additionalProperties`, and Pydantic emits that for
any open-ended dict. Every list-of-objects field needs a typed inner model.
The wrapper class also forces a top-level JSON object, which keeps Gemini
from collapsing single-field schemas into a bare list.

Every top-level output schema ends with `narrative: str` — a 1-2 sentence
reader-friendly summary the agent writes about its own structured output.
The frontend displays this uniformly so users get prose instead of JSON.
The structured fields stay so downstream agents can still consume them.
"""
from typing import Literal, Optional
from uagents import Model
from pydantic import BaseModel, Field


_NARRATIVE_DESC = (
    "A 1-2 sentence reader-friendly summary of this agent's findings. "
    "Write in plain prose for a human user — never quote raw JSON or list "
    "field names. Name specific items, places, characters, materials, or "
    "values from your structured output rather than meta-summarizing what "
    "you produced (e.g. say 'a brass desk lamp and worn leather chair' "
    "instead of 'a list of objects'). If the captures only show the "
    "exterior of a building, say so explicitly."
)


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
    narrative: str = Field(description=_NARRATIVE_DESC)


class InventoryObject(BaseModel):
    name: str
    position: str


class ObjectInventory(BaseModel):
    objects: list[InventoryObject]
    narrative: str = Field(description=_NARRATIVE_DESC)


class Room(BaseModel):
    name: str
    approx_sqft: int


class SpatialLayout(BaseModel):
    rooms: list[Room]
    entrances: list[str]
    sightlines: list[str]
    total_sqft_estimate: int
    narrative: str = Field(description=_NARRATIVE_DESC)


class RegionCandidate(BaseModel):
    region: str
    confidence: float
    reasoning: str = ""


class GeolocationResult(BaseModel):
    candidates: list[RegionCandidate]
    narrative: str = Field(description=_NARRATIVE_DESC)


class FilmingLocation(BaseModel):
    name: str
    address: str = ""
    match_reason: str = ""


class FilmingScoutResult(BaseModel):
    locations: list[FilmingLocation]
    narrative: str = Field(description=_NARRATIVE_DESC)


class EraEstimate(BaseModel):
    period: str
    confidence: float
    reasoning: str
    narrative: str = Field(description=_NARRATIVE_DESC)


class ArchitecturalStyle(BaseModel):
    style: str
    confidence: float
    reasoning: str
    narrative: str = Field(description=_NARRATIVE_DESC)


class Shot(BaseModel):
    name: str
    angle: str
    lens_mm: int
    time_of_day: str
    notes: str = ""


class ShotList(BaseModel):
    shots: list[Shot]
    narrative: str = Field(description=_NARRATIVE_DESC)


class MoodPalette(BaseModel):
    palette: list[str]
    luts: list[str]
    film_stocks: list[str]
    narrative: str = Field(description=_NARRATIVE_DESC)


class Soundscape(BaseModel):
    ambient: list[str]
    foley: list[str]
    narrative: str = Field(description=_NARRATIVE_DESC)


class PropItem(BaseModel):
    name: str
    vendor: str
    url: str = ""
    price_estimate_usd: int


class PropShopping(BaseModel):
    items: list[PropItem]
    narrative: str = Field(description=_NARRATIVE_DESC)


class DressingSuggestion(BaseModel):
    theme: str
    additions: list[str]


class SetDressing(BaseModel):
    suggestions: list[DressingSuggestion]
    narrative: str = Field(description=_NARRATIVE_DESC)


class Premise(BaseModel):
    title: str
    logline: str
    genre: str


class StorySeed(BaseModel):
    premises: list[Premise]
    narrative: str = Field(description=_NARRATIVE_DESC)


class Character(BaseModel):
    name: str
    role: str
    bio: str


class Characters(BaseModel):
    characters: list[Character]
    narrative: str = Field(description=_NARRATIVE_DESC)


class DialogueLine(BaseModel):
    character: str
    line: str


class NPCDialogue(BaseModel):
    lines: list[DialogueLine]
    narrative: str = Field(description=_NARRATIVE_DESC)


class RealEstate(BaseModel):
    estimated_monthly_rent_usd: int
    market: str
    reasoning: str
    narrative: str = Field(description=_NARRATIVE_DESC)


class Hazard(BaseModel):
    type: str
    severity: str
    description: str


class HazardAudit(BaseModel):
    hazards: list[Hazard]
    narrative: str = Field(description=_NARRATIVE_DESC)


class AccessibilityIssue(BaseModel):
    category: str
    description: str


class Accessibility(BaseModel):
    issues: list[AccessibilityIssue]
    suggestions: list[str]
    narrative: str = Field(description=_NARRATIVE_DESC)


class CarbonItem(BaseModel):
    material: str
    kg_co2e: int


class CarbonScore(BaseModel):
    embodied_carbon_kg_co2e: int
    breakdown: list[CarbonItem]
    reasoning: str
    narrative: str = Field(description=_NARRATIVE_DESC)
