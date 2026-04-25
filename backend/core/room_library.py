"""Hand-designed room templates with fixed footprints, doors, and furniture.

Unlike core/room_templates.py (which keys furniture by Room.type), this module
provides full RoomTemplates the LLM can pick from by name. Each template fixes
the room's width/depth, pre-places its doors, and lays out its furniture.

Furniture room_offset semantics match core/room_templates.py: [x, y] from the
room's SW corner (NOT the center), with size [w, h, d]. To stay inside the
footprint, every piece must satisfy `0 <= offset_x` and `offset_x + w <= width`
(same for depth).
"""

from math import pi

from pydantic import BaseModel

from .room_templates import FurnitureTemplate
from .world_spec import Door

# Re-export Door under the spec'd name for callers; the shape is identical.
DoorSpec = Door


class RoomTemplate(BaseModel):
    name: str
    type: str
    width: float
    depth: float
    door_specs: list[DoorSpec]
    furniture: list[FurnitureTemplate]
    description: str


# --------------------------------------------------------------------------- #
# Template definitions
# --------------------------------------------------------------------------- #

_office_private_small = RoomTemplate(
    name="office_private_small",
    type="office",
    width=4.0,
    depth=4.0,
    door_specs=[DoorSpec(wall="south", offset=1.6, width=0.9)],
    furniture=[
        # Desk against north wall, chair tucked in front of it (facing north/desk).
        FurnitureTemplate(
            type="desk", room_offset=[1.3, 2.8], size=[1.4, 0.75, 0.7]
        ),
        FurnitureTemplate(
            type="office_chair", room_offset=[1.7, 1.9],
            size=[0.6, 1.1, 0.6],
        ),
        FurnitureTemplate(
            type="filing_cabinet", room_offset=[3.4, 0.2],
            size=[0.5, 1.2, 0.5],
        ),
    ],
    description=(
        "Single private office (4x4m) with one desk, an office chair, "
        "and a small filing cabinet. South-wall door."
    ),
)


def _bullpen_furniture() -> list[FurnitureTemplate]:
    items: list[FurnitureTemplate] = []
    # 6 desks in 2 rows of 3. Room is 12 wide x 8 deep.
    # Row A (north side, desks face north so chairs sit south of desks).
    # Row B (south side, desks face south so chairs sit north of desks).
    desk_w, desk_h, desk_d = 1.4, 0.75, 0.7
    chair_w, chair_h, chair_d = 0.6, 1.1, 0.6

    col_xs = [1.3, 5.3, 9.3]  # SW-corner x for each desk in a row

    # North row: desks pushed near north wall (depth=8), facing south.
    north_desk_y = 6.6  # 6.6 + 0.7 = 7.3 < 8.0
    north_chair_y = 5.3  # chair sits just south of desk

    for cx in col_xs:
        items.append(FurnitureTemplate(
            type="desk", room_offset=[cx, north_desk_y],
            size=[desk_w, desk_h, desk_d], rotation=pi,
        ))
        items.append(FurnitureTemplate(
            type="office_chair",
            room_offset=[cx + (desk_w - chair_w) / 2, north_chair_y],
            size=[chair_w, chair_h, chair_d], rotation=pi,
        ))

    # South row: desks pushed near south wall, facing north.
    south_desk_y = 0.7
    south_chair_y = 2.0
    for cx in col_xs:
        items.append(FurnitureTemplate(
            type="desk", room_offset=[cx, south_desk_y],
            size=[desk_w, desk_h, desk_d],
        ))
        items.append(FurnitureTemplate(
            type="office_chair",
            room_offset=[cx + (desk_w - chair_w) / 2, south_chair_y],
            size=[chair_w, chair_h, chair_d],
        ))
    return items


_office_open_bullpen = RoomTemplate(
    name="office_open_bullpen",
    type="office",
    width=12.0,
    depth=8.0,
    door_specs=[DoorSpec(wall="south", offset=2.0, width=1.2)],
    furniture=_bullpen_furniture(),
    description=(
        "Open bullpen office (12x8m) with six desks arranged in two rows "
        "of three. South-wall door at offset 2."
    ),
)


_conference_small = RoomTemplate(
    name="conference_small",
    type="conference_room",
    width=5.0,
    depth=4.0,
    door_specs=[DoorSpec(wall="south", offset=2.0, width=1.0)],
    furniture=[
        # Table 2.4 x 1.0 centered: x=(5-2.4)/2=1.3, y=(4-1.0)/2=1.5
        FurnitureTemplate(
            type="conference_table", room_offset=[1.3, 1.5],
            size=[2.4, 0.75, 1.0],
        ),
        # 3 chairs on the north side of the table, 3 on the south.
        FurnitureTemplate(
            type="office_chair", room_offset=[1.4, 2.6],
            size=[0.6, 1.1, 0.6], rotation=pi,
        ),
        FurnitureTemplate(
            type="office_chair", room_offset=[2.2, 2.6],
            size=[0.6, 1.1, 0.6], rotation=pi,
        ),
        FurnitureTemplate(
            type="office_chair", room_offset=[3.0, 2.6],
            size=[0.6, 1.1, 0.6], rotation=pi,
        ),
        FurnitureTemplate(
            type="office_chair", room_offset=[1.4, 0.8],
            size=[0.6, 1.1, 0.6],
        ),
        FurnitureTemplate(
            type="office_chair", room_offset=[2.2, 0.8],
            size=[0.6, 1.1, 0.6],
        ),
        FurnitureTemplate(
            type="office_chair", room_offset=[3.0, 0.8],
            size=[0.6, 1.1, 0.6],
        ),
        # Whiteboard mounted on north wall.
        FurnitureTemplate(
            type="whiteboard", room_offset=[1.6, 3.9],
            size=[1.8, 1.0, 0.05], rotation=pi,
        ),
    ],
    description=(
        "Small conference room (5x4m) with a 6-seat table, "
        "north-wall whiteboard, and a south-wall door."
    ),
)


def _conference_large_furniture() -> list[FurnitureTemplate]:
    items: list[FurnitureTemplate] = []
    # Table: long boardroom 4.8 x 1.2 centered in 8x6 room.
    # x=(8-4.8)/2=1.6, y=(6-1.2)/2=2.4
    items.append(FurnitureTemplate(
        type="conference_table", room_offset=[1.6, 2.4],
        size=[4.8, 0.75, 1.2],
    ))
    # 5 chairs along the north side of the table, 5 along the south.
    chair_xs = [1.7, 2.6, 3.5, 4.4, 5.3]
    for cx in chair_xs:
        items.append(FurnitureTemplate(
            type="office_chair", room_offset=[cx, 3.7],
            size=[0.6, 1.1, 0.6], rotation=pi,
        ))
        items.append(FurnitureTemplate(
            type="office_chair", room_offset=[cx, 1.7],
            size=[0.6, 1.1, 0.6],
        ))
    # Two chairs at the table heads.
    items.append(FurnitureTemplate(
        type="office_chair", room_offset=[0.8, 2.7],
        size=[0.6, 1.1, 0.6], rotation=pi / 2,
    ))
    items.append(FurnitureTemplate(
        type="office_chair", room_offset=[6.6, 2.7],
        size=[0.6, 1.1, 0.6], rotation=-pi / 2,
    ))
    # Two whiteboards on the north wall.
    items.append(FurnitureTemplate(
        type="whiteboard", room_offset=[1.5, 5.9],
        size=[1.8, 1.0, 0.05], rotation=pi,
    ))
    items.append(FurnitureTemplate(
        type="whiteboard", room_offset=[4.7, 5.9],
        size=[1.8, 1.0, 0.05], rotation=pi,
    ))
    return items


_conference_large = RoomTemplate(
    name="conference_large",
    type="conference_room",
    width=8.0,
    depth=6.0,
    door_specs=[DoorSpec(wall="south", offset=3.5, width=1.2)],
    furniture=_conference_large_furniture(),
    description=(
        "Large boardroom (8x6m) with a 12-seat table, dual whiteboards "
        "on the north wall, and a south-wall door."
    ),
)


_lobby_modern = RoomTemplate(
    name="lobby_modern",
    type="lobby",
    width=12.0,
    depth=6.0,
    door_specs=[
        # Entrance from outside — south wall, offset 6 so the doorway
        # straddles x=6..7 (centered on the front of the building).
        DoorSpec(wall="south", offset=5.4, width=1.6),
        # Pass-through to interior corridor on the north wall.
        DoorSpec(wall="north", offset=5.5, width=1.4),
    ],
    furniture=[
        # Reception desk 2.5x1.0 against north wall, centered on x.
        FurnitureTemplate(
            type="reception_desk", room_offset=[4.75, 4.5],
            size=[2.5, 1.0, 0.8], rotation=pi,
        ),
        # Two couches flanking the entrance, 2.2x0.9 deep.
        FurnitureTemplate(
            type="couch", room_offset=[1.0, 0.5],
            size=[2.2, 0.8, 0.9],
        ),
        FurnitureTemplate(
            type="couch", room_offset=[8.8, 0.5],
            size=[2.2, 0.8, 0.9],
        ),
    ],
    description=(
        "Modern lobby (12x6m) with a reception desk against the north wall, "
        "two flanking couches, a south entrance, and a north pass-through door."
    ),
)


_breakroom = RoomTemplate(
    name="breakroom",
    type="breakroom",
    width=6.0,
    depth=5.0,
    door_specs=[DoorSpec(wall="south", offset=2.5, width=1.0)],
    furniture=[
        # Table 1.5x1.0 roughly centered.
        FurnitureTemplate(
            type="table", room_offset=[2.25, 2.0],
            size=[1.5, 0.75, 1.0],
        ),
        # 4 chairs around the table.
        FurnitureTemplate(
            type="chair", room_offset=[2.5, 1.1],
            size=[0.5, 1.0, 0.5],
        ),
        FurnitureTemplate(
            type="chair", room_offset=[2.5, 3.4],
            size=[0.5, 1.0, 0.5], rotation=pi,
        ),
        FurnitureTemplate(
            type="chair", room_offset=[1.4, 2.25],
            size=[0.5, 1.0, 0.5], rotation=pi / 2,
        ),
        FurnitureTemplate(
            type="chair", room_offset=[4.1, 2.25],
            size=[0.5, 1.0, 0.5], rotation=-pi / 2,
        ),
    ],
    description=(
        "Breakroom (6x5m) with a central table seating four. South-wall door."
    ),
)


_corridor_wide = RoomTemplate(
    name="corridor_wide",
    type="corridor",
    width=12.0,
    depth=2.5,
    door_specs=[
        DoorSpec(wall="south", offset=5.5, width=1.0),
        DoorSpec(wall="north", offset=5.5, width=1.0),
    ],
    furniture=[],
    description=(
        "Wide pass-through corridor (12x2.5m) connecting north and south "
        "rooms. No furniture."
    ),
)


_corridor_long = RoomTemplate(
    name="corridor_long",
    type="corridor",
    width=20.0,
    depth=2.0,
    door_specs=[DoorSpec(wall="south", offset=9.5, width=1.0)],
    furniture=[],
    description=(
        "Long corridor (20x2m) with a single south-wall door. "
        "Use for spine hallways."
    ),
)


_restroom = RoomTemplate(
    name="restroom",
    type="restroom",
    width=3.0,
    depth=3.0,
    door_specs=[DoorSpec(wall="south", offset=1.0, width=0.8)],
    furniture=[],
    description=(
        "Compact restroom (3x3m). Walls only by design — fixtures are "
        "implied by the room type. South-wall door."
    ),
)


_server_room = RoomTemplate(
    name="server_room",
    type="server_room",
    width=4.0,
    depth=3.0,
    door_specs=[DoorSpec(wall="south", offset=1.6, width=0.9)],
    furniture=[
        # Two server racks (filing-cabinet shaped) along the east wall.
        FurnitureTemplate(
            type="filing_cabinet", room_offset=[3.4, 0.6],
            size=[0.5, 1.2, 0.5],
        ),
        FurnitureTemplate(
            type="filing_cabinet", room_offset=[3.4, 1.9],
            size=[0.5, 1.2, 0.5],
        ),
    ],
    description=(
        "Server room (4x3m) with two cabinet-shaped racks along the east "
        "wall and a south-wall door."
    ),
)


# --------------------------------------------------------------------------- #
# Residential templates
# --------------------------------------------------------------------------- #

_house_foyer = RoomTemplate(
    name="house_foyer",
    type="foyer",
    width=4.0,
    depth=3.0,
    door_specs=[
        # External entrance.
        DoorSpec(wall="south", offset=1.6, width=1.2),
        # Pass-through to the rest of the house.
        DoorSpec(wall="north", offset=1.6, width=1.0),
    ],
    furniture=[
        # Console table by the entrance + a small plant.
        FurnitureTemplate(
            type="table", room_offset=[0.3, 2.3],
            size=[1.2, 0.8, 0.4],
        ),
        FurnitureTemplate(
            type="plant", room_offset=[3.2, 2.3],
            size=[0.6, 1.2, 0.6],
        ),
    ],
    description="Compact entry foyer (4x3m) with a console table and plant.",
)


_living_room = RoomTemplate(
    name="living_room",
    type="living_room",
    width=6.0,
    depth=5.0,
    door_specs=[DoorSpec(wall="south", offset=2.5, width=1.1)],
    furniture=[
        # Large couch facing south (out of the room toward an imaginary TV).
        FurnitureTemplate(
            type="couch", room_offset=[1.7, 3.4],
            size=[2.6, 0.8, 0.95], rotation=pi,
        ),
        # Coffee table in front of the couch.
        FurnitureTemplate(
            type="table", room_offset=[2.1, 1.9],
            size=[1.8, 0.45, 0.9],
        ),
        # Armchair to the east.
        FurnitureTemplate(
            type="chair", room_offset=[4.6, 2.2],
            size=[0.8, 0.9, 0.8], rotation=-pi / 2,
        ),
        # Bookshelf and lamp on the west wall.
        FurnitureTemplate(
            type="bookshelf", room_offset=[0.2, 2.0],
            size=[1.0, 1.8, 0.4],
        ),
        FurnitureTemplate(
            type="lamp", room_offset=[0.3, 0.3],
            size=[0.4, 1.5, 0.4],
        ),
        # Rug centered.
        FurnitureTemplate(
            type="rug", room_offset=[1.5, 1.0],
            size=[3.0, 0.02, 2.5],
        ),
    ],
    description="Living room (6x5m) with couch, coffee table, armchair, bookshelf, and rug.",
)


_bedroom = RoomTemplate(
    name="bedroom",
    type="bedroom",
    width=4.5,
    depth=4.0,
    door_specs=[DoorSpec(wall="south", offset=1.8, width=0.9)],
    furniture=[
        # Bed against the north wall, head pointing north.
        FurnitureTemplate(
            type="bed", room_offset=[1.25, 1.7],
            size=[2.0, 0.5, 2.2],
        ),
        # Nightstand (table) with a lamp on it (rendered as a separate item).
        FurnitureTemplate(
            type="table", room_offset=[3.5, 2.7],
            size=[0.5, 0.5, 0.5],
        ),
        FurnitureTemplate(
            type="lamp", room_offset=[3.55, 2.75],
            size=[0.3, 0.7, 0.3],
        ),
        # Wardrobe.
        FurnitureTemplate(
            type="bookshelf", room_offset=[0.2, 0.2],
            size=[1.4, 2.0, 0.6],
        ),
    ],
    description="Bedroom (4.5x4m) with bed, nightstand, lamp, and wardrobe.",
)


_kitchen = RoomTemplate(
    name="kitchen",
    type="kitchen",
    width=5.0,
    depth=4.0,
    door_specs=[DoorSpec(wall="south", offset=2.0, width=1.0)],
    furniture=[
        # Counter run along the north wall (filing-cabinet shape gives a
        # cabinet-with-handles look).
        FurnitureTemplate(
            type="filing_cabinet", room_offset=[0.3, 3.2],
            size=[1.2, 0.9, 0.6],
        ),
        FurnitureTemplate(
            type="filing_cabinet", room_offset=[1.6, 3.2],
            size=[1.2, 0.9, 0.6],
        ),
        FurnitureTemplate(
            type="filing_cabinet", room_offset=[2.9, 3.2],
            size=[1.2, 0.9, 0.6],
        ),
        # Fridge — taller cabinet on the right.
        FurnitureTemplate(
            type="filing_cabinet", room_offset=[4.2, 3.0],
            size=[0.6, 1.8, 0.6],
        ),
        # Center island.
        FurnitureTemplate(
            type="table", room_offset=[1.5, 1.4],
            size=[2.0, 0.9, 1.0],
        ),
    ],
    description="Kitchen (5x4m) with a counter run, fridge, and center island.",
)


_dining_room = RoomTemplate(
    name="dining_room",
    type="dining_room",
    width=5.0,
    depth=4.0,
    door_specs=[DoorSpec(wall="south", offset=2.0, width=1.0)],
    furniture=[
        # Dining table (rectangular) centered.
        FurnitureTemplate(
            type="table", room_offset=[1.5, 1.0],
            size=[2.0, 0.75, 2.0],
        ),
        # 4 chairs around it.
        FurnitureTemplate(
            type="chair", room_offset=[1.6, 0.2],
            size=[0.5, 1.0, 0.5],
        ),
        FurnitureTemplate(
            type="chair", room_offset=[2.9, 0.2],
            size=[0.5, 1.0, 0.5],
        ),
        FurnitureTemplate(
            type="chair", room_offset=[1.6, 3.2],
            size=[0.5, 1.0, 0.5], rotation=pi,
        ),
        FurnitureTemplate(
            type="chair", room_offset=[2.9, 3.2],
            size=[0.5, 1.0, 0.5], rotation=pi,
        ),
        # Plant in the corner.
        FurnitureTemplate(
            type="plant", room_offset=[4.3, 0.3],
            size=[0.5, 1.4, 0.5],
        ),
    ],
    description="Dining room (5x4m) with a 4-seat table and a corner plant.",
)


_bathroom = RoomTemplate(
    name="bathroom",
    type="bathroom",
    width=3.0,
    depth=3.0,
    door_specs=[DoorSpec(wall="south", offset=1.0, width=0.8)],
    furniture=[
        # Vanity counter (filing_cabinet shape, low) along the east wall.
        FurnitureTemplate(
            type="filing_cabinet", room_offset=[2.4, 0.4],
            size=[0.5, 0.85, 1.4],
        ),
    ],
    description="Bathroom (3x3m) with a vanity counter against the east wall.",
)


# --------------------------------------------------------------------------- #
# Library + lookup
# --------------------------------------------------------------------------- #

ROOM_LIBRARY: dict[str, RoomTemplate] = {
    t.name: t
    for t in [
        _office_private_small,
        _office_open_bullpen,
        _conference_small,
        _conference_large,
        _lobby_modern,
        _breakroom,
        _corridor_wide,
        _corridor_long,
        _restroom,
        _server_room,
        _house_foyer,
        _living_room,
        _bedroom,
        _kitchen,
        _dining_room,
        _bathroom,
    ]
}


def get_template(name: str) -> RoomTemplate | None:
    """Look up a RoomTemplate by its unique name. Returns None if missing."""
    return ROOM_LIBRARY.get(name)
