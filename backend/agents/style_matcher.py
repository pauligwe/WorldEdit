"""Re-rank/filter scout results to span style variants per slot.
Heuristic: keep up to 5 products, prefer ones with distinct vendors.
"""
from core.world_spec import WorldSpec


def run(spec: WorldSpec) -> WorldSpec:
    for f in spec.furniture:
        seen_vendors: set[str] = set()
        chosen: list[str] = []
        for pid in f.alternates:
            p = spec.products.get(pid)
            if not p:
                continue
            v = p.vendor or "_"
            if v not in seen_vendors:
                seen_vendors.add(v)
            chosen.append(pid)
            if len(chosen) >= 5:
                break
        f.alternates = chosen
        if chosen:
            f.selectedProductId = chosen[0]
    return spec
