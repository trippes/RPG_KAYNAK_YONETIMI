class MainMenu:
    def __init__(self):
        self.options = ("Oyuna Başla", "Çıkış")
        self.selected = 0

    def handle(self, state):
        if state.pressed("up") or state.pressed("down"):
            self.selected = 1 - self.selected
        if state.pressed("quit"):
            return "quit"
        if state.pressed("confirm"):
            return "world" if self.selected == 0 else "quit"
        return None

    def render(self, renderer):
        renderer.clear((14, 18, 28))
        renderer.text("Eldoria", 80, 100, (220, 190, 120), title=True)
        renderer.text("Kaynak Yönetimi — oynanabilir dikey dilim", 84, 158)
        for index, option in enumerate(self.options):
            renderer.button(renderer.pg.Rect(84, 250 + index * 64, 300, 48), option, index == self.selected)
        renderer.text("↑/↓ seç   Enter onayla   Q çıkış", 84, 410, (155, 172, 196))
