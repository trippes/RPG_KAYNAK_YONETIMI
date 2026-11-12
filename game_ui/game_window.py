"""Pygame application shell for the playable vertical slice."""

from pathlib import Path

from .input import InputMapper
from .renderer import GOLD, NAV_ALIASES, Renderer
from .screens.character_screen import CharacterScreen
from .screens.inventory_screen import InventoryScreen
from .screens.main_menu import MainMenu
from .screens.map_screen import MapScreen
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

# Screens that show the navigation tab bar / resource bar.
NAV_SCREENS = frozenset()
# Gameplay tools are windows owned by the persistent MainScreen surface.
GAMEPLAY_WINDOW_IDS = frozenset({
    "character", "inventory", "quest_log", "map", "production", "market", "trade", "container", "currency_exchange",
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
            "map": MapScreen(service),
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
            "map",
            self.screens["map"],
            (24, 110, min(self.width - 48, 912), min(self.height - 110, 470)),
            content_origin=(24, 126),
            title="Harita",
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

    def _start_new_game(self):
        from application.content_pack import populate_opening_content
        from application.game_application import GameApplication

        service, _ = populate_opening_content(
            GameApplication.create_default(),
            content_package_path=self.content_package_path,
        )
        self.service = service
        self.screens.update({
            "opening": OpeningScreen(),
            "map": MapScreen(service),
            "main": MainScreen(service),
            "inventory": InventoryScreen(service),
            "production": ProductionScreen(service),
            "character": CharacterScreen(service),
            "quest_log": QuestLogScreen(service),
            "market": MarketScreen(service),
            "currency_exchange": CurrencyExchangeScreen(service),
            "trade": TradeScreen(service),
            "dialogue": DialogueScreen(service),
            "combat": CombatScreen(service),
            "character_creation": CharacterCreationScreen(service),
            "container": ContainerScreen(service),
        })
        self.window_manager.windows["inventory"].screen = self.screens["inventory"]
        self.window_manager.windows["character"].screen = self.screens["character"]
        self.window_manager.windows["quest_log"].screen = self.screens["quest_log"]
        self.window_manager.windows["production"].screen = self.screens["production"]
        self.window_manager.windows["market"].screen = self.screens["market"]
        if "currency_exchange" in self.window_manager.windows:
            self.window_manager.windows["currency_exchange"].screen = self.screens["currency_exchange"]
        if "trade" in self.window_manager.windows:
            self.window_manager.windows["trade"].screen = self.screens["trade"]
        self.window_manager.windows["map"].screen = self.screens["map"]
        if "container" in self.window_manager.windows:
            self.window_manager.windows["container"].screen = self.screens["container"]
        for window_id in tuple(self.window_manager.open_ids):
            self.window_manager.close(window_id)
        self.pause_menu_open = False
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
        self.pause_menu_open = True
        self.pause_menu_selected = 0

    def _close_pause_menu(self):
        self.pause_menu_open = False

    def _handle_pause_menu(self, state):
        if state.pressed("back"):
            self._close_pause_menu()
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
        overlay = self.pg.Rect(0, 0, self.width, self.height)
        self.pg.draw.rect(self.screen, (5, 8, 14), overlay)
        panel_width = 420
        panel_height = len(PAUSE_MENU_OPTIONS) * 58 + 110
        panel = self.pg.Rect(
            (self.width - panel_width) // 2,
            (self.height - panel_height) // 2,
            panel_width,
            panel_height,
        )
        self.renderer.panel(panel, (23, 29, 43), (145, 118, 70))
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

    def _current_location(self):
        """Return the active actor's current location without a legacy world screen."""
        actors = self.service.state().actors
        if not actors:
            return None
        world_map = self.service.application.holder.current.movement.map_for(
            actors[0].world_id
        )
        return world_map.get(actors[0].location_id) if world_map is not None else None

    def _nav_enabled(self):
        """Which navigation tabs may be used from the current location."""
        try:
            location = self._current_location()
            return {}
        except (KeyError, ValueError, RuntimeError, AttributeError):
            return {}

    def _handle_nav_click(self, state):
        """Route gameplay navigation from the visible tabs and mapped shortcuts."""
        if self.current not in NAV_SCREENS:
            return

        target = None
        for action in ("map",):
            if action in state.actions:
                state.actions.discard(action)
                target = action
                break

        if target is None:
            if not (state.mouse_clicked and state.mouse_pos is not None):
                return
            target = self.renderer.nav_hit(state.mouse_pos)
            if target is None:
                return
            state.mouse_clicked = False

        if target == "quest_log":
            self.window_manager.toggle("quest_log")
            return
        if target == "world":
            target = "main"
        if not self._nav_enabled().get(target, True):
            self._set_notice("Pazar yalnızca yerleşim yerlerinde kullanılabilir.", "error")
            return
        if target in self.screens:
            self._set_current(target)

    def _render_current(self):
        """Render the persistent world before the current gameplay surface."""
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
        state = self.input.collect(events)

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
            self.screens["container"].set_container(container_id)
            self.window_manager.open("container")
            next_screen = None
        if next_screen == "continue":
            next_screen = self._open_save_slots("load")
        elif next_screen == "new_game":
            self._start_new_game()
            next_screen = "opening"
        elif next_screen == "test_world":
            self._start_test_world()
            next_screen = None
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
            populate_gameplay_resources(self.service)
            actors = self.service.state().actors
            if actors and actors[0].inventory_id is None:
                self.service.bind_actor_inventory(actors[0].actor_id, "player")

        if next_screen == "market":
            dialogue = self.screens["dialogue"]
            context = getattr(dialogue, "context", None)
            profile = (
                self.service.market_for_npc(context[1])
                if context is not None else None
            )
            if profile is None:
                self._set_notice("Bu NPC için tanımlı bir pazar bulunamadı.", "error")
            else:
                self.screens["market"].set_market(profile.market_id)
                self.window_manager.open("market")
                dialogue._reset_dialogue()
            next_screen = self.gameplay_screen

        if next_screen == "trade":
            dialogue = self.screens["dialogue"]
            context = getattr(dialogue, "context", None)
            npc_id = context[1] if context is not None else None
            partner = (
                self.service.trade_partner_for_npc(npc_id)
                if npc_id is not None else None
            )
            if partner is None:
                self._set_notice("Bu NPC ile ticaret yapılamıyor.", "error")
            else:
                self.screens["trade"].set_npc(npc_id)
                self.window_manager.open("trade")
                dialogue._reset_dialogue()
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

        self._advance_active_time(elapsed_seconds)

        # Tell the renderer which chrome to draw for the screen shown this frame.
        shown = self.current
        if shown in NAV_SCREENS:
            self.renderer.nav_current = NAV_ALIASES.get(shown, shown)
            self.renderer.nav_enabled = self._nav_enabled()
        else:
            self.renderer.nav_current = None
        self._render_current()
        if self.pause_menu_open:
            self._render_pause_menu()

        if self.notice:
            self.renderer.toast(self.notice, self.notice_level)
            self._notice_frames -= 1
            if self._notice_frames <= 0:
                self.notice = ""

    def run(self, *, fps=60):
        self.running = True
        clock = self.pg.time.Clock()

        while self.running:
            elapsed_seconds = clock.tick(fps) / 1000.0
            self.step(self.pg.event.get(), elapsed_seconds=elapsed_seconds)
            self.pg.display.flip()

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