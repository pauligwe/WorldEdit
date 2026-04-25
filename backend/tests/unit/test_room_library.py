from core.room_library import ROOM_LIBRARY, get_template


def test_library_has_at_least_10_templates():
    assert len(ROOM_LIBRARY) >= 10


def test_every_template_has_at_least_one_door():
    for t in ROOM_LIBRARY.values():
        assert len(t.door_specs) >= 1, f"{t.name} has no doors"


def test_every_template_has_positive_dimensions():
    for t in ROOM_LIBRARY.values():
        assert t.width > 0 and t.depth > 0


def test_office_templates_have_office_type():
    offices = [t for t in ROOM_LIBRARY.values() if t.name.startswith("office")]
    assert len(offices) >= 2
    for t in offices:
        assert t.type == "office"


def test_lobby_has_south_entrance_door():
    lobby = get_template("lobby_modern")
    assert lobby is not None
    assert any(d.wall == "south" for d in lobby.door_specs)


def test_conference_template_has_table():
    conf = get_template("conference_small")
    assert conf is not None
    assert any(f.type == "conference_table" for f in conf.furniture)


def test_furniture_offsets_inside_room():
    # FurnitureTemplate.room_offset is the SW corner of the piece (matches
    # core/room_templates.py semantics), so the piece must satisfy
    # 0 <= offset and offset + size <= room dimension.
    for t in ROOM_LIBRARY.values():
        for f in t.furniture:
            ox, oy = f.room_offset
            fw, _, fd = f.size
            assert ox >= 0, f"{t.name}/{f.type} negative offset x {ox}"
            assert oy >= 0, f"{t.name}/{f.type} negative offset y {oy}"
            assert ox + fw <= t.width + 0.01, (
                f"{t.name}/{f.type} offset {ox} + width {fw} exceeds "
                f"room width {t.width}"
            )
            assert oy + fd <= t.depth + 0.01, (
                f"{t.name}/{f.type} offset {oy} + depth {fd} exceeds "
                f"room depth {t.depth}"
            )


def test_door_offsets_inside_walls():
    # Each door's offset + width must fit on its assigned wall.
    for t in ROOM_LIBRARY.values():
        for d in t.door_specs:
            wall_len = t.width if d.wall in ("north", "south") else t.depth
            assert d.offset >= 0, f"{t.name} door negative offset"
            assert d.offset + d.width <= wall_len + 0.01, (
                f"{t.name} door on {d.wall} exceeds wall length"
            )


def test_get_template_returns_none_for_unknown():
    assert get_template("does_not_exist") is None
