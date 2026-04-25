from .world_spec import FurnitureItem, Product, Cost


def compute_cost(furniture: list[FurnitureItem], products: dict[str, Product]) -> Cost:
    by_room: dict[str, float] = {}
    total = 0.0
    for f in furniture:
        if not f.selectedProductId:
            continue
        prod = products.get(f.selectedProductId)
        if not prod or prod.price is None:
            continue
        by_room[f.roomId] = by_room.get(f.roomId, 0.0) + prod.price
        total += prod.price
    return Cost(total=total, byRoom=by_room)
