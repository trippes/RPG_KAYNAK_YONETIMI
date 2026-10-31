class MainMenu:
    def __init__(self):
        self.options = ("Yeni Oyun", "Devam Et", "Çıkış")
        self.selected = 0


    def handle(self, state):
        if state.mouse_clicked and state.mouse_pos is not None:
            x, y = state.mouse_pos
            for index, option in enumerate(self.options):
                rect_left, rect_top = 84, 250 + index * 64
                if rect_left <= x <= rect_left + 300 and rect_top <= y <= rect_top + 48:
                    self.selected = index
                    return ("save_slots" if index in (0, 1) else "quit")

        if state.pressed("up") or state.pressed("down"):
            delta = -1 if state.pressed("up") else 1
            self.selected = (self.selected + delta) % len(self.options)
        if state.pressed("quit"):
            return "quit"
        if state.pressed("confirm"):
            return "save_slots" if self.selected in (0, 1) else "quit"
        return None

    def render(self, renderer):
        renderer.clear((14, 18, 28))
        left = max(48, renderer.width // 2 - 260)
        renderer.text("Eldoria", left, 100, (220, 190, 120), title=True)
        renderer.text(
            "RPG-Kaynak Yönetimi — oynanabilir dikey dilim",
            left, 158, max_width=min(520, renderer.width - left - 48),
        )
        for index, option in enumerate(self.options):
            renderer.button(
                renderer.pg.Rect(left, 250 + index * 64, 300, 48),
                option, index == self.selected,
            )
        renderer.text(
            "↑/↓ seç   Enter onayla   Q çıkış   F11 tam ekran",
            left, 470, (155, 172, 196), max_width=renderer.width - left - 48,
        )
