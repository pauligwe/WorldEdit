from .world_spec import WorldSpec


def check_site_constraints(spec: WorldSpec) -> list[str]:
    """Validate Site-level invariants: rooms inside footprint, entrance landing."""
    errors: list[str] = []
    if spec.site is None or spec.blueprint is None:
        return errors

    fw, fd = spec.site.buildingFootprint
    for fl in spec.blueprint.floors:
        for r in fl.rooms:
            if r.x < 0 or r.y < 0 or r.x + r.width > fw + 1e-6 or r.y + r.depth > fd + 1e-6:
                errors.append(
                    f"room {r.id} (level {fl.level}) is outside building footprint "
                    f"{fw}x{fd}"
                )

    ground = next((f for f in spec.blueprint.floors if f.level == 0), None)
    if ground is None:
        errors.append("no ground floor (level 0)")
        return errors

    e = spec.site.entrance
    matched = False
    for r in ground.rooms:
        if e.wall == "south" and abs(r.y) < 1e-6:
            matched = True
        elif e.wall == "north" and abs((r.y + r.depth) - fd) < 1e-6:
            matched = True
        elif e.wall == "west" and abs(r.x) < 1e-6:
            matched = True
        elif e.wall == "east" and abs((r.x + r.width) - fw) < 1e-6:
            matched = True
        if matched:
            break
    if not matched:
        errors.append(
            f"no ground-floor room sits on the {e.wall} edge of the building"
        )

    return errors
