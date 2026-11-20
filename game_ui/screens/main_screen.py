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
        self.context_menu_npc_id = None
        self.context_menu_position = None
        self.context_menu_is_companion = False
        self.context_menu_target_id = None
        self.context_menu_target_kind = None
        self.selected_interaction_target_id = None
        self.notice = None

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
            self.selected_scene_object_id = getattr(
                self._view(), "selected_scene_object_id", None,
            )
            self.context_menu_npc_id = getattr(
                self._view(), "context_menu_npc_id", None,
            )
            self.context_menu_position = getattr(
                self._view(), "context_menu_position", None,
            )
            self.context_menu_is_companion = getattr(
                self._view(), "context_menu_is_companion", False,
            )
            self.context_menu_target_id = getattr(
                self._view(), "context_menu_target_id", None,
            )
            self.context_menu_target_kind = getattr(
                self._view(), "context_menu_target_kind", None,
            )
            self.selected_interaction_target_id = getattr(
                self._view(), "selected_interaction_target_id", None,
            )
            if result == "dialogue":
                self.selected_npc_id = self._view().selected_npc_id
                self.selected_scene_object_id = None
                return "dialogue"
            if result == "inspect":
                self.selected_scene_object_id = self._view().selected_scene_object_id
                self.context_menu_npc_id = None
                return "inspect"
            if result == "companion_menu":
                return "companion_menu"
            if result == "npc_menu":
                return "npc_menu"
            if result == "inspect_npc":
                self.notice = f"NPC: {getattr(self._view(), 'selected_npc_id', 'Bilinmeyen')}"
                return "inspect_npc"
            if result == "companion_command":
                self.context_menu_npc_id = None
                self.context_menu_position = None
                self.notice = "Yoldaş komutu uygulandı."
                return "companion_command"
            if result in {"world_target_menu", "gather", "inspect_target"}:
                if result == "inspect_target":
                    self.notice = (
                        f"Hedef: {self.selected_interaction_target_id}"
                    )
                return result
            if isinstance(result, str) and (
                result.startswith("container:") or result.startswith("door:")
            ):
                return result
        return None

    def render(self, renderer):
        if self._runtime() is not None and self._view().render(renderer):
            if self.selected_scene_object_id is not None:
                renderer.text(
                    f"Seçili çevre nesnesi: {self.selected_scene_object_id}",
                    28, 34,
                )
            if self.notice is not None:
                renderer.text(self.notice, 28, 58)
            if self.context_menu_position is not None and (
                self.context_menu_npc_id is not None
                or self.context_menu_target_kind is not None
            ):
                x, y = self.context_menu_position
                x = min(max(8, x), max(8, renderer.width - 184))
                y = min(max(8, y), max(8, renderer.height - 64))
                menu = renderer.pg.Rect(x, y, 176, 56)
                renderer.panel(menu, (28, 35, 49), (131, 151, 176))
                if self.context_menu_is_companion:
                    renderer.text("Beni takip et", x + 10, y + 6)
                    renderer.text("Burada bekle", x + 10, y + 31)
                elif self.context_menu_npc_id is not None:
                    renderer.text("Konuş", x + 10, y + 6)
                    renderer.text("İncele", x + 10, y + 31)
                else:
                    first_label = {
                        "resource_node": "Topla",
                        "container": "Aç",
                        "door": "Kullan",
                    }.get(self.context_menu_target_kind, "Kullan")
                    renderer.text(first_label, x + 10, y + 6)
                    renderer.text("İncele", x + 10, y + 31)
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
