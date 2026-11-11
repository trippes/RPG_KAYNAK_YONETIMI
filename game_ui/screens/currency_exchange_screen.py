"""Player-facing currency exchange window."""

from economy import currency_name


class CurrencyExchangeScreen:
    scale_to_window = True
    design_size = (912, 438)

    OPTIONS = (
        (60, "bronze", "silver"),
        (1, "silver", "bronze"),
        (60, "silver", "gold"),
        (1, "gold", "silver"),
        (3600, "bronze", "gold"),
        (1, "gold", "bronze"),
    )
    BUTTON_RECTS = (
        (60, 280, 380, 48),
        (472, 280, 380, 48),
        (60, 344, 380, 48),
        (472, 344, 380, 48),
        (60, 408, 380, 48),
        (472, 408, 380, 48),
    )

    def __init__(self, service):
        self.service = service
        self.selected = 0
        self.message = "Dönüştürmek istediğin işlemi seç."

    def _exchange(self, index):
        amount, source, target = self.OPTIONS[index]
        try:
            received = self.service.exchange_currency("hero", source, target, amount)
            self.message = (
                f"{amount} {currency_name(source)} bozduruldu; "
                f"{received.amount} {currency_name(target)} alındı."
            )
        except (KeyError, TypeError, ValueError, RuntimeError) as error:
            self.message = f"Döviz işlemi yapılamadı: {error}"

    def handle(self, state):
        if state.pressed("up"):
            self.selected = (self.selected - 1) % len(self.OPTIONS)
        if state.pressed("down"):
            self.selected = (self.selected + 1) % len(self.OPTIONS)

        if state.mouse_pos is not None:
            for index, (x, y, width, height) in enumerate(self.BUTTON_RECTS):
                if x <= state.mouse_pos[0] <= x + width and y <= state.mouse_pos[1] <= y + height:
                    self.selected = index
                    if state.mouse_clicked:
                        self._exchange(index)
                    break

        if state.pressed("confirm"):
            self._exchange(self.selected)
        return None

    def render(self, renderer):
        renderer.panel(renderer.pg.Rect(36, 136, 888, 402))
        renderer.text("Döviz Bürosu", 60, 154, title=True)
        balances = (
            self.service.balance("hero", "bronze").amount,
            self.service.balance("hero", "silver").amount,
            self.service.balance("hero", "gold").amount,
        )
        renderer.text(
            f"Cüzdan: {balances[0]} {currency_name('bronze')}  •  "
            f"{balances[1]} {currency_name('silver')}  •  "
            f"{balances[2]} {currency_name('gold')}",
            60, 204,
        )
        renderer.text("Kur: 60 bronz = 1 gümüş  |  60 gümüş = 1 altın", 60, 238)
        labels = (
            "60 Bronz → 1 Gümüş",
            "1 Gümüş → 60 Bronz",
            "60 Gümüş → 1 Altın",
            "1 Altın → 60 Gümüş",
            "3.600 Bronz → 1 Altın",
            "1 Altın → 3.600 Bronz",
        )
        for index, (bounds, label) in enumerate(zip(self.BUTTON_RECTS, labels)):
            renderer.button(renderer.pg.Rect(*bounds), label, selected=index == self.selected)
        renderer.text(renderer.fit_text(self.message, 760), 60, 480)


__all__ = ["CurrencyExchangeScreen"]
