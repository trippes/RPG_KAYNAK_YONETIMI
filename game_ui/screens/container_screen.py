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
    SLOT_SIZE = 68
    SLOT_GAP = 5
    GRID_X = 242
    GRID_Y = 238
    GRID_VIEW = (220, 230, 470, 300)
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

    @staticmethod
    def _rarity(item):
        value = str(getattr(item, "rarity", "common")).lower()
        return value if value in {"uncommon", "rare", "epic", "legendary"} else "common"

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

            pg, surface = renderer.pg, renderer.surface
            outer = pg.Rect(132, 145, 656, 478)
            pg.draw.rect(surface, (10, 8, 7), outer.inflate(10, 10), border_radius=18)
            pg.draw.rect(surface, (67, 46, 31), outer, border_radius=15)
            pg.draw.rect(surface, (29, 23, 20), outer.inflate(-8, -8), 3, border_radius=12)
            pg.draw.rect(surface, (31, 25, 22), pg.Rect(139, 152, 642, 464), border_radius=12)
            pg.draw.rect(surface, (112, 82, 51), pg.Rect(139, 152, 642, 464), 1, border_radius=12)
            for x, direction in ((outer.left + 15, 1), (outer.right - 15, -1)):
                pg.draw.line(surface, (190, 148, 87), (x, outer.top + 10), (x + 13 * direction, outer.top - 2), 3)
                pg.draw.line(surface, (190, 148, 87), (x, outer.bottom - 10), (x + 13 * direction, outer.bottom + 2), 2)

            # Chest emblem and the wide, dark sorting bar from the reference.
            emblem = pg.Rect(158, 166, 52, 52)
            pg.draw.circle(surface, (12, 10, 9), emblem.center, 27)
            pg.draw.circle(surface, (139, 105, 62), emblem.center, 24, 2)
            pg.draw.circle(surface, (48, 35, 25), emblem.center, 20)
            self._draw_chest_emblem(renderer, emblem.x - 6, emblem.y - 17)
            sort_rect = pg.Rect(222, 166, 492, 48)
            pg.draw.rect(surface, (8, 8, 8), sort_rect.move(0, 3), border_radius=18)
            pg.draw.rect(surface, (13, 12, 11), sort_rect, border_radius=18)
            pg.draw.rect(surface, (117, 91, 61), sort_rect, 2, border_radius=18)
            renderer.text("≡", sort_rect.x + 17, sort_rect.y + 8, (222, 194, 145))
            renderer.text("Sort By", sort_rect.x + 52, sort_rect.y + 10, (225, 214, 195))
            self._sort_rect = sort_rect

            entries = self._filtered_entries(view)
            mode = getattr(self, "sort_mode", "name")
            if mode == "rarity":
                rank = {"common": 0, "uncommon": 1, "rare": 2, "epic": 3, "legendary": 4}
                entries = tuple(sorted(entries, key=lambda row: rank.get(self._rarity(row[2]), 0), reverse=True))
            elif mode == "quantity":
                entries = tuple(sorted(entries, key=lambda row: row[1], reverse=True))
            elif mode == "category":
                entries = tuple(sorted(entries, key=lambda row: (row[3], row[2].name.casefold())))
            self._display_entries = entries
            self.scroll_row = max(0, min(self.scroll_row, self._max_scroll(len(entries))))

            grid = pg.Rect(166, 226, 588, 310)
            pg.draw.rect(surface, (17, 14, 13), grid, border_radius=5)
            pg.draw.rect(surface, (73, 57, 43), grid, 1, border_radius=5)
            self._grid_rect = grid
            previous_clip = surface.get_clip()
            surface.set_clip(grid)
            self._row_rects = []
            slot_rects = self._slot_rects(renderer, len(entries))
            for index, rect in enumerate(slot_rects):
                entry_index = self.scroll_row * self.COLUMNS + index
                entry = entries[entry_index] if entry_index < len(entries) else None
                if entry is None:
                    self._draw_slot(renderer, rect)
                    self._row_rects.append(rect)
                    continue
                item_id, amount, item, category = entry
                rarity = self._rarity(item)
                self._draw_slot(renderer, rect, selected=entry_index == self.selected_index,
                                hovered=renderer.hovered(rect), rarity=rarity)
                self._row_rects.append(rect)
                self._draw_item_icon(renderer, item, rect.inflate(-9, -9), category)
                if amount > 1:
                    badge = pg.Rect(rect.right - 24, rect.bottom - 19, 21, 15)
                    pg.draw.rect(surface, (8, 8, 8), badge, border_radius=3)
                    renderer.text(str(amount), badge.x + 2, badge.y - 1, (245, 235, 218), max_width=18)
            surface.set_clip(previous_clip)

            visible_rows = max(1, grid.height // (self.SLOT_SIZE + self.SLOT_GAP))
            total_rows = self._visible_rows(len(entries))
            if total_rows > visible_rows:
                track = pg.Rect(grid.right + 8, grid.y + 5, 7, grid.height - 10)
                pg.draw.rect(surface, (11, 10, 9), track, border_radius=4)
                thumb_h = max(28, int(track.height * visible_rows / total_rows))
                travel = track.height - thumb_h
                thumb_y = track.y + int(travel * self.scroll_row / max(1, total_rows - visible_rows))
                pg.draw.rect(surface, (173, 133, 77), pg.Rect(track.x, thumb_y, 7, thumb_h), border_radius=4)
            if not entries:
                renderer.text("Sandıkta ganimet yok.", grid.x + 22, grid.centery - 10, MUTED)

            take = pg.Rect(282, 552, 356, 54)
            pg.draw.rect(surface, (8, 7, 7), take.move(0, 4), border_radius=22)
            pg.draw.rect(surface, (36, 27, 22), take, border_radius=22)
            pg.draw.rect(surface, (135, 99, 57), take, 2, border_radius=22)
            pg.draw.line(surface, (194, 151, 89), (take.x + 28, take.y + 3), (take.right - 28, take.y + 3), 2)
            renderer.text("Tümünü Al", take.x + 128, take.y + 14, (238, 224, 199))
            renderer.text("➜", take.right - 48, take.y + 13, (225, 193, 137))
            self._take_all_rect = take
            if self.message and "hazır" not in self.message:
                renderer.text(self.message, outer.x + 18, outer.bottom - 18, TEXT_SOFT, max_width=620)
        except (KeyError, ValueError, RuntimeError, GameplayServiceError) as error:
            renderer.text(f"Sandık görüntülenemedi: {error}", 72, 180, WARN)


__all__ = ["ContainerScreen"]
