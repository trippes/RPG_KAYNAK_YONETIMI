from ..renderer import (
    BAD, BUTTON_HOVER, BUTTON_SELECTED, GOOD, GOLD, HIGHLIGHT, MUTED,
    PANEL_BORDER, TEXT, TEXT_SOFT, WARN,
)


class QuestLogScreen:
    """Window content for the four-state quest journal."""

    CATEGORIES = (
        ("active", "Devam Eden"),
        ("available", "Mevcut"),
        ("completed", "Tamamlanan"),
        ("failed", "Başarısız"),
    )
    CATEGORY_COLORS = {
        "active": WARN,
        "available": TEXT_SOFT,
        "completed": GOOD,
        "failed": BAD,
    }
    STATUS_LABELS = {
        "active": "Devam ediyor",
        "available": "Mevcut",
        "completed": "Tamamlandı",
        "failed": "Başarısız",
    }
    CONTENT_X = 24
    CONTENT_Y = 126
    CONTENT_MARGIN = 16
    HEADER_HEIGHT = 42
    TAB_HEIGHT = 34
    BODY_HEIGHT = 230
    REWARD_HEIGHT = 76

    def __init__(self, service):
        self.service = service
        self.category = 0
        self.selected = 0
        self.scroll = 0
        self.detail_scroll = 0
        self._viewport = (960, 640)

    def handle(self, state):
        """Handle journal navigation without changing quest lifecycle state."""
        if state.pressed("left") or state.pressed("right"):
            direction = -1 if state.pressed("left") else 1
            self._select_category((self.category + direction) % len(self.CATEGORIES))
            return None

        quests = self._quests()
        if state.pressed("up") and quests:
            self.selected = max(0, self.selected - 1)
            self.detail_scroll = 0
            self._ensure_selected_visible()
        elif state.pressed("down") and quests:
            self.selected = min(len(quests) - 1, self.selected + 1)
            self.detail_scroll = 0
            self._ensure_selected_visible()

        list_bounds = self._list_bounds()
        detail_bounds = self._details_bounds()
        if state.mouse_wheel and (
            state.mouse_pos is None
            or self._contains(list_bounds, state.mouse_pos)
            or self._contains(detail_bounds, state.mouse_pos)
        ):
            if state.mouse_pos is not None and self._contains(detail_bounds, state.mouse_pos):
                self.detail_scroll -= state.mouse_wheel * 28
                self._clamp_detail_scroll()
            else:
                self.scroll -= state.mouse_wheel * 28
                self._clamp_scroll()
            return None

        if not state.mouse_clicked or state.mouse_pos is None:
            return None

        for index, rect in enumerate(self._tab_bounds()):
            if self._contains(rect, state.mouse_pos):
                self._select_category(index)
                return None

        list_x, list_y, list_width, list_height = list_bounds
        visible_top = list_y + 34
        visible_bottom = list_y + list_height - 8
        if not (list_x <= state.mouse_pos[0] < list_x + list_width
                and visible_top <= state.mouse_pos[1] < visible_bottom):
            return None
        for index, rect in enumerate(self._row_bounds()):
            row_top, row_height = rect[1], rect[3]
            if row_top < visible_bottom and row_top + row_height > visible_top:
                if self._contains(rect, state.mouse_pos):
                    self.selected = index
                    self.detail_scroll = 0
                    return None
        return None

    def _select_category(self, index):
        self.category = index
        self.selected = 0
        self.scroll = 0
        self.detail_scroll = 0

    def _ensure_selected_visible(self):
        quests = self._quests()
        if not quests:
            self.scroll = 0
            return
        list_x, list_y, _list_width, list_height = self._list_bounds()
        visible_top = list_y + 34
        visible_bottom = list_y + list_height - 8
        row_top = list_y + 38 + self.selected * 54 - self.scroll
        if row_top < visible_top:
            self.scroll -= visible_top - row_top
        elif row_top + 48 > visible_bottom:
            self.scroll += row_top + 48 - visible_bottom
        self._clamp_scroll()

    def render(self, renderer):
        self._viewport = (renderer.width, renderer.height)
        # WindowManager owns the outer title bar. This screen renders only its content.
        layout = self._layout(renderer.width, renderer.height)
        outer = renderer.pg.Rect(*layout["outer"])
        renderer.panel(outer, (25, 31, 43), (145, 118, 70))
        renderer.text("MACERA DEFTERİ", outer.x + 20, outer.y + 12, GOLD)
        renderer.text("Görevlerini ve ilerlemeni takip et.", outer.x + 20, outer.y + 28, MUTED)

        counts = self._counts()
        for index, (_key, label) in enumerate(self.CATEGORIES):
            title = f"{label} ({counts[index]})"
            renderer.button(
                renderer.pg.Rect(*self._tab_bounds()[index]),
                title,
                selected=index == self.category,
            )

        quests = self._quests()
        self._normalize_selection(quests)
        self._render_list(renderer, quests)
        self._render_details(renderer, quests[self.selected] if quests else None)
        self._render_rewards(
            renderer,
            quests[self.selected].reward if quests else None,
            *self._reward_origin(),
        )

    def _quest_log(self):
        return self.service.application.holder.current.quest_log

    def _category_quests(self, category=None):
        key = self.CATEGORIES[self.category if category is None else category][0]
        return getattr(self._quest_log(), key)()

    def _quests(self):
        return self._category_quests()

    def _counts(self):
        return tuple(len(self._category_quests(index)) for index in range(len(self.CATEGORIES)))

    def _normalize_selection(self, quests):
        if not quests:
            self.selected = 0
            self.scroll = 0
            self.detail_scroll = 0
        else:
            self.selected = max(0, min(self.selected, len(quests) - 1))
        self._clamp_scroll()
        self._ensure_selected_visible()
        self._clamp_detail_scroll()

    def _clamp_scroll(self):
        quests = self._quests()
        list_bounds = self._list_bounds()
        visible_height = list_bounds[3] - 42
        content_height = len(quests) * 54
        self.scroll = max(0, min(self.scroll, max(0, content_height - visible_height)))

    def _clamp_detail_scroll(self):
        quests = self._quests()
        quest = quests[self.selected] if quests and self.selected < len(quests) else None
        content_height = self._detail_content_height(quest)
        visible_height = self._details_bounds()[3] - 62
        self.detail_scroll = max(
            0, min(self.detail_scroll, max(0, content_height - visible_height))
        )

    @staticmethod
    def _contains(rect, position):
        return (
            position is not None
            and rect[0] <= position[0] < rect[0] + rect[2]
            and rect[1] <= position[1] < rect[1] + rect[3]
        )

    def _layout(self, width=None, height=None):
        width, height = self._viewport if width is None or height is None else (width, height)
        x = self.CONTENT_X
        y = self.CONTENT_Y
        available_width = max(420, width - x * 2)
        # WindowManager clips content to the registered window height minus its title bar.
        # The quest window is 470 px high with a 32 px title bar, so its content
        # viewport is 438 px; keep the layout inside that source surface.
        available_height = max(280, min(height - y - 76, 438))
        return {
            "outer": (x, y, available_width, available_height),
            "body_y": y + self.HEADER_HEIGHT + self.TAB_HEIGHT + 10,
            "body_height": min(self.BODY_HEIGHT, max(120, available_height - self.REWARD_HEIGHT - self.HEADER_HEIGHT - self.TAB_HEIGHT - 44)),
        }

    def _tab_bounds(self):
        layout = self._layout()
        outer_x, outer_y, outer_width, _outer_height = layout["outer"]
        gap = 8
        x = outer_x + self.CONTENT_MARGIN
        y = outer_y + self.HEADER_HEIGHT
        usable_width = outer_width - self.CONTENT_MARGIN * 2 - gap * (len(self.CATEGORIES) - 1)
        width = max(72, usable_width // len(self.CATEGORIES))
        return tuple(
            (x + index * (width + gap), y, width, self.TAB_HEIGHT)
            for index in range(len(self.CATEGORIES))
        )

    def _list_bounds(self):
        layout = self._layout()
        return (
            self.CONTENT_X + self.CONTENT_MARGIN,
            layout["body_y"],
            max(180, min(304, (self._layout()["outer"][2] - 48) // 3)),
            layout["body_height"],
        )

    def _details_bounds(self):
        layout = self._layout()
        list_x, _list_y, list_width, _list_height = self._list_bounds()
        return (
            list_x + list_width + 12,
            layout["body_y"],
            max(180, self._layout()["outer"][2] - list_width - 3 * self.CONTENT_MARGIN),
            layout["body_height"],
        )

    def _reward_bounds(self):
        layout = self._layout()
        outer_x, outer_y, outer_width, outer_height = layout["outer"]
        return (
            outer_x + self.CONTENT_MARGIN,
            outer_y + outer_height - self.REWARD_HEIGHT - self.CONTENT_MARGIN,
            outer_width - 2 * self.CONTENT_MARGIN,
            self.REWARD_HEIGHT,
        )

    def _reward_origin(self):
        bounds = self._reward_bounds()
        return bounds[0] + 16, bounds[1] + 34

    def _row_bounds(self):
        list_x, list_y, list_width, _list_height = self._list_bounds()
        return tuple(
            (list_x + 10, list_y + 38 + index * 54 - self.scroll, list_width - 20, 48)
            for index in range(len(self._quests()))
        )

    def _tab_rects(self, renderer=None):
        pg = renderer.pg if renderer is not None else getattr(self.service, "_pygame", None)
        values = self._tab_bounds()
        return tuple(pg.Rect(value) for value in values) if pg is not None else values

    def _list_rect(self, renderer=None):
        pg = renderer.pg if renderer is not None else getattr(self.service, "_pygame", None)
        value = self._list_bounds()
        return pg.Rect(value) if pg is not None else value

    def _row_rects(self, renderer=None):
        values = self._row_bounds()
        pg = renderer.pg if renderer is not None else getattr(self.service, "_pygame", None)
        return tuple(pg.Rect(value) for value in values) if pg is not None else values

    def _render_list(self, renderer, quests):
        rect = self._list_rect(renderer)
        renderer.panel(rect, (32, 40, 54), PANEL_BORDER)
        renderer.text("Görevler", rect.x + 16, rect.y + 12, GOLD)
        if not quests:
            renderer.text(
                "Bu kategoride görev yok.",
                rect.x + 16,
                rect.y + 58,
                MUTED,
                max_width=rect.width - 32,
            )
            return

        self._clamp_scroll()
        row_rects = self._row_rects(renderer)
        category_key = self.CATEGORIES[self.category][0]
        for index, quest in enumerate(quests):
            row = row_rects[index]
            if row.y < rect.y + 34 or row.bottom > rect.bottom - 8:
                continue
            selected = index == self.selected
            fill = (
                BUTTON_SELECTED
                if selected
                else BUTTON_HOVER if renderer.hovered(row) else (29, 38, 52)
            )
            renderer.panel(row, fill, HIGHLIGHT if selected else PANEL_BORDER)
            marker = "●" if category_key == "active" else "✓" if category_key == "completed" else "!"
            renderer.text(marker, row.x + 10, row.y + 10,
                          self.CATEGORY_COLORS[category_key])
            renderer.text(
                renderer.fit_text(quest.title, row.width - 42),
                row.x + 30,
                row.y + 8,
                self.CATEGORY_COLORS[category_key] if selected else TEXT,
                max_width=row.width - 42,
            )
            renderer.text(
                self.STATUS_LABELS[category_key],
                row.x + 30,
                row.y + 29,
                MUTED,
                max_width=row.width - 42,
            )

    def _detail_content_height(self, quest):
        if quest is None:
            return 80
        return 78 + len(quest.objectives) * 50

    def _render_details(self, renderer, quest):
        rect = renderer.pg.Rect(*self._details_bounds())
        renderer.panel(rect, (27, 35, 50), PANEL_BORDER)
        if quest is None:
            renderer.text("Bir görev seçin.", rect.x + 18, rect.y + 18, MUTED)
            return

        category_key = self.CATEGORIES[self.category][0]
        renderer.text(
            renderer.fit_text(quest.title, rect.width - 36),
            rect.x + 18,
            rect.y + 16,
            self.CATEGORY_COLORS[category_key],
            title=True,
            max_width=rect.width - 36,
        )
        renderer.text(
            self.STATUS_LABELS[category_key],
            rect.x + 18,
            rect.y + 50,
            MUTED,
        )
        heading_y = rect.y + 78 - self.detail_scroll
        if rect.y + 58 <= heading_y <= rect.bottom - 24:
            renderer.text("Hedefler", rect.x + 18, heading_y, GOLD)

        y = rect.y + 106 - self.detail_scroll
        for objective in quest.objectives:
            if y >= rect.y + 58 and y + 42 <= rect.bottom - 12:
                marker = "[x]" if objective.completed else "[ ]"
                required_label = "İsteğe bağlı" if objective.optional else "Zorunlu"
                color = GOOD if objective.completed else TEXT_SOFT
                renderer.text(
                    f"{marker} {objective.description}",
                    rect.x + 18,
                    y,
                    color,
                    max_width=rect.width - 36,
                )
                renderer.text(
                    f"{required_label}  {objective.progress}/{objective.required}",
                    rect.x + 18,
                    y + 22,
                    MUTED,
                )
                ratio = (
                    objective.progress / objective.required
                    if objective.required > 0 else 0
                )
                renderer.bar(
                    renderer.pg.Rect(rect.x + 160, y + 25, rect.width - 178, 10),
                    ratio,
                    GOOD if objective.completed else WARN,
                )
            y += 50

        self._clamp_detail_scroll()
        if self.detail_scroll:
            renderer.text("Daha fazla hedef...", rect.x + 18, rect.bottom - 20, MUTED)

    def _render_rewards(self, renderer, reward, x, y):
        rect = renderer.pg.Rect(*self._reward_bounds())
        renderer.panel(rect, (34, 39, 49), (112, 96, 65))
        renderer.text("Ödüller", rect.x + 16, rect.y + 12, GOLD)
        if reward is None:
            renderer.text("Bir görev seçin.", x, y, MUTED)
            return

        lines = []
        if reward.experience:
            lines.append(f"XP {reward.experience}")
        if reward.currency:
            lines.append(f"Para {reward.currency}")
        for item_id, amount in reward.items:
            try:
                item = self.service.item(item_id)
            except (KeyError, ValueError, RuntimeError):
                item = None
            name = getattr(item, "name", None) if item is not None else None
            lines.append(f"Eşya: {name or item_id} x{amount}")
        for faction_id, amount in reward.reputation:
            lines.append(f"İtibar: {faction_id} {amount:+d}")
        if not lines:
            renderer.text("Bu görev için ödül yok.", x, y, MUTED)
            return
        for index, line in enumerate(lines[:4]):
            renderer.text(line, x, y + index * 20, TEXT_SOFT,
                          max_width=rect.width - 32)
