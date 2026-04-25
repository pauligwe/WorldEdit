from agents_v2.messages import (
    PerceptionInput, AgentRequest, AgentResponse,
    SceneDescription, ObjectInventory, SpatialLayout,
    GeolocationResult, FilmingScoutResult,
    EraEstimate, ArchitecturalStyle,
    ShotList, MoodPalette, Soundscape, PropShopping, SetDressing,
    StorySeed, Characters, NPCDialogue,
    RealEstate, HazardAudit, Accessibility, CarbonScore,
)


def test_perception_input_roundtrip():
    p = PerceptionInput(
        world_id="cabin", prompt="rustic cabin",
        view_paths=["/a.jpg", "/b.jpg", "/c.jpg"],
    )
    assert p.world_id == "cabin"
    assert len(p.view_paths) == 3


def test_agent_request_carries_upstream_outputs():
    req = AgentRequest(
        world_id="cabin",
        agent_id="filming_scout",
        prompt="rustic cabin",
        view_paths=["/a.jpg"],
        upstream={"geolocator": {"candidates": [{"region": "PNW", "confidence": 0.7}]}},
    )
    assert req.upstream["geolocator"]["candidates"][0]["region"] == "PNW"


def test_agent_response_done_shape():
    r = AgentResponse(
        world_id="cabin",
        agent_id="scene_describer",
        status="done",
        output={"summary": "x", "tags": []},
        duration_ms=1234,
    )
    assert r.status == "done"
    assert r.error_message is None


def test_agent_response_error_shape():
    r = AgentResponse(
        world_id="cabin",
        agent_id="scene_describer",
        status="error",
        error_message="boom",
        duration_ms=42,
    )
    assert r.output is None


def test_scene_description_fields():
    s = SceneDescription(summary="A rustic cabin", tags=["rustic", "warm"])
    assert s.summary
    assert "rustic" in s.tags


def test_geolocation_candidate_shape():
    g = GeolocationResult(candidates=[
        {"region": "PNW", "confidence": 0.7, "reasoning": "conifers"},
    ])
    assert g.candidates[0]["confidence"] == 0.7
