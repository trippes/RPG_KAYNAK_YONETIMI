from application.gameplay_service import GameplayService


def test_npc_simulation_advances_systems_in_canonical_order_and_merges_moved_ids():
    calls = []

    class ServiceDouble:
        def advance_npc_patrols(self, delta_seconds):
            calls.append(("patrol", delta_seconds))
            return ("guard",)

        def advance_npc_avoidance(self, delta_seconds):
            calls.append(("avoidance", delta_seconds))
            return ("wolf", "guard")

        def advance_companions(self, delta_seconds):
            calls.append(("companions", delta_seconds))
            return ("companion",)

    moved = GameplayService.advance_npc_simulation(
        ServiceDouble(), 1.0 / 60.0,
    )

    assert calls == [
        ("patrol", 1.0 / 60.0),
        ("avoidance", 1.0 / 60.0),
        ("companions", 1.0 / 60.0),
    ]
    assert moved == ("companion", "guard", "wolf")
