"""NPC-specific trade window for selling accepted resources to a trade partner."""

from ..renderer import GOLD, GOOD, MUTED, TEXT, TEXT_SOFT, resource_color, resource_name, unit_label
from economy import currency_name


class TradeScreen:
    scale_to_window = True
    design_size = (912, 438)

    VISIBLE_OFFERS = 6
    ROW_X, ROW_Y, ROW_W, ROW_H = 72, 208, 790, 42
    SELL_RECT = (636, 470, 220, 42)

    def __init__(self, service):
        self.service = service
        self.npc_id = None
        self.selected = 0
        self.message = "Satmak istediğin kaynağı seç."

    def set_npc(self, npc_id):
        if self.service.trade_partner_for_npc(npc_id) is None:
            raise ValueError("Bu NPC ile ticaret yapılamıyor.")
        self.npc_id = npc_id
        self.selected = 0
        self.message = "NPC'nin kabul ettiği kaynakları burada satabilirsin."

    def _quotes(self):
        if self.npc_id is None:
            return ()
        return self.service.trade_sellable_items(self.npc_id)

    def _sell(self, quotes):
        if not quotes:
            return
        resource_type, available, unit_price = quotes[self.selected]
        try:
            trade = self.service.sell_to_npc(
                self.npc_id, resource_type, quantity=1,
            )
            self.message = (
                f"1 {resource_name(resource_type)} satıldı. "
                f"+{trade.total.amount} {currency_name(trade.total.currency)}"
            )
        except (KeyError, ValueError, RuntimeError) as error:
            self.message = f"Ticaret başarısız: {error}"

    def handle(self, state):
        quotes = self._quotes()
        if quotes:
            self.selected %= len(quotes)

        if quotes and state.mouse_clicked and state.mouse_pos is not None:
            mx, my = state.mouse_pos
            if self.ROW_X <= mx <= self.ROW_X + self.ROW_W and my >= self.ROW_Y:
                row = (my - self.ROW_Y) // self.ROW_H
                if 0 <= row < self.VISIBLE_OFFERS and row < len(quotes):
                    self.selected = row
            bx, by, bw, bh = self.SELL_RECT
            if bx <= mx <= bx + bw and by <= my <= by + bh:
                self._sell(quotes)

        if quotes and (state.pressed("up") or state.pressed("down")):
            self.selected = (self.selected + (1 if state.pressed("down") else -1)) % len(quotes)
        if quotes and state.pressed("confirm"):
            self._sell(quotes)
        return None

    def render(self, renderer):
        renderer.panel(renderer.pg.Rect(36, 136, 888, 402))
        bundle = self.service.application.holder.current
        npc = bundle.social.npcs.get(self.npc_id) if self.npc_id else None
        merchant = self.service.trade_partner_for_npc(self.npc_id) if self.npc_id else None
        npc_name = npc.name if npc is not None else "NPC"
        balance = (
            self.service.balance(merchant.account_id, "gold").amount
            if merchant is not None else 0
        )
        renderer.text(f"{npc_name} ile Ticaret", 60, 154, title=True)
        renderer.text(f"Alım bütçesi: {balance} {currency_name('gold')}", 60, 192, GOLD)
        quotes = self._quotes()
        if not quotes:
            renderer.text(
                "Bu NPC'nin kabul ettiği satılabilir kaynağın şu anda yok.",
                64, 244, MUTED,
            )
        for index, (resource_type, available, unit_price) in enumerate(quotes[:self.VISIBLE_OFFERS]):
            y = self.ROW_Y + index * self.ROW_H
            selected = index == self.selected
            if selected:
                renderer.panel(
                    renderer.pg.Rect(self.ROW_X, y, self.ROW_W, self.ROW_H - 4),
                    (55, 75, 105),
                )
            renderer.text(
                resource_name(resource_type), self.ROW_X + 12, y + 8,
                resource_color(resource_type),
            )
            renderer.text(
                f"Stok: {available} {unit_label('item')}",
                self.ROW_X + 340, y + 8, TEXT_SOFT,
            )
            renderer.text(
                f"Birim: {unit_price.amount} {currency_name(unit_price.currency)}",
                self.ROW_X + 530, y + 8, GOLD,
            )
        bx, by, bw, bh = self.SELL_RECT
        renderer.button(renderer.pg.Rect(bx, by, bw, bh), "1 Adet Sat", selected=bool(quotes))
        renderer.text(self.message, 64, 526, GOOD if "satıldı" in self.message else MUTED)
