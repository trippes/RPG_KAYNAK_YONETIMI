from ..renderer import GOLD, MUTED, TEXT, resource_name, unit_label


class InventoryScreen:
    COLUMNS = 2
    ROWS = 4
    CARD_W, CARD_H = 380, 52
    LEFT, TOP, GAP = 98, 200, 8

    def __init__(self, service, inventory_id="player"):
        self.service = service
        self.inventory_id = inventory_id
        self.message = "Ekmek ve su tüketilebilir."

    def handle(self, state):
        if state.pressed("world") or state.pressed("back"):
            return "local_map"
        if state.pressed("market"):
            return "market"
        if state.pressed("character"):
            return "character"
        if state.pressed("confirm"):
            stocks = self.service.inventory(self.inventory_id).stocks
            consumable = next(
                (resource for resource, amount, _unit in stocks
                 if resource in {"bread", "water"} and amount > 0),
                None,
            )
            if consumable is not None:
                try:
                    hp = self.service.consume_item("hero", self.inventory_id, consumable)
                    self.message = f"{resource_name(consumable)} tüketildi. Can: {hp}"
                except (KeyError, ValueError, RuntimeError) as error:
                    self.message = f"Tüketilemedi: {error}"
            else:
                self.message = "Tüketilebilir ekmek veya su yok."
        return None

    def render(self, renderer):
        snapshot = self.service.inventory(self.inventory_id)
        stocks = list(snapshot.stocks)
        renderer.frame("Envanter")
        renderer.hud(self.service)
        renderer.panel(renderer.pg.Rect(70, 130, 820, 350))
        renderer.text("Oyuncu çantası", 98, 150, title=True)
        if not stocks:
            renderer.text("Çanta boş", 100, 230, MUTED)

        capacity = self.COLUMNS * self.ROWS
        for index, (resource, amount, unit) in enumerate(stocks[:capacity]):
            column, row = index % self.COLUMNS, index // self.COLUMNS
            rect = renderer.pg.Rect(
                self.LEFT + column * (self.CARD_W + self.GAP),
                self.TOP + row * (self.CARD_H + self.GAP),
                self.CARD_W, self.CARD_H,
            )
            renderer.panel(
                rect,
                (50, 66, 94) if renderer.hovered(rect) else (38, 49, 69),
                (62, 78, 101),
            )
            renderer.resource_icon(rect.x + 14, rect.centery - 14, resource, 28)
            renderer.text(resource_name(resource), rect.x + 56, rect.centery - 9, TEXT)
            value = f"{amount} {unit_label(unit)}"
            renderer.text(value, rect.right - 14 - renderer.text_width(value), rect.centery - 9, GOLD)
        if len(stocks) > capacity:
            renderer.text(f"+{len(stocks) - capacity} kaynak daha", 100, 448, MUTED)
        renderer.text(renderer.fit_text(self.message, 760), 100, 470, GOLD)
        renderer.footer("Enter: ekmek/su tüket   M Ticaret   W Harita   Esc Kapat")
