"""Deterministic floor-plan packer for hand-designed room templates.

The LLM picks a list of template names per floor. This module lays them out
inside a building footprint using a simple greedy row-packing strategy. No
geometry is invented here -- each room reuses its template's exact width,
depth, and door specs.
"""

from pydantic import BaseModel

from .room_library import ROOM_LIBRARY
from .world_spec import Door, Floor, Room


class FloorTemplateSelection(BaseModel):
    level: int
    template_names: list[str]


class BuildingTemplateSelection(BaseModel):
    floors: list[FloorTemplateSelection]


def pack_floor_plan(
    template_names: list[str],
    footprint: tuple[float, float],
    level: int,
    ceiling_height: float = 3.0,
) -> Floor:
    """Place templates inside the footprint and return a Floor with rooms.

    Strategy: greedy left-to-right, top-to-bottom row-packing. Each template
    occupies its (width, depth). When a row fills up, start a new row. Rooms
    that don't fit are silently dropped (with a debug print). Level 0 always
    has 'lobby_modern' prepended if missing so the building has an entrance.
    """
    names = list(template_names)
    if level == 0 and "lobby_modern" not in names:
        names.insert(0, "lobby_modern")

    fw, fd = footprint
    cursor_x = 0.0
    cursor_y = 0.0
    row_max_depth = 0.0
    rooms: list[Room] = []

    for slot_index, name in enumerate(names):
        template = ROOM_LIBRARY.get(name)
        if template is None:
            print(f"[floor_packer] skipping unknown template: {name}")
            continue

        # Wrap to a new row if this template won't fit horizontally.
        if cursor_x + template.width > fw:
            cursor_x = 0.0
            cursor_y += row_max_depth
            row_max_depth = 0.0

        # Drop if it can't fit vertically (or even on its own row).
        if cursor_y + template.depth > fd or template.width > fw:
            print(
                f"[floor_packer] dropping {name}: doesn't fit at "
                f"({cursor_x},{cursor_y}) within footprint ({fw}x{fd})"
            )
            continue

        rooms.append(
            Room(
                id=f"{template.name}_{level}_{slot_index}",
                type=template.type,
                x=cursor_x,
                y=cursor_y,
                width=template.width,
                depth=template.depth,
                doors=[
                    Door(wall=d.wall, offset=d.offset, width=d.width)
                    for d in template.door_specs
                ],
                windows=[],
            )
        )

        cursor_x += template.width
        row_max_depth = max(row_max_depth, template.depth)

    return Floor(
        level=level,
        ceilingHeight=ceiling_height,
        rooms=rooms,
        stairs=[],
    )
