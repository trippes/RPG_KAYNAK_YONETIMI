import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from application import GameApplication, GameplayService, migrate_save_data
from application.content_pack import populate_opening_content
from combat import calculate_damage, order_initiative, tick_statuses
from game_ui.game_window import GameWindow
from game_ui.input import InputMapper, InputState
from game_ui.window_manager import WindowManager
from game_ui.screens.character_creation import CharacterCreationScreen
from game_ui.screens.character_screen import CharacterScreen
from game_ui.screens.combat_screen import CombatScreen
from game_ui.screens.dialogue_screen import DialogueScreen
from game_ui.screens.market_screen import MarketScreen
from game_ui.screens.main_menu import MainMenu
from game_ui.screens.inventory_screen import InventoryScreen
from game_ui.screens.map_screen import MapScreen
from game_ui.screens.main_screen import MainScreen
from game_ui.screens.quest_log_screen import QuestLogScreen
from game_ui.screens.save_slots_screen import SaveSlotsScreen
from quests import Objective, ObjectiveType, Quest, QuestLog, QuestState, Reward


class TestPhaseDQuality(unittest.TestCase):
    def test_quest_log_uses_shared_responsive_layout_without_panel_overlap(self):
        service, _ = populate_opening_content(GameApplication.create_default())
        screen = QuestLogScreen(service)
        screen.set_viewport(600, 488)

        compact = screen._layout()
        outer = compact["outer"]
        inner = compact["inner"]
        quest_list = screen._list_bounds()
        details = screen._details_bounds()
        rewards = screen._reward_bounds()

        self.assertTrue(screen.responsive_layout)
        self.assertEqual((screen.min_window_width, screen.min_window_height), (600, 520))
        self.assertGreaterEqual(quest_list[0], inner[0])
        self.assertLessEqual(quest_list[0] + quest_list[2], details[0])
        self.assertLessEqual(details[0] + details[2], inner[0] + inner[2])
        self.assertLessEqual(quest_list[1] + quest_list[3], rewards[1])
        self.assertLessEqual(details[1] + details[3], rewards[1])
        self.assertLessEqual(rewards[1] + rewards[3], outer[1] + outer[3])
        for tab in screen._tab_bounds():
            self.assertGreaterEqual(tab[0], outer[0])
            self.assertGreaterEqual(tab[1], outer[1])
            self.assertLessEqual(tab[0] + tab[2], outer[0] + outer[2])
            self.assertLessEqual(tab[1] + tab[3], outer[1] + outer[3])

        screen.set_viewport(1200, 700)
        expanded = screen._layout()
        self.assertGreater(expanded["outer"][2], outer[2])
        self.assertGreater(expanded["outer"][3], outer[3])
        expanded_list = screen._list_bounds()
        expanded_details = screen._details_bounds()
        self.assertLessEqual(expanded_list[0] + expanded_list[2], expanded_details[0])
        self.assertLessEqual(
            expanded_details[0] + expanded_details[2],
            expanded["inner"][0] + expanded["inner"][2],
        )

    def test_quest_log_category_tabs_use_responsive_hitboxes(self):
        service, _ = populate_opening_content(GameApplication.create_default())
        screen = QuestLogScreen(service)
        screen.set_viewport(600, 488)
        tab = screen._tab_bounds()[1]
        screen.handle(InputState(
            mouse_pos=(tab[0] + tab[2] // 2, tab[1] + tab[3] // 2),
            mouse_clicked=True,
        ))
        self.assertEqual(screen.category, 1)
        self.assertEqual(screen.selected, 0)

    def test_character_screen_uses_responsive_viewport_layout(self):
        service, _ = populate_opening_content(GameApplication.create_default())
        screen = CharacterScreen(service)

        screen.set_viewport(912, 438)
        standard = screen._layout()
        screen.set_viewport(1200, 700)
        expanded = screen._layout()

        self.assertTrue(screen.responsive_layout)
        self.assertGreater(expanded["outer"][2], standard["outer"][2])
        self.assertGreater(expanded["outer"][3], standard["outer"][3])
        for key in ("identity", "combat", "attributes", "skills"):
            rect = expanded[key]
            self.assertIsNotNone(rect)
            self.assertGreater(rect[2], 0)
            self.assertGreater(rect[3], 0)

    def test_character_screen_compact_layout_separates_attributes_and_skills(self):
        service, _ = populate_opening_content(GameApplication.create_default())
        screen = CharacterScreen(service)
        screen.set_viewport(600, 470)
        layout = screen._layout()
        attributes = layout["attributes"]
        skills = layout["skills"]

        self.assertTrue(layout["compact"])
        self.assertIsNone(layout["combat"])
        self.assertLessEqual(attributes[1] + attributes[3], skills[1])
        self.assertGreater(skills[3], 0)
        x, y, width, height = screen._skill_bounds()
        self.assertGreater(width, 0)
        self.assertGreater(height, 0)
        self.assertGreaterEqual(x, skills[0])
        self.assertGreaterEqual(y, skills[1])
        self.assertLessEqual(x + width, skills[0] + skills[2])
        self.assertLessEqual(y + height, skills[1] + skills[3])

    def test_character_minimum_viewport_keeps_all_skills_and_cards_inside_panels(self):
        service, _ = populate_opening_content(GameApplication.create_default())
        screen = CharacterScreen(service)
        # A 520px framed window leaves a 488px responsive content viewport.
        screen.set_viewport(600, 488)
        layout = screen._layout()
        attributes = layout["attributes"]
        skills_panel = layout["skills"]

        self.assertLessEqual(
            attributes[1] + attributes[3], skills_panel[1]
        )
        cards = screen._attribute_card_rects(attributes)
        for x, y, width, height in cards:
            self.assertGreaterEqual(x, attributes[0])
            self.assertGreaterEqual(y, attributes[1])
            self.assertLessEqual(x + width, attributes[0] + attributes[2])
            self.assertLessEqual(y + height, attributes[1] + attributes[3])

        skill_rows = screen._skill_rows()
        self.assertIn("survival", {name.lower() for name, _value in skill_rows})
        row_rect, visible_count = screen._skill_geometry()
        self.assertGreaterEqual(visible_count, len(skill_rows))
        row_x, row_y, row_width, row_height = row_rect
        for index in range(len(skill_rows)):
            row_top = row_y + index * row_height
            self.assertGreaterEqual(row_x, skills_panel[0])
            self.assertGreaterEqual(row_top, skills_panel[1])
            self.assertLessEqual(
                row_x + row_width, skills_panel[0] + skills_panel[2]
            )
            self.assertLessEqual(
                row_top + row_height - 3,
                skills_panel[1] + skills_panel[3] - 24,
            )

    def test_character_attribute_cards_stay_inside_compact_panel(self):
        service, _ = populate_opening_content(GameApplication.create_default())
        screen = CharacterScreen(service)
        screen.set_viewport(600, 440)
        panel = screen._layout()["attributes"]

        for x, y, width, height in screen._attribute_card_rects(panel):
            self.assertGreaterEqual(x, panel[0])
            self.assertGreaterEqual(y, panel[1])
            self.assertLessEqual(x + width, panel[0] + panel[2])
            self.assertLessEqual(y + height, panel[1] + panel[3])

    def _quest_screen(self):
        quests = QuestLog((
            Quest("active", "Aktif Görev", (
                Objective("a", "İki odun topla", ObjectiveType.COLLECT, required=2, progress=1),
                Objective("optional", "İsteğe bağlı konuş", ObjectiveType.TALK, optional=True),
            ), Reward(experience=20, currency=3, items=(("iron_sword", 1),), reputation=(("wardens", 2),)),
               state=QuestState.ACTIVE),
            Quest("active-2", "İkinci Aktif Görev", (Objective("a2", "Bir taş topla", ObjectiveType.COLLECT),),
               state=QuestState.ACTIVE),
            Quest("available", "Mevcut Görev", (Objective("b", "Köye ulaş", ObjectiveType.REACH),)),
            Quest("completed", "Biten Görev", (Objective("c", "Tamamlandı", ObjectiveType.CUSTOM, progress=1),),
               state=QuestState.COMPLETED),
            Quest("failed", "Başarısız Görev", (Objective("d", "Başarısız", ObjectiveType.CUSTOM),),
               state=QuestState.FAILED),
        ))
        service = SimpleNamespace(
            application=SimpleNamespace(holder=SimpleNamespace(current=SimpleNamespace(quest_log=quests))),
            item=lambda item_id: SimpleNamespace(name="Demir Kılıç") if item_id == "iron_sword" else None,
        )
        return QuestLogScreen(service)

    def test_quest_log_categories_and_counts_use_quest_log_filters(self):
        screen = self._quest_screen()

        self.assertEqual(screen._counts(), (2, 1, 1, 1))
        self.assertEqual([quest.quest_id for quest in screen._quests()], ["active", "active-2"])
        screen.category = 1
        self.assertEqual([quest.quest_id for quest in screen._quests()], ["available"])
        screen.category = 2
        self.assertEqual([quest.quest_id for quest in screen._quests()], ["completed"])
        screen.category = 3
        self.assertEqual([quest.quest_id for quest in screen._quests()], ["failed"])

    def test_quest_log_selection_and_tab_click_reset_selection_and_scroll(self):
        screen = self._quest_screen()
        screen.selected = 4
        screen.scroll = 90

        screen.handle(InputState(mouse_clicked=True, mouse_pos=(50, 50)))

        self.assertEqual(screen.category, 0)
        self.assertEqual(screen.selected, 0)
        self.assertEqual(screen.scroll, 0)

        screen.handle(InputState(mouse_clicked=True, mouse_pos=(55, 190)))
        self.assertEqual(screen.selected, 1)

    def test_quest_log_scroll_is_clamped_to_list_bounds(self):
        screen = self._quest_screen()
        screen.category = 0
        screen.handle(InputState(mouse_pos=(100, 300), mouse_wheel=-100))
        self.assertGreaterEqual(screen.scroll, 0)
        self.assertLessEqual(screen.scroll, 54 * len(screen._quests()))

        screen.handle(InputState(mouse_pos=(100, 300), mouse_wheel=100))
        self.assertEqual(screen.scroll, 0)

    def test_quest_log_detail_scroll_is_independent_from_list_scroll(self):
        objectives = tuple(
            Objective(f"objective-{index}", f"Hedef {index}", ObjectiveType.CUSTOM)
            for index in range(10)
        )
        quest = Quest("long", "Uzun Görev", objectives, state=QuestState.ACTIVE)
        screen = QuestLogScreen(SimpleNamespace(
            application=SimpleNamespace(
                holder=SimpleNamespace(current=SimpleNamespace(quest_log=QuestLog((quest,))))
            ),
            item=lambda _item_id: None,
        ))

        detail_x, detail_y, detail_width, _detail_height = screen._details_bounds()
        screen.handle(InputState(
            mouse_pos=(detail_x + 10, detail_y + 80),
            mouse_wheel=-5,
        ))

        self.assertGreater(screen.detail_scroll, 0)
        self.assertEqual(screen.scroll, 0)
        self.assertGreater(screen._detail_content_height(quest), screen._details_bounds()[3])

    def test_quest_log_layout_stays_inside_window_content_viewport(self):
        screen = self._quest_screen()
        layout = screen._layout(960, 640)
        reward = screen._reward_bounds()

        self.assertEqual(layout["outer"][0:2], (24, 126))
        self.assertEqual(layout["outer"][2:4], (912, 624))
        self.assertLessEqual(
            reward[1] + reward[3],
            layout["outer"][1] + layout["outer"][3],
        )

    def test_quest_log_layout_scales_with_renderer_viewport(self):
        layout = self._quest_screen()._layout(1200, 800)

        self.assertEqual(layout["outer"][0:2], (24, 126))
        self.assertEqual(layout["outer"][2], 1152)
        self.assertEqual(layout["outer"][3], 784)
        self.assertLessEqual(layout["body_height"], 230)

    def test_quest_log_details_use_objective_and_reward_fields(self):
        screen = self._quest_screen()
        quest = screen._quests()[0]

        self.assertEqual(quest.objectives[0].progress, 1)
        self.assertEqual(quest.objectives[0].required, 2)
        self.assertTrue(quest.objectives[1].optional)
        self.assertEqual(quest.reward.experience, 20)
        self.assertEqual(quest.reward.currency, 3)
        self.assertEqual(quest.reward.items, (("iron_sword", 1),))
        self.assertEqual(quest.reward.reputation, (("wardens", 2),))

    def test_quest_log_window_mouse_coordinates_reach_screen(self):
        class Rect:
            def __init__(self, *value):
                self.x, self.y, self.width, self.height = (
                    value[0] if len(value) == 1 else value
                )
            @property
            def right(self):
                return self.x + self.width
            @property
            def bottom(self):
                return self.y + self.height
            @property
            def topleft(self):
                return self.x, self.y
            @topleft.setter
            def topleft(self, value):
                self.x, self.y = value
            def collidepoint(self, point):
                return self.x <= point[0] < self.right and self.y <= point[1] < self.bottom

        RectType = Rect
        class Backend:
            Rect = RectType

        screen = self._quest_screen()
        manager = WindowManager(Backend(), 960, 640)
        manager.register("quest_log", screen, (100, 100, 500, 470), content_origin=(24, 126))
        manager.open("quest_log")

        # Source tab (40, 174) maps to screen coordinates (116, 180).
        self.assertTrue(manager.handle_input(InputState(
            mouse_pos=(116, 180), mouse_clicked=True, mouse_button_down=True,
        )))
        self.assertEqual(screen.category, 0)

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
            self.assertEqual(migrated["schema_version"], 2)
            path.write_text(json.dumps(migrated), encoding="utf-8")
            service.load(path)

    def test_demo_save_is_deterministic(self):
        payloads = []
        for _ in range(2):
            app = GameApplication.create_default()
            service, ids = populate_opening_content(app)
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "save.json"
                service.save(path)
                payloads.append(path.read_text(encoding="utf-8"))
        self.assertEqual(payloads[0], payloads[1])

    def test_demo_starts_next_to_eren_at_southern_gate(self):
        service, ids = populate_opening_content(GameApplication.create_default())

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
                "main"
                if isinstance(screen, DialogueScreen)
                else "world"
                if isinstance(screen, (CombatScreen, CharacterCreationScreen))
                else None
            )
            self.assertEqual(screen.handle(InputState(actions={"back"})), expected)

    def test_market_window_does_not_own_window_close_navigation(self):
        service = SimpleNamespace(market_offers=lambda _market_id=None: ())
        screen = MarketScreen(service)

        self.assertIsNone(screen.handle(InputState(actions={"back", "world", "inventory", "character"})))

    def test_map_window_supports_map_input_without_screen_navigation(self):
        from application.content_pack import populate_opening_content
        service, _ = populate_opening_content(GameApplication.create_default())
        screen = MapScreen(service)
        screen.handle(InputState(actions={"down", "confirm"}))
        self.assertEqual(service.actor("hero").location_id, "village")
        self.assertIn("yalnızca konumları gösterir", screen.message)
        self.assertIsNone(screen.handle(InputState(actions={"back"})))

    def test_market_is_not_exposed_as_global_navigation(self):
        service, _ = populate_opening_content(GameApplication.create_default())
        window = object.__new__(GameWindow)
        window.service = service
        self.assertNotIn("market", window._nav_enabled())

    def test_legacy_navigation_bar_does_not_open_gameplay_windows(self):
        opened = []
        window = object.__new__(GameWindow)
        window.current = "main"
        window.gameplay_active = True
        window.screens = {
            "main": SimpleNamespace(menu_open=False),
            "map": object(),
        }
        window.renderer = SimpleNamespace(nav_hit=lambda _position: "map")
        window.window_manager = SimpleNamespace(
            windows={"map": object()},
            open=lambda window_id: opened.append(window_id),
        )
        window._nav_enabled = lambda: {"market": True}
        state = InputState(mouse_clicked=True, mouse_pos=(900, 30))

        window._handle_nav_click(state)

        self.assertEqual(opened, [])
        self.assertTrue(state.mouse_clicked)

    def test_legacy_navigation_shortcuts_are_not_routed_by_navigation_bar(self):
        opened = []
        window = object.__new__(GameWindow)
        window.current = "main"
        window.gameplay_active = True
        window.screens = {
            "main": SimpleNamespace(menu_open=False),
            "map": object(),
            "market": object(),
        }
        window.renderer = SimpleNamespace(nav_hit=lambda _position: None)
        window.window_manager = SimpleNamespace(
            windows={"map": object(), "market": object()},
            open=lambda window_id: opened.append(window_id),
        )
        window._nav_enabled = lambda: {"market": True}

        map_state = InputState(actions={"map"})
        market_state = InputState(actions={"market"})
        window._handle_nav_click(map_state)
        window._handle_nav_click(market_state)

        self.assertEqual(opened, [])
        self.assertEqual(map_state.actions, {"map"})
        self.assertEqual(market_state.actions, {"market"})

    def test_market_shortcut_is_not_a_supported_navigation_action(self):
        notices = []
        opened = []
        window = object.__new__(GameWindow)
        window.current = "main"
        window.gameplay_active = True
        window.screens = {"main": SimpleNamespace(menu_open=False), "market": object()}
        window.renderer = SimpleNamespace(nav_hit=lambda _position: None)
        window.window_manager = SimpleNamespace(
            windows={"market": object()},
            open=lambda window_id: opened.append(window_id),
        )
        window._nav_enabled = lambda: {}
        window._set_notice = lambda message, level: notices.append((message, level))

        window._handle_nav_click(InputState(actions={"market"}))

        self.assertEqual(opened, [])
        self.assertEqual(notices, [])

    def test_main_screen_is_reachable_from_world_map(self):
        from application.content_pack import populate_opening_content
        service, _ = populate_opening_content(GameApplication.create_default())
        map_screen = MapScreen(service)
        self.assertIsNone(map_screen.handle(InputState(actions={"confirm"})))
        local_screen = MainScreen(service)
        self.assertEqual(local_screen.menu_options[0], ("main", "Ana Ekrana Dön"))
        self.assertIsNone(local_screen.handle(InputState(actions={"confirm"})))

    def test_main_screen_finds_safe_paths_and_blocks_static_landmarks(self):
        from application.content_pack import populate_opening_content
        service, _ = populate_opening_content(GameApplication.create_default())
        local_screen = MainScreen(service)
        path = local_screen._path_to((16, 16), (8, 8))
        self.assertTrue(path)
        self.assertEqual(path[0], (16, 16))
        self.assertEqual(path[-1], (8, 8))
        self.assertFalse(local_screen._is_walkable((7, 10)))

    def test_mine_landmark_collects_iron_ore(self):
        service, ids = populate_opening_content(GameApplication.create_default())
        from application.content_pack import populate_gameplay_resources
        populate_gameplay_resources(service)
        service.move_actor(ids.hero_id, ids.forest_id)
        service.advance_by(1)
        service.move_actor(ids.hero_id, "north_mine")
        service.advance_by(1)

        local_screen = MainScreen(service)
        local_screen.selected = (15, 15)
        self.assertTrue(local_screen._gather_at_selected_tree())
        service.advance_by(service.gathering_duration(ids.hero_id))
        self.assertEqual(service.inventory("player").stocks, (("iron_ore", 1, "item"),))


    def test_dialogue_objective_helpers_tolerate_missing_and_malformed_data(self):
        self.assertIsNone(DialogueScreen._find_objective(None, "missing"))
        self.assertFalse(DialogueScreen._objective_completed(None, "missing"))
        self.assertFalse(DialogueScreen._objective_completed(
            SimpleNamespace(objectives=(SimpleNamespace(objective_id="collect"),)),
            "collect",
        ))
        self.assertFalse(DialogueScreen._objective_completed(
            SimpleNamespace(objectives=None), "collect",
        ))

    def test_dialogue_blacksmith_choice_hides_delivery_for_incomplete_objective_data(self):
        choice = SimpleNamespace(choice_id="deliver_blacksmith_ore", text="Teslim et")
        ordinary = SimpleNamespace(choice_id="ask_question", text="Soru sor")
        malformed_quest = SimpleNamespace(
            state=SimpleNamespace(value="active"),
            objectives=(SimpleNamespace(objective_id="collect_iron_ore"),),
        )
        bundle = SimpleNamespace(social=SimpleNamespace(dialogues={}))
        service = SimpleNamespace(
            application=SimpleNamespace(holder=SimpleNamespace(current=bundle)),
            blacksmith_quest=malformed_quest,
            inventory=lambda _inventory_id: SimpleNamespace(
                stocks=(("iron_ore", 3, "item"),)
            ),
            _dialogue_context=lambda *_args: {},
        )
        screen = DialogueScreen(service)
        screen.context = ("hero", "village_blacksmith", "missing_dialogue")
        screen.node = SimpleNamespace(node_id="start", choices=(choice, ordinary))

        self.assertEqual(screen._visible_choices(), (ordinary,))

    def test_dialogue_prompt_uses_selected_npc_name(self):
        from application.content_pack import populate_opening_content
        service, ids = populate_opening_content(GameApplication.create_default())
        screen = DialogueScreen(service)
        screen.set_target_npc(ids.npc_id)
        self.assertIn("Eren", screen.message)

    def test_village_menu_opens_market(self):
        service, _ids = populate_opening_content(GameApplication.create_default())
        screen = MainScreen(service)
        screen.menu_open = True
        screen.menu_selected = 4
        self.assertEqual(screen.handle(InputState(actions={"confirm"})), "market")

    def test_inventory_and_market_windows_ignore_legacy_screen_navigation(self):
        inventory = SimpleNamespace(items=(), stocks=(), weight=0)
        service = SimpleNamespace(
            inventory=lambda _inventory_id: inventory,
            item=lambda _item_id: None,
            actor_activity=lambda _actor_id: None,
            state=lambda: SimpleNamespace(simulation_tick=0),
            market_offers=lambda _market_id=None: (),
        )
        self.assertIsNone(
            InventoryScreen(service).handle(InputState(actions={"back", "world", "market", "character"}))
        )
        self.assertIsNone(
            MarketScreen(service).handle(InputState(actions={"back", "world", "inventory", "character"}))
        )

    def test_character_window_preserves_skill_selection_without_legacy_close_route(self):
        service, _ = populate_opening_content(GameApplication.create_default())
        screen = CharacterScreen(service)
        character = service.actor_character("hero")
        skills = tuple(character.skills.to_dict())
        self.assertTrue(skills)
        screen.handle(InputState(actions={"down"}))
        self.assertEqual(screen.selected_skill, 1 % len(skills))
        self.assertIsNone(screen.handle(InputState(actions={"back"})))

    def test_escape_opens_and_closes_central_pause_menu(self):
        window = object.__new__(GameWindow)
        window.gameplay_active = True
        window.pause_menu_open = False
        window.pause_menu_selected = 0
        window.running = True
        window._render_current = lambda: None

        window.step = lambda events=(): None
        window._open_pause_menu()
        self.assertTrue(window.pause_menu_open)
        window._handle_pause_menu(InputState(actions={"back"}))
        self.assertFalse(window.pause_menu_open)

    def test_pause_menu_actions_do_not_dispatch_to_gameplay_windows(self):
        dispatched = []
        window = object.__new__(GameWindow)
        window.gameplay_active = True
        window.pause_menu_open = True
        window.pause_menu_selected = 0
        window.running = True
        window._handle_pause_menu(InputState(actions={"down"}))
        self.assertEqual(window.pause_menu_selected, 1)

        manager = type(
            "Manager", (), {"handle_input": lambda self, state: dispatched.append(state)
            }
        )()
        self.assertEqual(dispatched, [])

    def test_village_gate_opens_eren_dialogue(self):
        from application.content_pack import populate_opening_content
        service, ids = populate_opening_content(GameApplication.create_default())
        local_screen = MainScreen(service)
        local_screen.selected = (16, 30)
        self.assertEqual(local_screen.handle(InputState(actions={"confirm"})), "dialogue")
        self.assertEqual(local_screen.selected_npc_id, ids.npc_id)

    def test_save_load_keys_are_part_of_the_input_contract(self):
        mapper = InputMapper()
        save_event = type("Event", (), {"type": "KEYDOWN", "key": "f5"})()
        load_event = type("Event", (), {"type": "KEYDOWN", "key": "f9"})()
        self.assertTrue(mapper.collect([save_event]).pressed("save"))
        self.assertTrue(mapper.collect([load_event]).pressed("load"))

    def test_market_is_not_keyboard_mapped_but_inventory_is(self):
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
        map_state = mapper.collect([market_event])
        self.assertFalse(map_state.pressed("market"))
        self.assertTrue(map_state.pressed("map"))
        self.assertTrue(mapper.collect([inventory_event]).pressed("inventory"))

    def test_c_key_maps_to_character_action(self):
        mapper = InputMapper()
        event = type("Event", (), {"type": "KEYDOWN", "key": "c"})()
        state = mapper.collect([event])
        self.assertTrue(state.pressed("character"))
        self.assertFalse(state.pressed("craft"))

    def test_main_menu_new_game_has_distinct_action(self):
        menu = MainMenu()
        self.assertIsNone(menu.handle(InputState(actions={"confirm"})))
        self.assertTrue(menu.new_game_open)
        self.assertEqual(
            menu.handle(InputState(actions={"confirm"})),
            "load_slots",
        )

    def test_main_menu_test_world_starts_directly_without_opening_new_game_submenu(self):
        menu = MainMenu()
        menu.selected = 2

        self.assertEqual(
            menu.handle(InputState(actions={"confirm"})),
            "test_world",
        )
        self.assertFalse(menu.new_game_open)

    def test_main_menu_new_game_mouse_click_also_opens_submenu(self):
        class Rect:
            def __init__(self, *value):
                if len(value) == 1:
                    value = value[0]
                self.x, self.y, self.width, self.height = value

            def collidepoint(self, point):
                return (
                    self.x <= point[0] < self.x + self.width
                    and self.y <= point[1] < self.y + self.height
                )

        RectType = Rect

        class Backend:
            Rect = RectType

        renderer = type(
            "Renderer",
            (),
            {"width": 1365, "height": 768, "pg": Backend()},
        )()
        menu = MainMenu()
        rect = menu._menu_rects(renderer)[0]

        self.assertIsNone(menu.handle(
            InputState(mouse_clicked=True, mouse_pos=(rect.x + 1, rect.y + 1)),
            renderer,
        ))
        self.assertTrue(menu.new_game_open)

    def test_main_menu_submenu_reopens_after_load_return_cycle(self):
        menu = MainMenu()

        self.assertIsNone(menu.handle(InputState(actions={"confirm"})))
        self.assertEqual(
            menu.handle(InputState(actions={"confirm"})),
            "load_slots",
        )
        self.assertFalse(menu.new_game_open)

        self.assertIsNone(menu.handle(InputState(actions={"confirm"})))
        self.assertTrue(menu.new_game_open)
        menu.new_game_selected = 1
        self.assertEqual(
            menu.handle(InputState(actions={"confirm"})),
            "new_game",
        )

    def test_main_menu_continue_opens_save_slots(self):
        menu = MainMenu()
        menu.selected = 1

        window = object.__new__(GameWindow)
        window.input = InputMapper()
        window.gameplay_active = False
        window.pause_menu_open = False
        window.running = True
        window.notice = ""
        window.notice_level = "info"
        window._notice_frames = 0
        window.current = "menu"
        window.gameplay_screen = "main"
        window.screens = {
            "menu": menu,
            "save_slots": type(
                "Slots", (), {"mode": "load", "selected": 0, "message": "",
                              "pending_overwrite": False}
            )(),
        }
        window.window_manager = type("Manager", (), {"windows": {}})()
        window.renderer = type(
            "Renderer",
            (),
            {"mouse_pos": None, "nav_current": None, "nav_enabled": {}},
        )()
        window._render_current = lambda: None

        window.step([type("Event", (), {"type": "KEYDOWN", "key": "return"})()])

        self.assertEqual(window.current, "save_slots")
        self.assertFalse(window.gameplay_active)

    def test_save_slots_save_mode_requires_overwrite_confirmation(self):
        with tempfile.TemporaryDirectory() as directory:
            selected = []
            screen = SaveSlotsScreen(
                directory,
                lambda index, path, exists: selected.append(
                    (index, path, exists)
                ) or "main",
                mode="save",
            )
            path = screen.slot_path(0)
            path.write_text("old", encoding="utf-8")
            screen.selected = 0

            self.assertIsNone(screen.handle(InputState(actions={"confirm"})))
            self.assertTrue(screen.pending_overwrite)
            self.assertEqual(selected, [])

            self.assertEqual(
                screen.handle(InputState(actions={"confirm"})),
                "main",
            )
            self.assertEqual(selected, [(0, path, True)])

    def test_new_game_rebuilds_session_and_opens_creation_flow(self):
        old_service, _ = populate_opening_content(GameApplication.create_default())
        old_service.application.customize_character(
            "hero",
            "Eski Kahraman",
            30,
            {
                attribute: 10
                for attribute, _label, _help in CharacterCreationScreen.ATTRIBUTES
            },
        )

        class Window:
            def __init__(self):
                self.screen = None

        class Manager:
            open_ids = ()

            def __init__(self):
                self.windows = {
                    "inventory": Window(),
                    "character": Window(),
                    "quest_log": Window(),
                    "production": Window(),
                    "market": Window(),
                    "map": Window(),
                }

            def close(self, window_id):
                return None

        window = object.__new__(GameWindow)
        window.service = old_service
        window.screens = {}
        window.window_manager = Manager()
        window.pause_menu_open = True
        window.current = "menu"
        window.gameplay_active = True
        window.selected_slot = 2

        window._start_new_game()

        self.assertIsNot(window.service, old_service)
        self.assertEqual(window.current, "opening")
        self.assertFalse(window.gameplay_active)
        self.assertFalse(window.pause_menu_open)
        self.assertIsNone(window.selected_slot)
        self.assertEqual(window.screens["character_creation"].name, "")
        self.assertNotEqual(
            window.service.application.holder.current.characters.get("hero").name,
            "Eski Kahraman",
        )
        self.assertIs(
            window.window_manager.windows["inventory"].screen,
            window.screens["inventory"],
        )
        self.assertIs(
            window.window_manager.windows["production"].screen,
            window.screens["production"],
        )
        self.assertIs(
            window.window_manager.windows["market"].screen,
            window.screens["market"],
        )
        self.assertIs(
            window.window_manager.windows["map"].screen,
            window.screens["map"],
        )

    def test_game_window_routes_real_backend_d_key_to_dialogue_history(self):
        class Backend:
            KEYDOWN = "KEYDOWN"
            K_d = 7

        class Manager:
            def handle_input(self, state):
                raise AssertionError("Dialogue history must bypass WindowManager")

        dialogue = DialogueScreen(SimpleNamespace())
        dialogue.opening_stage = "dialogue"
        dialogue.node = object()
        dialogue.history = [("NPC", "Mesaj")]

        window = object.__new__(GameWindow)
        window.input = InputMapper(Backend())
        window.gameplay_active = True
        window.pause_menu_open = False
        window.running = True
        window.notice = ""
        window.notice_level = "info"
        window._notice_frames = 0
        window.current = "dialogue"
        window.gameplay_screen = "main"
        window.screens = {"dialogue": dialogue}
        window.window_manager = Manager()
        window.renderer = type("Renderer", (), {"mouse_pos": None})()
        window._handle_nav_click = lambda state: None
        window._render_current = lambda: None
        dialogue.target_npc_id = "npc"

        event = type("Event", (), {"type": "KEYDOWN", "key": 7})()
        window.step([event])
        self.assertTrue(dialogue.history_open)
        self.assertIsNotNone(dialogue.node)

        window.step([event])
        self.assertFalse(dialogue.history_open)
        self.assertIsNotNone(dialogue.node)

    def test_dialogue_overlay_routes_d_when_main_screen_is_current(self):
        class Backend:
            KEYDOWN = "KEYDOWN"
            K_d = 7

        class Manager:
            def handle_input(self, state):
                raise AssertionError("Active dialogue must receive D before WindowManager")

        dialogue = DialogueScreen(SimpleNamespace())
        dialogue.target_npc_id = "npc"
        dialogue.opening_stage = "dialogue"
        dialogue.node = object()
        dialogue.history = [("NPC", "Mesaj")]

        window = object.__new__(GameWindow)
        window.input = InputMapper(Backend())
        window.gameplay_active = True
        window.pause_menu_open = False
        window.running = True
        window.notice = ""
        window.notice_level = "info"
        window._notice_frames = 0
        window.current = "main"
        window.gameplay_screen = "main"
        window.screens = {
            "main": type("World", (), {"menu_open": False})(),
            "dialogue": dialogue,
        }
        window.window_manager = Manager()
        window.renderer = type("Renderer", (), {"mouse_pos": None})()
        window._handle_nav_click = lambda state: None
        window._render_current = lambda: None

        event = type("Event", (), {"type": "KEYDOWN", "key": 7})()
        window.step([event])

        self.assertTrue(dialogue.history_open)
        self.assertIsNotNone(dialogue.node)

    def test_dialogue_overlay_is_inactive_without_target_npc(self):
        dialogue = DialogueScreen(SimpleNamespace())
        self.assertFalse(dialogue.is_active())

    def test_game_window_d_key_does_not_change_history_while_pause_menu_is_open(self):
        class Backend:
            KEYDOWN = "KEYDOWN"
            K_d = 7

        dialogue = DialogueScreen(SimpleNamespace())
        dialogue.opening_stage = "dialogue"
        dialogue.node = object()
        window = object.__new__(GameWindow)
        window.input = InputMapper(Backend())
        window.gameplay_active = True
        window.pause_menu_open = True
        window.running = True
        window.notice = ""
        window.notice_level = "info"
        window._notice_frames = 0
        window.current = "dialogue"
        window.screens = {"dialogue": dialogue}
        window.window_manager = type("Manager", (), {})()
        window.renderer = type("Renderer", (), {"mouse_pos": None})()
        window._handle_pause_menu = lambda state: None
        window._render_current = lambda: None
        window._render_pause_menu = lambda: None

        event = type("Event", (), {"type": "KEYDOWN", "key": 7})()
        window.step([event])
        self.assertFalse(dialogue.history_open)

        window.pause_menu_open = False
        dialogue.target_npc_id = "npc"
        window.step([event])
        self.assertTrue(dialogue.history_open)

    def test_game_window_routes_real_c_key_to_character_window(self):
        class Rect:
            def __init__(self, value):
                self.x, self.y, self.width, self.height = value
            @property
            def right(self):
                return self.x + self.width
            @property
            def bottom(self):
                return self.y + self.height
            @property
            def topleft(self):
                return self.x, self.y
            @topleft.setter
            def topleft(self, value):
                self.x, self.y = value
            def collidepoint(self, point):
                return self.x <= point[0] < self.right and self.y <= point[1] < self.bottom

        RectType = Rect
        class Backend:
            Rect = RectType

        manager = WindowManager(Backend(), 960, 640)
        manager.register("character", object(), (100, 100, 300, 240))
        window = object.__new__(GameWindow)
        window.input = InputMapper()
        window.gameplay_active = True
        window.pause_menu_open = False
        window.running = True
        window.notice = ""
        window.notice_level = "info"
        window._notice_frames = 0
        window.current = "main"
        window.gameplay_screen = "main"
        window.screens = {
            "main": type("World", (), {"menu_open": False, "name_entry_active": False})(),
        }
        window.window_manager = manager
        window.renderer = type("Renderer", (), {"mouse_pos": None})()
        window._nav_enabled = lambda: {}
        window._render_current = lambda: None
        window.step([type("Event", (), {"type": "KEYDOWN", "key": "c"})()])

        self.assertEqual(manager.open_ids, ("character",))

    def test_game_window_routes_real_i_key_as_inventory_toggle(self):
        class Rect:
            def __init__(self, value):
                self.x, self.y, self.width, self.height = value
            @property
            def right(self):
                return self.x + self.width
            @property
            def bottom(self):
                return self.y + self.height
            @property
            def topleft(self):
                return self.x, self.y
            @topleft.setter
            def topleft(self, value):
                self.x, self.y = value
            def collidepoint(self, point):
                return self.x <= point[0] < self.right and self.y <= point[1] < self.bottom

        RectType = Rect
        class Backend:
            Rect = RectType

        manager = WindowManager(Backend(), 960, 640)
        manager.register("inventory", object(), (24, 110, 912, 470))
        manager.register("character", object(), (80, 90, 760, 470))
        manager.register("quest_log", object(), (24, 110, 912, 470))
        window = object.__new__(GameWindow)
        window.input = InputMapper()
        window.gameplay_active = True
        window.pause_menu_open = False
        window.running = True
        window.notice = ""
        window.notice_level = "info"
        window._notice_frames = 0
        window.current = "main"
        window.gameplay_screen = "main"
        window.screens = {
            "main": type("World", (), {"menu_open": False, "name_entry_active": False})(),
        }
        window.window_manager = manager
        window.renderer = type("Renderer", (), {"mouse_pos": None})()
        window._render_current = lambda: None

        event = type("Event", (), {"type": "KEYDOWN", "key": "i"})()
        window.step([event])
        self.assertEqual(manager.open_ids, ("inventory",))
        window.step([event])
        self.assertEqual(manager.open_ids, ())

        window.step([event])
        window.step([type("Event", (), {"type": "KEYDOWN", "key": "c"})()])
        window.step([type("Event", (), {"type": "KEYDOWN", "key": "j"})()])
        self.assertEqual(manager.open_ids, ("inventory", "character", "quest_log"))

    def test_i_key_is_ignored_while_pause_menu_is_open(self):
        class Rect:
            def __init__(self, value):
                self.x, self.y, self.width, self.height = value
            @property
            def right(self):
                return self.x + self.width
            @property
            def bottom(self):
                return self.y + self.height
            def collidepoint(self, point):
                return self.x <= point[0] < self.right and self.y <= point[1] < self.bottom

        RectType = Rect
        class Backend:
            Rect = RectType

        manager = WindowManager(Backend(), 960, 640)
        manager.register("inventory", object(), (24, 110, 912, 470))
        window = object.__new__(GameWindow)
        window.input = InputMapper()
        window.gameplay_active = True
        window.pause_menu_open = True
        window.running = True
        window.notice = ""
        window.notice_level = "info"
        window._notice_frames = 0
        window.current = "main"
        window.screens = {"main": object()}
        window.window_manager = manager
        window._handle_pause_menu = lambda state: None
        window._render_current = lambda: None
        window._render_pause_menu = lambda: None

        window.step([type("Event", (), {"type": "KEYDOWN", "key": "i"})()])

        self.assertEqual(manager.open_ids, ())

    def test_j_key_toggles_quest_window_through_real_game_window_step(self):
        class Rect:
            def __init__(self, value):
                self.x, self.y, self.width, self.height = value
            @property
            def right(self):
                return self.x + self.width
            @property
            def bottom(self):
                return self.y + self.height
            @property
            def topleft(self):
                return self.x, self.y
            @topleft.setter
            def topleft(self, value):
                self.x, self.y = value
            def collidepoint(self, point):
                return self.x <= point[0] < self.right and self.y <= point[1] < self.bottom

        RectType = Rect
        class Backend:
            Rect = RectType

        manager = WindowManager(Backend(), 960, 640)
        manager.register("quest_log", object(), (120, 100, 720, 470))
        window = object.__new__(GameWindow)
        window.input = InputMapper()
        window.gameplay_active = True
        window.pause_menu_open = False
        window.running = True
        window.notice = ""
        window.notice_level = "info"
        window._notice_frames = 0
        window.current = "main"
        window.gameplay_screen = "main"
        window.screens = {
            "main": type("World", (), {"menu_open": False, "name_entry_active": False})(),
        }
        window.window_manager = manager
        window.renderer = type("Renderer", (), {"mouse_pos": None})()
        window._render_current = lambda: None

        event = type("Event", (), {"type": "KEYDOWN", "key": "j"})()
        window.step([event])
        self.assertEqual(manager.open_ids, ("quest_log",))
        window.step([event])
        self.assertEqual(manager.open_ids, ())

    def test_j_key_is_ignored_while_pause_menu_is_open(self):
        class Rect:
            def __init__(self, value):
                self.x, self.y, self.width, self.height = value
            @property
            def right(self):
                return self.x + self.width
            @property
            def bottom(self):
                return self.y + self.height
            def collidepoint(self, point):
                return self.x <= point[0] < self.right and self.y <= point[1] < self.bottom

        RectType = Rect
        class Backend:
            Rect = RectType

        manager = WindowManager(Backend(), 960, 640)
        manager.register("quest_log", object(), (120, 100, 720, 470))
        window = object.__new__(GameWindow)
        window.input = InputMapper()
        window.gameplay_active = True
        window.pause_menu_open = True
        window.running = True
        window.notice = ""
        window.notice_level = "info"
        window._notice_frames = 0
        window.current = "main"
        window.screens = {"main": object()}
        window.window_manager = manager
        window._handle_pause_menu = lambda state: None
        window._render_current = lambda: None
        window._render_pause_menu = lambda: None

        window.step([type("Event", (), {"type": "KEYDOWN", "key": "j"})()])

        self.assertEqual(manager.open_ids, ())

    def test_gameplay_world_is_persistent_and_cannot_return_to_menu(self):
        window = object.__new__(GameWindow)
        window.gameplay_active = False
        window.gameplay_screen = "main"
        window.current = "menu"
        window.screens = {"main": object(), "menu": object()}
        window.window_manager = type(
            "Manager", (), {"windows": {}, "render": lambda self, renderer: None}
        )()
        window.notice = ""
        window.notice_level = "info"
        window._notice_frames = 0

        self.assertTrue(window._set_current("main"))
        self.assertTrue(window.gameplay_active)
        self.assertFalse(window._set_current("menu"))
        self.assertEqual(window.current, "main")

    def test_gameplay_tool_routes_open_windows_without_replacing_main_screen(self):
        class Manager:
            def __init__(self):
                self.windows = {"inventory": object()}
                self.opened = []

            def open(self, window_id):
                self.opened.append(window_id)

        window = object.__new__(GameWindow)
        window.gameplay_active = True
        window.gameplay_screen = "main"
        window.current = "main"
        window.window_manager = Manager()

        self.assertTrue(window._set_current("inventory"))
        self.assertEqual(window.window_manager.opened, ["inventory"])
        self.assertEqual(window.current, "main")
        self.assertTrue(window.gameplay_active)

        window.gameplay_active = False
        self.assertFalse(window._set_current("inventory"))
        self.assertEqual(window.current, "main")
        self.assertEqual(window.window_manager.opened, ["inventory"])

    def test_gameplay_window_ids_include_separate_market_and_trade_tools(self):
        from game_ui.game_window import GAMEPLAY_WINDOW_IDS

        self.assertEqual(GAMEPLAY_WINDOW_IDS, {
            "character", "inventory", "quest_log", "map", "production", "market", "trade",
            "container",
        })

    def test_gameplay_world_renders_before_active_surface(self):
        calls = []

        class Surface:
            def __init__(self, name):
                self.name = name

            def render(self, renderer):
                calls.append(self.name)

        window = object.__new__(GameWindow)
        window.gameplay_active = True
        window.gameplay_screen = "main"
        window.current = "inventory"
        window.renderer = object()
        window.window_manager = type(
            "Manager", (), {"render": lambda self, renderer: calls.append("inventory")}
        )()
        window.screens = {
            "main": Surface("world"),
            "inventory": Surface("inventory"),
        }

        window._render_current()

        self.assertEqual(calls, ["world", "inventory"])

    def test_dialogue_history_toggles_without_advancing_dialogue(self):
        screen = DialogueScreen(SimpleNamespace())
        screen.opening_stage = "dialogue"
        screen.history = [
            ("Eren" if index % 2 == 0 else "Sen", f"Mesaj {index}")
            for index in range(10)
        ]
        screen.history_scroll = 0

        screen.handle(InputState(actions={"dialogue_history"}))

        self.assertTrue(screen.history_open)
        self.assertEqual(screen.history_scroll, 760)
        self.assertEqual(len(screen.history), 10)
        self.assertEqual(screen.opening_stage, "dialogue")

        screen.handle(InputState(actions={"dialogue_history"}))

        self.assertFalse(screen.history_open)
        self.assertEqual(screen.history_scroll, 0)
        self.assertEqual(screen.opening_stage, "dialogue")

    def test_dialogue_choice_mouse_click_updates_selection(self):
        screen = DialogueScreen(SimpleNamespace())
        screen.opening_stage = "ask_reason"
        screen.selected = 0
        x, y, _width, _height = screen.panel_rect()

        screen.handle(InputState(
            mouse_clicked=True,
            mouse_pos=(x + 160, y + 124 + 30),
        ))

        self.assertEqual(screen.selected, 1)

    def test_dialogue_render_order_keeps_world_windows_and_overlay(self):
        calls = []

        class Surface:
            def render(self, renderer):
                calls.append("world")

        class Dialogue:
            def is_active(self):
                return True

            def render(self, renderer):
                calls.append("dialogue")

        window = object.__new__(GameWindow)
        window.gameplay_active = True
        window.gameplay_screen = "main"
        window.current = "dialogue"
        window.renderer = object()
        window.window_manager = type(
            "Manager", (), {"render": lambda self, renderer: calls.append("windows")}
        )()
        window.screens = {
            "main": Surface(),
            "dialogue": Dialogue(),
        }

        window._render_current()

        self.assertEqual(calls, ["world", "windows", "dialogue"])

    def test_window_manager_keeps_two_windows_open_and_singleton(self):
        class Rect:
            def __init__(self, *value):
                self.x, self.y, self.width, self.height = (
                    value[0] if len(value) == 1 else value
                )
            @property
            def right(self):
                return self.x + self.width
            @property
            def bottom(self):
                return self.y + self.height
            @property
            def topleft(self):
                return self.x, self.y
            @topleft.setter
            def topleft(self, value):
                self.x, self.y = value
            def collidepoint(self, point):
                return (
                    self.x <= point[0] < self.right
                    and self.y <= point[1] < self.bottom
                )

        RectType = Rect
        class Backend:
            Rect = RectType

        manager = WindowManager(Backend(), 960, 640)
        manager.register("inventory", object(), (20, 20, 300, 240))
        manager.register("character", object(), (100, 100, 300, 240))
        manager.open("inventory")
        manager.open("character")

        self.assertEqual(manager.open_ids, ("inventory", "character"))
        manager.focus("inventory")
        self.assertEqual(manager.open_ids, ("character", "inventory"))
        with self.assertRaises(ValueError):
            manager.register("inventory", object(), (0, 0, 100, 100))

    def test_window_manager_keeps_three_windows_open_and_preserves_focus_order(self):
        class Rect:
            def __init__(self, value):
                self.x, self.y, self.width, self.height = value
            @property
            def right(self):
                return self.x + self.width
            @property
            def bottom(self):
                return self.y + self.height
            @property
            def topleft(self):
                return self.x, self.y
            @topleft.setter
            def topleft(self, value):
                self.x, self.y = value
            def collidepoint(self, point):
                return self.x <= point[0] < self.right and self.y <= point[1] < self.bottom

        RectType = Rect
        class Backend:
            Rect = RectType

        manager = WindowManager(Backend(), 960, 640)
        manager.register("inventory", object(), (20, 20, 300, 240))
        manager.register("character", object(), (100, 100, 300, 240))
        manager.register("quest_log", object(), (180, 140, 400, 240))
        manager.open("inventory")
        manager.open("character")
        manager.open("quest_log")
        original_position = manager.windows["quest_log"].bounds.topleft

        manager.focus("inventory")

        self.assertEqual(manager.open_ids, ("character", "quest_log", "inventory"))
        self.assertEqual(manager.windows["quest_log"].bounds.topleft, original_position)

    def test_window_manager_closes_only_quest_window_with_x(self):
        class Rect:
            def __init__(self, *value):
                self.x, self.y, self.width, self.height = (
                    value[0] if len(value) == 1 else value
                )
            @property
            def right(self):
                return self.x + self.width
            @property
            def bottom(self):
                return self.y + self.height
            @property
            def topleft(self):
                return self.x, self.y
            @topleft.setter
            def topleft(self, value):
                self.x, self.y = value
            def collidepoint(self, point):
                return self.x <= point[0] < self.right and self.y <= point[1] < self.bottom

        RectType = Rect
        class Backend:
            Rect = RectType

        manager = WindowManager(Backend(), 960, 640)
        manager.register("inventory", object(), (20, 20, 300, 240))
        manager.register("character", object(), (100, 100, 300, 240))
        manager.register("quest_log", object(), (180, 140, 400, 240))
        manager.open("inventory")
        manager.open("character")
        manager.open("quest_log")

        close_position = (manager.windows["quest_log"].bounds.right - 10, 150)
        self.assertTrue(manager.handle_input(InputState(
            mouse_pos=close_position, mouse_clicked=True, mouse_button_down=True,
        )))

        self.assertFalse(manager.is_open("quest_log"))
        self.assertEqual(manager.open_ids, ("inventory", "character"))

    def test_character_shortcut_toggles_character_without_closing_inventory(self):
        class Rect:
            def __init__(self, value):
                self.x, self.y, self.width, self.height = value
            @property
            def right(self):
                return self.x + self.width
            @property
            def bottom(self):
                return self.y + self.height
            @property
            def topleft(self):
                return self.x, self.y
            @topleft.setter
            def topleft(self, value):
                self.x, self.y = value
            def collidepoint(self, point):
                return self.x <= point[0] < self.right and self.y <= point[1] < self.bottom

        RectType = Rect
        class Backend:
            Rect = RectType

        manager = WindowManager(Backend(), 960, 640)
        manager.register("inventory", object(), (20, 20, 300, 240))
        manager.register("character", object(), (100, 100, 300, 240))
        manager.open("inventory")
        state = InputState(actions={"character"})
        self.assertTrue(manager.handle_input(state))
        self.assertEqual(manager.open_ids, ("inventory", "character"))
        self.assertEqual(state.actions, set())
        self.assertTrue(manager.handle_input(InputState(actions={"character"})))
        self.assertEqual(manager.open_ids, ("inventory",))

    def test_window_manager_drag_focus_and_event_consumption(self):
        class Rect:
            def __init__(self, *value):
                self.x, self.y, self.width, self.height = (
                    value[0] if len(value) == 1 else value
                )
            @property
            def right(self):
                return self.x + self.width
            @property
            def bottom(self):
                return self.y + self.height
            @property
            def topleft(self):
                return self.x, self.y
            @topleft.setter
            def topleft(self, value):
                self.x, self.y = value
            def collidepoint(self, point):
                return (
                    self.x <= point[0] < self.right
                    and self.y <= point[1] < self.bottom
                )

        RectType = Rect
        class Backend:
            Rect = RectType

        class Screen:
            def __init__(self):
                self.calls = []
            def handle(self, state):
                self.calls.append(state.mouse_pos)

        manager = WindowManager(Backend(), 960, 640)
        screen = Screen()
        manager.register("inventory", screen, (100, 100, 300, 240))
        manager.open("inventory")

        self.assertTrue(manager.handle_input(InputState(
            mouse_pos=(130, 110), mouse_clicked=True, mouse_button_down=True,
        )))
        self.assertTrue(manager.windows["inventory"].dragging)
        self.assertTrue(manager.handle_input(InputState(
            mouse_pos=(220, 180), mouse_motion=True,
        )))
        self.assertEqual(manager.windows["inventory"].bounds.topleft, (190, 170))
        self.assertTrue(manager.handle_input(InputState(
            mouse_pos=(220, 180), mouse_button_up=True,
        )))
        self.assertFalse(manager.windows["inventory"].dragging)

        self.assertTrue(manager.handle_input(InputState(
            mouse_pos=(220, 220), mouse_clicked=True, mouse_button_down=True,
        )))
        self.assertEqual(screen.calls[-1], (54, 144))
        self.assertEqual(
            manager._screen_position(
                manager.windows["inventory"], (190 + 320, 170 + 32 + 64)
            ),
            (344, 190),
        )

    def test_window_manager_routes_focused_keyboard_text_and_wheel_input(self):
        class Rect:
            def __init__(self, value):
                self.x, self.y, self.width, self.height = value
            @property
            def right(self):
                return self.x + self.width
            @property
            def bottom(self):
                return self.y + self.height
            @property
            def topleft(self):
                return self.x, self.y
            @topleft.setter
            def topleft(self, value):
                self.x, self.y = value
            def collidepoint(self, point):
                return self.x <= point[0] < self.right and self.y <= point[1] < self.bottom

        RectType = Rect
        class Backend:
            Rect = RectType

        class Screen:
            def __init__(self):
                self.states = []
            def handle(self, state):
                self.states.append(state)

        screen = Screen()
        manager = WindowManager(Backend(), 960, 640)
        manager.register("inventory", screen, (100, 100, 300, 240))
        manager.open("inventory")

        self.assertTrue(manager.handle_input(InputState(actions={"up"})))
        self.assertEqual(screen.states[-1].actions, {"up"})

        self.assertTrue(manager.handle_input(InputState(text="a")))
        self.assertEqual(screen.states[-1].text, "a")

        self.assertTrue(manager.handle_input(InputState(
            mouse_pos=(150, 150), mouse_wheel=1,
        )))
        self.assertEqual(screen.states[-1].mouse_wheel, 1)
        self.assertEqual(len(screen.states), 3)

    def test_window_manager_close_preserves_gameplay_owner(self):
        class Rect:
            def __init__(self, *value):
                self.x, self.y, self.width, self.height = (
                    value[0] if len(value) == 1 else value
                )
            @property
            def right(self):
                return self.x + self.width
            @property
            def bottom(self):
                return self.y + self.height
            @property
            def topleft(self):
                return self.x, self.y
            @topleft.setter
            def topleft(self, value):
                self.x, self.y = value
            def collidepoint(self, point):
                return (
                    self.x <= point[0] < self.right
                    and self.y <= point[1] < self.bottom
                )

        RectType = Rect
        class Backend:
            Rect = RectType

        manager = WindowManager(Backend(), 960, 640)
        manager.register("inventory", object(), (20, 20, 300, 240))
        manager.open("inventory")
        manager.close("inventory")
        self.assertEqual(manager.open_ids, ())
        self.assertFalse(manager.is_open("inventory"))

    def test_inventory_control_uses_window_coordinates_after_move(self):
        class Rect:
            def __init__(self, *value):
                self.x, self.y, self.width, self.height = (
                    value[0] if len(value) == 1 else value
                )
            @property
            def right(self):
                return self.x + self.width
            @property
            def bottom(self):
                return self.y + self.height
            @property
            def topleft(self):
                return self.x, self.y
            @topleft.setter
            def topleft(self, value):
                self.x, self.y = value
            def collidepoint(self, point):
                return (
                    self.x <= point[0] < self.right
                    and self.y <= point[1] < self.bottom
                )

        RectType = Rect
        class Backend:
            Rect = RectType

        service, _ = populate_opening_content(GameApplication.create_default())
        from application.content_pack import populate_gameplay_resources
        populate_gameplay_resources(service)
        screen = InventoryScreen(service)
        manager = WindowManager(Backend(), 960, 640)
        manager.register("inventory", screen, (100, 100, 912, 470))
        manager.open("inventory")

        # Use the responsive layout's real second-tab bounds, then translate
        # screen-local coordinates into the moved window's pointer space.
        tab = screen._layout()["tabs"][1]
        local_point = (tab[0] + tab[2] // 2, tab[1] + tab[3] // 2)
        pointer = (
            100 + local_point[0] - 24,
            100 + manager.TITLE_HEIGHT + local_point[1] - 126,
        )
        self.assertTrue(manager.handle_input(InputState(
            mouse_pos=pointer,
            mouse_clicked=True,
            mouse_button_down=True,
        )))
        self.assertEqual(screen.tab, 1)

    def test_inventory_tab_hitbox_tracks_responsive_window_scale(self):
        class Rect:
            def __init__(self, *value):
                self.x, self.y, self.width, self.height = (
                    value[0] if len(value) == 1 else value
                )
            @property
            def right(self):
                return self.x + self.width
            @property
            def bottom(self):
                return self.y + self.height
            @property
            def topleft(self):
                return self.x, self.y
            @topleft.setter
            def topleft(self, value):
                self.x, self.y = value
            def collidepoint(self, point):
                return (
                    self.x <= point[0] < self.right
                    and self.y <= point[1] < self.bottom
                )

        RectType = Rect
        class Backend:
            Rect = RectType

        service, _ = populate_opening_content(GameApplication.create_default())
        from application.content_pack import populate_gameplay_resources
        populate_gameplay_resources(service)
        screen = InventoryScreen(service)
        manager = WindowManager(Backend(), 960, 640)
        manager.register("inventory", screen, (100, 100, 500, 470))
        manager.open("inventory")

        # Responsive windows use their live viewport directly: no legacy
        # design-size scaling or letterbox offset is applied to pointer input.
        tab = screen._layout()["tabs"][1]
        local_point = (tab[0] + tab[2] // 2, tab[1] + tab[3] // 2)
        pointer = (
            100 + local_point[0] - 24,
            100 + manager.TITLE_HEIGHT + local_point[1] - 126,
        )
        self.assertTrue(manager.handle_input(InputState(
            mouse_pos=pointer, mouse_clicked=True, mouse_button_down=True,
        )))
        self.assertEqual(screen.tab, 1)

    def test_inventory_drag_swaps_slots_and_invalid_drop_preserves_order(self):
        class Rect:
            def __init__(self, *value):
                self.x, self.y, self.width, self.height = (
                    value[0] if len(value) == 1 else value
                )
            @property
            def right(self):
                return self.x + self.width
            @property
            def bottom(self):
                return self.y + self.height
            @property
            def topleft(self):
                return self.x, self.y
            @topleft.setter
            def topleft(self, value):
                self.x, self.y = value
            def collidepoint(self, point):
                return (
                    self.x <= point[0] < self.right
                    and self.y <= point[1] < self.bottom
                )

        class Service:
            def inventory(self, inventory_id):
                return type(
                    "InventoryView",
                    (),
                    {"items": (("iron_sword", 1), ("bread_item", 2)), "stocks": ()},
                )()
            def item(self, item_id):
                return None

        RectType = Rect
        class Backend:
            Rect = RectType

        screen = InventoryScreen(Service())
        manager = WindowManager(Backend(), 960, 640)
        manager.register("inventory", screen, (100, 100, 912, 470))
        manager.open("inventory")
        screen._slot_entries()

        def window_point(slot_index):
            rect = screen._slot_rects()[slot_index]
            local_x = rect[0] + rect[2] // 2
            local_y = rect[1] + rect[3] // 2
            return (
                100 + local_x - 24,
                100 + manager.TITLE_HEIGHT + local_y - 126,
            )

        source = window_point(0)
        target = window_point(1)

        manager.handle_input(InputState(
            mouse_pos=source, mouse_clicked=True, mouse_button_down=True,
        ))
        manager.handle_input(InputState(
            mouse_pos=target, mouse_motion=True,
        ))
        manager.handle_input(InputState(
            mouse_pos=target, mouse_button_up=True,
        ))
        self.assertEqual(screen.slot_order[:2], [
            ("item", "bread_item"), ("item", "iron_sword"),
        ])

        empty_target = window_point(4)
        manager.handle_input(InputState(
            mouse_pos=(target[0], target[1]), mouse_clicked=True,
            mouse_button_down=True,
        ))
        manager.handle_input(InputState(
            mouse_pos=empty_target, mouse_motion=True,
        ))
        manager.handle_input(InputState(
            mouse_pos=empty_target, mouse_button_up=True,
        ))
        self.assertEqual(screen.slot_order[1], None)
        self.assertEqual(screen.slot_order[4], ("item", "iron_sword"))

        before = list(screen.slot_order)
        manager.handle_input(InputState(
            mouse_pos=empty_target, mouse_clicked=True, mouse_button_down=True,
        ))
        manager.handle_input(InputState(
            mouse_pos=(900, 600), mouse_motion=True,
        ))
        manager.handle_input(InputState(
            mouse_pos=(900, 600), mouse_button_up=True,
        ))
        self.assertEqual(screen.slot_order, before)


    def _character_screen_fixture(self, skill_count=3):
        skills = {f"skill_{index}": index for index in range(skill_count)}
        character = SimpleNamespace(
            skills=SimpleNamespace(to_dict=lambda: dict(skills)),
            progression=SimpleNamespace(unspent_points=2),
            equipment=SimpleNamespace(snapshot=lambda: {"main_hand": "iron_sword"}),
            race=SimpleNamespace(name="İnsan"),
            character_class=SimpleNamespace(name="Savaşçı"),
            name="Arin",
            age=24,
        )
        calls = []
        service = SimpleNamespace(
            actor_character=lambda _actor_id: character,
            improve_skill=lambda actor_id, skill: calls.append((actor_id, skill)) or 4,
            item=lambda item_id: SimpleNamespace(name="Demir Kılıç"),
        )
        return CharacterScreen(service), calls

    def test_character_screen_skill_mouse_selection_and_improvement(self):
        screen, calls = self._character_screen_fixture()
        row_rect, visible_count = screen._skill_geometry()
        self.assertGreaterEqual(visible_count, 1)
        # Use the live responsive row geometry and scroll to the second skill.
        screen.skill_scroll = 1
        x, y, width, height = row_rect
        screen.handle(InputState(
            mouse_pos=(x + width // 2, y + height // 2),
            mouse_clicked=True,
        ))
        self.assertEqual(screen.selected_skill, 1)
        screen.handle(InputState(actions={"confirm"}))
        self.assertEqual(calls, [("hero", "skill_1")])
        self.assertIn("skill_1", screen.message)

    def test_character_screen_skill_navigation_keeps_selection_visible(self):
        screen, _calls = self._character_screen_fixture(skill_count=9)
        _row_rect, visible_count = screen._skill_geometry()
        for _ in range(7):
            screen.handle(InputState(actions={"down"}))
        self.assertEqual(screen.selected_skill, 7)
        # The selected skill must remain inside the responsive visible range.
        self.assertLessEqual(screen.skill_scroll, screen.selected_skill)
        self.assertLess(screen.selected_skill, screen.skill_scroll + visible_count)
        self.assertEqual(
            screen.skill_scroll,
            max(0, screen.selected_skill - visible_count + 1),
        )

    def test_character_screen_keeps_equipment_out_of_character_sheet(self):
        screen, _calls = self._character_screen_fixture()
        self.assertFalse(hasattr(screen, "_equipment_rows"))
        self.assertEqual(
            tuple(slot for slot, _label in InventoryScreen.SLOTS),
            (
                "head", "chest", "hands", "legs", "feet",
                "main_hand", "off_hand", "accessory",
            ),
        )

    def test_character_screen_handles_missing_character_without_crashing(self):
        screen = CharacterScreen(SimpleNamespace(actor_character=lambda _actor_id: None))
        screen.handle(InputState(actions={"down", "confirm"}))
        self.assertEqual(screen.selected_skill, 0)



if __name__ == "__main__":
    unittest.main()
