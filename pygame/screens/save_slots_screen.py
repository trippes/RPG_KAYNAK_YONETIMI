from pathlib import Path

from ..renderer import GOLD, MUTED, TEXT_SOFT


class SaveSlotsScreen:
    SLOT_COUNT = 10

    def __init__(self, save_dir, on_selected):
        self.save_dir = Path(save_dir)
        self.on_selected = on_selected
        self.selected = 0
        self.message = ""
        self.pending_delete = False
        self.delete_rects = ()

    def slot_path(self, index):
        return self.save_dir / f"slot_{index + 1}.json"

    def _request_delete(self, index):
        path = self.slot_path(index)
        if not path.exists():
            self.message = f"Slot {index + 1} zaten boş."
            return
        self.selected = index
        self.pending_delete = True
        self.message = ""

    def _delete_selected(self):
        path = self.slot_path(self.selected)
        try:
            path.unlink()
        except OSError as error:
            self.message = f"Kayıt silinemedi: {error}"
        else:
            self.message = f"Slot {self.selected + 1} silindi."
        self.pending_delete = False

    def handle(self, state):
        if self.pending_delete:
            if state.pressed("back"):
                self.pending_delete = False
                return None
            if state.pressed("confirm"):
                self._delete_selected()
                return None
            if state.mouse_clicked and state.mouse_pos is not None:
                if self.confirm_rect.collidepoint(state.mouse_pos):
                    self._delete_selected()
                elif self.cancel_rect.collidepoint(state.mouse_pos):
                    self.pending_delete = False
                return None
            return None

        if state.pressed("up"):
            self.selected = (self.selected - 1) % self.SLOT_COUNT
        if state.pressed("down"):
            self.selected = (self.selected + 1) % self.SLOT_COUNT
        if state.pressed("back"):
            return "menu"
        if state.pressed("delete"):
            self._request_delete(self.selected)
            return None
        if state.pressed("confirm"):
            path = self.slot_path(self.selected)
            self.save_dir.mkdir(parents=True, exist_ok=True)
            return self.on_selected(self.selected, path, path.exists())
        if state.mouse_clicked and state.mouse_pos is not None:
            for index, rect in enumerate(self.delete_rects):
                if rect.collidepoint(state.mouse_pos):
                    self._request_delete(index)
                    return None
            for index, rect in enumerate(self.slot_rects):
                if rect.collidepoint(state.mouse_pos):
                    self.selected = index
                    path = self.slot_path(self.selected)
                    self.save_dir.mkdir(parents=True, exist_ok=True)
                    return self.on_selected(self.selected, path, path.exists())
        return None

    def render(self, renderer):
        renderer.frame("Kayıt Slotları")
        panel = renderer.pg.Rect(70, 100, renderer.width - 140, min(440, renderer.height - 170))
        renderer.panel(panel)
        renderer.text("Bir kayıt slotu seç", panel.x + 30, panel.y + 25, title=True)
        row_height = max(24, min(34, (panel.height - 90) // self.SLOT_COUNT))
        self.slot_rects = []
        self.delete_rects = []
        for index in range(self.SLOT_COUNT):
            rect = renderer.pg.Rect(
                panel.x + 20, panel.y + 70 + index * row_height,
                panel.width - 150, row_height - 5,
            )
            delete_rect = renderer.pg.Rect(
                rect.right + 10, rect.y, 100, rect.height,
            )
            self.slot_rects.append(rect)
            self.delete_rects.append(delete_rect)
            exists = self.slot_path(index).exists()
            label = f"{index + 1:02d}   {'Dolu kayıt' if exists else 'Boş slot'}"
            renderer.panel(
                rect,
                (55, 75, 105) if index == self.selected else (38, 49, 69),
                GOLD if index == self.selected else (62, 78, 101),
            )
            renderer.text(label, rect.x + 14, rect.y + 5, TEXT_SOFT if exists else MUTED)
            renderer.action_button(
                delete_rect, "Delete", "Sil", enabled=exists,
                selected=exists and index == self.selected,
            )
        if self.pending_delete:
            modal = renderer.pg.Rect(
                (renderer.width - 460) // 2, (renderer.height - 220) // 2,
                460, 220,
            )
            renderer.panel(modal, (23, 29, 43), (180, 90, 75))
            renderer.text(
                "Kaydı Sil",
                modal.centerx - renderer.text_width("Kaydı Sil", title=True) // 2,
                modal.y + 24,
                GOLD,
                title=True,
            )
            renderer.text(
                f"Slot {self.selected + 1} silinsin mi?",
                modal.x + 30, modal.y + 76, TEXT_SOFT,
            )
            self.cancel_rect = renderer.pg.Rect(modal.x + 45, modal.bottom - 62, 160, 40)
            self.confirm_rect = renderer.pg.Rect(modal.right - 205, modal.bottom - 62, 160, 40)
            renderer.button(self.cancel_rect, "İptal")
            renderer.button(self.confirm_rect, "Onayla", True)
        if self.message:
            renderer.text(
                self.message,
                panel.x + 30,
                panel.bottom - 48,
                GOLD if self.pending_delete else TEXT_SOFT,
                max_width=panel.width - 60,
            )
        renderer.footer("↑/↓ Slot seç   Enter Aç/Yeni Oyun   Satırdaki Sil butonu   Esc Menü")
