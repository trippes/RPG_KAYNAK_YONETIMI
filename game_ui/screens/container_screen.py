"""Scrollable, filterable fantasy loot window for physical containers."""

from ..renderer import (
    GOLD, TEXT, TEXT_SOFT, MUTED, GOOD, WARN, BAD,
    PANEL_BORDER, STRIP_BORDER,
)
from application import GameplayServiceError


class ContainerScreen:
    """Chest-only loot grid with search, category filters and safe transfers."""
    scale_to_window = True
    design_size = (920, 500)


    COLUMNS = 6
    MIN_ROWS = 4
    SLOT_WIDTH = 104
    SLOT_HEIGHT = 68
    SLOT_GAP = 10
    GRID_X = 123
    GRID_Y = 236
    GRID_VIEW = (78, 228, 764, 316)
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
        visible_rows = max(1, self.GRID_VIEW[3] // (self.SLOT_HEIGHT + self.SLOT_GAP))
        return max(0, total_rows - visible_rows)

    def _slot_rects(self, renderer, entry_count):
        pitch_x = self.SLOT_WIDTH + self.SLOT_GAP
        pitch_y = self.SLOT_HEIGHT + self.SLOT_GAP
        first = self.scroll_row * self.COLUMNS
        count = self._visible_rows(entry_count) * self.COLUMNS
        return tuple(
            renderer.pg.Rect(
                self.GRID_X + (index % self.COLUMNS) * pitch_x,
                self.GRID_Y + (index // self.COLUMNS - self.scroll_row) * pitch_y,
                self.SLOT_WIDTH, self.SLOT_HEIGHT,
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
        pg, surface = renderer.pg, renderer.surface
        palette = {
            "common": ((30, 36, 48), (100, 116, 137)),
            "uncommon": ((23, 49, 40), (77, 174, 116)),
            "rare": ((24, 42, 69), (87, 151, 225)),
            "epic": ((52, 34, 66), (176, 111, 218)),
            "legendary": ((67, 47, 23), (230, 177, 77)),
        }
        fill, edge = palette.get(str(rarity).lower(), palette["common"])
        if hovered or selected:
            fill = tuple(min(255, channel + 9) for channel in fill)
        pg.draw.rect(surface, (5, 8, 14), rect.move(0, 4), border_radius=9)
        pg.draw.rect(surface, (12, 17, 27), rect, border_radius=9)
        inner = rect.inflate(-4, -4)
        pg.draw.rect(surface, fill, inner, border_radius=7)
        pg.draw.line(surface, tuple(min(255, v + 22) for v in fill),
                     (inner.x + 8, inner.y + 2), (inner.right - 8, inner.y + 2), 1)
        pg.draw.rect(surface, edge if not selected else (244, 207, 126),
                     rect, 2 if selected else 1, border_radius=9)
        if selected:
            pg.draw.rect(surface, (244, 207, 126), rect.inflate(4, 4), 1, border_radius=11)

    @staticmethod
    def _draw_item_icon(renderer, item, rect, category):
        pg, surface = renderer.pg, renderer.surface
        cx, cy = rect.center
        shadow = (7, 10, 16)
        if category == "weapon":
            blade = [(cx, cy - 23), (cx + 7, cy - 1), (cx + 2, cy + 8),
                     (cx - 2, cy + 8), (cx - 7, cy - 1)]
            pg.draw.polygon(surface, shadow, [(x + 2, y + 3) for x, y in blade])
            pg.draw.polygon(surface, (190, 207, 218), blade)
            pg.draw.line(surface, (245, 250, 252), (cx, cy - 19), (cx - 3, cy + 1), 2)
            pg.draw.line(surface, (201, 157, 83), (cx, cy + 7), (cx, cy + 22), 4)
            pg.draw.line(surface, (231, 198, 126), (cx - 10, cy + 10), (cx + 10, cy + 10), 3)
            pg.draw.circle(surface, (238, 208, 139), (cx, cy + 22), 3)
        elif category == "armor":
            points = [(cx - 19, cy - 16), (cx - 8, cy - 21), (cx, cy - 14),
                      (cx + 8, cy - 21), (cx + 19, cy - 16), (cx + 15, cy + 8),
                      (cx, cy + 23), (cx - 15, cy + 8)]
            pg.draw.polygon(surface, shadow, [(x + 2, y + 3) for x, y in points])
            pg.draw.polygon(surface, (92, 126, 151), points)
            pg.draw.line(surface, (178, 204, 218), points[0], points[1], 3)
            pg.draw.line(surface, (178, 204, 218), points[1], points[2], 3)
            pg.draw.line(surface, (190, 158, 91), (cx, cy - 12), (cx, cy + 16), 2)
            pg.draw.line(surface, (190, 158, 91), (cx - 11, cy - 7), (cx + 11, cy - 7), 2)
        elif category == "potion":
            pg.draw.rect(surface, shadow, pg.Rect(cx - 9, cy - 12, 20, 31), border_radius=6)
            pg.draw.rect(surface, (173, 202, 215), pg.Rect(cx - 10, cy - 15, 20, 31), border_radius=6)
            pg.draw.rect(surface, (152, 48, 66), pg.Rect(cx - 7, cy + 1, 14, 12), border_radius=4)
            pg.draw.rect(surface, (221, 188, 119), pg.Rect(cx - 6, cy - 23, 12, 9), border_radius=2)
            pg.draw.line(surface, (246, 248, 231), (cx - 5, cy - 9), (cx - 5, cy + 1), 2)
            pg.draw.line(surface, (222, 117, 128), (cx - 5, cy + 5), (cx + 4, cy + 5), 2)
        elif category == "food":
            pg.draw.ellipse(surface, shadow, pg.Rect(cx - 21, cy - 10, 44, 28))
            pg.draw.ellipse(surface, (171, 112, 58), pg.Rect(cx - 21, cy - 13, 42, 26))
            pg.draw.ellipse(surface, (236, 190, 119), pg.Rect(cx - 16, cy - 10, 32, 18), 2)
            pg.draw.arc(surface, (255, 222, 160), pg.Rect(cx - 12, cy - 9, 22, 14), 0.2, 2.7, 2)
        else:
            pg.draw.polygon(surface, shadow, [(cx + 1, cy - 23), (cx + 20, cy - 2),
                (cx + 12, cy + 19), (cx - 11, cy + 19), (cx - 20, cy - 2)])
            pg.draw.polygon(surface, (82, 135, 165), [(cx, cy - 24), (cx + 18, cy - 3),
                (cx + 10, cy + 17), (cx - 10, cy + 17), (cx - 18, cy - 3)])
            pg.draw.polygon(surface, (174, 215, 224), [(cx, cy - 17), (cx + 8, cy - 3),
                (cx + 3, cy + 8), (cx - 5, cy + 5), (cx - 8, cy - 3)])
            pg.draw.line(surface, (226, 244, 241), (cx, cy - 16), (cx - 5, cy - 4), 2)

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
            outer = pg.Rect(52, 145, 816, 478)
            pg.draw.rect(surface, (7, 9, 14), outer.move(0, 5), border_radius=18)
            pg.draw.rect(surface, (19, 24, 34), outer, border_radius=18)
            pg.draw.rect(surface, (153, 119, 68), outer, 2, border_radius=18)
            inner = outer.inflate(-10, -10)
            pg.draw.rect(surface, (25, 31, 43), inner, border_radius=14)
            pg.draw.rect(surface, (68, 81, 101), inner, 1, border_radius=14)

            header = pg.Rect(66, 158, 788, 62)
            pg.draw.rect(surface, (17, 23, 34), header, border_radius=11)
            pg.draw.line(surface, (184, 143, 78), (82, 219), (838, 219), 1)
            emblem = pg.Rect(82, 168, 42, 42)
            pg.draw.rect(surface, (47, 39, 30), emblem, border_radius=10)
            pg.draw.rect(surface, (184, 143, 78), emblem, 1, border_radius=10)
            pg.draw.rect(surface, (103, 68, 39), pg.Rect(91, 184, 24, 14), border_radius=3)
            pg.draw.rect(surface, (205, 166, 103), pg.Rect(89, 178, 28, 9), border_radius=3)
            pg.draw.rect(surface, (231, 197, 125), pg.Rect(89, 178, 28, 9), 1, border_radius=3)
            pg.draw.line(surface, (225, 190, 119), (103, 179), (103, 198), 2)
            pg.draw.rect(surface, (225, 190, 119), pg.Rect(99, 185, 8, 8), border_radius=2)
            renderer.text(view.name.upper(), 137, 169, (239, 220, 181), title=True, max_width=360)
            count = sum(amount for _, amount in view.items)
            renderer.text(f"{count} eşya  •  {len(view.items)} farklı tür", 139, 196, (151, 165, 184))

            self._sort_rect = pg.Rect(558, 170, 270, 38)
            pg.draw.rect(surface, (9, 13, 21), self._sort_rect, border_radius=10)
            pg.draw.rect(surface, (103, 119, 143), self._sort_rect, 1, border_radius=10)
            renderer.text("≡", 572, 177, (220, 184, 111))
            labels = {"name": "Ada göre", "category": "Türe göre", "rarity": "Nadirliğe göre", "quantity": "Miktara göre"}
            renderer.text("SIRALA", 600, 174, (130, 146, 166))
            renderer.text(labels.get(self.sort_mode, "Ada göre"), 600, 190, (235, 226, 207))
            renderer.text("▾", 802, 180, (220, 184, 111))

            entries = list(self._filtered_entries(view))
            if self.sort_mode == "quantity":
                entries.sort(key=lambda row: row[1], reverse=True)
            elif self.sort_mode == "rarity":
                order = {"legendary": 0, "epic": 1, "rare": 2, "uncommon": 3, "common": 4}
                entries.sort(key=lambda row: order.get(str(getattr(row[2], "rarity", "common")).lower(), 5))
            elif self.sort_mode == "category":
                entries.sort(key=lambda row: (row[3], row[2].name.casefold()))
            else:
                entries.sort(key=lambda row: row[2].name.casefold())
            entries = tuple(entries)
            self._display_entries = entries
            self.scroll_row = max(0, min(self.scroll_row, self._max_scroll(len(entries))))

            board = pg.Rect(76, 229, 768, 320)
            pg.draw.rect(surface, (10, 14, 22), board, border_radius=12)
            pg.draw.rect(surface, (56, 68, 86), board, 1, border_radius=12)
            self._grid_rect = board
            previous_clip = surface.get_clip()
            surface.set_clip(board)
            self._row_rects = []
            slot_rects = self._slot_rects(renderer, len(entries))
            for index, rect in enumerate(slot_rects):
                entry_index = self.scroll_row * self.COLUMNS + index
                entry = entries[entry_index] if entry_index < len(entries) else None
                selected = entry is not None and entry_index == self.selected_index
                hovered = renderer.hovered(rect)
                rarity = str(getattr(entry[2], "rarity", "common")).lower() if entry else "common"
                self._draw_slot(renderer, rect, selected=selected, hovered=hovered, rarity=rarity)
                self._row_rects.append(rect)
                if entry is None:
                    continue
                _item_id, amount, item, category = entry
                icon_rect = pg.Rect(rect.x + 8, rect.y + 5, 48, 56)
                self._draw_item_icon(renderer, item, icon_rect, category)
                short_name = renderer.fit_text(item.name, 43)
                renderer.text(short_name, rect.x + 58, rect.y + 12, (226, 230, 237), max_width=42)
                badge = pg.Rect(rect.right - 29, rect.bottom - 22, 23, 16)
                pg.draw.rect(surface, (7, 10, 16), badge, border_radius=5)
                renderer.text(str(amount), badge.x + 4, badge.y, (248, 222, 166), max_width=18)
            surface.set_clip(previous_clip)

            total_rows = self._visible_rows(len(entries))
            visible_rows = max(1, self.GRID_VIEW[3] // (self.SLOT_HEIGHT + self.SLOT_GAP))
            if total_rows > visible_rows:
                track = pg.Rect(850, board.y + 8, 5, board.height - 16)
                pg.draw.rect(surface, (19, 25, 35), track, border_radius=3)
                thumb_h = max(30, int(track.height * visible_rows / total_rows))
                travel = track.height - thumb_h
                thumb_y = track.y + int(travel * self.scroll_row / max(1, total_rows - visible_rows))
                pg.draw.rect(surface, (190, 151, 87), pg.Rect(track.x, thumb_y, track.width, thumb_h), border_radius=3)

            if not entries:
                renderer.text("Sandıkta henüz eşya bulunmuyor.", 300, 376, (143, 157, 177))

            footer_y = 562
            pg.draw.line(surface, (72, 83, 101), (82, footer_y - 8), (838, footer_y - 8), 1)
            self._take_all_rect = pg.Rect(650, 570, 184, 40)
            button = self._take_all_rect
            pg.draw.rect(surface, (7, 10, 16), button.move(0, 3), border_radius=10)
            pg.draw.rect(surface, (93, 68, 39), button, border_radius=10)
            pg.draw.rect(surface, (202, 158, 83), button, 1, border_radius=10)
            if renderer.hovered(button):
                pg.draw.rect(surface, (119, 88, 47), button.inflate(-4, -4), border_radius=8)
            renderer.text("TÜMÜNÜ AL", button.x + 48, button.y + 12, (248, 224, 181))
            renderer.text("›", button.right - 24, button.y + 7, (248, 224, 181), title=True)
            status_color = (139, 207, 160) if "aktarıldı" in self.message else (151, 165, 184)
            renderer.text(self.message, 86, 581, status_color, max_width=540)
        except (KeyError, ValueError, RuntimeError, GameplayServiceError) as error:
            renderer.text(f"Sandık görüntülenemedi: {error}", 72, 180, WARN)


__all__ = ["ContainerScreen"]
