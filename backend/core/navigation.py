from .world_spec import Blueprint, Navigation


def compute_navigation(bp: Blueprint) -> Navigation:
    """Spawn just inside the south door of the entrance room.

    Entrance room: room with a 'south' door on the ground floor; if multiple, prefer hallways.
    Falls back to the first room on level 0.
    """
    ground = next((f for f in bp.floors if f.level == 0), None)
    if ground is None or not ground.rooms:
        return Navigation(spawnPoint=[0, 1.7, 0])

    entrance = None
    for r in ground.rooms:
        if any(d.wall == "south" for d in r.doors):
            if r.type == "hallway" or entrance is None:
                entrance = r

    if entrance is None:
        entrance = ground.rooms[0]

    south_door = next((d for d in entrance.doors if d.wall == "south"), None)
    if south_door is not None:
        sx = entrance.x + south_door.offset
        sy_blueprint = entrance.y + 0.8  # 0.8m inside the room from the south wall
    else:
        sx = entrance.x + entrance.width / 2
        sy_blueprint = entrance.y + entrance.depth / 2

    spawn = [sx, 1.7, -sy_blueprint]

    walkable = [f"floor-{r.id}" for fl in bp.floors for r in fl.rooms]
    stair_colliders = list({s.id for fl in bp.floors for s in fl.stairs})

    return Navigation(spawnPoint=spawn, walkableMeshIds=walkable, stairColliders=stair_colliders)
