from ..renderer import GOLD, MUTED, TEXT, resource_name


class MarketScreen:
    VISIBLE_OFFERS = 4
    ROW_X, ROW_Y, ROW_W, ROW_H = 96, 206, 760, 44
    BUY_RECT = (636, 408, 220, 42)

    def __init__(self, service):
        self.service = service
        self.selected = 0
        self.message = "Enter ile seçili teklifi satın al."

    def _first_visible(self, offers):
        return max(0, min(self.selected - self.VISIBLE_OFFERS + 1, len(offers) - self.VISIBLE_OFFERS))

    def _buy(self, offers):
        offer = offers[self.selected]
        try:
            self.service.buy_offer(offer.offer_id, "hero", "player", quantity=1)
            self.message = f"1 {resource_name(offer.resource_type)} satın alındı."
        except (KeyError, ValueError, RuntimeError) as error:
            self.message = f"Satın alma başarısız: {error}"

    def handle(self, state):
        offers = self.service.market_offers()
        if offers:
            self.selected %= len(offers)

        if offers and state.mouse_clicked and state.mouse_pos is not None:
            mx, my = state.mouse_pos
            first = self._first_visible(offers)
            if self.ROW_X <= mx <= self.ROW_X + self.ROW_W and my >= self.ROW_Y:
                row = (my - self.ROW_Y) // self.ROW_H
                if 0 <= row < self.VISIBLE_OFFERS and first + row < len(offers):
                    self.selected = first + row
            bx, by, bw, bh = self.BUY_RECT
            if bx <= mx <= bx + bw and by <= my <= by + bh:
                self._buy(offers)

        if offers and (state.pressed("up") or state.pressed("down")):
            self.selected = (self.selected + (1 if state.pressed("down") else -1)) % len(offers)
        if offers and state.pressed("confirm"):
            self._buy(offers)
        if state.pressed("world") or state.pressed("back"):
            return "local_map"
        if state.pressed("inventory"):
            return "inventory"
        if state.pressed("character"):
            return "character"
        return None

    def render(self, renderer):
        renderer.frame("Pazar")
        renderer.hud(self.service)
        renderer.panel(renderer.pg.Rect(70, 130, 820, 350))
        renderer.text("Satın alınabilir teklifler", 98, 150, title=True)
        offers = self.service.market_offers()
        if not offers:
            renderer.text("Aktif market teklifi yok.", 100, 230, MUTED)
        else:
            self.selected %= len(offers)
        first = self._first_visible(offers) if offers else 0
        for row, offer in enumerate(offers[first:first + self.VISIBLE_OFFERS]):
            index = first + row
            chosen = index == self.selected
            rect = renderer.pg.Rect(
                self.ROW_X, self.ROW_Y + row * self.ROW_H, self.ROW_W, self.ROW_H - 4,
            )
            renderer.panel(
                rect,
                (55, 75, 105) if chosen else (50, 66, 94) if renderer.hovered(rect) else (38, 49, 69),
                (245, 210, 120) if chosen else (62, 78, 101),
            )
            renderer.resource_icon(rect.x + 12, rect.centery - 10, offer.resource_type, 20)
            renderer.text(
                f"{resource_name(offer.resource_type)} × {offer.quantity}",
                rect.x + 44, rect.centery - 9, TEXT,
            )
            price = f"{offer.unit_price.amount} {resource_name(offer.unit_price.currency)} / adet"
            renderer.text(price, rect.right - 14 - renderer.text_width(price), rect.centery - 9, GOLD)
        if len(offers) > self.VISIBLE_OFFERS:
            renderer.text(f"{self.selected + 1}/{len(offers)} teklif", 100, 384, MUTED)
        try:
            balance = self.service.balance("hero", "gold").amount
            renderer.text(f"Altın: {balance}", 100, 420, GOLD)
        except (KeyError, ValueError):
            pass
        renderer.action_button(
            renderer.pg.Rect(*self.BUY_RECT), "ENTER", "Satın al", enabled=bool(offers), selected=True,
        )
        renderer.text(renderer.fit_text(self.message, 760), 100, 455, GOLD)
        renderer.footer("↑/↓ Teklif seç   Enter / Buton: Satın al   P Karakter   Esc Dünya")
