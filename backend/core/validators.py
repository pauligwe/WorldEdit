from dataclasses import dataclass, field
from .world_spec import Blueprint, Floor, Room, Stairs


@dataclass
class ValidationReport:
    ok: bool
    errors: list[str] = field(default_factory=list)


def _rects_overlap(a: Room, b: Room) -> bool:
    if a.x + a.width <= b.x:
        return False
    if b.x + b.width <= a.x:
        return False
    if a.y + a.depth <= b.y:
        return False
    if b.y + b.depth <= a.y:
        return False
    return True


def _room_has_doors(r: Room) -> bool:
    return len(r.doors) > 0


def _stairs_aligned(s1: Stairs, s2: Stairs) -> bool:
    return (
        abs(s1.x - s2.x) < 1e-6
        and abs(s1.y - s2.y) < 1e-6
        and abs(s1.width - s2.width) < 1e-6
        and abs(s1.depth - s2.depth) < 1e-6
    )


def validate_blueprint(bp: Blueprint) -> ValidationReport:
    errors: list[str] = []

    if not bp.floors:
        errors.append("blueprint has no floors")
        return ValidationReport(ok=False, errors=errors)

    floors_by_level: dict[int, Floor] = {}
    for fl in bp.floors:
        if fl.level in floors_by_level:
            errors.append(f"duplicate floor level {fl.level}")
        floors_by_level[fl.level] = fl

    if 0 not in floors_by_level:
        errors.append("missing ground floor (level 0)")

    for fl in bp.floors:
        if not fl.rooms:
            errors.append(f"floor {fl.level} has no rooms")
            continue

        ids: set[str] = set()
        for r in fl.rooms:
            if r.id in ids:
                errors.append(f"duplicate room id {r.id} on floor {fl.level}")
            ids.add(r.id)
            if not _room_has_doors(r):
                errors.append(f"room {r.id} on floor {fl.level} has no door")

        for i, a in enumerate(fl.rooms):
            for b in fl.rooms[i + 1:]:
                if _rects_overlap(a, b):
                    errors.append(f"rooms {a.id} and {b.id} overlap on floor {fl.level}")

    for fl in bp.floors:
        for s in fl.stairs:
            target = floors_by_level.get(s.toLevel)
            if target is None:
                errors.append(f"stair {s.id} on floor {fl.level} targets missing floor {s.toLevel}")
                continue
            mate = next((ts for ts in target.stairs if ts.id == s.id), None)
            if mate is None:
                errors.append(f"stair {s.id} on floor {fl.level} has no matching stair on floor {s.toLevel}")
                continue
            if not _stairs_aligned(s, mate):
                errors.append(f"stair {s.id} not aligned between floors {fl.level} and {s.toLevel}")

    return ValidationReport(ok=not errors, errors=errors)
