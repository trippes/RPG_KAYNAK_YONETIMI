import json
import tempfile
import unittest
from pathlib import Path

from application import GameApplication, GameplayService, migrate_save_data
from application.content_pack import populate_demo_content
from combat import calculate_damage, order_initiative, tick_statuses
from pygame.input import InputMapper, InputState
from pygame.screens.character_creation import CharacterCreationScreen
from pygame.screens.combat_screen import CombatScreen
from pygame.screens.dialogue_screen import DialogueScreen
from pygame.screens.market_screen import MarketScreen
from pygame.screens.inventory_screen import InventoryScreen
from pygame.screens.map_screen import MapScreen
from pygame.screens.local_map_screen import LocalMapScreen


class TestPhaseDQuality(unittest.TestCase):
    def test_legacy_envelope_migrates_without_mutating_input(self):
        app = GameApplication.create_default()
        app.dunya_olustur("Legacy", world_id="legacy")
        service = GameplayService(app)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "save.json"
            service.save(path)
            data = json.loads(path.read_text(encoding="utf-8"))
            data.pop("economy", None); data.pop("social", None); data.pop("combat", None)
            data["schema_version"] = 0
            original = json.loads(json.dumps(data))
            service.load(path) if False else None
            migrated = migrate_save_data(data)
            self.assertEqual(data, original)
            self.assertEqual(migrated["schema_version"], 1)
            path.write_text(json.dumps(migrated), encoding="utf-8")
            service.load(path)

    def test_demo_save_is_deterministic(self):
        payloads = []
        for _ in range(2):
            app = GameApplication.create_default()
            service, ids = populate_demo_content(app)
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "save.json"
                service.save(path)
                payloads.append(path.read_text(encoding="utf-8"))
        self.assertEqual(payloads[0], payloads[1])

    def test_demo_starts_next_to_eren_at_southern_gate(self):
        service, ids = populate_demo_content(GameApplication.create_default())

        self.assertEqual(service.actor(ids.hero_id).position.x, 16)
        self.assertEqual(service.actor(ids.hero_id).position.y, 29)

    def test_combat_primitives_are_deterministic(self):
        self.assertEqual(calculate_damage(8, 3), 5)
        self.assertEqual(order_initiative(("b", "a"), {"a": 4, "b": 4}), ("a", "b"))
        self.assertEqual(tick_statuses({"poison": 2, "stun": 1}), {"poison": 1})

    def test_ui_screen_smoke_handles_basic_input(self):
        service = GameplayService(GameApplication.create_default())
        screens = [MarketScreen(service), DialogueScreen(service), CombatScreen(service), CharacterCreationScreen(service)]
        for screen in screens:
            screen.handle(InputState(actions={"confirm"}))
            expected = (
                "local_map"
                if isinstance(screen, (MarketScreen, DialogueScreen))
                else "world"
            )
            self.assertEqual(screen.handle(InputState(actions={"back"})), expected)

    def test_map_screen_routes_to_world_and_supports_map_input(self):
        from application.content_pack import populate_demo_content
        service, _ = populate_demo_content(GameApplication.create_default())
        screen = MapScreen(service)
        screen.handle(InputState(actions={"down", "confirm"}))
        self.assertEqual(service.actor("hero").location_id, "village")
        self.assertIn("yalnızca konumları gösterir", screen.message)
        self.assertEqual(screen.handle(InputState(actions={"back"})), "local_map")

    def test_locations_expose_meaningful_context_and_gate_actions(self):
        from application.content_pack import populate_demo_content
        service, _ = populate_demo_content(GameApplication.create_default())
        screen = __import__("pygame.screens.world_screen", fromlist=["WorldScreen"]).WorldScreen(service)
        self.assertEqual(screen.handle(InputState(actions={"market"})), "market")
        screen.handle(InputState(actions={"right"}))
        self.assertIsNone(screen.handle(InputState(actions={"market"})))
        self.assertIn("Pazar", screen.message)

    def test_local_map_is_reachable_from_world_map(self):
        from application.content_pack import populate_demo_content
        service, _ = populate_demo_content(GameApplication.create_default())
        map_screen = MapScreen(service)
        self.assertEqual(map_screen.handle(InputState(actions={"confirm"})), "local_map")
        local_screen = LocalMapScreen(service)
        self.assertIsNone(local_screen.handle(InputState(actions={"confirm"})))

    def test_local_map_finds_safe_paths_and_blocks_static_landmarks(self):
        from application.content_pack import populate_demo_content
        service, _ = populate_demo_content(GameApplication.create_default())
        local_screen = LocalMapScreen(service)
        path = local_screen._path_to((16, 16), (8, 8))
        self.assertTrue(path)
        self.assertEqual(path[0], (16, 16))
        self.assertEqual(path[-1], (8, 8))
        self.assertFalse(local_screen._is_walkable((7, 10)))

    def test_mine_landmark_collects_iron_ore(self):
        service, ids = populate_demo_content(GameApplication.create_default())
        service.move_actor(ids.hero_id, ids.forest_id)
        service.advance_by(1)
        service.move_actor(ids.hero_id, "north_mine")
        service.advance_by(1)

        local_screen = LocalMapScreen(service)
        local_screen.selected = (15, 15)
        self.assertTrue(local_screen._gather_at_selected_tree())
        self.assertEqual(service.inventory(ids.inventory_id).stocks, (("iron_ore", 1, "item"),))

    def test_dialogue_prompt_uses_selected_npc_name(self):
        from application.content_pack import populate_demo_content
        service, ids = populate_demo_content(GameApplication.create_default())
        screen = DialogueScreen(service)
        screen.set_target_npc(ids.carpenter_id)
        self.assertIn("Marangoz Hilmi", screen.message)

    def test_inn_dialogue_opens_trade_window(self):
        from application.content_pack import populate_demo_content
        service, ids = populate_demo_content(GameApplication.create_default())
        screen = DialogueScreen(service)
        screen.set_target_npc(ids.innkeeper_id)
        screen.handle(InputState(actions={"confirm"}))
        self.assertEqual(screen.handle(InputState(actions={"confirm"})), "market")

    def test_inventory_and_market_windows_close_to_local_map(self):
        from application.content_pack import populate_demo_content
        service, _ = populate_demo_content(GameApplication.create_default())
        self.assertEqual(
            InventoryScreen(service).handle(InputState(actions={"back"})),
            "local_map",
        )
        self.assertEqual(
            MarketScreen(service).handle(InputState(actions={"back"})),
            "local_map",
        )

    def test_village_gate_opens_eren_dialogue(self):
        from application.content_pack import populate_demo_content
        service, ids = populate_demo_content(GameApplication.create_default())
        local_screen = LocalMapScreen(service)
        local_screen.selected = (16, 30)
        self.assertEqual(local_screen.handle(InputState(actions={"confirm"})), "dialogue")
        self.assertEqual(local_screen.selected_npc_id, ids.npc_id)

    def test_save_load_keys_are_part_of_the_input_contract(self):
        mapper = InputMapper()
        save_event = type("Event", (), {"type": "KEYDOWN", "key": "f5"})()
        load_event = type("Event", (), {"type": "KEYDOWN", "key": "f9"})()
        self.assertTrue(mapper.collect([save_event]).pressed("save"))
        self.assertTrue(mapper.collect([load_event]).pressed("load"))

    def test_trade_and_inventory_keys_are_mapped_by_backend(self):
        class Backend:
            KEYDOWN = "KEYDOWN"
            K_m = 1
            K_i = 2
            K_d = 3
            K_b = 4
            K_n = 5

        mapper = InputMapper(Backend())
        market_event = type("Event", (), {"type": "KEYDOWN", "key": 1})()
        inventory_event = type("Event", (), {"type": "KEYDOWN", "key": 2})()
        self.assertTrue(mapper.collect([market_event]).pressed("market"))
        self.assertTrue(mapper.collect([inventory_event]).pressed("inventory"))


if __name__ == "__main__":
    unittest.main()
