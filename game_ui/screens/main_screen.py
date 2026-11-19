"""Persistent gameplay surface backed by the authoritative axial world."""

from game_ui.world_rendering.hex_gameplay_view import HexGameplayView


class MainScreen:
    """Render the live HexWorldRuntime when the active package provides one."""

    def __init__(self, service):
        self.service = service
        self.message = "Yeni dünya haritası hazırlanıyor."
        self._hex_view = None

    def _runtime(self):
        return self.service.hex_world_runtime

    def _view(self):
        if self._hex_view is None:
            self._hex_view = HexGameplayView(self.service)
        return self._hex_view

    def update(self, elapsed_seconds=0.0):
        if self._runtime() is not None:
            self._view().update(elapsed_seconds)

    def handle(self, state):
        if self._runtime() is not None:
            self._view().handle(state)
        return None

    def render(self, renderer):
        if self._runtime() is not None and self._view().render(renderer):
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
