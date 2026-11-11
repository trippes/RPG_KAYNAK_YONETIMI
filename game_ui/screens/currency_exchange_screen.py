"""Royal Mint currency exchange window using the dedicated fantasy frame asset."""

from pathlib import Path

from core.constants import (
    ALTIN_SIKKE_BRONZ,
    ALTIN_SIKKE_GUMUS,
    GUMUS_SIKKE_BRONZ,
)


class CurrencyExchangeScreen:
    scale_to_window = True
    transparent_window_background = True
    custom_close_button = True
    close_size = 48
    title_bar_height = 130
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
    CARD_RECTS = (
        (80, 201, 205, 107), (290, 201, 205, 107), (500, 201, 205, 107),
        (80, 315, 205, 107), (290, 315, 205, 107), (500, 315, 205, 107),
    )
    CARD_AMOUNT_OFFSETS = (58, 147)
    BALANCE_CENTERS = (230, 414, 598)

    # Only the transparent field directly behind the six exchange cards.
    EXCHANGE_FIELD = (64, 190, 640, 244)

    def __init__(self, service):
        self.service = service
        self.selected = 0
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

    def _fill_exchange_field(self, renderer, target, scale):
        """Color only the transparent area behind the exchange cards."""
        pg = renderer.pg
        x, y, width, height = self.EXCHANGE_FIELD
        field = pg.Rect(
            round(x * scale), round(y * scale),
            max(1, round(width * scale)), max(1, round(height * scale)),
        )
        palette = (
            (12, 22, 39),
            (16, 31, 53),
            (20, 39, 63),
            (24, 43, 66),
            (19, 35, 58),
            (14, 27, 47),
        )
        band_height = max(1, field.height // len(palette))
        try:
            for index, color in enumerate(palette):
                top = field.y + index * band_height
                band = pg.Rect(
                    field.x, top, field.width,
                    field.bottom - top if index == len(palette) - 1 else band_height,
                )
                pg.draw.rect(target, color, band)
        except (AttributeError, TypeError, ValueError, RuntimeError):
            pg.draw.rect(target, palette[1], field)

    def _draw_background(self, renderer):
        image = self._load_background(renderer.pg)
        if image is None:
            return
        scale = getattr(renderer.surface, "_scale", 1.0)
        target = getattr(renderer.surface, "_surface", renderer.surface)
        self._fill_exchange_field(renderer, target, scale)
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
        if self._balance(source) < amount:
            return
        try:
            self.service.exchange_currency("hero", source, target, amount)
        except (KeyError, TypeError, ValueError, RuntimeError):
            return

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
        """Draw balances and coin-aligned amounts over the supplied frame."""
        self._draw_background(renderer)
        pg = renderer.pg
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
            values = (amount, received)
            color = (248, 225, 190) if available else (177, 151, 139)
            for offset, value in zip(self.CARD_AMOUNT_OFFSETS, values):
                label = self._number(value)
                renderer.text(
                    label,
                    rect.x + offset - renderer.text_width(label) // 2,
                    rect.y + rect.height - 27,
                    color,
                )


__all__ = ["CurrencyExchangeScreen"]
