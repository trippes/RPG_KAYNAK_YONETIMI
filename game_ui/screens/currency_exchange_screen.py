"""Royal Mint currency exchange window."""

from core.constants import (
    ALTIN_SIKKE_BRONZ,
    ALTIN_SIKKE_GUMUS,
    GUMUS_SIKKE_BRONZ,
)
from economy import currency_name


class CurrencyExchangeScreen:
    scale_to_window = True
    design_size = (912, 438)

    OPTIONS = (
        (GUMUS_SIKKE_BRONZ, "bronze", "silver"),
        (1, "silver", "bronze"),
        (ALTIN_SIKKE_GUMUS, "silver", "gold"),
        (1, "gold", "silver"),
        (ALTIN_SIKKE_BRONZ, "bronze", "gold"),
        (1, "gold", "bronze"),
    )
    CARD_RECTS = (
        (60, 304, 396, 50),
        (480, 304, 396, 50),
        (60, 364, 396, 50),
        (480, 364, 396, 50),
        (60, 424, 396, 50),
        (480, 424, 396, 50),
    )

    def __init__(self, service):
        self.service = service
        self.selected = 0
        self.message = "Bir işlem seç. Enter ile dönüştür."

    def _balance(self, currency):
        try:
            return self.service.balance("hero", currency).amount
        except (KeyError, TypeError, ValueError, RuntimeError):
            return 0

    def _has_funds(self, index):
        amount, source, _target = self.OPTIONS[index]
        return self._balance(source) >= amount

    def _exchange(self, index):
        amount, source, target = self.OPTIONS[index]
        if not self._has_funds(index):
            self.message = (
                f"Yetersiz bakiye: {amount} {currency_name(source)} gerekiyor."
            )
            return
        try:
            received = self.service.exchange_currency("hero", source, target, amount)
            self.message = (
                f"İşlem tamamlandı: {amount} {currency_name(source)} "
                f"→ {received.amount} {currency_name(target)}."
            )
        except (KeyError, TypeError, ValueError, RuntimeError) as error:
            self.message = f"Döviz işlemi yapılamadı: {error}"

    def handle(self, state):
        if state.pressed("up") or state.pressed("left"):
            self.selected = (self.selected - 1) % len(self.OPTIONS)
        if state.pressed("down") or state.pressed("right"):
            self.selected = (self.selected + 1) % len(self.OPTIONS)

        if state.mouse_pos is not None:
            for index, (x, y, width, height) in enumerate(self.CARD_RECTS):
                if x <= state.mouse_pos[0] <= x + width and y <= state.mouse_pos[1] <= y + height:
                    self.selected = index
                    if state.mouse_clicked:
                        self._exchange(index)
                    break

        if state.pressed("confirm"):
            self._exchange(self.selected)
        return None

    def render(self, renderer):
        """Draw the Royal Mint interface inside the managed window viewport."""
        pg = renderer.pg
        renderer.panel(
            pg.Rect(36, 136, 888, 402),
            (23, 29, 43),
            (145, 118, 70),
        )

        # Header: restrained heraldic styling, with a clear information hierarchy.
        renderer.text("Kraliyet Darphanesi", 60, 150, title=True)
        renderer.text(
            "Sikkelerini güvenli biçimde daha büyük veya küçük birimlere dönüştür.",
            62, 194, (177, 188, 205),
        )
        pg.draw.line(renderer.surface, (112, 91, 57), (60, 216), (876, 216), 1)

        # The player's complete balance remains visible above the exchange choices.
        renderer.panel(
            pg.Rect(60, 224, 816, 38),
            (31, 39, 55),
            (91, 104, 126),
        )
        renderer.wallet(self.service, "hero", 76, 232, label="Cüzdan")

        # Canonical rates are read from core.constants, not duplicated in the UI.
        renderer.panel(
            pg.Rect(60, 270, 816, 24),
            (39, 42, 54),
            (112, 91, 57),
        )
        rate_text = (
            f"SABİT KURLAR   •   {GUMUS_SIKKE_BRONZ} BRONZ = 1 GÜMÜŞ"
            f"   •   {ALTIN_SIKKE_GUMUS} GÜMÜŞ = 1 ALTIN"
        )
        renderer.text(rate_text, 76, 273, (220, 190, 125))

        # Six exchange directions are presented as paired, tactile transaction cards.
        for index, bounds in enumerate(self.CARD_RECTS):
            amount, source, target = self.OPTIONS[index]
            selected = index == self.selected
            available = self._has_funds(index)
            rect = pg.Rect(*bounds)

            if selected:
                fill, border = (57, 65, 83), (230, 190, 112)
            elif renderer.hovered(rect):
                fill, border = (43, 54, 73), (135, 151, 177)
            else:
                fill, border = (30, 39, 55), (72, 87, 110)
            if not available and not selected:
                fill, border = (27, 32, 43), (57, 64, 77)
            renderer.panel(rect, fill, border)

            icon_y = rect.y + 13
            renderer.coin_icon(rect.x + 14, icon_y, source, 24)
            source_color = (232, 235, 242) if available else (125, 133, 146)
            source_label = f"{amount:,}".replace(",", ".") + f" {currency_name(source)}"
            renderer.text(source_label, rect.x + 48, rect.y + 16, source_color)

            arrow_color = (232, 194, 112) if available else (104, 112, 126)
            arrow_x = rect.x + 207
            pg.draw.line(
                renderer.surface, arrow_color,
                (arrow_x - 10, rect.y + 25), (arrow_x + 10, rect.y + 25), 2,
            )
            pg.draw.polygon(
                renderer.surface, arrow_color,
                [
                    (arrow_x + 10, rect.y + 25),
                    (arrow_x + 3, rect.y + 20),
                    (arrow_x + 3, rect.y + 30),
                ],
            )

            received_amount = amount
            if source == "bronze" and target == "silver":
                received_amount = 1
            elif source == "silver" and target == "bronze":
                received_amount = GUMUS_SIKKE_BRONZ
            elif source == "silver" and target == "gold":
                received_amount = 1
            elif source == "gold" and target == "silver":
                received_amount = ALTIN_SIKKE_GUMUS
            elif source == "bronze" and target == "gold":
                received_amount = 1
            elif source == "gold" and target == "bronze":
                received_amount = ALTIN_SIKKE_BRONZ

            renderer.coin_icon(rect.x + 238, icon_y, target, 24)
            target_color = (232, 235, 242) if available else (125, 133, 146)
            target_label = (
                f"{received_amount:,}".replace(",", ".")
                + f" {currency_name(target)}"
            )
            renderer.text(target_label, rect.x + 272, rect.y + 16, target_color)

            if not available:
                renderer.text(
                    "Yetersiz bakiye", rect.right - 122, rect.y + 2,
                    (190, 132, 120),
                )

        # Persistent feedback keeps both successful and rejected transactions legible.
        feedback_color = (
            (145, 220, 165) if self.message.startswith("İşlem tamamlandı")
            else (224, 157, 135) if self.message.startswith("Yetersiz")
            else (190, 199, 214)
        )
        renderer.panel(
            pg.Rect(60, 488, 816, 32),
            (29, 38, 52),
            (91, 104, 126),
        )
        renderer.text(
            renderer.fit_text(self.message, 780),
            76, 495, feedback_color,
        )


__all__ = ["CurrencyExchangeScreen"]
