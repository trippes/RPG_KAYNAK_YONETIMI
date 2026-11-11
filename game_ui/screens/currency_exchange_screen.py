"""Royal Mint currency exchange window using the dedicated fantasy frame asset."""

from pathlib import Path

from core.constants import (
    ALTIN_SIKKE_BRONZ,
    ALTIN_SIKKE_GUMUS,
    GUMUS_SIKKE_BRONZ,
)
from economy import currency_name


class CurrencyExchangeScreen:
    scale_to_window = True
    transparent_window_background = True
    custom_close_button = True
    close_size = 48
    design_size = (768, 512)

    BACKGROUND_NAME = "royal_mint_exchange_frame.png"
    OPTIONS = (
        (GUMUS_SIKKE_BRONZ, "bronze", "silver"),
        (1, "silver", "bronze"),
        (ALTIN_SIKKE_GUMUS, "silver", "gold"),
        (1, "gold", "silver"),
        (ALTIN_SIKKE_BRONZ, "bronze", "gold"),
        (1, "gold", "bronze"),
    )
    DENOMINATION_NAMES = {"bronze": "Bronz", "silver": "Gümüş", "gold": "Altın"}
    CARD_RECTS = (
        (80, 201, 205, 107), (290, 201, 205, 107), (500, 201, 205, 107),
        (80, 315, 205, 107), (290, 315, 205, 107), (500, 315, 205, 107),
    )
    BALANCE_CENTERS = (230, 414, 598)

    def __init__(self, service):
        self.service = service
        self.selected = 0
        self.message = "Bir işlem seç. Enter ile dönüştür."
        self._background = None
        self._background_attempted = False

    def _load_background(self, pg):
        if self._background is not None or self._background_attempted:
            return self._background
        self._background_attempted = True
        try:
            asset = Path(__file__).resolve().parents[1] / "assets" / self.BACKGROUND_NAME
            self._background = pg.image.load(str(asset))
        except (AttributeError, OSError, RuntimeError):
            self._background = None
        return self._background

    def _draw_background(self, renderer):
        image = self._load_background(renderer.pg)
        if image is None:
            renderer.surface.fill((13, 20, 34))
            return
        scale = getattr(renderer.surface, "_scale", 1.0)
        target = getattr(renderer.surface, "_surface", renderer.surface)
        size = (
            max(1, round(self.design_size[0] * scale)),
            max(1, round(self.design_size[1] * scale)),
        )
        try:
            artwork = renderer.pg.transform.smoothscale(image, size)
        except (AttributeError, TypeError, ValueError):
            artwork = image
        target.blit(artwork, (0, 0))

    def _balance(self, currency):
        try:
            return self.service.balance("hero", currency).amount
        except (KeyError, TypeError, ValueError, RuntimeError):
            return 0

    def _has_funds(self, index):
        amount, source, _target = self.OPTIONS[index]
        return self._balance(source) >= amount

    def _received_amount(self, amount, source, target):
        if source == "bronze" and target == "silver":
            return amount // GUMUS_SIKKE_BRONZ
        if source == "silver" and target == "bronze":
            return amount * GUMUS_SIKKE_BRONZ
        if source == "silver" and target == "gold":
            return amount // ALTIN_SIKKE_GUMUS
        if source == "gold" and target == "silver":
            return amount * ALTIN_SIKKE_GUMUS
        if source == "bronze" and target == "gold":
            return amount // ALTIN_SIKKE_BRONZ
        if source == "gold" and target == "bronze":
            return amount * ALTIN_SIKKE_BRONZ
        return amount

    @staticmethod
    def _number(value):
        return f"{value:,}".replace(",", ".")

    def _exchange(self, index):
        amount, source, target = self.OPTIONS[index]
        if not self._has_funds(index):
            self.message = (
                f"Yetersiz bakiye: {self._number(amount)} "
                f"{currency_name(source)} gerekiyor."
            )
            return
        try:
            received = self.service.exchange_currency("hero", source, target, amount)
            self.message = (
                f"İşlem tamamlandı: {self._number(amount)} "
                f"{currency_name(source)} → {self._number(received.amount)} "
                f"{currency_name(target)}."
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
        """Draw currency values and interaction feedback over the supplied frame."""
        self._draw_background(renderer)
        pg = renderer.pg
        title = "KRALİYET DARPHANESİ"
        renderer.text(
            title, 384 - renderer.text_width(title, title=True) // 2,
            91, title=True, max_width=430,
        )
        rates = (
            f"{GUMUS_SIKKE_BRONZ} BRONZ = 1 GÜMÜŞ"
            f"     •     {ALTIN_SIKKE_GUMUS} GÜMÜŞ = 1 ALTIN"
        )
        renderer.text(rates, 384 - renderer.text_width(rates) // 2, 119, (239, 205, 137))

        for center, currency in zip(self.BALANCE_CENTERS, ("bronze", "silver", "gold")):
            amount = self._number(self._balance(currency))
            renderer.text(
                amount, center - renderer.text_width(amount) // 2,
                160, (248, 226, 190),
            )

        for index, bounds in enumerate(self.CARD_RECTS):
            amount, source, target = self.OPTIONS[index]
            rect = pg.Rect(*bounds)
            selected = index == self.selected
            available = self._has_funds(index)
            if selected or renderer.hovered(rect):
                border = (255, 224, 151) if available else (224, 151, 132)
                pg.draw.rect(
                    renderer.surface, border,
                    pg.Rect(rect.x + 3, rect.y + 3, rect.width - 6, rect.height - 6),
                    2, border_radius=9,
                )
            received = self._received_amount(amount, source, target)
            label = (
                f"{self._number(amount)} {self.DENOMINATION_NAMES[source]}"
                f"  →  {self._number(received)} {self.DENOMINATION_NAMES[target]}"
            )
            if not available:
                label = "Bakiye yetersiz"
            label = renderer.fit_text(label, rect.width - 30)
            color = (248, 225, 190) if available else (177, 151, 139)
            renderer.text(
                label, rect.centerx - renderer.text_width(label) // 2,
                rect.y + rect.height - 27, color,
            )

        feedback_color = (
            (174, 238, 184) if self.message.startswith("İşlem tamamlandı")
            else (245, 174, 153) if self.message.startswith("Yetersiz")
            else (239, 220, 183)
        )
        feedback = renderer.fit_text(self.message, 560)
        renderer.text(
            feedback, 384 - renderer.text_width(feedback) // 2,
            448, feedback_color,
        )


__all__ = ["CurrencyExchangeScreen"]
