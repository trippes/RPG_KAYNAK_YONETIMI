from ..renderer import (
    BAD, BUTTON_FILL, BUTTON_SELECTED, GOLD, GOOD, HIGHLIGHT, MUTED,
    PANEL_BORDER, TEXT, TEXT_SOFT, duration_label, resource_color, resource_name, unit_label,
)


class InventoryScreen:
    """RPG-style inventory with equipment, item grid and detail panel."""

    TABS = ("Envanter", "Kuşanımlar", "Görev Eşyaları", "Tüketilebilir", "Diğer")
    SLOTS = (
        ("head", "Baş"), ("chest", "Gövde"), ("hands", "Eller"),
        ("legs", "Bacak"), ("feet", "Ayak"), ("main_hand", "Ana El"),
        ("off_hand", "Yan El"), ("accessory", "Aksesuar"),
    )

    def __init__(self, service, inventory_id="player"):
        self.service = service
        self.inventory_id = inventory_id
        self.tab = 0
        self.selected = 0
        self.message = "Bir eşya seçin. E: Kuşan | Enter: Kullan"

    def _items(self):
        return list(self.service.inventory(self.inventory_id).items)

    def _entries(self):
        snapshot = self.service.inventory(self.inventory_id)
        return (
            [("item", item_id, amount) for item_id, amount in snapshot.items]
            + [("resource", resource, amount) for resource, amount, _unit in snapshot.stocks]
        )

    def _selected_item(self):
        entries = self._entries()
        if not entries:
            return None
        kind, entry_id, _amount = entries[self.selected % len(entries)]
        return self.service.item(entry_id) if kind == "item" else None

    def handle(self, state):
        if state.pressed("world") or state.pressed("back"):
            return "local_map"
        if state.pressed("market"):
            return "market"
        if state.pressed("character"):
            return "character"
        if state.pressed("left"):
            self.tab = (self.tab - 1) % len(self.TABS)
        if state.pressed("right"):
            self.tab = (self.tab + 1) % len(self.TABS)
        if state.pressed("up"):
            self.selected = max(0, self.selected - 1)
        if state.pressed("down"):
            self.selected += 1
        entries = self._entries()
        if entries:
            self.selected %= len(entries)
        if state.mouse_clicked and state.mouse_pos is not None:
            x, y = state.mouse_pos
            for index in range(len(self.TABS)):
                rect = (48 + index * 142, 190, 132, 34)
                if rect[0] <= x <= rect[0] + rect[2] and rect[1] <= y <= rect[1] + rect[3]:
                    self.tab = index
                    return None
            grid_x, grid_y = 320, 236
            for index in range(min(20, len(entries))):
                column, row = index % 5, index // 5
                left, top = grid_x + column * 70, grid_y + row * 58
                if left <= x <= left + 60 and top <= y <= top + 50:
                    self.selected = index
                    break
        item = self._selected_item()
        if state.pressed("equip") and item is not None:
            try:
                self.service.equip_item("hero", self.inventory_id, item.item_id)
                self.message = f"{item.name} kuşanıldı."
            except (KeyError, ValueError, RuntimeError) as error:
                self.message = f"Kuşanılamadı: {error}"
        if state.pressed("confirm"):
            stocks = self.service.inventory(self.inventory_id).stocks
            consumable = next(
                (resource for resource, amount, _unit in stocks
                 if resource in {"bread", "water"} and amount > 0),
                None,
            )
            if consumable is None:
                self.message = "Seçili eşya kuşanılabilir veya kullanılamaz."
            else:
                try:
                    hp = self.service.consume_item("hero", self.inventory_id, consumable)
                    self.message = f"{resource_name(consumable)} tüketildi. Can: {hp}"
                except (KeyError, ValueError, RuntimeError) as error:
                    self.message = f"Tüketilemedi: {error}"
        return None

    def render(self, renderer):
        snapshot = self.service.inventory(self.inventory_id)
        stats = self.service.actor_stats("hero") or {}
        equipment = self.service.equipment("hero")
        items = self._items()
        entries = self._entries()
        renderer.frame("Envanter")
        renderer.hud(self.service)

        # Main parchment-like inventory frame.
        renderer.panel(renderer.pg.Rect(24, 126, renderer.width - 48, 430), (25, 31, 43), (145, 118, 70))
        renderer.text("Envanter", 48, 142, GOLD, title=True)
        renderer.text(
            f"{len(entries)} eşya / kaynak",
            48, 172, MUTED,
        )
        for index, label in enumerate(self.TABS):
            rect = renderer.pg.Rect(48 + index * 142, 190, 132, 34)
            renderer.button(rect, label, selected=index == self.tab)

        # Equipment pane, matching the reference's left character layout.
        renderer.panel(renderer.pg.Rect(48, 236, 250, 276), (32, 40, 54), PANEL_BORDER)
        name = stats.get("name", "Kahraman")
        level = stats.get("level", 1)
        renderer.text(name, 66, 248, TEXT, title=True, max_width=210)
        renderer.text(f"Seviye {level}", 68, 286, GOLD)
        silhouette = renderer.pg.Rect(130, 320, 86, 112)
        renderer.pg.draw.rect(renderer.surface, (52, 65, 82), silhouette, border_radius=18)
        renderer.pg.draw.circle(renderer.surface, (190, 150, 112), (173, 300), 22)
        renderer.pg.draw.rect(renderer.surface, (65, 98, 137), (145, 345, 56, 70), border_radius=10)
        for index, (slot, label) in enumerate(self.SLOTS):
            left = 60 if index < 4 else 220
            top = 306 + (index % 4) * 48
            rect = renderer.pg.Rect(left, top, 62, 38)
            equipped = equipment.get(slot)
            renderer.panel(rect, (71, 58, 38) if equipped else (39, 49, 64),
                           HIGHLIGHT if equipped else PANEL_BORDER)
            equipped_name = self.service.item(equipped).name if equipped and self.service.item(equipped) else equipped
            renderer.text(equipped_name or label, rect.x + 5, rect.y + 10, GOLD if equipped else MUTED,
                          max_width=rect.width - 10)

        # Stat strip under the character.
        stat_text = (
            f"Can {stats.get('current_hit_points', 0)}/{stats.get('max_hit_points', 0)}  "
            f"Saldırı {stats.get('attack_bonus', 0)}  "
            f"Savunma {stats.get('defense_bonus', 0)}"
        )
        renderer.text(stat_text, 62, 490, TEXT_SOFT, max_width=225)

        # Item grid.
        grid_x, grid_y = 320, 236
        for index in range(20):
            column, row = index % 5, index // 5
            rect = renderer.pg.Rect(grid_x + column * 70, grid_y + row * 58, 60, 50)
            renderer.panel(
                rect,
                BUTTON_SELECTED if index == self.selected and index < len(entries) else (29, 38, 52),
                HIGHLIGHT if index == self.selected and index < len(entries) else PANEL_BORDER,
            )
            if index >= len(entries):
                continue
            kind, entry_id, amount = entries[index]
            item = self.service.item(entry_id) if kind == "item" else None
            color = resource_color(entry_id)
            renderer.pg.draw.circle(renderer.surface, color, (rect.centerx, rect.y + 21), 15)
            renderer.text(str(amount), rect.right - 17, rect.bottom - 20, GOLD)
            label = item.name if item is not None else resource_name(entry_id)
            renderer.text(label[:9], rect.x + 4, rect.y + 34, TEXT_SOFT, max_width=52)

        # Detail pane on the right, with explicit item stats.
        detail_x = 700
        renderer.panel(renderer.pg.Rect(detail_x, 236, 220, 276), (32, 40, 54), PANEL_BORDER)
        item = self._selected_item()
        if item is None:
            renderer.text("Kaynak seçildi", detail_x + 18, 258, MUTED, title=True)
            renderer.text("Kuşanılabilir bir eşya seçmek", detail_x + 18, 312, TEXT_SOFT, max_width=180)
            renderer.text("için ızgaradan bir kart seçin.", detail_x + 18, 338, TEXT_SOFT, max_width=180)
        else:
            renderer.text(item.name, detail_x + 18, 258, GOLD, title=True, max_width=184)
            renderer.text("Kuşanılabilir eşya" if item.equippable else "Eşya", detail_x + 18, 302, TEXT_SOFT)
            renderer.wrapped_text(item.description or "Bu eşyanın özel açıklaması yok.", detail_x + 18, 332, 184, MUTED, line_height=22, max_lines=3)
            stat_rows = (
                ("Saldırı", item.attack),
                ("Savunma", item.defense),
                ("Hasar", item.damage),
                ("Maks. Can", item.max_hit_points),
            )
            for row, (label, value) in enumerate(stat_rows):
                y = 402 + row * 22
                renderer.text(label, detail_x + 18, y, TEXT_SOFT)
                renderer.text(f"+{value}", detail_x + 166, y, GOOD)
            renderer.text(f"Ağırlık  {item.weight:.1f}", detail_x + 18, 494, MUTED)

        renderer.text(f"Ağırlık  {snapshot.weight:.1f} / 80.0", 320, 520, TEXT_SOFT)
        renderer.bar(renderer.pg.Rect(320, 540, 360, 10), min(1.0, snapshot.weight / 80.0), GOLD)
        activity = self.service.actor_activity("hero")
        if activity is not None and activity.state == "running" and activity.end_tick is not None:
            remaining = max(0, activity.end_tick - self.service.state().simulation_tick)
            renderer.text(f"Toplama sürüyor: {duration_label(remaining)} kaldı", 320, 555, GOOD)
        renderer.text(renderer.fit_text(self.message, 560), 48, 580, GOLD)
        renderer.footer("←/→ Sekme   ↑/↓ Eşya   E Kuşan   Enter Kullan   M Pazar   Esc Kapat")
