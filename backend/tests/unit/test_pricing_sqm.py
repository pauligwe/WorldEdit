from core.world_spec import WorldSpec, Blueprint, Floor, Room, Door
from core.pricing import compute_cost, COST_PER_SQM


def _spec(rooms_per_floor):
    floors = []
    for level, rooms in enumerate(rooms_per_floor):
        floors.append(Floor(level=level, ceilingHeight=3.0, rooms=rooms))
    return WorldSpec(worldId="x", prompt="t", blueprint=Blueprint(floors=floors))


def test_pricing_single_room_one_floor():
    rooms = [Room(id="r1", type="office", x=0, y=0, width=10, depth=5,
                  doors=[Door(wall="south", offset=2, width=1)])]
    spec = _spec([rooms])
    cost = compute_cost(spec)
    assert cost.total == 10 * 5 * COST_PER_SQM
    assert cost.byRoom == {"r1": 10 * 5 * COST_PER_SQM}


def test_pricing_multiroom_multifloor():
    rooms_lvl0 = [Room(id="lobby", type="lobby", x=0, y=0, width=8, depth=4,
                       doors=[Door(wall="south", offset=2, width=1)])]
    rooms_lvl1 = [Room(id="off1", type="office", x=0, y=0, width=4, depth=4,
                       doors=[Door(wall="north", offset=1, width=1)]),
                  Room(id="off2", type="office", x=4, y=0, width=4, depth=4,
                       doors=[Door(wall="north", offset=1, width=1)])]
    spec = _spec([rooms_lvl0, rooms_lvl1])
    cost = compute_cost(spec)
    assert cost.total == (8*4 + 4*4 + 4*4) * COST_PER_SQM
    assert len(cost.byRoom) == 3


def test_pricing_no_blueprint_returns_zero():
    spec = WorldSpec(worldId="x", prompt="t")
    cost = compute_cost(spec)
    assert cost.total == 0
