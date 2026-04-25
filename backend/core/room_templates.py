from pydantic import BaseModel
from .world_spec import Room, FurnitureItem


class FurnitureTemplate(BaseModel):
    type: str
    room_offset: list[float]   # [x, y] in meters from room SW corner
    size: list[float]          # [w, h, d]
    rotation: float = 0.0


ROOM_FURNITURE: dict[str, list[FurnitureTemplate]] = {
    "office": [
        FurnitureTemplate(type="desk", room_offset=[1.0, 1.0],
                          size=[1.4, 0.75, 0.7]),
        FurnitureTemplate(type="office_chair", room_offset=[1.7, 2.0],
                          size=[0.6, 1.1, 0.6], rotation=3.14159),
    ],
    "conference_room": [
        FurnitureTemplate(type="conference_table", room_offset=[1.5, 1.5],
                          size=[2.4, 0.75, 1.0]),
        FurnitureTemplate(type="office_chair", room_offset=[1.0, 1.0],
                          size=[0.6, 1.1, 0.6]),
        FurnitureTemplate(type="office_chair", room_offset=[1.0, 2.5],
                          size=[0.6, 1.1, 0.6]),
        FurnitureTemplate(type="office_chair", room_offset=[3.5, 1.0],
                          size=[0.6, 1.1, 0.6], rotation=3.14159),
        FurnitureTemplate(type="office_chair", room_offset=[3.5, 2.5],
                          size=[0.6, 1.1, 0.6], rotation=3.14159),
    ],
    "lobby": [
        FurnitureTemplate(type="reception_desk", room_offset=[2.0, 2.0],
                          size=[2.5, 1.0, 0.8]),
        FurnitureTemplate(type="couch", room_offset=[1.0, 4.0],
                          size=[2.2, 0.8, 0.9]),
    ],
    "reception": [
        FurnitureTemplate(type="reception_desk", room_offset=[1.5, 1.5],
                          size=[2.5, 1.0, 0.8]),
    ],
    "breakroom": [
        FurnitureTemplate(type="table", room_offset=[1.5, 1.5],
                          size=[1.5, 0.75, 1.0]),
        FurnitureTemplate(type="chair", room_offset=[1.5, 0.6],
                          size=[0.5, 1.0, 0.5]),
        FurnitureTemplate(type="chair", room_offset=[1.5, 3.1],
                          size=[0.5, 1.0, 0.5], rotation=3.14159),
    ],
    "corridor": [],
    "restroom": [],
    "stairwell": [],
    "bedroom": [
        FurnitureTemplate(type="bed", room_offset=[1.0, 1.0],
                          size=[2.0, 0.5, 1.5]),
    ],
    "kitchen": [
        FurnitureTemplate(type="table", room_offset=[1.5, 1.5],
                          size=[1.2, 0.75, 0.8]),
    ],
    "living_room": [
        FurnitureTemplate(type="couch", room_offset=[1.0, 1.0],
                          size=[2.2, 0.8, 0.9]),
    ],
    "bathroom": [],
    "default": [],
}


def apply_template(room: Room, level_y: float,
                   anchor: tuple[float, float]) -> list[FurnitureItem]:
    """Pure-code: produce FurnitureItems for a room from its type template.

    `anchor` is buildingAnchor (plot-world offset). Room positions are
    building-local. Output positions are plot-world. Items whose template
    offset+size would exceed room dimensions are skipped.
    """
    template = ROOM_FURNITURE.get(room.type, [])
    items: list[FurnitureItem] = []
    ax, ay = anchor
    for i, t in enumerate(template):
        ox, oy = t.room_offset
        w, _, d = t.size
        if ox + w > room.width or oy + d > room.depth:
            continue
        # plot-world center of the item
        px = ax + room.x + ox + w / 2
        py = ay + room.y + oy + d / 2
        items.append(FurnitureItem(
            id=f"{room.id}-{t.type}-{i}",
            roomId=room.id,
            type=t.type,
            position=[px, level_y, -py],
            rotation=t.rotation,
            size=t.size,
        ))
    return items
