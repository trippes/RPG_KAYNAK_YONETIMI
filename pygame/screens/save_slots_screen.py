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
        self._background = None

    def _load_background(self, renderer):
        if self._background is not None:
            return self._background
        image = getattr(renderer.pg, "image", None)
        path = Path(__file__).resolve().parents[1] / "assets" / "main_menu.png"
        if image is None or not hasattr(image, "load") or not path.is_file():
            return None
        self._background = image.load(str(path))
        return self._background

    def _polygon(self, renderer, rect, inset=0):
        rect = renderer.pg.Rect(
            rect.x + inset, rect.y + inset,
            rect.width - inset * 2, rect.height - inset * 2,
        )
        bevel = max(8, round(rect.height * 0.35))
        return [
            (rect.left + bevel, rect.top), (rect.right - bevel, rect.top),
            (rect.right, rect.top + bevel), (rect.right - bevel, rect.bottom),
            (rect.left + bevel, rect.bottom), (rect.left, rect.bottom - bevel),
            (rect.left, rect.top + bevel),
        ]

    def _draw_slot(self, renderer, rect, index, exists, active):
        draw = renderer.pg.draw
        polygon = self._polygon(renderer, rect)
        shadow = [(x, y + 4) for x, y in polygon]
        draw.polygon(renderer.surface, (17, 12, 9), shadow)
        draw.polygon(
            renderer.surface,
            (152, 103, 26) if active else (61, 48, 34),
            polygon,
        )
        inner = self._polygon(renderer, rect, max(3, round(rect.height * 0.12)))
        draw.polygon(renderer.surface, (87, 52, 18) if active else (25, 28, 32), inner)
        draw.lines(
            renderer.surface,
            (255, 218, 104) if active else (115, 92, 59),
            True, polygon, 2,
        )
        draw.lines(
            renderer.surface,
            (255, 242, 165) if active else (64, 64, 63),
            True, inner, 1,
        )

        number_rect = renderer.pg.Rect(rect.x + 10, rect.y + 3, 54, rect.height - 6)
        draw.polygon(
            renderer.surface,
            (45, 28, 14) if active else (29, 32, 36),
            self._polygon(renderer, number_rect, 1),
        )
        draw.lines(
            renderer.surface,
            (239, 191, 76) if active else (128, 101, 63),
            True, self._polygon(renderer, number_rect, 1), 1,
        )
        renderer.text(
            f"{index + 1:02d}", number_rect.x + 12, number_rect.y + 7,
            (255, 241, 190) if active else (222, 211, 186),
        )
        renderer.text(
            "Dolu kayıt" if exists else "Boş slot",
            rect.x + 82, rect.y + 7,
            TEXT_SOFT if exists else (192, 185, 164),
            max_width=rect.width - 115,
        )

    def _draw_delete(self, renderer, rect, enabled, active):
        draw = renderer.pg.draw
        polygon = self._polygon(renderer, rect)
        fill = (61, 42, 25) if active else (28, 29, 31)
        border = (220, 166, 68) if active else (104, 87, 62)
        draw.polygon(renderer.surface, fill, polygon)
        draw.lines(renderer.surface, border, True, polygon, 2)
        color = (245, 224, 179) if enabled else (102, 98, 89)
        draw.rect(renderer.surface, color, renderer.pg.Rect(rect.x + 15, rect.y + 10, 9, 13), 2)
        draw.line(renderer.surface, color, (rect.x + 13, rect.y + 8), (rect.x + 26, rect.y + 8), 2)
        renderer.text("Detaylar ..." if enabled else "Boş", rect.x + 34, rect.y + 7, color)

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
        if state.mouse_pos is not None:
            for index, rect in enumerate(getattr(self, "slot_rects", ())):
                if rect.collidepoint(state.mouse_pos):
                    self.selected = index
                    break
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
        background = self._load_background(renderer)
        if background is None:
            renderer.clear((14, 18, 28))
        else:
            surface = background
            if surface.get_size() != (renderer.width, renderer.height):
                transform = getattr(renderer.pg, "transform", None)
                if transform is not None and hasattr(transform, "smoothscale"):
                    surface = transform.smoothscale(background, (renderer.width, renderer.height))
            renderer.surface.blit(surface, (0, 0))

        scale_x = renderer.width / 1365
        scale_y = renderer.height / 768
        panel = renderer.pg.Rect(
            round(135 * scale_x), round(137 * scale_y),
            round(1095 * scale_x), round(548 * scale_y),
        )
        renderer.pg.draw.polygon(renderer.surface, (18, 20, 23), self._polygon(renderer, panel))
        renderer.pg.draw.lines(renderer.surface, (132, 101, 57), True, self._polygon(renderer, panel), 3)
        title_rect = renderer.pg.Rect(
            round(455 * scale_x), round(28 * scale_y),
            round(455 * scale_x), round(92 * scale_y),
        )
        renderer.pg.draw.polygon(renderer.surface, (27, 29, 31), self._polygon(renderer, title_rect))
        renderer.pg.draw.lines(renderer.surface, (205, 157, 69), True, self._polygon(renderer, title_rect), 3)
        renderer.text(
            "Kayıt Slotları",
            title_rect.centerx - renderer.text_width("Kayıt Slotları", title=True) // 2,
            title_rect.y + 24, (249, 225, 167), title=True,
        )
        renderer.text("▣  Bir kayıt slotu seç", panel.x + 32, panel.y + 22, (240, 225, 195))

        row_height = max(25, min(48, round(panel.height * 0.075)))
        row_top = panel.y + 72
        self.slot_rects = []
        self.delete_rects = []
        for index in range(self.SLOT_COUNT):
            rect = renderer.pg.Rect(
                panel.x + 34, row_top + index * row_height,
                panel.width - 190, row_height - 5,
            )
            delete_rect = renderer.pg.Rect(
                rect.right + 12, rect.y, 140, rect.height,
            )
            self.slot_rects.append(rect)
            self.delete_rects.append(delete_rect)
            exists = self.slot_path(index).exists()
            active = index == self.selected
            self._draw_slot(renderer, rect, index, exists, active)
            self._draw_delete(renderer, delete_rect, exists, active)
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
        renderer.footer("↑/↓ Slot seç   Enter Aç/Yeni Oyun   Delete Sil   Esc Menü")
