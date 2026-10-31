
class OpeningScreen:
    """Show the opening narration before the first dialogue."""

    INTRO_TEXT = (
        "Uzak diyarlardan geldin.\n\n"
        "Uzun bir yolculuğun ardından nihayet "
        "küçük bir köyün girişine ulaştın.\n\n"
        "Yolun iki yanında uzanan tepeler sislerin "
        "ardında kayboluyor.\n\n"
        "Tahta surların önünde nöbet tutan bir muhafız "
        "seni fark ediyor ve sana doğru yaklaşıyor.\n\n"
        "Yeni bir yolculuk başlamak üzere..."
    )

    def __init__(self):
        self.visible_chars = 0
        self.scroll_speed = 2
        self.finished = False

    def handle(self, state):
        if state.pressed("confirm"):
            if not self.finished:
                self.visible_chars = len(self.INTRO_TEXT)
                self.finished = True
            else:
                return "dialogue"

        if state.pressed("back") or state.pressed("world"):
            # Açılış sahnesi atlanamaz.
            return None

        return None

    def update(self):
        if not self.finished:
            self.visible_chars = min(
                len(self.INTRO_TEXT),
                self.visible_chars + self.scroll_speed,
            )
            if self.visible_chars >= len(self.INTRO_TEXT):
                self.finished = True

    def render(self, renderer):
        renderer.frame("Eldoria")
        panel = renderer.pg.Rect(70, 110, renderer.width - 140, min(390, renderer.height - 210))
        renderer.panel(panel)

        visible_text = self.INTRO_TEXT[:self.visible_chars]
        renderer.wrapped_text(
            visible_text, panel.x + 30, panel.y + 40, panel.width - 60,
            line_height=28, max_lines=max(1, (panel.height - 70) // 28),
        )

        if self.finished:
            renderer.footer("Enter: Devam et")
        else:
            renderer.footer("Enter: Metni göster")
