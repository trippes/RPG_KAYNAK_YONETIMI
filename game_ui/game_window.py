"""Pygame application shell for the playable vertical slice."""

import json
from pathlib import Path
from time import perf_counter_ns

from game_ui.click_move_diagnostics import record_click_move_event

from .input import InputMapper
from .movement_input import PygameMovementInput
from .renderer import GOLD, NAV_ALIASES, Renderer
from .screens.character_screen import CharacterScreen
from .screens.inventory_screen import InventoryScreen
from .screens.main_menu import MainMenu
from .screens.main_screen import MainScreen
from .screens.market_screen import MarketScreen
from .screens.trade_screen import TradeScreen
from .screens.currency_exchange_screen import CurrencyExchangeScreen
from .screens.dialogue_screen import DialogueScreen
from .screens.combat_screen import CombatScreen
from .screens.character_creation import CharacterCreationScreen
from .screens.production_screen import ProductionScreen
from .screens.opening_screen import OpeningScreen
from .screens.save_slots_screen import SaveSlotsScreen
from .screens.quest_log_screen import QuestLogScreen
from .screens.container_screen import ContainerScreen
from .window_manager import WindowManager
from application.save_storage import SaveStorage, SaveStorageError
from application.gameplay_step_clock import FixedStepAccumulator
from application.continuous_player_movement import ContinuousPlayerMovementController
from application.performance_monitor import PerformanceMonitor
from core.domain.movement import MovementIntent

# Screens that show the navigation tab bar / resource bar.
NAV_SCREENS = frozenset()
# Gameplay tools are windows owned by the persistent MainScreen surface.
GAMEPLAY_WINDOW_IDS = frozenset({
    "character", "inventory", "quest_log", "production", "market", "trade", "container", "currency_exchange",
})
NOTICE_FRAMES = 240  # ~4 seconds at 60 fps
PAUSE_MENU_OPTIONS = (
    ("resume", "Oyuna Dön"),
    ("save", "Kaydet"),
    ("main_menu", "Ana Menü"),
    ("quit", "Oyundan Çık"),
)


class GameWindow:
    """Own the frame loop and route input between screens.

    ``backend`` is injected so tests can use a fake pygame-compatible module.
    """

    def __init__(
        self,
        service,
        backend,
        *,
        width=960,
        height=640,
        title="Eldoria",
        save_path=None,
        save_storage=None,
        fullscreen=True,
    ):
        self.service = service
        self.content_package_path = getattr(service, "_content_package_path", None)
        self.pg = backend
        self.performance_monitor = PerformanceMonitor()
        self._frame_phase_times = {}
        self.width, self.height = width, height

        # The adapter is intentionally import-safe, so initialize pygame only
        # when an actual window is created.
        if hasattr(backend, "init"):
            backend.init()
        if hasattr(backend, "font") and hasattr(backend.font, "init"):
            backend.font.init()

        self.fullscreen = bool(fullscreen)
        self.screen = self._create_display(width, height, self.fullscreen)
        actual_size = getattr(self.screen, "get_size", lambda: (width, height))()
        self.width, self.height = actual_size
        backend.display.set_caption(title)
        self.renderer = Renderer(backend, self.screen, self.width, self.height)
        self.input = InputMapper(backend)
        key_module = getattr(backend, "key", None)
        self.movement_input = (
            PygameMovementInput(backend)
            if callable(getattr(key_module, "get_pressed", None))
            else None
        )
        self._movement_clock = FixedStepAccumulator()
        self._player_movement_controller = None
        self._player_movement_controller_key = None
        # NPC simulation advances independently from player input. Opening an
        # overlay or standing still must not freeze patrols and companions.
        self._npc_simulation_clock = FixedStepAccumulator()
        self._movement_configs = {}
        self.save_storage = save_storage
        migration_report = None
        self._save_storage_failure = None
        if self.save_storage is None and save_path is None:
            self.save_storage = SaveStorage()
        if self.save_storage is not None:
            try:
                migration_report = self.save_storage.prepare()
            except SaveStorageError as error:
                self._save_storage_failure = error
        self.save_path = (
            Path(save_path)
            if save_path is not None
            else (
                self.save_storage.slot_path(0)
                if self._save_storage_failure is None
                else None
            )
        )

        self.screens = {
            "menu": MainMenu(width=self.width, height=self.height),
            "opening": OpeningScreen(),
            "main": MainScreen(service),
            "inventory": InventoryScreen(service),
            "production": ProductionScreen(service),
            "character": CharacterScreen(service),
            "quest_log": QuestLogScreen(service),
            "market": MarketScreen(service),
            "currency_exchange": CurrencyExchangeScreen(service),
            "trade": TradeScreen(service),            "dialogue": DialogueScreen(service),
            "combat": CombatScreen(service),
            "character_creation": CharacterCreationScreen(service),
            "container": ContainerScreen(service),
        }
        self.save_dir = self.save_path.parent if self.save_path is not None else None
        self.selected_slot = None
        self.screens["save_slots"] = SaveSlotsScreen(
            self.save_dir,
            self._select_save_slot,
            save_available=self._save_storage_failure is None,
            unavailable_message=(
                str(self._save_storage_failure)
                if self._save_storage_failure is not None
                else ""
            ),
        )
        self.window_manager = WindowManager(
            backend,
            self.width,
            self.height,
            on_result=self._handle_window_result,
        )
        self.window_manager.register(
            "inventory",
            self.screens["inventory"],
            (24, 110, min(self.width - 48, 912), min(self.height - 110, 470)),
            content_origin=(24, 126),
            title="Envanter",
        )
        self.window_manager.register(
            "character",
            self.screens["character"],
            (80, 90, min(self.width - 80, 760), min(self.height - 90, 520)),
            content_origin=(24, 126),
            title="Karakter",
        )
        self.window_manager.register(
            "quest_log",
            self.screens["quest_log"],
            (
                max(24, (self.width - min(self.width - 80, 944)) // 2),
                88,
                min(self.width - 80, 944),
                min(self.height - 160, 502),
            ),
            content_origin=(24, 126),
            title="Görev Günlüğü",
        )
        self.window_manager.register(
            "production",
            self.screens["production"],
            (24, 110, min(self.width - 48, 912), min(self.height - 110, 470)),
            content_origin=(24, 126),
            title="Üretim",
        )
        self.window_manager.register(
            "market",
            self.screens["market"],
            (24, 110, min(self.width - 48, 912), min(self.height - 110, 470)),
            content_origin=(24, 126),
            title="Pazar",
        )
        exchange_width = min(self.width - 48, int((self.height - 96) * 1.5))
        exchange_height = int(exchange_width / 1.5)
        exchange_x = (self.width - exchange_width) // 2
        exchange_y = (self.height - exchange_height) // 2
        self.window_manager.register(
            "currency_exchange",
            self.screens["currency_exchange"],
            (exchange_x, exchange_y, exchange_width, exchange_height),
            content_origin=(0, 0),
            title="",
            frame=False,
            close_offset=(686, 68),
        )
        self.window_manager.register(
            "trade",
            self.screens["trade"],
            (40, 100, min(self.width - 80, 880), min(self.height - 100, 470)),
            content_origin=(24, 126),
            title="Ticaret",
        )
        self.window_manager.register(
            "container",
            self.screens["container"],
            (40, 70, min(self.width - 80, 920), min(self.height - 80, 560)),
            content_origin=(24, 126),
            title="Konteyner",
            frame=False,
            close_offset=(808, 25),
        )

        self.current = "menu"
        self.gameplay_active = False
        self.gameplay_screen = "main"
        self.pause_menu_open = False
        self.pause_menu_selected = 0
        self.running = False
        # Canonical simulation time runs at 60 ticks per real second while a timed activity is active.
        self._auto_time_fraction = 0.0
        self._simulation_ticks_per_second = 60
        self.notice = ""
        self.notice_level = "info"
        self._notice_frames = 0
        if migration_report and (migration_report.conflicts or migration_report.invalid_sources):
            self.notice = "Eski kayıtlarla ilgili geçiş uyarısı var; kayıt ekranını kontrol edin."
            self.notice_level = "error"
            self._notice_frames = NOTICE_FRAMES
        if self._save_storage_failure is not None:
            self.notice = f"Kayıt sistemi kullanılamıyor: {self._save_storage_failure}"
            self.notice_level = "error"
            self._notice_frames = NOTICE_FRAMES
        self._load_movement_profiles()

    def _ensure_movement_runtime(self):
        """Provide inert defaults for lightweight/headless GameWindow test doubles."""
        if not hasattr(self, "movement_input"):
            self.movement_input = None
        if not hasattr(self, "_movement_clock"):
            self._movement_clock = FixedStepAccumulator()
        if not hasattr(self, "_movement_configs"):
            self._movement_configs = {}
        if not hasattr(self, "_player_movement_controller"):
            self._player_movement_controller = None
        if not hasattr(self, "_player_movement_controller_key"):
            self._player_movement_controller_key = None

    def _load_movement_profiles(self):
        """Load explicit actor movement tuning from the selected content package."""
        from application.content_pack import load_movement_configs

        try:
            self._movement_configs = dict(
                load_movement_configs(package_path=getattr(self, "content_package_path", None))
            )
        except (OSError, ValueError, TypeError) as error:
            self._movement_configs = {}
            self._set_notice(
                f"Hareket yapılandırması yüklenemedi: {error}",
                "error",
            )

    def _advance_continuous_player_movement(
        self,
        elapsed_seconds,
        intent,
        *,
        active,
        click_to_move=False,
    ):
        """Consume fixed movement steps without advancing canonical world time."""
        service = getattr(self, "service", None)
        if service is None:
            self._movement_clock.advance(elapsed_seconds, active=False)
            self._player_movement_controller = None
            self._player_movement_controller_key = None
            return
        actor_id = service.player_actor_id
        config = self._movement_configs.get(actor_id)
        input_focused = (
            self.movement_input is not None and self.movement_input.focused
        )
        active = active and config is not None and (input_focused or click_to_move)
        step_count = self._movement_clock.advance(
            elapsed_seconds,
            active=active,
        )
        if not active:
            self._player_movement_controller = None
            self._player_movement_controller_key = None
            return
        if step_count <= 0:
            return

        binding = self.service.hex_actor_binding
        snapshot = binding.physics_snapshot
        body = binding.player_body
        if snapshot is None or body is None:
            self._movement_clock.reset()
            self._player_movement_controller = None
            self._player_movement_controller_key = None
            return
        controller_key = (
            id(binding), id(snapshot), id(body), actor_id, id(config),
        )
        if (
            getattr(self, "_player_movement_controller", None) is None
            or getattr(self, "_player_movement_controller_key", None) != controller_key
        ):
            self._player_movement_controller = ContinuousPlayerMovementController(
                binding,
                snapshot,
                body,
                config,
                npc_bodies=getattr(self.service, "npc_physics_bodies", {}),
            )
            self._player_movement_controller_key = controller_key
        controller = self._player_movement_controller
        for _ in range(step_count):
            step_intent = intent
            step_target = None
            if click_to_move:
                route_screen = self.screens[self.gameplay_screen]
                click_intent = route_screen.click_move_intent()
                target_reader = getattr(route_screen, "click_move_target", None)
                if callable(target_reader):
                    step_target = target_reader()
                if click_intent.is_moving:
                    # Route direction is mouse-driven; movement mode remains
                    # owned by the live keyboard adapter for this fixed step.
                    step_intent = MovementIntent(click_intent.direction, intent.mode)
            step_kwargs = {"target": step_target} if step_target is not None else {}
            movement_step = controller.step(
                actor_id,
                step_intent,
                self._movement_clock.step_seconds,
                **step_kwargs,
            )
            if click_to_move:
                try:
                    committed_position = self.service.hex_world_runtime.continuous_position(actor_id).point
                except (AttributeError, KeyError, RuntimeError, ValueError):
                    committed_position = None
                record_click_move_event(
                    "game_window.physics_step",
                    target=step_target,
                    intent=step_intent,
                    movement_result=getattr(movement_step, "movement", None),
                    controller_position=getattr(
                        getattr(movement_step, "state", None),
                        "position",
                        None,
                    ),
                    committed_position=committed_position,
                )
            self.service._player_movement_mode = step_intent.mode

    def _advance_npc_simulation(self, elapsed_seconds, *, active):
        """Advance NPC behaviors on their own fixed clock, even while the player is idle.

        Overlay windows do not pause the world. The pause menu and active dialogue
        do, matching the gameplay input/simulation pause policy.
        """
        service = getattr(self, "service", None)
        clock = getattr(self, "_npc_simulation_clock", None)
        if service is None or clock is None:
            return
        step_count = clock.advance(elapsed_seconds, active=active)
        if not active or step_count <= 0:
            return

        advance_simulation = getattr(service, "advance_npc_simulation", None)
        if not callable(advance_simulation):
            # Keep lightweight legacy test doubles and adapters compatible.
            behavior_steps = (
                "advance_npc_patrols",
                "advance_npc_avoidance",
                "advance_companions",
            )
        else:
            behavior_steps = ()

        for _ in range(step_count):
            try:
                if callable(advance_simulation):
                    advance_simulation(clock.step_seconds)
                else:
                    for method_name in behavior_steps:
                        advance = getattr(service, method_name, None)
                        if callable(advance):
                            advance(clock.step_seconds)
            except (KeyError, RuntimeError, ValueError) as error:
                clock.reset()
                self._set_notice(f"NPC simülasyonu durduruldu: {error}", "error")
                break

    def _ensure_save_storage(self):
        failure = getattr(self, "_save_storage_failure", None)
        if failure is not None:
            raise SaveStorageError(str(failure))

    def _create_display(self, width, height, fullscreen):
        flags = 0
        if fullscreen:
            flags |= getattr(self.pg, "FULLSCREEN", 0)
        try:
            return self.pg.display.set_mode((0, 0) if fullscreen else (width, height), flags)
        except TypeError:
            return self.pg.display.set_mode((width, height))

    def _toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self.screen = self._create_display(self.width, self.height, self.fullscreen)
        self.width, self.height = getattr(
            self.screen, "get_size", lambda: (self.width, self.height)
        )()
        self.renderer.surface = self.screen
        self.renderer.width = self.width
        self.renderer.height = self.height
        self.window_manager.set_viewport(self.width, self.height)

    def _select_save_slot(self, index, path, exists):
        self.selected_slot = index
        self.save_path = path
        if self.screens["save_slots"].mode == "save":
            try:
                self._ensure_save_storage()
                self.service.save(path)
            except (OSError, KeyError, ValueError, RuntimeError) as error:
                self._set_notice(f"Kayıt başarısız: {error}", "error")
                return "save_slots"
            self._set_notice(f"Slot {index + 1} kaydedildi.", "ok")
            return "main"
        if exists:
            try:
                self._ensure_save_storage()
                self.service.load(path)
            except (OSError, KeyError, ValueError, RuntimeError) as error:
                self._set_notice(f"Kayıt yüklenemedi: {error}", "error")
                return "save_slots"
            self._recreate_gameplay_screens()
            return "main"
        return "opening"

    def _open_save_slots(self, mode, return_target="menu"):
        screen = self.screens["save_slots"]
        screen.mode = mode
        screen.return_target = return_target
        screen.selected = 0
        screen.message = ""
        screen.pending_overwrite = False
        screen.pending_overwrite_signature = None
        screen.pending_delete = False
        return "save_slots"

    def _latest_save_path(self):
        if self.save_path is None or self.save_dir is None:
            return None
        candidates = {}
        if self.save_path.is_file():
            candidates[self.save_path] = self.save_path.stat().st_mtime_ns
        if self.save_dir.is_dir():
            for path in self.save_dir.glob("slot_*.json"):
                if path.is_file():
                    candidates[path] = path.stat().st_mtime_ns
            # A missing primary can still be recovered by the adapter from
            # its validated .bak file. Keep the primary path as the load target.
            for backup in self.save_dir.glob("slot_*.json.bak"):
                if backup.is_file():
                    primary = backup.with_suffix("")
                    candidates[primary] = max(
                        candidates.get(primary, 0),
                        backup.stat().st_mtime_ns,
                    )
        if not candidates:
            return None
        return max(candidates, key=candidates.get)

    def _continue_latest_save(self):
        try:
            self._ensure_save_storage()
        except SaveStorageError as error:
            self._set_notice(f"Kayıt yüklenemedi: {error}", "error")
            return None
        try:
            path = self._latest_save_path()
        except OSError as error:
            self._set_notice(f"Kayıt yüklenemedi: kayıt dosyaları taranamadı ({error})", "error")
            return None
        if path is None:
            self._set_notice("Açılacak kayıt bulunamadı.", "error")
            return None
        try:
            self._ensure_save_storage()
            self.service.load(path)
        except (OSError, KeyError, ValueError, RuntimeError) as error:
            self._set_notice(f"Kayıt yüklenemedi: {error}", "error")
            return None
        self._recreate_gameplay_screens()
        self.save_path = path
        self.selected_slot = (
            int(path.stem.removeprefix("slot_")) - 1
            if path.stem.startswith("slot_") and path.stem.removeprefix("slot_").isdigit()
            else None
        )
        return "main"

    def _set_notice(self, message, level="info"):
        self.notice = message
        self.notice_level = level
        self._notice_frames = NOTICE_FRAMES

    def _recreate_gameplay_screens(self):
        """Rebind every gameplay panel to the current session after a load/reset."""
        self._ensure_movement_runtime()
        for window_id in tuple(self.window_manager.open_ids):
            self.window_manager.close(window_id)

        self.screens.update({
            "opening": OpeningScreen(),
            "main": MainScreen(self.service),
            "inventory": InventoryScreen(self.service),
            "production": ProductionScreen(self.service),
            "character": CharacterScreen(self.service),
            "quest_log": QuestLogScreen(self.service),
            "market": MarketScreen(self.service),
            "currency_exchange": CurrencyExchangeScreen(self.service),
            "trade": TradeScreen(self.service),
            "dialogue": DialogueScreen(self.service),
            "combat": CombatScreen(self.service),
            "character_creation": CharacterCreationScreen(self.service),
            "container": ContainerScreen(self.service),
        })
        for window_id in GAMEPLAY_WINDOW_IDS:
            managed = self.window_manager.windows.get(window_id)
            if managed is not None:
                managed.screen = self.screens[window_id]

        self._movement_clock.reset()
        npc_clock = getattr(self, "_npc_simulation_clock", None)
        if npc_clock is not None:
            npc_clock.reset()
        self._player_movement_controller = None
        self._player_movement_controller_key = None
        self.pause_menu_open = False
        self.current = getattr(self, "gameplay_screen", "main")
        self.gameplay_active = True

    def _start_new_game(self):
        self._ensure_movement_runtime()
        from application.content_pack import populate_opening_content
        from application.game_application import GameApplication

        service, _ = populate_opening_content(
            GameApplication.create_default(),
            content_package_path=getattr(self, "content_package_path", None),
        )
        self.service = service
        self._movement_clock.reset()
        self._load_movement_profiles()
        self._recreate_gameplay_screens()
        self.current = "opening"
        self.gameplay_active = False
        self.selected_slot = None

    def _set_current(self, target):
        """Change application state without allowing gameplay to close."""
        if target == "world":
            target = self.gameplay_screen

        if target in GAMEPLAY_WINDOW_IDS:
            if not self.gameplay_active or target not in self.window_manager.windows:
                return False
            self.window_manager.open(target)
            return True

        if target == "menu" and self.gameplay_active:
            self._set_notice("Oyun ekranı açık kalmalıdır.", "info")
            return False

        if target not in self.screens:
            return False

        if target == self.gameplay_screen:
            self.gameplay_active = True
        elif target == "menu":
            self.gameplay_active = False

        self.current = target
        return True

    def _handle_window_result(self, result, window_id):
        if result in self.window_manager.windows:
            self.window_manager.open(result)
        elif result in {"main", "world"}:
            self.window_manager.close(window_id)

    def _pause_menu_rects(self):
        width, height = 360, 48
        left = (self.width - width) // 2
        top = max(120, (self.height - (len(PAUSE_MENU_OPTIONS) * 58 + 76)) // 2 + 54)
        return tuple(
            self.pg.Rect(left, top + index * 58, width, height)
            for index in range(len(PAUSE_MENU_OPTIONS))
        )

    def _open_pause_menu(self):
        if not self.pause_menu_open:
            self.pause_menu_selected = 0
        self.pause_menu_open = True

    def _close_pause_menu(self):
        self.pause_menu_open = False

    def _handle_pause_menu(self, state):
        if state.pressed("back"):
            return
        if state.pressed("up"):
            self.pause_menu_selected = (self.pause_menu_selected - 1) % len(PAUSE_MENU_OPTIONS)
        if state.pressed("down"):
            self.pause_menu_selected = (self.pause_menu_selected + 1) % len(PAUSE_MENU_OPTIONS)
        selected = None
        if state.mouse_pos is not None:
            for index, rect in enumerate(self._pause_menu_rects()):
                if rect.collidepoint(state.mouse_pos):
                    self.pause_menu_selected = index
                    if state.mouse_clicked:
                        selected = PAUSE_MENU_OPTIONS[index][0]
                    break
        if state.pressed("confirm"):
            selected = PAUSE_MENU_OPTIONS[self.pause_menu_selected][0]

        if selected == "resume":
            self._close_pause_menu()
        elif selected == "save":
            self._close_pause_menu()
            self.gameplay_active = False
            self.current = self._open_save_slots("save", "main")
        elif selected == "main_menu":
            self._close_pause_menu()
            self.gameplay_active = False
            self.current = "menu"
        elif selected == "quit":
            self.running = False

    def _save_game(self):
        try:
            self._ensure_save_storage()
        except SaveStorageError as error:
            self._set_notice(f"Kaydetme başarısız: {error}", "error")
            return
        # Never write directly to the last-used slot from a shortcut/helper.
        # All writes must pass through the slot picker and its overwrite prompt.
        self.gameplay_active = False
        self.current = self._open_save_slots("save", "main")

    def _render_pause_menu(self):
        panel_width = 420
        panel_height = len(PAUSE_MENU_OPTIONS) * 58 + 110
        panel = self.pg.Rect(
            (self.width - panel_width) // 2,
            (self.height - panel_height) // 2,
            panel_width,
            panel_height,
        )

        # Keep the world and gameplay windows visible beneath the pause menu.
        # Only the menu panel itself is composited with partial transparency.
        panel_surface = self.pg.Surface(
            (panel.width, panel.height),
            self.pg.SRCALPHA,
        )
        panel_surface.fill((23, 29, 43, 176))
        self.pg.draw.rect(
            panel_surface,
            (145, 118, 70, 230),
            panel_surface.get_rect(),
            2,
            border_radius=8,
        )
        self.screen.blit(panel_surface, panel.topleft)
        self.renderer.text(
            "Oyun Menüsü",
            panel.centerx - self.renderer.text_width("Oyun Menüsü", title=True) // 2,
            panel.y + 22,
            GOLD,
            title=True,
        )
        for index, (_action, label) in enumerate(PAUSE_MENU_OPTIONS):
            rect = self._pause_menu_rects()[index]
            self.renderer.button(rect, label, selected=index == self.pause_menu_selected)

    def _nav_enabled(self):
        """No legacy map-dependent navigation tabs are active during migration."""
        return {}

    def _handle_nav_click(self, _state):
        return None

    def _render_current(self):
        """Clear the previous frame, then render the active screen and overlays."""
        self.renderer.clear()

        if self.gameplay_active:
            world = self.screens[self.gameplay_screen]
            world.render(self.renderer)
            self.window_manager.render(self.renderer)
            dialogue = self.screens.get("dialogue")
            if dialogue is not None and getattr(dialogue, "is_active", lambda: False)():
                dialogue.render(self.renderer)
            return

        self.screens[self.current].render(self.renderer)

    def _has_running_timed_activity(self):
        """Return whether any actor activity still requires simulation time."""
        try:
            return any(
                activity.state == "running"
                for activity in self.service.activities_state()
            )
        except (AttributeError, KeyError, RuntimeError, ValueError):
            return False

    def _advance_active_time(self, elapsed_seconds):
        """Advance canonical time only while a duration-based activity is running."""
        if (
            not self.gameplay_active
            or self.pause_menu_open
            or elapsed_seconds <= 0
            or not self._has_running_timed_activity()
        ):
            self._auto_time_fraction = 0.0
            return

        self._auto_time_fraction += elapsed_seconds * self._simulation_ticks_per_second
        ticks_to_advance = int(self._auto_time_fraction)
        if ticks_to_advance <= 0:
            return

        self._auto_time_fraction -= ticks_to_advance
        for _ in range(ticks_to_advance):
            if not self._has_running_timed_activity():
                self._auto_time_fraction = 0.0
                break
            try:
                self.service.advance_by(1)
            except (KeyError, RuntimeError, ValueError) as error:
                self._auto_time_fraction = 0.0
                self._set_notice(f"Süreli eylem durduruldu: {error}", "error")
                break

    def step(self, events=(), *, elapsed_seconds=0.0):
        # Some focused tests construct GameWindow without running __init__.
        # Keep optional telemetry safe for those lightweight test instances.
        if not hasattr(self, "_frame_phase_times"):
            self._frame_phase_times = {}
        self._ensure_movement_runtime()
        events = tuple(events)
        state = self.input.collect(events)
        if self.movement_input is not None:
            self.movement_input.handle_events(events)

        if state.mouse_pos is not None:
            self.renderer.mouse_pos = state.mouse_pos

        if state.quit_requested:
            self.running = False
            return

        if state.pressed("fullscreen"):
            self._toggle_fullscreen()

        # While a screen collects typed text (e.g. the name prompt), letters such
        # as "q" belong to the text, not to the global shortcuts.
        capturing_text = getattr(self.screens[self.current], "name_entry_active", False)

        if state.pressed("quit") and not capturing_text:
            self.running = False
            return

        if self.gameplay_active and state.pressed("back"):
            if self.pause_menu_open:
                self._close_pause_menu()
            else:
                self._open_pause_menu()
            self._render_current()
            if self.pause_menu_open:
                self._render_pause_menu()
            return

        if state.pressed("save"):
            try:
                self._ensure_save_storage()
                # Route the shortcut through the slot screen so occupied slots
                # always require an explicit overwrite confirmation.
                self.gameplay_active = False
                self.current = self._open_save_slots("save", "main")
            except SaveStorageError as error:
                self._set_notice(f"Kaydetme başarısız: {error}", "error")

        if state.pressed("load"):
            try:
                self._ensure_save_storage()
                self.service.load(self.save_path)
                self._recreate_gameplay_screens()
                self._set_notice(f"Oyun yüklendi: {self.save_path}", "ok")
            except (OSError, KeyError, ValueError, RuntimeError) as error:
                self._set_notice(f"Oyun yüklenemedi: {error}", "error")

        if self.pause_menu_open:
            self._handle_pause_menu(state)
            self._render_current()
            if self.pause_menu_open:
                self._render_pause_menu()
            return

        self._handle_nav_click(state)
        current_screen = self.screens[self.current]
        dialogue_screen = self.screens.get("dialogue")
        dialogue_active = (
            dialogue_screen is not None
            and dialogue_screen.is_active()
        )
        if dialogue_active and state.pressed("dialogue_history"):
            dialogue_screen.handle(state)
            next_screen = None
            window_consumed = True
            dialogue_input = True
        elif dialogue_active and (
            state.pressed("confirm")
            or state.pressed("up")
            or state.pressed("down")
            or state.mouse_clicked
            or state.mouse_wheel
        ):
            next_screen = dialogue_screen.handle(state)
            window_consumed = True
            dialogue_input = True
        else:
            window_consumed = self.gameplay_active and self.window_manager.handle_input(state)
            dialogue_input = False

        movement_intent = None
        service = getattr(self, "service", None)
        movement_configured = (
            service is not None
            and service.player_actor_id in self._movement_configs
            and self.movement_input is not None
        )
        movement_input_active = (
            self.gameplay_active
            and not self.pause_menu_open
            and not dialogue_active
            and not window_consumed
            and not self.window_manager.open_ids
            and self.current == self.gameplay_screen
            and movement_configured
        )
        if movement_input_active:
            movement_intent = self.movement_input.read_intent()
            to_world = getattr(current_screen, "movement_intent_to_world", None)
            if callable(to_world):
                movement_intent = to_world(movement_intent)
            if movement_intent.is_moving:
                # WASD owns gameplay movement. Its W/D letters must not also
                # trigger the legacy world/dialogue-history shortcuts.
                state.actions.difference_update({
                    "world", "dialogue_history",
                    "left", "right", "up", "down",
                    "hex_north_west", "hex_south_west",
                })

        if self.current == "world" and not window_consumed:
            current_screen._inject_mouse_action(state, self.renderer)

        if self.current == "opening":
              current_screen.update()

        next_screen = next_screen if dialogue_input else (None if window_consumed else (
            current_screen.handle(state, self.renderer)
            if self.current == "menu"
            else current_screen.handle(state)
        ))

        if next_screen == "quit":
            self.running = False
            return
        if isinstance(next_screen, str) and next_screen.startswith("container:"):
            container_id = next_screen.split(":", 1)[1]
            try:
                self.screens["container"].set_container(container_id)
                self.window_manager.open("container")
                next_screen = None
            except (KeyError, RuntimeError, ValueError) as error:
                self._set_notice(f"Sandık açılamadı: {error}", "error")
                next_screen = self.gameplay_screen
        elif next_screen == "gather":
            main_screen = self.screens.get(self.gameplay_screen)
            node_id = getattr(main_screen, "selected_interaction_target_id", None)
            try:
                if not node_id:
                    raise ValueError("Önce bir kaynak düğümü seçilmelidir.")
                self.service.start_gathering_one(
                    self.service.player_actor_id, node_id, self.service.player_inventory_id,
                )
                self._set_notice("Kaynak toplama başladı.", "info")
            except (KeyError, RuntimeError, ValueError) as error:
                self._set_notice(f"Kaynak toplanamadı: {error}", "error")
            next_screen = self.gameplay_screen
        elif isinstance(next_screen, str) and next_screen.startswith("structure:"):
            facility_id = next_screen.split(":", 1)[1]
            self.screens["production"].set_facility(facility_id)
            self.window_manager.open("production")
            next_screen = self.gameplay_screen
        elif isinstance(next_screen, str) and next_screen.startswith("door:"):
            transition_id = next_screen.split(":", 1)[1]
            try:
                result = self.service.hex_actor_binding.transition(
                    self.service.player_actor_id, transition_id,
                )
                self._set_notice(
                    "Geçiş kullanıldı." if result.success else "Geçiş kullanılamadı.",
                    "info" if result.success else "error",
                )
            except (KeyError, RuntimeError, ValueError) as error:
                self._set_notice(f"Geçiş kullanılamadı: {error}", "error")
            next_screen = self.gameplay_screen
        if next_screen == "continue":
            next_screen = self._open_save_slots("load")
        elif next_screen == "new_game":
            self._start_new_game()
            next_screen = "opening"
        elif next_screen == "load_slots":
            next_screen = self._open_save_slots("load")

        if self.current == "menu" and next_screen in {"settings", "guide", "about"}:
            notices = {
                "settings": "Ayarlar ekranı arayüz geliştirmesinin sonraki adımında açılacak.",
                "guide": "Oyun rehberi arayüz geliştirmesinin sonraki adımında açılacak.",
                "about": "Eldoria: Kaynak Yönetimi — v1.0.0",
            }
            self._set_notice(notices[next_screen])
            next_screen = None

        if (
            current_screen is self.screens.get("character_creation")
            and next_screen in {"world", "dialogue"}
        ):
            from application.content_pack import populate_gameplay_resources
            from application.hex_world_initializer import (
                HexWorldInitializationError,
                initialize_hex_world,
            )
            populate_gameplay_resources(self.service)
            player_actor = self.service.actor(self.service.player_actor_id)
            if player_actor.inventory_id is None:
                self.service.bind_actor_inventory(
                    self.service.player_actor_id,
                    self.service.player_inventory_id,
                )
            try:
                initialize_hex_world(
                    self.service,
                    content_package_path=self.content_package_path,
                )
            except (HexWorldInitializationError, KeyError, ValueError, RuntimeError) as error:
                self._set_notice(
                    f"Altıgen dünya başlatılamadı: {error}",
                    "error",
                )

        if next_screen == "market":
            dialogue = self.screens["dialogue"]
            npc_id = dialogue.active_npc_id
            profile = (
                self.service.market_for_npc(npc_id)
                if npc_id is not None else None
            )
            if profile is None:
                self._set_notice("Bu NPC için tanımlı bir pazar bulunamadı.", "error")
            else:
                self.screens["market"].set_market(profile.market_id)
                self.window_manager.open("market")
                dialogue.complete_external_transition()
            next_screen = self.gameplay_screen

        if next_screen == "trade":
            dialogue = self.screens["dialogue"]
            npc_id = dialogue.active_npc_id
            partner = (
                self.service.trade_partner_for_npc(npc_id)
                if npc_id is not None else None
            )
            if partner is None:
                self._set_notice("Bu NPC ile ticaret yapılamıyor.", "error")
            else:
                self.screens["trade"].set_npc(npc_id)
                self.window_manager.open("trade")
                dialogue.complete_external_transition()
            next_screen = self.gameplay_screen

        if next_screen == "world":
            next_screen = self.gameplay_screen

        if next_screen in self.screens:
            if next_screen == "dialogue":
                if self.current == "character_creation":
                    self.screens["dialogue"].resume_after_creation()
                self.screens["dialogue"].set_target_npc(
                    getattr(current_screen, "selected_npc_id", None)
                )
            self._set_current(next_screen)

        dialogue_now_active = (
            self.screens.get("dialogue") is not None
            and self.screens["dialogue"].is_active()
        )
        movement_active = (
            movement_intent is not None
            and self.gameplay_active
            and not self.pause_menu_open
            and not dialogue_now_active
            and not self.window_manager.open_ids
            and self.current == self.gameplay_screen
        )
        manual_movement = movement_intent is not None and movement_intent.is_moving
        if manual_movement:
            self.screens[self.gameplay_screen].cancel_click_to_move()
        click_to_move = (
            movement_active
            and not manual_movement
            and bool(getattr(
                self.screens[self.gameplay_screen], "has_click_move_goal", False,
            ))
        )
        gameplay_view = self.screens.get(
            getattr(self, "gameplay_screen", "main")
        )
        has_click_move_goal = bool(
            getattr(gameplay_view, "has_click_move_goal", False)
        )
        if state.mouse_clicked or click_to_move or has_click_move_goal:
            record_click_move_event(
                "game_window.click_gate",
                mouse_pos=state.mouse_pos,
                movement_intent_present=movement_intent is not None,
                manual_movement=manual_movement,
                movement_active=movement_active,
                click_to_move=click_to_move,
                input_focused=(self.movement_input.focused if self.movement_input else None),
                movement_configured=movement_configured,
                window_consumed=window_consumed,
                open_windows=tuple(self.window_manager.open_ids),
                current_screen=self.current,
                gameplay_screen=self.gameplay_screen,
            )
        phase_started = perf_counter_ns()
        self._advance_continuous_player_movement(
            elapsed_seconds,
            movement_intent,
            active=movement_active,
            click_to_move=click_to_move,
        )
        self._frame_phase_times["player_physics"] = (perf_counter_ns() - phase_started) / 1_000_000.0
        phase_started = perf_counter_ns()
        self._advance_npc_simulation(
            elapsed_seconds,
            active=(
                self.gameplay_active
                and not self.pause_menu_open
                and not dialogue_now_active
            ),
        )
        self._frame_phase_times["npc_simulation"] = (perf_counter_ns() - phase_started) / 1_000_000.0

        if self.gameplay_active:
            phase_started = perf_counter_ns()
            world_screen = self.screens.get(getattr(self, "gameplay_screen", "main"))
            update = getattr(world_screen, "update", None)
            if update is not None:
                update(elapsed_seconds)
            self._frame_phase_times["world_update"] = (perf_counter_ns() - phase_started) / 1_000_000.0

        self._advance_active_time(elapsed_seconds)

        # Tell the renderer which chrome to draw for the screen shown this frame.
        shown = self.current
        if shown in NAV_SCREENS:
            self.renderer.nav_current = NAV_ALIASES.get(shown, shown)
            self.renderer.nav_enabled = self._nav_enabled()
        else:
            self.renderer.nav_current = None
        phase_started = perf_counter_ns()
        self._render_current()
        self._frame_phase_times["render"] = (perf_counter_ns() - phase_started) / 1_000_000.0
        if self.pause_menu_open:
            self._render_pause_menu()

        if self.notice:
            self.renderer.toast(self.notice, self.notice_level)
            self._notice_frames -= 1
            if self._notice_frames <= 0:
                self.notice = ""

    @property
    def performance_stats(self):
        """Return rolling telemetry; activate it with ELDORIA_PERF=1."""
        return self.performance_monitor.stats

    def _performance_counters(self):
        if (
            not self.gameplay_active
            or not getattr(self.performance_monitor, "enabled", False)
        ):
            return {}
        world = self.screens.get(self.gameplay_screen)
        counters = {}
        view = None
        for name in ("view", "gameplay_view", "_view", "_gameplay_view", "_hex_view"):
            candidate = getattr(world, name, None)
            if candidate is None:
                continue
            view = candidate
            stats = getattr(candidate, "render_stats", None)
            if isinstance(stats, dict):
                counters.update(stats)
                break
        if not counters:
            stats = getattr(world, "render_stats", None)
            if isinstance(stats, dict):
                counters.update(stats)
        clock = getattr(self, "_movement_clock", None)
        if clock is not None:
            counters.update({
                "movement_fixed_step_cap": clock.max_substeps,
                "movement_fixed_steps_last_frame": clock.last_substeps,
                "movement_fixed_step_dropped_seconds_total": (
                    clock.total_dropped_seconds
                ),
                "movement_fixed_step_dropped_seconds_last_frame": (
                    clock.last_dropped_seconds
                ),
            })
        route = getattr(view, "_click_move_route", None)
        metrics = getattr(route, "metrics_snapshot", None)
        if callable(metrics):
            counters.update(metrics())
        return counters

    def run(self, *, fps=60):
        self.running = True
        clock = self.pg.time.Clock()
        performance_frame_count = 0

        while self.running:
            self._frame_phase_times = {}
            elapsed_seconds = clock.tick(fps) / 1000.0
            step_started = perf_counter_ns()
            self.step(self.pg.event.get(), elapsed_seconds=elapsed_seconds)
            self._frame_phase_times["game_step"] = (
                perf_counter_ns() - step_started
            ) / 1_000_000.0
            flip_started = perf_counter_ns()
            self.pg.display.flip()
            self._frame_phase_times["display_flip"] = (
                perf_counter_ns() - flip_started
            ) / 1_000_000.0
            raw_frame_ms = (
                self._frame_phase_times["game_step"]
                + self._frame_phase_times["display_flip"]
            )
            self.performance_monitor.record_frame(
                raw_frame_ms,
                phases=self._frame_phase_times,
                counters=self._performance_counters(),
            )
            if self.performance_monitor.enabled:
                performance_frame_count += 1
                if performance_frame_count % 300 == 0:
                    print(
                        "ELDORIA_PERF " + json.dumps(
                            self.performance_stats, ensure_ascii=False,
                        ),
                        flush=True,
                    )

        self.pg.quit()


def launch(service, backend=None, **kwargs):
    """Create and run a window; importing this module remains headless-safe."""
    if backend is None:
        raise RuntimeError(
            "Pygame backend bulunamadı. `pip install pygame-ce` sonrası "
            "launch(service, backend=pygame) kullanın."
        )

    window = GameWindow(service, backend, **kwargs)
    window.run()
    return window