from .world_spec import WorldSpec, Navigation


def compute_navigation(spec: WorldSpec) -> Navigation:
    """Spawn 3m south of the building entrance, on the grass, looking north."""
    if spec.site is None:
        return Navigation(spawnPoint=[50.0, 1.7, -50.0])
    s = spec.site
    spawn_x = s.buildingAnchor[0] + s.entrance.offset
    spawn_y_plot = s.buildingAnchor[1] - 3.0
    return Navigation(
        spawnPoint=[spawn_x, 1.7, -spawn_y_plot],
        walkableMeshIds=[],
        stairColliders=[],
    )
