"""Hand-authored residential floor archetypes.

Each archetype is a fixed shape (room rectangles + doors + optional stairwell).
Use ``archetype_pack_floor(name, level)`` to retrieve a ``Floor`` for a given
level. No randomness; identical inputs always yield identical floors.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from .world_spec import Door, Floor, Room, Stairs


class _RoomSpec(BaseModel):
    role: str
    type: str
    x: float
    y: float
    width: float = Field(gt=0)
    depth: float = Field(gt=0)
    doors: list[Door] = Field(default_factory=list)


class _FloorSpec(BaseModel):
    rooms: list[_RoomSpec]


class ArchetypeSpec(BaseModel):
    name: str
    footprint: tuple[float, float]
    floors: list[_FloorSpec]
    stair_position: Optional[tuple[float, float]] = None
    stair_size: tuple[float, float] = (2.0, 3.0)


# --------------------------------------------------------------------------- #
# Ranch: single story, 14 x 9
# --------------------------------------------------------------------------- #

_ranch = ArchetypeSpec(
    name="ranch",
    footprint=(14.0, 9.0),
    floors=[
        _FloorSpec(rooms=[
            _RoomSpec(
                role="living", type="living_room",
                x=0.0, y=0.0, width=8.0, depth=5.0,
                doors=[
                    Door(wall="south", offset=3.5, width=1.6),
                    Door(wall="north", offset=7.0, width=0.9),
                    Door(wall="east", offset=2.0, width=0.9),
                ],
            ),
            _RoomSpec(
                role="kitchen", type="kitchen",
                x=8.0, y=0.0, width=6.0, depth=5.0,
                doors=[
                    Door(wall="west", offset=2.0, width=0.9),
                    Door(wall="north", offset=1.5, width=0.9),
                ],
            ),
            _RoomSpec(
                role="bedroom", type="bedroom",
                x=0.0, y=5.0, width=6.0, depth=4.0,
                doors=[
                    Door(wall="east", offset=2.0, width=0.9),
                ],
            ),
            _RoomSpec(
                role="hallway", type="hallway",
                x=6.0, y=5.0, width=2.0, depth=4.0,
                doors=[
                    Door(wall="south", offset=1.0, width=0.9),
                    Door(wall="west", offset=2.0, width=0.9),
                    Door(wall="east", offset=2.0, width=0.9),
                ],
            ),
            _RoomSpec(
                role="bathroom", type="bathroom",
                x=8.0, y=5.0, width=3.0, depth=4.0,
                doors=[
                    Door(wall="west", offset=2.0, width=0.9),
                    Door(wall="south", offset=1.5, width=0.9),
                ],
            ),
        ]),
    ],
)


# --------------------------------------------------------------------------- #
# Two-story colonial: 12 x 10, stair (5,4) 2x3
# --------------------------------------------------------------------------- #

_colonial_level0 = _FloorSpec(rooms=[
    _RoomSpec(
        role="living", type="living_room",
        x=0.0, y=0.0, width=5.0, depth=5.0,
        doors=[
            Door(wall="east", offset=2.0, width=0.9),
            Door(wall="north", offset=0.5, width=0.9),
            Door(wall="north", offset=3.5, width=0.9),
        ],
    ),
    _RoomSpec(
        role="foyer", type="foyer",
        x=5.0, y=0.0, width=2.0, depth=4.0,
        doors=[
            Door(wall="south", offset=0.2, width=1.6),
            Door(wall="west", offset=2.0, width=0.9),
            Door(wall="east", offset=2.0, width=0.9),
        ],
    ),
    _RoomSpec(
        role="dining", type="dining_room",
        x=7.0, y=0.0, width=5.0, depth=5.0,
        doors=[
            Door(wall="west", offset=2.0, width=0.9),
            Door(wall="north", offset=2.0, width=0.9),
        ],
    ),
    _RoomSpec(
        role="powder", type="bathroom",
        x=0.0, y=5.0, width=2.0, depth=2.0,
        doors=[
            Door(wall="east", offset=0.5, width=0.8),
        ],
    ),
    _RoomSpec(
        role="hall_west", type="hallway",
        x=2.0, y=5.0, width=3.0, depth=5.0,
        doors=[
            Door(wall="south", offset=1.5, width=0.9),
            Door(wall="west", offset=0.5, width=0.8),
            Door(wall="east", offset=3.0, width=0.9),
        ],
    ),
    _RoomSpec(
        role="hall_north", type="hallway",
        x=5.0, y=7.0, width=2.0, depth=3.0,
        doors=[
            Door(wall="west", offset=1.0, width=0.9),
            Door(wall="east", offset=1.0, width=0.9),
        ],
    ),
    _RoomSpec(
        role="kitchen", type="kitchen",
        x=7.0, y=5.0, width=5.0, depth=5.0,
        doors=[
            Door(wall="south", offset=2.0, width=0.9),
            Door(wall="west", offset=3.0, width=0.9),
        ],
    ),
])

_colonial_level1 = _FloorSpec(rooms=[
    _RoomSpec(
        role="master_bedroom", type="bedroom",
        x=0.0, y=0.0, width=5.0, depth=5.0,
        doors=[
            Door(wall="east", offset=2.0, width=0.9),
            Door(wall="north", offset=2.0, width=0.9),
        ],
    ),
    _RoomSpec(
        role="hall_south", type="hallway",
        x=5.0, y=0.0, width=2.0, depth=4.0,
        doors=[
            Door(wall="west", offset=2.0, width=0.9),
            Door(wall="east", offset=2.0, width=0.9),
        ],
    ),
    _RoomSpec(
        role="bedroom_2", type="bedroom",
        x=7.0, y=0.0, width=5.0, depth=5.0,
        doors=[
            Door(wall="west", offset=2.0, width=0.9),
            Door(wall="north", offset=2.0, width=0.9),
        ],
    ),
    _RoomSpec(
        role="bathroom", type="bathroom",
        x=0.0, y=5.0, width=5.0, depth=5.0,
        doors=[
            Door(wall="south", offset=2.0, width=0.9),
            Door(wall="east", offset=3.5, width=0.9),
        ],
    ),
    _RoomSpec(
        role="hall_north", type="hallway",
        x=5.0, y=7.0, width=2.0, depth=3.0,
        doors=[
            Door(wall="west", offset=1.0, width=0.9),
            Door(wall="east", offset=1.0, width=0.9),
        ],
    ),
    _RoomSpec(
        role="bedroom_3", type="bedroom",
        x=7.0, y=5.0, width=5.0, depth=5.0,
        doors=[
            Door(wall="south", offset=2.0, width=0.9),
            Door(wall="west", offset=3.5, width=0.9),
        ],
    ),
])

_two_story_colonial = ArchetypeSpec(
    name="two_story_colonial",
    footprint=(12.0, 10.0),
    floors=[_colonial_level0, _colonial_level1],
    stair_position=(5.0, 4.0),
    stair_size=(2.0, 3.0),
)


# --------------------------------------------------------------------------- #
# Studio: single story, 7 x 6
# --------------------------------------------------------------------------- #

_studio = ArchetypeSpec(
    name="studio",
    footprint=(7.0, 6.0),
    floors=[
        _FloorSpec(rooms=[
            _RoomSpec(
                role="main", type="studio",
                x=0.0, y=0.0, width=7.0, depth=4.0,
                doors=[
                    Door(wall="south", offset=3.0, width=1.6),
                    Door(wall="north", offset=5.5, width=0.8),
                ],
            ),
            _RoomSpec(
                role="bathroom", type="bathroom",
                x=5.0, y=4.0, width=2.0, depth=2.0,
                doors=[
                    Door(wall="south", offset=0.5, width=0.8),
                ],
            ),
        ]),
    ],
)


# --------------------------------------------------------------------------- #
# Loft: two stories, 10 x 8, stair (8, 2) 1.5 x 2.5
# --------------------------------------------------------------------------- #

_loft_level0 = _FloorSpec(rooms=[
    _RoomSpec(
        role="main", type="open_living",
        x=0.0, y=0.0, width=8.0, depth=8.0,
        doors=[
            Door(wall="south", offset=3.5, width=1.6),
            Door(wall="east", offset=5.5, width=0.8),
        ],
    ),
    _RoomSpec(
        role="bathroom", type="bathroom",
        x=8.0, y=4.5, width=2.0, depth=3.5,
        doors=[
            Door(wall="west", offset=1.0, width=0.8),
        ],
    ),
])

_loft_level1 = _FloorSpec(rooms=[
    _RoomSpec(
        role="bedroom", type="bedroom",
        x=0.0, y=0.0, width=8.0, depth=8.0,
        doors=[
            Door(wall="east", offset=5.5, width=0.8),
        ],
    ),
    _RoomSpec(
        role="bathroom", type="bathroom",
        x=8.0, y=4.5, width=2.0, depth=3.5,
        doors=[
            Door(wall="west", offset=1.0, width=0.8),
        ],
    ),
])

_loft = ArchetypeSpec(
    name="loft",
    footprint=(10.0, 8.0),
    floors=[_loft_level0, _loft_level1],
    stair_position=(8.0, 2.0),
    stair_size=(1.5, 2.5),
)


# --------------------------------------------------------------------------- #
# Registry
# --------------------------------------------------------------------------- #

RESIDENTIAL_ARCHETYPES: dict[str, ArchetypeSpec] = {
    a.name: a for a in (_ranch, _two_story_colonial, _studio, _loft)
}


def archetype_pack_floor(
    archetype: str,
    level: int,
    ceiling_height: float = 3.0,
    stair_position: Optional[tuple[float, float]] = None,
) -> Floor:
    spec = RESIDENTIAL_ARCHETYPES.get(archetype)
    if spec is None:
        raise ValueError(f"unknown archetype: {archetype}")

    num_floors = len(spec.floors)
    if level < 0 or level >= num_floors:
        raise ValueError(
            f"archetype {archetype!r} has {num_floors} floor(s); "
            f"level {level} is out of range"
        )

    floor_spec = spec.floors[level]
    rooms: list[Room] = [
        Room(
            id=f"{archetype}_{r.role}_{level}",
            type=r.type,
            x=r.x,
            y=r.y,
            width=r.width,
            depth=r.depth,
            doors=[Door(wall=d.wall, offset=d.offset, width=d.width) for d in r.doors],
            windows=[],
        )
        for r in floor_spec.rooms
    ]

    stairs_list: list[Stairs] = []
    if num_floors > 1 and spec.stair_position is not None:
        sx, sy = stair_position if stair_position is not None else spec.stair_position
        sw, sd = spec.stair_size
        if level == num_floors - 1:
            direction = "south"
            to_level = level - 1
        else:
            direction = "north"
            to_level = level + 1
        stairs_list.append(
            Stairs(
                id=f"{archetype}_stair_{level}",
                x=sx,
                y=sy,
                width=sw,
                depth=sd,
                direction=direction,
                toLevel=to_level,
            )
        )

    return Floor(
        level=level,
        ceilingHeight=ceiling_height,
        rooms=rooms,
        stairs=stairs_list,
    )
