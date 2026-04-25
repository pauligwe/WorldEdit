from .world_spec import Intent, Site, Plot, Entrance

PLOT_SIZE = 100.0
MARGIN = 10.0


def derive_site_from_intent(intent: Intent) -> Site:
    """Pure-code Site computation from Intent.

    Building is centered on a fixed 100x100m plot. Footprint scales with
    sizeHint; clamped so 10m of grass remains on every side. Entrance is
    on the south wall, centered.
    """
    bonus = {"small": 0, "medium": 10, "large": 20}.get(intent.sizeHint, 10)
    fw = min(20.0 + bonus, PLOT_SIZE - 2 * MARGIN)
    fd = min(15.0 + bonus, PLOT_SIZE - 2 * MARGIN)

    ax = (PLOT_SIZE - fw) / 2
    ay = (PLOT_SIZE - fd) / 2

    return Site(
        plot=Plot(),
        buildingFootprint=[fw, fd],
        buildingAnchor=[ax, ay],
        entrance=Entrance(wall="south", offset=fw / 2),
    )
