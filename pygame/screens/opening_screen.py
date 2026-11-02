from pathlib import Path


class OpeningScreen:
    """Opening narration with a bottom-to-top cinematic text crawl."""

    INTRO_TEXT = (
        "Uzak diyarlardan geldin.\n\n"
        "Uzun bir yolculuğun ardından nihayet küçük bir köyün girişine ulaştın.\n\n"
        "Yolun iki yanında uzanan tepeler sislerin ardında kayboluyor.\n\n"
        "Tahta surların önünde nöbet tutan bir muhafız seni fark ediyor ve sana doğru yaklaşıyor.\n\n"
        "Yeni bir yolculuk başlamak üzere..."
    )
    ARTWORK_SIZE = (1365, 768)

    def __init__(self):
        self.visible_chars = 0
        self.scroll_offset = 0.0
        self.scroll_speed = 0.85
        self.finished = False
        self._background = None

    def handle(self, state):
        if state.pressed("confirm"):
            if not self.finished:
                self.visible_chars = len(self.INTRO_TEXT)
                self.scroll_offset = 0
                self.finished = True
            else:
                return "dialogue"

        if state.pressed("back") or state.pressed("world"):
            return None
        return None

    def update(self):
        if self.finished:
            return
        self.visible_chars = min(
            len(self.INTRO_TEXT), self.visible_chars + 2
        )
        self.scroll_offset += self.scroll_speed
        if self.visible_chars >= len(self.INTRO_TEXT):
            self.finished = True

    def _load_background(self, renderer):
        if self._background is not None:
            return self._background
        image = getattr(renderer.pg, "image", None)
        path = Path(__file__).resolve().parents[1] / "assets" / "opening.png"
        if image is None or not hasattr(image, "load") or not path.is_file():
            return None
        self._background = image.load(str(path))
        return self._background

    def _lines(self, renderer, text, max_width):
        lines = []
        for paragraph in text.splitlines():
            words = paragraph.split()
            if not words:
                lines.append("")
                continue
            line = ""
            for word in words:
                candidate = f"{line} {word}".strip()
                if line and renderer.text_width(candidate) > max_width:
                    lines.append(line)
                    line = word
                else:
                    line = candidate
            lines.append(line)
        return lines

    def render(self, renderer):
        background = self._load_background(renderer)
        if background is None:
            renderer.clear((14, 18, 28))
        else:
            surface = background
            if surface.get_size() != (renderer.width, renderer.height):
                transform = getattr(renderer.pg, "transform", None)
                if transform is not None and hasattr(transform, "smoothscale"):
                    surface = transform.smoothscale(
                        background, (renderer.width, renderer.height)
                    )
            renderer.surface.blit(surface, (0, 0))

        scale_x = renderer.width / self.ARTWORK_SIZE[0]
        scale_y = renderer.height / self.ARTWORK_SIZE[1]
        panel = renderer.pg.Rect(
            round(80 * scale_x), round(198 * scale_y),
            round(1205 * scale_x), round(380 * scale_y),
        )
        renderer.pg.draw.rect(renderer.surface, (17, 21, 28), panel, border_radius=18)
        renderer.pg.draw.rect(renderer.surface, (21, 25, 33), panel, 4, border_radius=18)
        renderer.pg.draw.line(
            renderer.surface, (242, 180, 59),
            (panel.x + 55, panel.y + 14), (panel.x + 55, panel.bottom - 14), 2,
        )
        renderer.pg.draw.circle(
            renderer.surface, (255, 216, 99),
            (panel.x + 55, panel.centery), 9,
        )

        max_width = panel.width - 130
        lines = self._lines(renderer, self.INTRO_TEXT[:self.visible_chars], max_width)
        line_height = max(24, round(31 * scale_y))
        baseline = panel.bottom - 52 - self.scroll_offset
        visible_top = panel.y + 26
        visible_bottom = panel.bottom - 28
        for index, line in enumerate(reversed(lines)):
            y = round(baseline - index * line_height)
            if visible_top <= y <= visible_bottom:
                renderer.text(
                    line, panel.x + 92, y, (239, 237, 232),
                    max_width=max_width,
                )

        title = renderer.pg.Rect(
            round(65 * scale_x), round(77 * scale_y),
            round(445 * scale_x), round(91 * scale_y),
        )
        renderer.pg.draw.rect(renderer.surface, (25, 27, 30), title, border_radius=12)
        renderer.pg.draw.rect(renderer.surface, (172, 127, 48), title, 3, border_radius=12)
        renderer.text(
            "Eldoria",
            title.x + 150, title.y + 23, (249, 218, 147),
            title=True, max_width=title.width - 170,
        )

        footer = renderer.pg.Rect(
            round(285 * scale_x), round(594 * scale_y),
            round(795 * scale_x), round(57 * scale_y),
        )
        renderer.pg.draw.rect(renderer.surface, (20, 23, 28), footer, border_radius=12)
        renderer.pg.draw.rect(renderer.surface, (175, 130, 53), footer, 2, border_radius=12)
        renderer.text(
            "Enter: Devam Et" if self.finished else "Enter: Metni hızlandır",
            footer.x + 42, footer.y + 17, (244, 215, 143),
            max_width=footer.width - 84,
        )
