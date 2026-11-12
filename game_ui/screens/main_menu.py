from pathlib import Path


class MainMenu:
    """Artwork-led title screen matching the supplied Eldoria key art."""

    ARTWORK_SIZE = (1365, 768)
    OPTIONS = (
        ("Yeni Oyun", "new_game"),
        ("Devam Et", "continue"),
            ("Ayarlar", "settings"),
        ("Oyun Rehberi", "guide"),
        ("Hakkında", "about"),
        ("Çıkış", "quit"),
    )
    HINTS = (
        "Yeni bir maceraya atıl",
        "Macerana devam et",
        "Hazır karakterle doğrudan test et",
        "Oyun ayarlarını düzenle",
        "Eldoria oyun rehberini aç",
        "Eldoria hakkında bilgi al",
        "Oyundan çık",
    )
    NEW_GAME_OPTIONS = (
        ("Kayıtlı Oyunu Yükle", "load_slots"),
        ("Yeni Oyun Başlat", "new_game"),
        ("Geri", "back"),
    )

    def __init__(self, width=1365, height=768):
        self.width = width
        self.height = height
        self.selected = 0
        self.new_game_open = False
        self.new_game_selected = 0
        self._background = None
        self._crest = None

    def _menu_rects(self, renderer):
        scale_x = renderer.width / self.ARTWORK_SIZE[0]
        scale_y = renderer.height / self.ARTWORK_SIZE[1]
        left, top, width, row_height, gap = 80, 295, 370, 53, 8
        return [
            renderer.pg.Rect(
                round(left * scale_x),
                round((top + index * (row_height + gap)) * scale_y),
                round(width * scale_x),
                round(row_height * scale_y),
            )
            for index in range(len(self.OPTIONS))
        ]

    def handle(self, state, renderer=None):
        if self.new_game_open:
            if state.mouse_clicked and state.mouse_pos is not None and renderer is not None:
                panel = renderer.pg.Rect(
                    renderer.width // 2 - 250, renderer.height // 2 - 120, 500, 300,
                )
                for index, _option in enumerate(self.NEW_GAME_OPTIONS):
                    button = renderer.pg.Rect(
                        panel.x + 45, panel.y + 90 + index * 55,
                        panel.width - 90, 42,
                    )
                    if button.collidepoint(state.mouse_pos):
                        self.new_game_selected = index
                        action = self.NEW_GAME_OPTIONS[index][1]
                        if action == "back":
                            self.new_game_open = False
                            return None
                        self.new_game_open = False
                        return action
            if state.pressed("up") or state.pressed("down"):
                delta = -1 if state.pressed("up") else 1
                self.new_game_selected = (
                    self.new_game_selected + delta
                ) % len(self.NEW_GAME_OPTIONS)
            if state.pressed("back"):
                self.new_game_open = False
                return None
            if state.pressed("confirm"):
                action = self.NEW_GAME_OPTIONS[self.new_game_selected][1]
                if action == "back":
                    self.new_game_open = False
                    return None
                self.new_game_open = False
                return action
            return None

        if state.mouse_pos is not None and renderer is not None:
            for index, rect in enumerate(self._menu_rects(renderer)):
                if rect.collidepoint(state.mouse_pos):
                    self.selected = index
                    if state.mouse_clicked:
                        action = self.OPTIONS[index][1]
                        if action == "new_game":
                            self.new_game_open = True
                            self.new_game_selected = 0
                            return None
                        return action
                    break

        if state.pressed("up") or state.pressed("down"):
            delta = -1 if state.pressed("up") else 1
            self.selected = (self.selected + delta) % len(self.OPTIONS)
        if state.pressed("quit"):
            return "quit"
        if state.pressed("confirm"):
            action = self.OPTIONS[self.selected][1]
            if action == "new_game":
                self.new_game_open = True
                self.new_game_selected = 0
                return None
            return action
        return None

    def _load_background(self, renderer):
        if self._background is not None:
            return self._background
        image = getattr(renderer.pg, "image", None)
        if image is None or not hasattr(image, "load"):
            return None
        path = Path(__file__).resolve().parents[1] / "assets" / "main_menu1.png"
        if not path.is_file():
            return None
        self._background = image.load(str(path))
        return self._background

    def _load_crest(self, renderer):
        if self._crest is not None:
            return self._crest
        image = getattr(renderer.pg, "image", None)
        if image is None or not hasattr(image, "load"):
            return None
        path = Path(__file__).resolve().parents[1] / "assets" / "eldoria_crest.png"
        if not path.is_file():
            return None
        self._crest = image.load(str(path))
        return self._crest

    def _draw_crest(self, renderer):
        crest = self._load_crest(renderer)
        transform = getattr(renderer.pg, "transform", None)
        if crest is None or transform is None or not hasattr(transform, "smoothscale"):
            return
        max_width = min(round(renderer.width * 0.28), 390)
        source_width, source_height = crest.get_size()
        scale = max_width / source_width
        size = (max_width, max(1, round(source_height * scale)))
        scaled = transform.smoothscale(crest, size)
        renderer.surface.blit(
            scaled,
            (renderer.width - max_width - round(renderer.width * 0.035),
             round(renderer.height * 0.025)),
        )

    def _button_polygon(self, rect):
        bevel = max(12, round(rect.height * 0.34))
        return [
            (rect.left + bevel, rect.top),
            (rect.right - bevel, rect.top),
            (rect.right, rect.top + bevel),
            (rect.right - bevel, rect.bottom),
            (rect.left + bevel, rect.bottom),
            (rect.left, rect.bottom - bevel),
            (rect.left, rect.top + bevel),
        ]

    def _inset_polygon(self, renderer, rect, inset):
        return self._button_polygon(
            renderer.pg.Rect(
                rect.x + inset,
                rect.y + inset,
                rect.width - inset * 2,
                rect.height - inset * 2,
            )
        )

    def _draw_button_layer(self, renderer, rect, index, active):
        draw = renderer.pg.draw
        polygon = self._button_polygon(rect)
        shadow = [(x, y + 5) for x, y in polygon]
        draw.polygon(renderer.surface, (18, 12, 8), shadow)
        draw.polygon(renderer.surface, (170, 119, 39) if active else (113, 89, 53), polygon)

        outer_inset = max(3, round(rect.height * 0.08))
        outer = self._inset_polygon(renderer, rect, outer_inset)
        draw.polygon(renderer.surface, (45, 28, 16) if active else (24, 25, 27), outer)
        draw.lines(renderer.surface, (255, 226, 126) if active else (177, 139, 79), True, outer, 2)

        inner_inset = max(7, round(rect.height * 0.17))
        inner = self._inset_polygon(renderer, rect, inner_inset)
        draw.polygon(renderer.surface, (92, 54, 18) if active else (35, 37, 39), inner)
        draw.lines(renderer.surface, (255, 239, 167) if active else (82, 77, 67), True, inner, 1)

        # A narrow highlight across the top edge gives the panel a forged,
        # dimensional look instead of a flat filled rectangle.
        highlight = [
            (rect.left + round(rect.width * 0.14), rect.top + outer_inset + 2),
            (rect.right - round(rect.width * 0.14), rect.top + outer_inset + 2),
        ]
        draw.line(
            renderer.surface,
            (255, 246, 191) if active else (122, 104, 73),
            highlight[0],
            highlight[1],
            1,
        )

        icon_x = rect.x + round(rect.width * 0.13)
        center_y = rect.centery
        icon_color = (255, 247, 205) if active else (226, 218, 187)
        draw.circle(renderer.surface, (53, 38, 24) if active else (25, 29, 34),
                    (icon_x, center_y), round(rect.height * 0.29))
        draw.circle(renderer.surface, (228, 178, 68) if active else (145, 116, 68),
                    (icon_x, center_y), round(rect.height * 0.29), 1)
        if index in (0, 1):
            icon = [
                (icon_x - 8, center_y - 12),
                (icon_x + 12, center_y),
                (icon_x - 8, center_y + 12),
            ]
            draw.polygon(renderer.surface, icon_color, icon)
        elif index == 2:
            draw.rect(renderer.surface, icon_color, renderer.pg.Rect(icon_x - 9, center_y - 9, 18, 18), 2)
            draw.line(renderer.surface, icon_color, (icon_x - 5, center_y), (icon_x + 5, center_y), 2)
            draw.line(renderer.surface, icon_color, (icon_x, center_y - 5), (icon_x, center_y + 5), 2)
        elif index == 3:
            draw.circle(renderer.surface, icon_color, (icon_x, center_y), 10, 3)
        elif index == 4:
            draw.rect(renderer.surface, icon_color, renderer.pg.Rect(icon_x - 12, center_y - 10, 24, 20), 2)
        elif index == 5:
            draw.circle(renderer.surface, icon_color, (icon_x, center_y), 11)
            renderer.text("i", icon_x - 3, center_y - 10, (70, 50, 20))
        else:
            draw.rect(renderer.surface, icon_color, renderer.pg.Rect(icon_x - 10, center_y - 10, 18, 20), 2)
            draw.polygon(renderer.surface, icon_color,
                         [(icon_x + 2, center_y - 6), (icon_x + 13, center_y), (icon_x + 2, center_y + 6)])

        label = self.OPTIONS[index][0]
        text_color = (255, 248, 218) if active else (232, 226, 208)
        renderer.text(
            label,
            rect.x + round(rect.width * 0.24),
            rect.y + (rect.height - 26) // 2,
            text_color,
            max_width=rect.width - round(rect.width * 0.34),
        )
        diamond_x = rect.right - round(rect.width * 0.12)
        diamond = [
            (diamond_x, center_y - 9),
            (diamond_x + 9, center_y),
            (diamond_x, center_y + 9),
            (diamond_x - 9, center_y),
        ]
        draw.polygon(renderer.surface, (255, 226, 120) if active else (183, 150, 83), diamond)
        draw.polygon(renderer.surface, (61, 93, 112) if active else (33, 65, 81),
                     [(diamond_x, center_y - 5), (diamond_x + 5, center_y),
                      (diamond_x, center_y + 5), (diamond_x - 5, center_y)])

    def _draw_hint(self, renderer):
        label = self.HINTS[self.selected]
        x = round(renderer.width * 1115 / self.ARTWORK_SIZE[0])
        y = round(renderer.height * 713 / self.ARTWORK_SIZE[1])
        # Keep the artwork visible; the shadow preserves readability over
        # bright scenery without adding an opaque or dark backing panel.
        renderer.text(label, x + 2, y + 2, (20, 17, 14), max_width=renderer.width - x - 16)
        renderer.text(
            label,
            x,
            y,
            (244, 224, 175),
            max_width=renderer.width - x - 16,
        )

    def render(self, renderer):
        background = self._load_background(renderer)
        if background is None:
            renderer.clear((14, 18, 28))
            renderer.text("Eldoria", 80, 100, (220, 190, 120), title=True)
            renderer.text("Kaynak Yönetimi", 84, 158)
        else:
            surface = background
            if surface.get_size() != (renderer.width, renderer.height):
                transform = getattr(renderer.pg, "transform", None)
                if transform is not None and hasattr(transform, "smoothscale"):
                    surface = transform.smoothscale(
                        background, (renderer.width, renderer.height)
                    )
            renderer.surface.blit(surface, (0, 0))

        self._draw_crest(renderer)
        rects = self._menu_rects(renderer)
        for index, rect in enumerate(rects):
            self._draw_button_layer(renderer, rect, index, index == self.selected)
        self._draw_hint(renderer)
        if self.new_game_open:
            panel = renderer.pg.Rect(
                renderer.width // 2 - 250, renderer.height // 2 - 120, 500, 300,
            )
            renderer.panel(panel, (23, 29, 43), (180, 145, 75))
            renderer.text(
                "Yeni Oyun",
                panel.centerx - renderer.text_width("Yeni Oyun", title=True) // 2,
                panel.y + 24,
                (240, 210, 135),
                title=True,
            )
            for index, (label, _action) in enumerate(self.NEW_GAME_OPTIONS):
                button = renderer.pg.Rect(
                    panel.x + 45, panel.y + 90 + index * 55,
                    panel.width - 90, 42,
                )
                renderer.button(
                    button, label, selected=index == self.new_game_selected,
                )
