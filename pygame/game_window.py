"""Pygame application shell for the playable vertical slice."""

from pathlib import Path

from .input import InputMapper
from .renderer import NAV_ALIASES, Renderer
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

# Screens that show the navigation tab bar / resource bar.
NAV_SCREENS = frozenset(
    {"world", "inventory", "production", "character", "quest_log", "market", "map", "local_map"}
)
NOTICE_FRAMES = 240  # ~4 seconds at 60 fps


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
        save_path="save/eldoria_save.json",
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
        self.save_path = Path(save_path)

        self.screens = {
            "menu": MainMenu(),
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
        self.save_dir = self.save_path.parent
        self.selected_slot = None
        self.screens["save_slots"] = SaveSlotsScreen(
            self.save_dir,
            self._select_save_slot,
        )

        self.current = "menu"
        self.running = False
        self.notice = ""
        self.notice_level = "info"
        self._notice_frames = 0

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
        if exists:
            try:
                self.service.load(path)
            except (OSError, KeyError, ValueError, RuntimeError) as error:
                self._set_notice(f"Kayıt yüklenemedi: {error}", "error")
                return "save_slots"
            return "local_map"
        return "opening"

    def _latest_save_path(self):
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
        path = self._latest_save_path()
        if path is None:
            self._set_notice("Açılacak kayıt bulunamadı.", "error")
            return None
        try:
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
        if target == "world":
            target = "local_map"
        if not self._nav_enabled().get(target, True):
            self._set_notice("Pazar yalnızca yerleşim yerlerinde kullanılabilir.", "error")
            return
        if target in self.screens:
            self.current = target

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

        if state.pressed("save"):
            try:
                self.save_path.parent.mkdir(parents=True, exist_ok=True)
                self.service.save(self.save_path)
                self._set_notice(f"Slot {self.selected_slot + 1 if self.selected_slot is not None else '?'} kaydedildi.", "ok")
            except (OSError, KeyError, ValueError, RuntimeError) as error:
                self._set_notice(f"Kaydetme başarısız: {error}", "error")

        if state.pressed("load"):
            try:
                self.service.load(self.save_path)
                self._set_notice(f"Oyun yüklendi: {self.save_path}", "ok")
            except (OSError, KeyError, ValueError, RuntimeError) as error:
                self._set_notice(f"Oyun yüklenemedi: {error}", "error")

        self._handle_nav_click(state)
        current_screen = self.screens[self.current]

        if self.current == "world":
            current_screen._inject_mouse_action(state, self.renderer)

        if self.current == "opening":
              current_screen.update()

        next_screen = current_screen.handle(state)

        if next_screen == "quit":
            self.running = False
            return
        if next_screen == "continue":
            next_screen = self._continue_latest_save()

        if next_screen == "world":
            next_screen = "local_map"

        if next_screen in self.screens:
            if next_screen == "dialogue":
                if self.current == "character_creation":
                    self.screens["dialogue"].resume_after_creation()
                self.screens["dialogue"].set_target_npc(
                    getattr(current_screen, "selected_npc_id", None)
                )
            self.current = next_screen

        # Tell the renderer which chrome to draw for the screen shown this frame.
        shown = self.current
        if shown in NAV_SCREENS and (
            shown != "local_map" or self.screens["local_map"].menu_open
        ):
            self.renderer.nav_current = NAV_ALIASES.get(shown, shown)
            self.renderer.nav_enabled = self._nav_enabled()
        else:
            self.renderer.nav_current = None
        self.screens[shown].render(self.renderer)

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
            "Pygame backend bulunamadı. `pip install pygame` sonrası "
            "launch(service, backend=pygame) kullanın."
        )

    window = GameWindow(service, backend, **kwargs)
    window.run()
    return window