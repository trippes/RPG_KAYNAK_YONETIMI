from ..renderer import (
    BAD, BUTTON_FILL, BUTTON_HOVER, BUTTON_SELECTED, GOLD, GOOD, HIGHLIGHT, MUTED,
    PANEL_BORDER, TEXT, TEXT_SOFT, ResponsiveLayout, duration_label, resource_color,
    resource_name, unit_label,
)


class InventoryScreen:
    """RPG-style inventory with equipment, item grid and detail panel."""
    responsive_layout = True
    min_window_width = 760
    min_window_height = 470


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
        self.slot_order = []
        self.drag_index = None
        self.drag_position = None
        self.drag_moved = False
        self.viewport_width = 912
        self.viewport_height = 438

    def set_viewport(self, width, height):
        self.viewport_width = max(1, int(width))
        self.viewport_height = max(1, int(height))

    def _layout(self):
        outer = (24, 126, max(1, self.viewport_width - 48), max(1, self.viewport_height - 16))
        inner = ResponsiveLayout.inset(outer, 24, 110, 24, 18)
        equipment_width = max(190, round(inner[2] * 0.28))
        detail_width = max(170, round(inner[2] * 0.25))
        grid_width = max(1, inner[2] - equipment_width - detail_width - 24)
        columns = ResponsiveLayout.split_columns(
            inner, (equipment_width, grid_width, detail_width), gap=12
        )
        equipment, grid, detail = columns
        slot_rects, slot_columns, slot_size = ResponsiveLayout.grid(
            (grid[0] + 4, grid[1] + 4, max(1, grid[2] - 8), max(1, grid[3] - 58)),
            20, min_cell=48, max_cell=60, gap=6,
        )
        tab_gap = 8
        tab_width = max(1, (outer[2] - 48 - tab_gap * (len(self.TABS) - 1)) // len(self.TABS))
        tabs = tuple(
            (outer[0] + 24 + index * (tab_width + tab_gap), outer[1] + 64, tab_width, 34)
            for index in range(len(self.TABS))
        )
        return {
            "outer": outer, "tabs": tabs, "equipment": equipment,
            "grid": grid, "detail": detail, "slot_rects": slot_rects,
            "slot_columns": slot_columns, "slot_size": slot_size,
        }

    @property
    def pointer_capture(self):
        return self.drag_index is not None

    def _items(self):
        return list(self.service.inventory(self.inventory_id).items)

    def _entries(self):
        snapshot = self.service.inventory(self.inventory_id)
        entries = (
            [("item", item_id, amount) for item_id, amount in snapshot.items]
            + [("resource", resource, amount) for resource, amount, _unit in snapshot.stocks]
        )
        by_key = {self._entry_key(entry): entry for entry in entries}
        order = list(self.slot_order)
        if not order:
            order = list(by_key)
        order = [key if key in by_key else None for key in order[:20]]
        for key in by_key:
            if key not in order:
                try:
                    order[order.index(None)] = key
                except ValueError:
                    if len(order) < 20:
                        order.append(key)
        self.slot_order = order[:20]
        return [by_key[key] for key in self.slot_order if key is not None]

    def _slot_entries(self):
        entries = self._entries()
        by_key = {self._entry_key(entry): entry for entry in entries}
        return [
            by_key.get(key) if key is not None else None
            for key in self.slot_order
        ] + [None] * max(0, 20 - len(self.slot_order))

    @staticmethod
    def _entry_key(entry):
        kind, entry_id, _amount = entry
        return kind, str(getattr(entry_id, "value", entry_id))

    def _slot_rects(self, renderer=None):
        values = self._layout()["slot_rects"]
        return (
            tuple(renderer.pg.Rect(value) for value in values)
            if renderer is not None else values
        )

    def _slot_at(self, position, renderer=None):
        return next(
            (index for index, rect in enumerate(self._slot_rects(renderer))
             if (
                 rect.collidepoint(position)
                 if renderer is not None
                 else rect[0] <= position[0] < rect[0] + rect[2]
                 and rect[1] <= position[1] < rect[1] + rect[3]
             )),
            None,
        )

    def _begin_drag(self, index, position):
        self.drag_index = index
        self.drag_position = position
        self.drag_moved = False

    def _finish_drag(self, target_index):
        source_index = self.drag_index
        self.drag_index = None
        self.drag_position = None
        self.drag_moved = False
        if source_index is None or target_index is None:
            return
        slot_entries = self._slot_entries()
        if source_index >= len(slot_entries) or target_index >= 20:
            return
        order = list(self.slot_order)
        if target_index >= len(order):
            order.extend([None] * (target_index + 1 - len(order)))
        source_key = order[source_index]
        target_key = order[target_index]
        if source_key is None:
            return
        if target_key is None:
            order[target_index] = source_key
            order[source_index] = None
        else:
            order[source_index], order[target_index] = target_key, source_key
        self.slot_order = order[:20]
        self.selected = target_index

    def dragged_item_payload(self):
        """Return the item stack currently being dragged, if it is transferable."""
        if self.drag_index is None:
            return None
        entries = self._slot_entries()
        if self.drag_index >= len(entries):
            return None
        entry = entries[self.drag_index]
        if entry is None:
            return None
        kind, item_id, quantity = entry
        if kind != "item":
            return None
        return {"item_id": item_id, "quantity": quantity}

    def cancel_drag(self):
        """Release pointer capture after a drop handled by another window."""
        self.drag_index = None
        self.drag_position = None
        self.drag_moved = False

    def _selected_item(self):
        entries = self._slot_entries()
        if self.selected >= len(entries) or entries[self.selected] is None:
            return None
        kind, entry_id, _amount = entries[self.selected]
        return self.service.item(entry_id) if kind == "item" else None

    def handle(self, state):
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
            self.selected %= 20
        if state.mouse_clicked and state.mouse_pos is not None:
            x, y = state.mouse_pos
            for index, rect in enumerate(self._layout()["tabs"]):
                if rect[0] <= x <= rect[0] + rect[2] and rect[1] <= y <= rect[1] + rect[3]:
                    self.tab = index
                    return None
            slot = self._slot_at(state.mouse_pos)
            if slot is not None and slot < len(self._slot_entries()) and self._slot_entries()[slot] is not None:
                self.selected = slot
                self._begin_drag(slot, state.mouse_pos)
        if self.drag_index is not None and state.mouse_motion and state.mouse_pos is not None:
            self.drag_position = state.mouse_pos
            self.drag_moved = True
        if self.drag_index is not None and state.mouse_button_up:
            target = self._slot_at(state.mouse_pos) if state.mouse_pos else None
            if self.drag_moved:
                self._finish_drag(target)
            else:
                self.drag_index = None
                self.drag_position = None
                self.drag_moved = False
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
        entries = self._entries()
        slot_entries = self._slot_entries()
        layout = self._layout()
        outer = renderer.pg.Rect(layout["outer"])
        equipment_rect = renderer.pg.Rect(layout["equipment"])
        grid_rect = renderer.pg.Rect(layout["grid"])
        detail_rect = renderer.pg.Rect(layout["detail"])

        renderer.panel(outer, (25, 31, 43), (145, 118, 70))
        renderer.text("Envanter", outer.x + 20, outer.y + 14, GOLD, title=True)
        renderer.text(f"{len(entries)} eşya / kaynak", outer.x + 20, outer.y + 48, MUTED)
        for index, label in enumerate(self.TABS):
            rect = renderer.pg.Rect(layout["tabs"][index])
            renderer.button(rect, label, selected=index == self.tab)

        renderer.panel(equipment_rect, (32, 40, 54), PANEL_BORDER)
        renderer.text(stats.get("name", "Kahraman"), equipment_rect.x + 12,
                      equipment_rect.y + 10, TEXT, title=True,
                      max_width=max(40, equipment_rect.width - 24))
        renderer.text(f"Seviye {stats.get('level', 1)}", equipment_rect.x + 12,
                      equipment_rect.y + 44, GOLD)
        silhouette_width = min(70, max(36, equipment_rect.width // 3))
        silhouette_height = min(92, max(54, equipment_rect.height // 3))
        silhouette = renderer.pg.Rect(
            equipment_rect.centerx - silhouette_width // 2,
            equipment_rect.y + 82, silhouette_width, silhouette_height,
        )
        renderer.pg.draw.rect(renderer.surface, (52, 65, 82), silhouette, border_radius=14)
        renderer.pg.draw.circle(
            renderer.surface, (190, 150, 112),
            (silhouette.centerx, silhouette.y - 14), max(10, silhouette_width // 4),
        )
        renderer.pg.draw.rect(
            renderer.surface, (65, 98, 137),
            (silhouette.x + silhouette_width // 4, silhouette.y + silhouette_height // 4,
             max(1, silhouette_width // 2), max(1, silhouette_height * 3 // 5)),
            border_radius=8,
        )
        equipment_rows_y = silhouette.bottom + 14
        equipment_slot_width = max(1, (equipment_rect.width - 28) // 2)
        for index, (slot, label) in enumerate(self.SLOTS):
            column = index // 4
            row = index % 4
            rect = renderer.pg.Rect(
                equipment_rect.x + 8 + column * (equipment_slot_width + 4),
                equipment_rows_y + row * 34,
                equipment_slot_width, 29,
            )
            equipped = equipment.get(slot)
            equipped_item = self.service.item(equipped) if equipped else None
            equipped_name = equipped_item.name if equipped_item else (equipped or label)
            renderer.panel(
                rect, (71, 58, 38) if equipped else (39, 49, 64),
                HIGHLIGHT if equipped else PANEL_BORDER,
            )
            renderer.text(
                equipped_name, rect.x + 5, rect.y + 7,
                GOLD if equipped else MUTED, max_width=max(1, rect.width - 10),
            )

        renderer.panel(grid_rect, (32, 40, 54), PANEL_BORDER)
        slot_rects = self._slot_rects(renderer)
        for index, rect in enumerate(slot_rects):
            hovered = renderer.hovered(rect)
            entry = slot_entries[index]
            selected = index == self.selected and entry is not None
            dragging_source = index == self.drag_index
            fill = BUTTON_HOVER if hovered else (
                BUTTON_SELECTED if selected else (29, 38, 52)
            )
            border = (
                (240, 190, 90) if dragging_source
                else HIGHLIGHT if selected
                else (115, 135, 160) if hovered
                else PANEL_BORDER
            )
            renderer.panel(rect, fill, border)
            if entry is None:
                continue
            kind, entry_id, amount = entry
            item = self.service.item(entry_id) if kind == "item" else None
            color = resource_color(entry_id)
            icon_radius = max(10, rect.width // 4)
            icon_center = (rect.centerx, rect.y + rect.height // 2 - 4)
            renderer.pg.draw.circle(renderer.surface, color, icon_center, icon_radius)
            renderer.pg.draw.circle(renderer.surface, (225, 225, 225), icon_center, icon_radius, 2)
            amount_text = str(amount)
            renderer.text(amount_text, rect.right - renderer.text_width(amount_text) - 4,
                          rect.y + 3, GOLD, max_width=max(1, rect.width - 8))
            label = item.name if item is not None else resource_name(entry_id)
            renderer.text(label, rect.x + 3, rect.bottom - 17, TEXT_SOFT,
                          max_width=max(1, rect.width - 6))

        if self.drag_index is not None and self.drag_position is not None:
            entry = slot_entries[self.drag_index] if self.drag_index < len(slot_entries) else None
            if entry is not None:
                kind, entry_id, amount = entry
                color = resource_color(entry_id)
                renderer.pg.draw.circle(renderer.surface, color, self.drag_position, 22)
                renderer.pg.draw.circle(renderer.surface, HIGHLIGHT, self.drag_position, 22, 2)
                renderer.text(str(amount), self.drag_position[0] + 8,
                              self.drag_position[1] + 8, GOLD)

        renderer.panel(detail_rect, (32, 40, 54), PANEL_BORDER)
        item = self._selected_item()
        detail_x = detail_rect.x + 12
        detail_width = max(1, detail_rect.width - 24)
        if item is None:
            renderer.text("Kaynak seçildi", detail_x, detail_rect.y + 16, MUTED,
                          title=True, max_width=detail_width)
            renderer.wrapped_text(
                "Kuşanılabilir bir eşya seçmek için ızgaradan bir kart seçin.",
                detail_x, detail_rect.y + 68, detail_width, TEXT_SOFT,
                line_height=20, max_lines=4,
            )
        else:
            renderer.text(item.name, detail_x, detail_rect.y + 16, GOLD,
                          title=True, max_width=detail_width)
            renderer.text(
                "Kuşanılabilir eşya" if item.equippable else "Eşya",
                detail_x, detail_rect.y + 52, TEXT_SOFT,
            )
            description_y = renderer.wrapped_text(
                item.description or "Bu eşyanın özel açıklaması yok.",
                detail_x, detail_rect.y + 82, detail_width, MUTED,
                line_height=20, max_lines=3,
            )
            stat_rows = (
                ("Saldırı", item.attack), ("Savunma", item.defense),
                ("Hasar", item.damage), ("Maks. Can", item.max_hit_points),
            )
            for row, (label, value) in enumerate(stat_rows):
                y = description_y + 8 + row * 22
                if y + 20 > detail_rect.bottom - 28:
                    break
                renderer.text(label, detail_x, y, TEXT_SOFT)
                renderer.text(f"+{value}", detail_rect.right - 54, y, GOOD)

        footer_y = outer.bottom - 42
        renderer.text(f"Ağırlık  {snapshot.weight:.1f} / 80.0",
                      grid_rect.x + 8, footer_y, TEXT_SOFT)
        bar_width = max(1, grid_rect.width - 16)
        renderer.bar(
            renderer.pg.Rect(grid_rect.x + 8, footer_y + 22, bar_width, 8),
            min(1.0, snapshot.weight / 80.0), GOLD,
        )
        activity = self.service.actor_activity("hero")
        if activity is not None and activity.state == "running" and activity.end_tick is not None:
            remaining = max(0, activity.end_tick - self.service.state().simulation_tick)
            renderer.text(
                f"Toplama sürüyor: {duration_label(remaining)} kaldı",
                grid_rect.x + 8, outer.bottom - 16, GOOD,
            )
