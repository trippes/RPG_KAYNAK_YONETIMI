"""Persistent gameplay surface backed by the authoritative axial world."""

from game_ui.world_rendering.hex_gameplay_view import HexGameplayView


class MainScreen:
    """Render the live HexWorldRuntime when the active package provides one."""

    def __init__(self, service):
        self.service = service
        self.message = "Yeni dünya haritası hazırlanıyor."
        self._hex_view = None
        self.selected_npc_id = None
        self.selected_scene_object_id = None

    def _runtime(self):
        return getattr(self.service, "hex_world_runtime", None)

    def _view(self):
        if self._hex_view is None:
            self._hex_view = HexGameplayView(self.service)
        return self._hex_view

    def update(self, elapsed_seconds=0.0):
        if self._runtime() is not None:
            self._view().update(elapsed_seconds)

    def cancel_click_to_move(self):
        """Give direct keyboard movement priority over an active click destination."""
        if self._hex_view is not None:
            self._hex_view._clear_move_goal()

    def handle(self, state):
        if self._runtime() is not None:
            result = self._view().handle(state)
            if result == "dialogue":
                self.selected_npc_id = self._view().selected_npc_id
                self.selected_scene_object_id = None
                return "dialogue"
            if result == "inspect":
                self.selected_scene_object_id = self._view().selected_scene_object_id
                return "inspect"
        return None

    def render(self, renderer):
        if self._runtime() is not None and self._view().render(renderer):
            if self.selected_scene_object_id is not None:
                renderer.text(
                    f"Seçili çevre nesnesi: {self.selected_scene_object_id}",
                    28, 34,
                )
            return

        panel = renderer.pg.Rect(
            24, 96, max(1, renderer.width - 48), max(1, renderer.height - 120)
        )
        renderer.panel(panel, (19, 26, 38), (62, 78, 101))
        renderer.text("ELDORIA", 48, 140)
        renderer.text(self.message, 48, 196)
        renderer.text(
            "Eski kare harita sistemi devreden çıkarıldı. Yeni axial dünya "
            "verileri ve oyuncu başlangıç hücresi hazır olduğunda oyun alanı açılacak.",
            48, 236,
        )
