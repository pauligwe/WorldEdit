from pathlib import Path

EXAMPLES_DIR = Path(__file__).parent / "examples"


def _example(name: str) -> str:
    return (EXAMPLES_DIR / name).read_text()


SYSTEM = """You are an architect that produces a JSON Blueprint of a building.

Hard rules - violating these is an error:
- All rooms are axis-aligned rectangles. Use only x, y, width, depth (in meters).
- All values must be multiples of 0.5 (the gridSize).
- Coords: +x = east, +y = north (top-down 2D).
- Every room must have at least one door.
- Doors and windows are positioned by named wall ("north"/"south"/"east"/"west") + offset along that wall.
- Two rooms on the same floor must NOT overlap.
- Adjacent rooms can share walls (have edges touching) - this is encouraged.
- One room on the ground floor must have a south door (the entrance).
- For multi-floor buildings, stairs must appear on both floors with the SAME id, x, y, width, depth, with `direction` flipped and `toLevel` set to the other floor.
- ceilingHeight is normally 3.0.

Respond with valid JSON only, conforming exactly to the Blueprint schema."""

USER_TMPL = """Generate a Blueprint matching this intent:

{intent_json}

Original prompt: "{prompt}"

Use these examples for reference (do NOT copy them verbatim - design a new building):

EXAMPLE 1 (tiny apartment, 1 floor):
{ex1}

EXAMPLE 2 (single-floor house):
{ex2}

EXAMPLE 3 (two-story house):
{ex3}

Output Blueprint JSON now."""


def make_user_prompt(intent_json: str, prompt: str) -> str:
    return USER_TMPL.format(
        intent_json=intent_json,
        prompt=prompt,
        ex1=_example("tiny_apartment.json"),
        ex2=_example("single_floor_house.json"),
        ex3=_example("two_story_house.json"),
    )


REPAIR_TMPL = """The previous Blueprint failed validation:

ERRORS:
{errors}

PREVIOUS JSON:
{previous}

Produce a corrected Blueprint JSON that fixes ALL errors. Output JSON only."""
