from core.world_spec import WorldSpec, Intent
from core.site import derive_site_from_intent
from core.navigation import compute_navigation


def test_spawn_is_on_grass_in_front_of_entrance():
    intent = Intent(buildingType="office", style="modern", floors=1,
                    vibe=[], sizeHint="medium")
    site = derive_site_from_intent(intent)
    spec = WorldSpec(worldId="x", prompt="t", intent=intent, site=site)
    nav = compute_navigation(spec)
    sx, sy_height, sz = nav.spawnPoint
    expected_x = site.buildingAnchor[0] + site.entrance.offset
    expected_z = -(site.buildingAnchor[1] - 3.0)
    assert abs(sx - expected_x) < 1e-6
    assert abs(sz - expected_z) < 1e-6
    assert sy_height == 1.7
