"""Scrollable, filterable fantasy loot window for physical containers."""

from ..renderer import (
    GOLD, TEXT, TEXT_SOFT, MUTED, GOOD, WARN, BAD,
    PANEL_BORDER, STRIP_BORDER,
)
from application import GameplayServiceError


class ContainerScreen:
    """Chest-only loot grid with search, category filters and safe transfers."""

    COLUMNS = 6
    MIN_ROWS = 4
    SLOT_SIZE = 52
    SLOT_GAP = 8
    GRID_X = 91
    GRID_Y = 300
    GRID_VIEW = (78, 292, 764, 252)
    CATEGORIES = (
        ("all", "Tümü"),
        ("weapon", "Silah"),
        ("armor", "Zırh"),
        ("potion", "İksir"),
        ("food", "Yiyecek"),
        ("misc", "Diğer"),
    )

    def __init__(self, service):
        self.service = service
        self.container_id = None
        self.selected_index = 0
        self.message = "Sandık incelenmeye hazır."
        self.search_text = ""
        self.category = "all"
        self.sort_mode = "name"
        self._sort_rect = None
        self.scroll_row = 0
        self._row_rects = ()
        self._display_entries = ()
        self._action_rects = {}
        self._drag_item_id = None
        self._take_all_rect = None
        self._search_rect = None
        self._category_rects = {}
        self._grid_rect = None

    def set_container(self, container_id):
        if not isinstance(container_id, str) or not container_id.strip():
            raise ValueError("container_id is required.")
        self.container_id = container_id
        self.selected_index = 0
        self.scroll_row = 0
        self.search_text = ""
        self.category = "all"
        self.sort_mode = "name"
        self._sort_rect = None
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
        pg = renderer.pg
        body = pg.Rect(x, y + 18, 66, 42)
        pg.draw.rect(renderer.surface, (76, 48, 31), body, border_radius=7)
        pg.draw.rect(renderer.surface, (177, 132, 72), body, 2, border_radius=7)
        pg.draw.rect(renderer.surface, (110, 72, 39), pg.Rect(x - 3, y + 7, 72, 23), border_radius=7)
        pg.draw.rect(renderer.surface, (218, 177, 105), pg.Rect(x - 3, y + 7, 72, 23), 2, border_radius=7)
        pg.draw.line(renderer.surface, (220, 186, 119), (x + 32, y + 10), (x + 32, y + 58), 3)
        pg.draw.rect(renderer.surface, (231, 197, 125), pg.Rect(x + 26, y + 30, 13, 17), border_radius=3)
        pg.draw.circle(renderer.surface, (66, 45, 27), (x + 32, y + 37), 2)

    @property
    def pointer_capture(self):
        return self._drag_item_id is not None

    def _take_all(self, actor_id, inventory_id):
        view = self.service.open_container(actor_id, inventory_id, self.container_id)
        moved = 0
        blocked = False
        for item_id, quantity in tuple(view.items):
            try:
                self.service.transfer_actor_item_from_container(
                    actor_id, inventory_id, self.container_id, item_id, quantity
                )
                moved += quantity
            except (ValueError, RuntimeError, GameplayServiceError):
                blocked = True
        self.message = (
            f"{moved} eşya alındı; kapasite nedeniyle kalanlar sandıkta."
            if blocked else f"{moved} eşya envantere aktarıldı." if moved else "Sandık boş."
        )

    @staticmethod
    def _item_category(item):
        raw = str(getattr(item, "category", "misc")).lower()
        tags = {str(tag).lower() for tag in getattr(item, "tags", ())}
        name = str(getattr(item, "name", "")).lower()
        if raw in {"weapon", "weapons"} or tags.intersection({"weapon", "melee"}):
            return "weapon"
        if raw in {"armor", "armour"} or tags.intersection({"armor", "armour", "shield"}):
            return "armor"
        if raw in {"potion", "consumable", "elixir"} or tags.intersection({"potion", "consumable"}) or any(
            word in name for word in ("iksir", "potion", "elixir")
        ):
            return "potion"
        if raw in {"food", "provision"} or tags.intersection({"food", "provision"}) or any(
            word in name for word in ("ekmek", "yiyecek", "food")
        ):
            return "food"
        return "misc"

    def _filtered_entries(self, view):
        entries = []
        for item_id, amount in view.items:
            item = self.service.item(item_id)
            if item is None:
                continue
            category = self._item_category(item)
            if self.category != "all" and category != self.category:
                continue
            if self.search_text and self.search_text.casefold() not in item.name.casefold():
                continue
            entries.append((item_id, amount, item, category))
        entries.sort(key=lambda row: (row[3], row[2].name.casefold()))
        return tuple(entries)

    def _visible_rows(self, entry_count):
        return max(self.MIN_ROWS, (entry_count + self.COLUMNS - 1) // self.COLUMNS)

    def _max_scroll(self, entry_count):
        total_rows = self._visible_rows(entry_count)
        visible_rows = max(1, self.GRID_VIEW[3] // (self.SLOT_SIZE + self.SLOT_GAP))
        return max(0, total_rows - visible_rows)

    def _slot_rects(self, renderer, entry_count):
        pitch = self.SLOT_SIZE + self.SLOT_GAP
        first = self.scroll_row * self.COLUMNS
        count = self._visible_rows(entry_count) * self.COLUMNS
        return tuple(
            renderer.pg.Rect(
                self.GRID_X + (index % self.COLUMNS) * pitch,
                self.GRID_Y + (index // self.COLUMNS - self.scroll_row) * pitch,
                self.SLOT_SIZE, self.SLOT_SIZE,
            )
            for index in range(first, first + count)
        )

    def receive_external_item(self, item_id, quantity):
        """Accept an item stack dragged from another gameplay window."""
        if self.container_id is None:
            return False
        try:
            actor_id, inventory_id = self._actor_context()
            self.service.transfer_actor_item_to_container(
                actor_id, inventory_id, self.container_id, item_id, quantity
            )
            item = self.service.item(item_id)
            label = item.name if item is not None else str(item_id)
            self.message = f"{label} sandığa aktarıldı."
            return True
        except (KeyError, ValueError, RuntimeError, GameplayServiceError) as error:
            self.message = f"Sandığa aktarılamadı: {error}"
            return False

    def _transfer(self, actor_id, inventory_id, item_id, quantity):
        self.service.transfer_actor_item_from_container(
            actor_id, inventory_id, self.container_id, item_id, quantity
        )
        self.message = "Eşya envantere aktarıldı."

    def handle(self, state):
        if self.container_id is None:
            return None
        try:
            actor_id, inventory_id = self._actor_context()
            lock = self.service.container_lock_state(self.container_id)
            try:
                view = self.service.open_container(actor_id, inventory_id, self.container_id)
            except GameplayServiceError:
                action = next((
                    name for name, rect in self._action_rects.items()
                    if state.mouse_clicked and state.mouse_pos and rect.collidepoint(state.mouse_pos)
                ), None)
                if state.pressed("lockpick"):
                    action = "lockpick"
                elif state.pressed("force_lock"):
                    action = "force"
                elif state.pressed("confirm") and lock and lock.required_key_id:
                    action = "key"
                if lock and lock.locked and action == "key":
                    self.message = (
                        "Kilit anahtarla açıldı." if self.service.unlock_with_key(
                            actor_id, inventory_id, lock.lock_id, lock.required_key_id
                        ) else "Uygun anahtar bulunamadı."
                    )
                elif lock and lock.locked and not lock.jammed and not lock.broken and action == "lockpick":
                    tool = self._find_tool(inventory_id, lock.lockpick_allowed_tool_tags)
                    self.message = self._format_attempt(
                        self.service.resolve_lockpick(actor_id, inventory_id, lock.lock_id, tool_item_id=tool)
                    )
                elif lock and lock.locked and not lock.jammed and not lock.broken and action == "force":
                    tool = self._find_tool(inventory_id, lock.force_required_tool_tags)
                    self.message = self._format_attempt(
                        self.service.resolve_force_lock(actor_id, inventory_id, lock.lock_id, tool_item_id=tool)
                    )
                return None

            entries = self._filtered_entries(view)
            self._display_entries = entries
            self.scroll_row = max(0, min(self.scroll_row, self._max_scroll(len(entries))))

            if state.text and self._search_rect is not None:
                if self.search_text:
                    self.search_text += state.text
                else:
                    self.search_text = state.text
                self.scroll_row = 0
                self.selected_index = 0
            if state.pressed("backspace") and self.search_text:
                self.search_text = self.search_text[:-1]
                self.scroll_row = 0
                self.selected_index = 0

            if state.mouse_wheel and state.mouse_pos and self._grid_rect and self._grid_rect.collidepoint(state.mouse_pos):
                self.scroll_row = max(
                    0, min(self._max_scroll(len(entries)), self.scroll_row - state.mouse_wheel)
                )

            if state.mouse_clicked and state.mouse_pos:
                if getattr(self, "_sort_rect", None) and self._sort_rect.collidepoint(state.mouse_pos):
                    modes = ("name", "category", "rarity", "quantity")
                    self.sort_mode = modes[(modes.index(self.sort_mode) + 1) % len(modes)]
                    self.scroll_row = 0
                    return None
                if self._take_all_rect and self._take_all_rect.collidepoint(state.mouse_pos):
                    self._take_all(actor_id, inventory_id)
                    self._drag_item_id = None
                    return None
                if self._search_rect and self._search_rect.collidepoint(state.mouse_pos):
                    pass
                else:
                    for category, rect in self._category_rects.items():
                        if rect.collidepoint(state.mouse_pos):
                            self.category = category
                            self.scroll_row = 0
                            self.selected_index = 0
                            self._drag_item_id = None
                            return None
                for index, rect in enumerate(self._row_rects):
                    if rect.collidepoint(state.mouse_pos):
                        entry_index = self.scroll_row * self.COLUMNS + index
                        if entry_index < len(entries):
                            self.selected_index = entry_index
                            self._drag_item_id = entries[entry_index][0]
                        break

            if state.mouse_button_up and self._drag_item_id:
                item_id, self._drag_item_id = self._drag_item_id, None
                quantity = next((amount for key, amount, *_ in entries if key == item_id), 0)
                if quantity:
                    self._transfer(actor_id, inventory_id, item_id, quantity)

            if state.pressed("confirm") and entries:
                index = min(self.selected_index, len(entries) - 1)
                item_id, quantity, *_ = entries[index]
                self._transfer(actor_id, inventory_id, item_id, quantity)

            if state.pressed("up") and entries:
                self.selected_index = max(0, self.selected_index - self.COLUMNS)
            if state.pressed("down") and entries:
                self.selected_index = min(len(entries) - 1, self.selected_index + self.COLUMNS)
            return None
        except (KeyError, ValueError, RuntimeError, GameplayServiceError) as error:
            self._drag_item_id = None
            self.message = f"İşlem yapılamadı: {error}"
            return None

    def _render_locked(self, renderer, lock):
        self._action_rects = {}
        renderer.panel(renderer.pg.Rect(52, 145, 816, 478), (24, 29, 39), (145, 112, 65))
        self._draw_chest_emblem(renderer, 776, 158)
        renderer.text("KİLİTLİ SANDIK", 82, 169, GOLD, title=True)
        status = "Sıkışmış" if lock and lock.jammed else "Hasarlı" if lock and lock.broken else "Kilitli"
        renderer.chip(82, 222, f"Durum: {status}", WARN)
        renderer.wrapped_text(
            "İçindekiler kilit açılana kadar gizli. Sandığı açmak için uygun bir yöntem seçin.",
            82, 270, 570, TEXT_SOFT, line_height=25, max_lines=2,
        )
        if lock is not None and lock.required_key_id:
            key_rect = renderer.pg.Rect(82, 390, 205, 44)
            renderer.action_button(key_rect, "ENTER", "Anahtarla aç")
            self._action_rects["key"] = key_rect
        if lock is not None and lock.lockpick_profile_id:
            renderer.text(
                f"Maymunculuk • Beceri {lock.lockpick_minimum_skill}+ • DC {lock.lockpick_difficulty_class}",
                310, 330, TEXT_SOFT, max_width=440,
            )
            pick_rect = renderer.pg.Rect(310, 390, 205, 44)
            renderer.action_button(pick_rect, "T", "Maymunculuk dene")
            self._action_rects["lockpick"] = pick_rect
        if lock is not None and lock.force_profile_id:
            renderer.text(
                f"Zorlama • Güç {lock.force_minimum_strength}+ • DC {lock.force_difficulty_class}",
                535, 330, TEXT_SOFT, max_width=300,
            )
            force_rect = renderer.pg.Rect(535, 390, 205, 44)
            renderer.action_button(force_rect, "F", "Kilidi zorla")
            self._action_rects["force"] = force_rect
        renderer.text(self.message, 82, 500, GOOD if "BAŞARILI" in self.message or "açıldı" in self.message else WARN)
        renderer.footer("Enter: anahtar   T: maymuncuk   F: zorla   X: pencereyi kapat")

    @staticmethod
    def _draw_slot(renderer, rect, *, selected=False, hovered=False, rarity="common"):
        pg = renderer.pg
        palette = {
            "common": ((34, 38, 48), (94, 105, 119)),
            "uncommon": ((29, 48, 39), (80, 158, 105)),
            "rare": ((30, 43, 65), (83, 137, 205)),
            "epic": ((53, 35, 61), (165, 94, 190)),
            "legendary": ((67, 47, 22), (218, 164, 66)),
        }
        fill, edge = palette.get(rarity, palette["common"])
        if hovered:
            fill = tuple(min(255, value + 12) for value in fill)
        pg.draw.rect(renderer.surface, (9, 11, 16), rect.move(2, 3), border_radius=7)
        pg.draw.rect(renderer.surface, (17, 20, 27), rect, border_radius=7)
        inner = rect.inflate(-4, -4)
        pg.draw.rect(renderer.surface, fill, inner, border_radius=5)
        pg.draw.rect(renderer.surface, GOLD if selected else edge, rect, 2 if selected else 1, border_radius=7)
        if selected:
            pg.draw.line(renderer.surface, GOLD, (rect.x + 7, rect.y + 4), (rect.right - 7, rect.y + 4), 2)

    @staticmethod
    def _draw_item_icon(renderer, item, rect, category):
        pg, surface = renderer.pg, renderer.surface
        cx, cy = rect.center
        if category == "weapon":
            pg.draw.polygon(surface, (222, 224, 225), [(cx, cy - 19), (cx + 6, cy + 2), (cx, cy + 10), (cx - 6, cy + 2)])
            pg.draw.line(surface, GOLD, (cx, cy + 8), (cx, cy + 20), 4)
            pg.draw.line(surface, (115, 77, 43), (cx - 9, cy + 12), (cx + 9, cy + 12), 4)
        elif category == "armor":
            pg.draw.polygon(surface, (114, 143, 160), [(cx - 17, cy - 15), (cx + 17, cy - 15), (cx + 13, cy + 5), (cx, cy + 19), (cx - 13, cy + 5)])
            pg.draw.polygon(surface, GOLD, [(cx, cy - 10), (cx + 8, cy - 6), (cx + 6, cy + 4), (cx, cy + 12), (cx - 6, cy + 4), (cx - 8, cy - 6)], 2)
        elif category == "potion":
            pg.draw.rect(surface, (105, 168, 199), pg.Rect(cx - 8, cy - 12, 16, 27), border_radius=5)
            pg.draw.rect(surface, (223, 190, 116), pg.Rect(cx - 5, cy - 19, 10, 9), border_radius=2)
            pg.draw.rect(surface, (185, 66, 73), pg.Rect(cx - 6, cy + 2, 12, 11), border_radius=3)
            pg.draw.line(surface, (225, 145, 145), (cx - 3, cy - 5), (cx + 2, cy + 3), 2)
        elif category == "food":
            pg.draw.ellipse(surface, (189, 135, 76), pg.Rect(cx - 17, cy - 10, 34, 23))
            pg.draw.ellipse(surface, (235, 196, 125), pg.Rect(cx - 17, cy - 10, 34, 23), 2)
        else:
            pg.draw.polygon(surface, (122, 153, 177), [(cx, cy - 18), (cx + 15, cy - 2), (cx + 8, cy + 16), (cx - 8, cy + 16), (cx - 15, cy - 2)])
            pg.draw.polygon(surface, GOLD, [(cx, cy - 10), (cx + 8, cy - 1), (cx + 4, cy + 10), (cx - 4, cy + 10), (cx - 8, cy - 1)], 2)

    def render(self, renderer):
        if self.container_id is None:
            return
        try:
            actor_id, inventory_id = self._actor_context()
            lock = self.service.container_lock_state(self.container_id)
            try:
                view = self.service.open_container(actor_id, inventory_id, self.container_id)
            except GameplayServiceError:
                self._render_locked(renderer, lock)
                return

            pg = renderer.pg
            outer = pg.Rect(52, 145, 816, 478)
            renderer.panel(outer, (23, 27, 37), (163, 124, 69))
            renderer.panel(pg.Rect(59, 152, 802, 464), (29, 31, 39), (91, 78, 61))
            self._draw_chest_emblem(renderer, 785, 157)
            renderer.text(view.name.upper(), 82, 166, GOLD, title=True, max_width=650)
            renderer.text("GANİMET", 84, 211, TEXT_SOFT)
            renderer.text(f"{sum(amount for _, amount in view.items)} adet • {len(view.items)} tür", 190, 211, MUTED)

            self._search_rect = pg.Rect(82, 242, 260, 34)
            pg.draw.rect(renderer.surface, (16, 19, 27), self._search_rect, border_radius=8)
            pg.draw.rect(renderer.surface, (104, 119, 143) if self.search_text else (74, 82, 96), self._search_rect, 1, border_radius=8)
            renderer.text("⌕", 94, 248, GOLD)
            search_label = self.search_text if self.search_text else "Eşya ara..."
            renderer.text(search_label, 122, 249, TEXT if self.search_text else MUTED, max_width=208)

            self._category_rects = {}
            x = 354
            for category, label in self.CATEGORIES:
                width = renderer.text_width(label) + 22
                rect = pg.Rect(x, 242, width, 34)
                active = self.category == category
                fill = (76, 59, 39) if active else (37, 42, 53)
                edge = GOLD if active else (79, 91, 111)
                pg.draw.rect(renderer.surface, fill, rect, border_radius=9)
                pg.draw.rect(renderer.surface, edge, rect, 1, border_radius=9)
                renderer.text(label, rect.x + 11, rect.y + 8, GOLD if active else TEXT_SOFT)
                self._category_rects[category] = rect
                x += width + 5

            entries = self._filtered_entries(view)
            self._display_entries = entries
            self.scroll_row = max(0, min(self.scroll_row, self._max_scroll(len(entries))))
            self._grid_rect = pg.Rect(*self.GRID_VIEW)
            pg.draw.rect(renderer.surface, (15, 18, 25), self._grid_rect, border_radius=8)
            pg.draw.rect(renderer.surface, (63, 71, 86), self._grid_rect, 1, border_radius=8)
            previous_clip = renderer.surface.get_clip()
            renderer.surface.set_clip(self._grid_rect)
            self._row_rects = []
            slot_rects = self._slot_rects(renderer, len(entries))
            for index, rect in enumerate(slot_rects):
                entry_index = self.scroll_row * self.COLUMNS + index
                entry = entries[entry_index] if entry_index < len(entries) else None
                selected = entry is not None and entry_index == self.selected_index
                hovered = renderer.hovered(rect)
                self._draw_slot(renderer, rect, selected=selected, hovered=hovered)
                self._row_rects.append(rect)
                if entry is None:
                    continue
                item_id, amount, item, category = entry
                self._draw_item_icon(renderer, item, rect.inflate(-7, -7), category)
                badge = pg.Rect(rect.right - 23, rect.bottom - 17, 20, 14)
                pg.draw.rect(renderer.surface, (9, 12, 18), badge, border_radius=4)
                renderer.text(str(amount), badge.x + 3, badge.y - 1, (245, 225, 183), max_width=15)
            renderer.surface.set_clip(previous_clip)

            total_rows = self._visible_rows(len(entries))
            visible_rows = max(1, self.GRID_VIEW[3] // (self.SLOT_SIZE + self.SLOT_GAP))
            if total_rows > visible_rows:
                track = pg.Rect(850, self.GRID_VIEW[1], 5, self.GRID_VIEW[3])
                pg.draw.rect(renderer.surface, (18, 21, 29), track, border_radius=3)
                thumb_h = max(28, int(track.height * visible_rows / total_rows))
                travel = track.height - thumb_h
                thumb_y = track.y + int(travel * self.scroll_row / max(1, total_rows - visible_rows))
                pg.draw.rect(renderer.surface, (171, 135, 81), pg.Rect(track.x, thumb_y, track.width, thumb_h), border_radius=3)

            if not entries:
                hint = "Bu sandıkta eşya yok." if not view.items else "Aramanızla eşleşen eşya bulunamadı."
                renderer.text(hint, 96, 398, MUTED)
            self._take_all_rect = pg.Rect(680, 566, 154, 38)
            renderer.action_button(self._take_all_rect, "T", "Tümünü Al", enabled=bool(view.items))
            renderer.text(self.message, 84, 576, GOOD if "aktarıldı" in self.message else TEXT_SOFT, max_width=560)
        except (KeyError, ValueError, RuntimeError, GameplayServiceError) as error:
            renderer.text(f"Sandık görüntülenemedi: {error}", 72, 180, WARN)


__all__ = ["ContainerScreen"]
