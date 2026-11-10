"""Movable fantasy-style window for inspecting and transferring container contents."""

from ..renderer import (
    GOLD, TEXT, TEXT_SOFT, MUTED, GOOD, WARN, BAD,
    PANEL_BORDER, STRIP_BORDER,
)
from application import GameplayServiceError


class ContainerScreen:
    """Compact two-pane container window with capacity bars and safe transfers."""

    def __init__(self, service):
        self.service = service
        self.container_id = None
        self.active_side = "container"
        self.selected_index = 0
        self.message = "Bir eşya seçin. Enter: taşı"
        self._row_rects = ()
        self._action_rects = {}

    def set_container(self, container_id):
        if not isinstance(container_id, str) or not container_id.strip():
            raise ValueError("container_id is required.")
        self.container_id = container_id
        self.active_side = "container"
        self.selected_index = 0
        self.message = "Sandık incelenmeye hazır."

    def _actor_context(self):
        actors = self.service.state().actors
        if not actors:
            raise GameplayServiceError("Aktif bir karakter bulunamadı.")
        actor = actors[0]
        if actor.inventory_id is None:
            raise GameplayServiceError("Karakterin envanteri henüz bağlanmamış.")
        return actor.actor_id, actor.inventory_id

    def _player_items(self, inventory_id):
        return self.service.inventory(inventory_id).items

    def _container_items(self, view):
        return view.items

    def _items_for_side(self, view, inventory_id):
        return self._container_items(view) if self.active_side == "container" else self._player_items(inventory_id)

    def _find_tool(self, inventory_id, allowed_tags):
        if not allowed_tags:
            return None
        for item_id, quantity in self._player_items(inventory_id):
            if quantity < 1:
                continue
            item = self.service.item(item_id)
            if item is not None and set(item.tags).intersection(allowed_tags):
                return item_id
        return None

    @staticmethod
    def _format_attempt(result):
        if not result.attempted:
            return result.message
        verdict = "BAŞARILI" if result.success else "BAŞARISIZ"
        return f"{verdict} — d20: {result.roll} + {result.modifier} = {result.total} / DC {result.difficulty_class}"

    @staticmethod
    def _draw_chest_emblem(renderer, x, y):
        """Draw a small chest motif using native UI primitives (no external asset)."""
        pg = renderer.pg
        body = pg.Rect(x, y + 18, 66, 42)
        pg.draw.rect(renderer.surface, (91, 57, 31), body, border_radius=6)
        pg.draw.rect(renderer.surface, (181, 132, 69), body, 3, border_radius=6)
        lid = pg.Rect(x - 3, y + 8, 72, 22)
        pg.draw.rect(renderer.surface, (126, 82, 42), lid, border_radius=7)
        pg.draw.rect(renderer.surface, (205, 163, 91), lid, 2, border_radius=7)
        pg.draw.line(renderer.surface, (207, 174, 111), (x + 32, y + 12), (x + 32, y + 58), 3)
        pg.draw.rect(renderer.surface, (222, 190, 112), pg.Rect(x + 27, y + 30, 12, 16), border_radius=3)
        pg.draw.circle(renderer.surface, (65, 45, 28), (x + 33, y + 37), 2)

    @staticmethod
    def _capacity_bar(renderer, x, y, width, label, current, maximum, unit):
        renderer.text(label, x, y, TEXT_SOFT)
        if maximum is None:
            ratio, value = 0.0, f"{current:.1f} {unit} / Sınırsız"
        else:
            ratio = current / maximum if maximum > 0 else (1.0 if current > 0 else 0.0)
            value = f"{current:.1f} / {maximum:.1f} {unit}"
        renderer.text(value, x, y + 22, MUTED, max_width=width)
        color = BAD if maximum is not None and ratio >= 1 else GOLD
        renderer.bar(renderer.pg.Rect(x, y + 47, width, 9), ratio, color)

    def handle(self, state):
        if self.container_id is None:
            return None
        try:
            actor_id, inventory_id = self._actor_context()
            lock = self.service.container_lock_state(self.container_id)
            try:
                view = self.service.open_container(actor_id, inventory_id, self.container_id)
            except GameplayServiceError:
                action = None
                if state.mouse_clicked and state.mouse_pos is not None:
                    for action_name, rect in self._action_rects.items():
                        if rect.collidepoint(state.mouse_pos):
                            action = action_name
                            break
                if state.pressed("lockpick"):
                    action = "lockpick"
                elif state.pressed("force_lock"):
                    action = "force"
                elif state.pressed("confirm") and lock is not None and lock.required_key_id:
                    action = "key"
                if lock is not None and lock.locked and action == "key":
                    self.message = (
                        "Kilit anahtarla açıldı."
                        if self.service.unlock_with_key(actor_id, inventory_id, lock.lock_id, lock.required_key_id)
                        else "Uygun anahtar bulunamadı veya anahtar size ait değil."
                    )
                elif lock is not None and lock.locked and not lock.jammed and not lock.broken and action == "lockpick":
                    tool_id = self._find_tool(inventory_id, lock.lockpick_allowed_tool_tags)
                    result = self.service.resolve_lockpick(actor_id, inventory_id, lock.lock_id, tool_item_id=tool_id)
                    self.message = self._format_attempt(result)
                elif lock is not None and lock.locked and not lock.jammed and not lock.broken and action == "force":
                    tool_id = self._find_tool(inventory_id, lock.force_required_tool_tags)
                    result = self.service.resolve_force_lock(actor_id, inventory_id, lock.lock_id, tool_item_id=tool_id)
                    self.message = self._format_attempt(result)
                elif lock is not None and lock.jammed:
                    self.message = "Kilit sıkışmış. Önce kilidin durumunu çözmelisiniz."
                elif lock is not None and lock.broken and lock.locked:
                    self.message = "Kilit hasarlı ve kapalı durumda."
                elif action is None:
                    self.message = "Konteyner kilitli."
                return None

            items = self._items_for_side(view, inventory_id)
            if state.pressed("left") or state.pressed("right"):
                self.active_side = "player" if self.active_side == "container" else "container"
                self.selected_index = 0
                items = self._items_for_side(view, inventory_id)
            if items and state.pressed("up"):
                self.selected_index = (self.selected_index - 1) % len(items)
            if items and state.pressed("down"):
                self.selected_index = (self.selected_index + 1) % len(items)
            if state.mouse_clicked and state.mouse_pos is not None:
                for index, rect in enumerate(self._row_rects):
                    if rect.collidepoint(state.mouse_pos):
                        self.selected_index = index
                        break
            if state.pressed("confirm") and items:
                item_id, _quantity = items[self.selected_index]
                if self.active_side == "container":
                    self.service.transfer_actor_item_from_container(actor_id, inventory_id, self.container_id, item_id, 1)
                    self.message = "Eşya çantaya aktarıldı."
                else:
                    self.service.transfer_actor_item_to_container(actor_id, inventory_id, self.container_id, item_id, 1)
                    self.message = "Eşya sandığa yerleştirildi."
                self.selected_index = 0
        except (KeyError, ValueError, RuntimeError) as error:
            self.message = f"İşlem yapılamadı: {error}"
        return None

    def _render_locked(self, renderer, lock):
        self._action_rects = {}
        renderer.panel(renderer.pg.Rect(40, 140, 724, 350), (29, 36, 49), (130, 102, 61))
        self._draw_chest_emblem(renderer, 680, 155)
        renderer.text("KİLİTLİ SANDIK", 62, 158, GOLD, title=True)
        status = "Sıkışmış" if lock and lock.jammed else "Hasarlı" if lock and lock.broken else "Kilitli"
        renderer.chip(62, 210, f"Durum: {status}", WARN)
        renderer.wrapped_text(
            "İçindekiler kilit açılana kadar gizli. Sandığı açmak için uygun bir yöntem seçin.",
            62, 252, 570, TEXT_SOFT, line_height=25, max_lines=2,
        )
        if lock is not None and lock.required_key_id:
            renderer.text("Anahtar", 62, 318, GOLD)
            renderer.text(f"Gerekli anahtar: {lock.required_key_id}", 62, 346, TEXT_SOFT)
            key_rect = renderer.pg.Rect(62, 386, 210, 44)
            renderer.action_button(key_rect, "ENTER", "Anahtarla aç")
            self._action_rects["key"] = key_rect
        if lock is not None and lock.lockpick_profile_id:
            renderer.text(
                f"Maymunculuk  •  Beceri {lock.lockpick_minimum_skill}+  •  DC {lock.lockpick_difficulty_class}",
                300, 318, TEXT_SOFT, max_width=440,
            )
            pick_rect = renderer.pg.Rect(300, 386, 210, 44)
            renderer.action_button(pick_rect, "T", "Maymunculuk dene")
            self._action_rects["lockpick"] = pick_rect
        if lock is not None and lock.force_profile_id:
            renderer.text(
                f"Zorlama  •  Güç {lock.force_minimum_strength}+  •  DC {lock.force_difficulty_class}",
                300, 350, TEXT_SOFT, max_width=440,
            )
            force_rect = renderer.pg.Rect(526, 386, 210, 44)
            renderer.action_button(force_rect, "F", "Kilidi zorla")
            self._action_rects["force"] = force_rect
        renderer.text(self.message, 62, 456, GOOD if "BAŞARILI" in self.message or "açıldı" in self.message else WARN)
        renderer.footer("Enter: anahtar   T: maymuncuk   F: zorla   X: pencereyi kapat")

    @staticmethod
    def _grid_slot_rects(renderer, origin_x, origin_y):
        """Return a fixed 5x3 inventory grid, including empty slot positions."""
        size, step_x, step_y = 62, 74, 78
        return tuple(
            renderer.pg.Rect(
                origin_x + (index % 5) * step_x,
                origin_y + (index // 5) * step_y,
                size,
                size,
            )
            for index in range(15)
        )

    @staticmethod
    def _draw_empty_slot(renderer, rect, selected=False, hovered=False):
        pg = renderer.pg
        border = GOLD if selected else (119, 91, 58) if hovered else (77, 66, 55)
        fill = (48, 39, 32) if selected else (28, 27, 27)
        pg.draw.rect(renderer.surface, (12, 12, 14),
                     pg.Rect(rect.x + 3, rect.y + 4, rect.width, rect.height), border_radius=7)
        pg.draw.rect(renderer.surface, fill, rect, border_radius=7)
        pg.draw.rect(renderer.surface, border, rect, 2, border_radius=7)
        inset = rect.inflate(-8, -8)
        pg.draw.rect(renderer.surface, (54, 46, 39), inset, 1, border_radius=5)
        cx, cy = rect.center
        pg.draw.line(renderer.surface, (67, 57, 47), (cx, cy - 9), (cx + 8, cy), 1)
        pg.draw.line(renderer.surface, (67, 57, 47), (cx + 8, cy), (cx, cy + 9), 1)
        pg.draw.line(renderer.surface, (67, 57, 47), (cx, cy + 9), (cx - 8, cy), 1)
        pg.draw.line(renderer.surface, (67, 57, 47), (cx - 8, cy), (cx, cy - 9), 1)

    @staticmethod
    def _draw_item_icon(renderer, item, rect):
        """Draw a compact category silhouette until Content Editor supplies item art."""
        pg = renderer.pg
        surface = renderer.surface
        category = str(getattr(item, "category", "misc")).lower()
        tags = {str(tag).lower() for tag in getattr(item, "tags", ())}
        name = str(getattr(item, "name", "")).lower()
        cx, cy = rect.center
        gold = (221, 183, 111)
        light = (222, 210, 181)
        dark = (89, 58, 36)
        if any(word in category or word in name for word in ("weapon", "sword", "blade")) or tags.intersection({"weapon", "melee"}):
            pg.draw.polygon(surface, light, [(cx, cy - 20), (cx + 8, cy + 5), (cx, cy + 12), (cx - 7, cy + 5)])
            pg.draw.line(surface, gold, (cx, cy + 8), (cx, cy + 23), 4)
            pg.draw.line(surface, dark, (cx - 9, cy + 11), (cx + 9, cy + 11), 4)
        elif any(word in category or word in name for word in ("armor", "shield", "armour")) or tags.intersection({"armor", "armour"}):
            pg.draw.polygon(surface, (119, 143, 151), [(cx - 18, cy - 18), (cx + 18, cy - 18), (cx + 15, cy + 5), (cx, cy + 22), (cx - 15, cy + 5)])
            pg.draw.polygon(surface, gold, [(cx, cy - 12), (cx + 10, cy - 8), (cx + 8, cy + 4), (cx, cy + 14), (cx - 8, cy + 4), (cx - 10, cy - 8)], 2)
        elif any(word in category or word in name for word in ("potion", "consum", "drink", "elixir")) or tags.intersection({"consumable", "potion"}):
            pg.draw.rect(surface, (110, 153, 173), pg.Rect(cx - 8, cy - 13, 16, 27), border_radius=5)
            pg.draw.rect(surface, gold, pg.Rect(cx - 5, cy - 21, 10, 9), border_radius=2)
            pg.draw.rect(surface, (191, 91, 75), pg.Rect(cx - 6, cy + 1, 12, 10), border_radius=3)
        elif any(word in category or word in name for word in ("food", "bread", "meal")) or tags.intersection({"food", "edible"}):
            pg.draw.ellipse(surface, (180, 128, 75), pg.Rect(cx - 19, cy - 12, 38, 26))
            pg.draw.ellipse(surface, (230, 193, 126), pg.Rect(cx - 14, cy - 8, 28, 17), 2)
            pg.draw.line(surface, (102, 76, 49), (cx - 4, cy - 5), (cx + 5, cy + 5), 2)
        else:
            pg.draw.polygon(surface, (116, 135, 151), [(cx, cy - 20), (cx + 16, cy - 3), (cx + 9, cy + 17), (cx - 9, cy + 17), (cx - 16, cy - 3)])
            pg.draw.polygon(surface, gold, [(cx, cy - 12), (cx + 9, cy - 2), (cx + 5, cy + 11), (cx - 5, cy + 11), (cx - 9, cy - 2)], 2)

    def render(self, renderer):
        if self.container_id is None:
            renderer.text("Bir sandık seçilmedi.", 52, 154, MUTED)
            return
        try:
            actor_id, inventory_id = self._actor_context()
            lock = self.service.container_lock_state(self.container_id)
            try:
                view = self.service.open_container(actor_id, inventory_id, self.container_id)
            except GameplayServiceError:
                self._render_locked(renderer, lock)
                return

            container_items = list(self._container_items(view))
            player_items = list(self._player_items(inventory_id))
            outer = renderer.pg.Rect(40, 140, 880, 500)
            renderer.panel(outer, (24, 20, 18), (163, 119, 64))
            inner = renderer.pg.Rect(46, 146, 868, 488)
            renderer.panel(inner, (34, 29, 26), (91, 68, 47))

            # Header: title, state and sorting affordance.
            self._draw_chest_emblem(renderer, 836, 151)
            renderer.text(view.name.upper(), 64, 154, GOLD, title=True, max_width=700)
            renderer.chip(64, 205, "AÇIK", GOOD)
            renderer.text("SANDIK KAPASİTESİ", 64, 239, GOLD)
            self._capacity_bar(renderer, 64, 264, 245, "Ağırlık", view.contents_weight_kg, view.max_contents_weight_kg, "kg")
            slot_max = float(view.max_slots) if view.max_slots is not None else None
            self._capacity_bar(renderer, 350, 264, 245, "Yuvalar", float(view.contents_slots), slot_max, "slot")
            self._capacity_bar(renderer, 636, 264, 245, "Hacim", view.contents_volume_liters, view.max_contents_volume_liters, "L")

            # Two independent, always-visible 5x3 item grids.
            left_panel = renderer.pg.Rect(56, 330, 420, 294)
            right_panel = renderer.pg.Rect(484, 330, 420, 294)
            renderer.panel(left_panel, (25, 23, 22), GOLD if self.active_side == "container" else (105, 82, 59))
            renderer.panel(right_panel, (25, 23, 22), GOLD if self.active_side == "player" else (105, 82, 59))
            renderer.text("SANDIK", 74, 341, GOLD if self.active_side == "container" else TEXT_SOFT)
            renderer.text(f"{len(container_items)} eşya türü", 330, 342, MUTED)
            renderer.text("KARAKTER ÇANTASI", 502, 341, GOLD if self.active_side == "player" else TEXT_SOFT)
            renderer.text(f"{len(player_items)} eşya türü", 758, 342, MUTED)

            self._row_rects = []
            grid_specs = (
                ("container", container_items, 82),
                ("player", player_items, 510),
            )
            for side, entries, origin_x in grid_specs:
                slot_rects = self._grid_slot_rects(renderer, origin_x, 374)
                for index, rect in enumerate(slot_rects):
                    entry = entries[index] if index < len(entries) else None
                    selected = side == self.active_side and index == self.selected_index
                    hovered = renderer.hovered(rect)
                    self._draw_empty_slot(renderer, rect, selected=selected and entry is None, hovered=hovered)
                    if entry is None:
                        continue
                    item_id, amount = entry
                    item = self.service.item(item_id)
                    if selected:
                        renderer.pg.draw.rect(renderer.surface, (79, 54, 32), rect, border_radius=7)
                        renderer.pg.draw.rect(renderer.surface, GOLD, rect, 3, border_radius=7)
                        renderer.pg.draw.rect(renderer.surface, (206, 169, 103), rect.inflate(-7, -7), 1, border_radius=5)
                    else:
                        renderer.pg.draw.rect(renderer.surface, (47, 38, 31), rect, border_radius=7)
                        renderer.pg.draw.rect(renderer.surface, (119, 89, 56) if hovered else (91, 72, 52), rect, 2, border_radius=7)
                    icon_rect = rect.inflate(-10, -12)
                    self._draw_item_icon(renderer, item, icon_rect)
                    quantity_text = str(amount)
                    badge_rect = renderer.pg.Rect(rect.right - 25, rect.bottom - 21, 21, 17)
                    renderer.pg.draw.rect(renderer.surface, (13, 13, 14), badge_rect, border_radius=5)
                    renderer.pg.draw.rect(renderer.surface, (155, 119, 66), badge_rect, 1, border_radius=5)
                    renderer.text(quantity_text, badge_rect.x + 4, badge_rect.y, GOLD, max_width=14)
                    label = item.name if item is not None else str(item_id).replace("_", " ").title()
                    renderer.text(label, rect.x - 5, rect.bottom + 2, TEXT_SOFT, max_width=rect.width + 10)
                    if side == self.active_side:
                        self._row_rects.append(rect)

            if not container_items:
                renderer.text("Sandık boş", 190, 614, MUTED)
            if not player_items:
                renderer.text("Çanta boş", 644, 614, MUTED)

            renderer.text(self.message, 64, 632, GOOD if "aktarıldı" in self.message else TEXT_SOFT, max_width=820)
            renderer.footer("Sol/Sağ: envanter seç   ↑/↓: eşya seç   Enter: 1 adet taşı   Sürükle: aktar")
        except (KeyError, ValueError, RuntimeError, GameplayServiceError) as error:
            renderer.text(f"Sandık görüntülenemedi: {error}", 52, 170, WARN)



__all__ = ["ContainerScreen"]
