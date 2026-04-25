from unittest.mock import patch
from agents_v2.agents import mood_palette
from agents_v2.messages import AgentRequest, MoodPalette


def test_returns_palette():
    fake = MoodPalette(palette=["#3a2a1a","#5e4630","#8a7256","#c2a98c","#e8dcc6"],
                       luts=["FilmConvert Tungsten"], film_stocks=["Kodak Portra 400"])
    with patch.object(mood_palette, "structured", return_value=fake):
        out = mood_palette.run(AgentRequest(
            world_id="cabin", agent_id="mood_palette", prompt="cabin", view_paths=[],
            upstream={"scene_describer": {"summary": "warm cabin", "tags": ["warm"]}},
        ))
    assert len(out["palette"]) == 5
