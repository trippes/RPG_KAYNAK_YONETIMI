from pathlib import Path

from ..renderer import GOLD, MUTED, TEXT_SOFT


class SaveSlotsScreen:
    SLOT_COUNT = 10

    def __init__(self, save_dir, on_selected):
        self.save_dir = Path(save_dir)
        self.on_selected = on_selected
        self.selected = 0
        self.message = ""

    def slot_path(self, index):
        return self.save_dir / f"slot_{index + 1}.json"

    def handle(self, state):
        if state.pressed("up"):
            self.selected = (self.selected - 1) % self.SLOT_COUNT
        if state.pressed("down"):
            self.selected = (self.selected + 1) % self.SLOT_COUNT
        if state.pressed("back"):
            return "menu"
        if state.pressed("confirm"):
            path = self.slot_path(self.selected)
            self.save_dir.mkdir(parents=True, exist_ok=True)
            return self.on_selected(self.selected, path, path.exists())
        if state.mouse_clicked and state.mouse_pos is not None:
            x, y = state.mouse_pos
            if 80 <= x <= 880 and 140 <= y < 140 + self.SLOT_COUNT * 38:
                self.selected = (y - 140) // 38
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
        for index in range(self.SLOT_COUNT):
            rect = renderer.pg.Rect(
                panel.x + 20, panel.y + 70 + index * row_height,
                panel.width - 40, row_height - 5,
            )
            exists = self.slot_path(index).exists()
            label = f"{index + 1:02d}   {'Dolu kayıt' if exists else 'Boş slot'}"
            renderer.panel(
                rect,
                (55, 75, 105) if index == self.selected else (38, 49, 69),
                GOLD if index == self.selected else (62, 78, 101),
            )
            renderer.text(label, rect.x + 14, rect.y + 5, TEXT_SOFT if exists else MUTED)
        renderer.footer("↑/↓ Slot seç   Enter Aç/Yeni Oyun   Esc Menü")
