from core.world_spec import FurnitureItem, Product
from core.pricing import compute_cost


def test_pricing_sums_per_room_and_total():
    furniture = [
        FurnitureItem(id="a", roomId="r1", type="couch", position=[0, 0, 0], size=[2, 1, 1], selectedProductId="p1"),
        FurnitureItem(id="b", roomId="r1", type="chair", position=[0, 0, 0], size=[1, 1, 1], selectedProductId="p2"),
        FurnitureItem(id="c", roomId="r2", type="bed", position=[0, 0, 0], size=[2, 1, 2], selectedProductId="p3"),
    ]
    products = {
        "p1": Product(name="couch", price=500),
        "p2": Product(name="chair", price=100),
        "p3": Product(name="bed", price=800),
    }
    cost = compute_cost(furniture, products)
    assert cost.total == 1400
    assert cost.byRoom["r1"] == 600
    assert cost.byRoom["r2"] == 800


def test_pricing_skips_missing_product():
    furniture = [
        FurnitureItem(id="a", roomId="r1", type="couch", position=[0, 0, 0], size=[2, 1, 1], selectedProductId=None),
    ]
    cost = compute_cost(furniture, {})
    assert cost.total == 0
