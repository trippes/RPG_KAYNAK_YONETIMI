"""Pygame application shell for the playable vertical slice."""

from pathlib import Path

from .input import InputMapper
from .renderer import GOLD, NAV_ALIASES, Renderer
from .screens.character_screen import CharacterScreen
from .screens.inventory_screen import InventoryScreen
from .screens.main_menu import MainMenu
from .screens.map_screen import MapScreen
from .screens.local_map_screen import LocalMapScreen
from .screens.world_screen import WorldScreen
from .screens.market_screen import MarketScreen
from .screens.dialogue_screen import DialogueScreen
from .screens.combat_screen import CombatScreen
from .screens.character_creation import CharacterCreationScreen
from .screens.production_screen import ProductionScreen
from .screens.opening_screen import OpeningScreen
from .screens.save_slots_screen import SaveSlotsScreen
from .screens.quest_log_screen import QuestLogScreen
from .window_manager import WindowManager
from application.save_storage import SaveStorage, SaveStorageError

# Screens that show the navigation tab bar / resource bar.
NAV_SCREENS = frozenset(
    {"world", "inventory", "production", "character", "market", "map", "local_map"}
)
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
            "world": WorldScreen(service),
            "map": MapScreen(service),
            "local_map": LocalMapScreen(service),
            "inventory": InventoryScreen(service),
            "production": ProductionScreen(service),
            "character": CharacterScreen(service),
            "quest_log": QuestLogScreen(service),
            "market": MarketScreen(service),
            "dialogue": DialogueScreen(service),
            "combat": CombatScreen(service),
            "character_creation": CharacterCreationScreen(service),
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
            (80, 90, min(self.width - 80, 760), min(self.height - 90, 470)),
            content_origin=(24, 126),
            title="Karakter",
        )
        self.window_manager.register(
            "quest_log",
            self.screens["quest_log"],
            (24, 110, min(self.width - 48, 912), min(self.height - 110, 470)),
            content_origin=(24, 126),
            title="Görev Günlüğü",
        )

        self.current = "menu"
        self.gameplay_active = False
        self.gameplay_screen = "local_map"
        self.pause_menu_open = False
        self.pause_menu_selected = 0
        self.running = False
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
            return "local_map"
        if exists:
            try:
                self._ensure_save_storage()
                self.service.load(path)
            except (OSError, KeyError, ValueError, RuntimeError) as error:
                self._set_notice(f"Kayıt yüklenemedi: {error}", "error")
                return "save_slots"
            return "local_map"
        return "opening"

    def _open_save_slots(self, mode, return_target="menu"):
        screen = self.screens["save_slots"]
        screen.mode = mode
        screen.return_target = return_target
        screen.selected = 0
        screen.message = ""
        screen.pending_overwrite = False
        return "save_slots"

    def _latest_save_path(self):
        if self.save_path is None or self.save_dir is None:
            return None
        candidates = []
        if self.save_path.is_file():
            candidates.append(self.save_path)
        if self.save_dir.is_dir():
            candidates.extend(
                path for path in self.save_dir.glob("slot_*.json")
                if path.is_file()
            )
        if not candidates:
            return None
        return max(candidates, key=lambda path: path.stat().st_mtime_ns)

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
        return "local_map"

    def _set_notice(self, message, level="info"):
        self.notice = message
        self.notice_level = level
        self._notice_frames = NOTICE_FRAMES

    def _start_new_game(self):
        from application.content_pack import populate_demo_content
        from application.game_application import GameApplication

        service, _ = populate_demo_content(GameApplication.create_default())
        self.service = service
        self.screens.update({
            "opening": OpeningScreen(),
            "world": WorldScreen(service),
            "map": MapScreen(service),
            "local_map": LocalMapScreen(service),
            "inventory": InventoryScreen(service),
            "production": ProductionScreen(service),
            "character": CharacterScreen(service),
            "quest_log": QuestLogScreen(service),
            "market": MarketScreen(service),
            "dialogue": DialogueScreen(service),
            "combat": CombatScreen(service),
            "character_creation": CharacterCreationScreen(service),
        })
        self.window_manager.windows["inventory"].screen = self.screens["inventory"]
        self.window_manager.windows["character"].screen = self.screens["character"]
        self.window_manager.windows["quest_log"].screen = self.screens["quest_log"]
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

        if target in self.window_manager.windows:
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
        elif result in {"local_map", "world"}:
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
            self.current = self._open_save_slots("save", "local_map")
        elif selected == "main_menu":
            self._close_pause_menu()
            self.gameplay_active = False
            self.current = "menu"
        elif selected == "quit":
            self.running = False

    def _save_game(self):
        try:
            self._ensure_save_storage()
            self.save_path.parent.mkdir(parents=True, exist_ok=True)
            self.service.save(self.save_path)
            self._set_notice(
                f"Slot {self.selected_slot + 1 if self.selected_slot is not None else '?'} kaydedildi.",
                "ok",
            )
        except (OSError, KeyError, ValueError, RuntimeError) as error:
            self._set_notice(f"Kaydetme başarısız: {error}", "error")

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

    def _nav_enabled(self):
        """Which navigation tabs may be used from the current location."""
        enabled = {}
        try:
            actors = self.service.state().actors
            _, location = self.screens["world"]._current_location(actors)
            enabled["market"] = location is not None and "market" in location.activities
        except (KeyError, ValueError, RuntimeError, AttributeError):
            enabled["market"] = True
        return enabled

    def _handle_nav_click(self, state):
        """Switch screens when a tab is clicked; the click is then consumed."""
        if not (state.mouse_clicked and state.mouse_pos is not None):
            return
        if self.current not in NAV_SCREENS:
            return
        if self.current == "local_map" and not self.screens["local_map"].menu_open:
            return
        target = self.renderer.nav_hit(state.mouse_pos)
        if target is None:
            return
        state.mouse_clicked = False
        if target == "quest_log":
            self.window_manager.toggle("quest_log")
            return
        if target == "world":
            target = "local_map"
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

    def step(self, events=()):
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
                self.save_path.parent.mkdir(parents=True, exist_ok=True)
                self.service.save(self.save_path)
                self._set_notice(f"Slot {self.selected_slot + 1 if self.selected_slot is not None else '?'} kaydedildi.", "ok")
            except (OSError, KeyError, ValueError, RuntimeError) as error:
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

        # Tell the renderer which chrome to draw for the screen shown this frame.
        shown = self.current
        if shown in NAV_SCREENS and (
            shown != "local_map" or self.screens["local_map"].menu_open
        ):
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
            self.step(self.pg.event.get())
            self.pg.display.flip()
            clock.tick(fps)

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