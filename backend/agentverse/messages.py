"""uagents.Model message types passed between Coordinator and pre-gen workers.

The pipeline is sequential: Coordinator dispatches a BuildRequest to each
agent in order, awaits a BuildArtifact reply, narrates the result back to
the user via ChatProtocol, then sends the next request.

Each artifact is intentionally small — just a structured summary the
Coordinator can quote in chat. Heavy state stays local.
"""
from typing import Optional
from uagents import Model


class BuildRequest(Model):
    """Coordinator → worker. Contains the user prompt + accumulated context."""
    request_id: str
    prompt: str
    # The end-user's agent address. Workers post their own ChatMessage
    # directly to this address so ASI:One renders each agent's update
    # as a separate bubble from that agent (rather than the coordinator).
    user_address: str = ""
    # Accumulated artifacts from earlier stages, keyed by agent_id. The worker
    # can ignore fields it doesn't need; the dict shape is intentionally loose.
    context: dict = {}


class BuildArtifact(Model):
    """Worker → coordinator. The result of one stage of the pipeline."""
    request_id: str
    agent_id: str
    # One-line headline for ASI:One chat ("✓ Mood: dusk, warm tungsten")
    headline: str
    # Optional structured payload, merged into context for downstream agents.
    payload: dict = {}
    error: Optional[str] = None
