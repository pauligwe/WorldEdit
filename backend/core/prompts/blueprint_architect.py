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

Valid room types include:
- Residential: bedroom, living_room, kitchen, bathroom, dining_room, hallway, garage, utility, storage
- Office/commercial: lobby, corridor, office, conference_room, breakroom, restroom, stairwell, reception

Example for "a 3-story tech startup office" (footprint 40×25):
{
  "gridSize": 0.5,
  "floors": [
    {"level": 0, "ceilingHeight": 3.0, "rooms": [
      {"id": "lobby", "type": "lobby", "x": 0, "y": 0, "width": 40, "depth": 8,
       "doors": [{"wall": "south", "offset": 20, "width": 1.6},
                 {"wall": "north", "offset": 20, "width": 1.5}]},
      {"id": "corr0", "type": "corridor", "x": 0, "y": 8, "width": 40, "depth": 2,
       "doors": [{"wall": "south", "offset": 20, "width": 1.5},
                 {"wall": "north", "offset": 5, "width": 1},
                 {"wall": "north", "offset": 35, "width": 1}]},
      {"id": "off0a", "type": "office", "x": 0, "y": 10, "width": 10, "depth": 15,
       "doors": [{"wall": "south", "offset": 5, "width": 1}]},
      {"id": "conf0", "type": "conference_room", "x": 10, "y": 10, "width": 20, "depth": 15,
       "doors": [{"wall": "south", "offset": 10, "width": 1}]},
      {"id": "off0b", "type": "office", "x": 30, "y": 10, "width": 10, "depth": 15,
       "doors": [{"wall": "south", "offset": 5, "width": 1}]}
    ], "stairs": [{"id": "stair", "x": 18, "y": 0.5, "width": 2, "depth": 4,
                   "direction": "north", "toLevel": 1}]},
    {"level": 1, "ceilingHeight": 3.0, "rooms": [...similar layout...],
     "stairs": [{"id": "stair", "x": 18, "y": 0.5, "width": 2, "depth": 4,
                 "direction": "north", "toLevel": 0}]},
    {"level": 2, "ceilingHeight": 3.0, "rooms": [...]}
  ]
}

Respond with valid JSON only, conforming exactly to the Blueprint schema."""

USER_TMPL = """Generate a Blueprint matching this intent:

{intent_json}

Original prompt: "{prompt}"

The building footprint is {footprint_w} m × {footprint_d} m.
ALL rooms (on every floor) MUST fit inside this footprint.
The ground floor MUST contain a room with a SOUTH-facing door at offset {entrance_offset} m
(width {entrance_width} m). This is the building entrance.

Use these examples for reference (do NOT copy them verbatim - design a new building):

EXAMPLE 1 (tiny apartment, 1 floor):
{ex1}

EXAMPLE 2 (single-floor house):
{ex2}

EXAMPLE 3 (two-story house):
{ex3}

Output Blueprint JSON now."""


def make_user_prompt(
    intent_json: str,
    prompt: str,
    footprint_w: float,
    footprint_d: float,
    entrance_offset: float,
    entrance_width: float,
) -> str:
    return USER_TMPL.format(
        intent_json=intent_json,
        prompt=prompt,
        footprint_w=footprint_w,
        footprint_d=footprint_d,
        entrance_offset=entrance_offset,
        entrance_width=entrance_width,
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
