"""Quest journal window fitted to the dedicated Eldoria quest-frame artwork."""

from collections import deque
from pathlib import Path

from ..renderer import (
    BAD, GOOD, GOLD, HIGHLIGHT, MUTED, TEXT, TEXT_SOFT, WARN,
)


class QuestLogScreen:
    """Quest journal content rendered over the dedicated fantasy frame."""

    responsive_layout = True
    transparent_window_background = True
    min_window_width = 700
    min_window_height = 420

    BACKGROUND_NAME = "Gemini_Generated_Image_im0xnbim0xnbim0x.jpg"
    ARTWORK_SIZE = (1450, 720)

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
    ROW_HEIGHT = 42
    ROW_STEP = 46

    def __init__(self, service):
        self.service = service
        self.category = 0
        self.selected = 0
        self.scroll = 0
        self.detail_scroll = 0
        self.viewport_width = 944
        self.viewport_height = 470
        self._background = None
        self._background_attempted = False
        self._branch_choice_rects = []

    def set_viewport(self, width, height):
        self.viewport_width = max(1, int(width))
        self.viewport_height = max(1, int(height))

    def _load_background(self, pg):
        if self._background is not None or self._background_attempted:
            return self._background
        self._background_attempted = True
        try:
            asset = Path(__file__).resolve().parents[1] / "assets" / self.BACKGROUND_NAME
            loaded = pg.image.load(str(asset))
            self._background = self._clear_edge_checkerboard(pg, loaded)
        except (AttributeError, OSError, RuntimeError):
            self._background = None
        return self._background

    @staticmethod
    def _clear_edge_checkerboard(pg, image):
        """Remove the neutral checkerboard baked into the JPG's outer corners."""
        width, height = image.get_size()
        if width < 2 or height < 2:
            return image

        try:
            transparent = pg.Surface((width, height), pg.SRCALPHA)
            transparent.blit(image, (0, 0))
            visited = bytearray(width * height)
            pending = deque()

            def enqueue(x, y):
                index = y * width + x
                if visited[index]:
                    return
                visited[index] = 1
                red, green, blue, _alpha = transparent.get_at((x, y))
                if (
                    min(red, green, blue) >= 190
                    and max(red, green, blue) - min(red, green, blue) <= 24
                ):
                    pending.append((x, y))

            for x in range(width):
                enqueue(x, 0)
                enqueue(x, height - 1)
            for y in range(height):
                enqueue(0, y)
                enqueue(width - 1, y)

            while pending:
                x, y = pending.popleft()
                red, green, blue, _alpha = transparent.get_at((x, y))
                transparent.set_at((x, y), (red, green, blue, 0))
                if x:
                    enqueue(x - 1, y)
                if x + 1 < width:
                    enqueue(x + 1, y)
                if y:
                    enqueue(x, y - 1)
                if y + 1 < height:
                    enqueue(x, y + 1)
            return transparent
        except (AttributeError, TypeError, ValueError):
            return image

    def _draw_background(self, renderer, outer):
        image = self._load_background(renderer.pg)
        if image is None:
            renderer.panel(renderer.pg.Rect(outer), (27, 22, 31), (145, 118, 70))
            return False
        try:
            artwork = renderer.pg.transform.smoothscale(
                image, (max(1, outer[2]), max(1, outer[3]))
            )
            renderer.surface.blit(artwork, (outer[0], outer[1]))
            return True
        except (AttributeError, TypeError, ValueError, RuntimeError):
            renderer.panel(renderer.pg.Rect(outer), (27, 22, 31), (145, 118, 70))
            return False

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

        for rect, source_id, group, target_id in self._branch_choice_rects:
            if self._contains(rect, state.mouse_pos):
                self.service.choose_quest_branch(source_id, group, target_id)
                self.detail_scroll = 0
                return None

        for index, rect in enumerate(self._tab_bounds()):
            if self._contains(rect, state.mouse_pos):
                self._select_category(index)
                return None

        list_x, list_y, list_width, list_height = list_bounds
        visible_top = list_y + 42
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
        _list_x, list_y, _list_width, list_height = self._list_bounds()
        visible_top = list_y + 42
        visible_bottom = list_y + list_height - 8
        row_top = list_y + 44 + self.selected * self.ROW_STEP - self.scroll
        if row_top < visible_top:
            self.scroll -= visible_top - row_top
        elif row_top + self.ROW_HEIGHT > visible_bottom:
            self.scroll += row_top + self.ROW_HEIGHT - visible_bottom
        self._clamp_scroll()

    def render(self, renderer):
        self.set_viewport(renderer.width, renderer.height)
        layout = self._layout(renderer.width, renderer.height)
        self._draw_background(renderer, layout["outer"])

        counts = self._counts()
        for index, (_key, label) in enumerate(self.CATEGORIES):
            self._render_tab(renderer, index, f"{label} ({counts[index]})")

        quests = self._quests()
        self._normalize_selection(quests)
        self._render_list(renderer, quests)
        selected_quest = quests[self.selected] if quests else None
        self._render_details(renderer, selected_quest)
        self._render_rewards(renderer, selected_quest.reward if selected_quest else None)

    def _render_tab(self, renderer, index, label):
        x, y, width, height = self._tab_bounds()[index]
        color = GOLD if index == self.category else TEXT_SOFT
        text_width = renderer.text_width(label)
        renderer.text(
            label,
            x + max(4, (width - text_width) // 2),
            y + max(3, (height - 22) // 2),
            color,
            max_width=max(1, width - 12),
        )
        if index == self.category and hasattr(renderer.pg, "draw"):
            renderer.pg.draw.rect(
                renderer.surface, HIGHLIGHT,
                renderer.pg.Rect(x + 8, y + height - 5, width - 16, 2),
                border_radius=1,
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
        visible_height = list_bounds[3] - 50
        content_height = len(quests) * self.ROW_STEP
        self.scroll = max(0, min(self.scroll, max(0, content_height - visible_height)))

    def _clamp_detail_scroll(self):
        quests = self._quests()
        quest = quests[self.selected] if quests and self.selected < len(quests) else None
        content_height = self._detail_content_height(quest)
        visible_height = self._details_bounds()[3] - 112
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
        width = self.viewport_width if width is None else max(1, int(width))
        height = self.viewport_height if height is None else max(1, int(height))
        outer = (
            self.CONTENT_X, self.CONTENT_Y,
            max(1, width - self.CONTENT_X),
            max(1, height - self.CONTENT_Y),
        )
        return {"outer": outer}

    def _art_rect(self, x, y, width, height):
        outer_x, outer_y, outer_width, outer_height = self._layout()["outer"]
        return (
            outer_x + round(outer_width * x),
            outer_y + round(outer_height * y),
            max(1, round(outer_width * width)),
            max(1, round(outer_height * height)),
        )

    def _tab_bounds(self):
        return tuple(
            self._art_rect(x, 0.105, width, 0.095)
            for x, width in (
                (0.055, 0.218), (0.283, 0.214),
                (0.507, 0.214), (0.730, 0.214),
            )
        )

    def _list_bounds(self):
        return self._art_rect(0.055, 0.205, 0.218, 0.505)

    def _details_bounds(self):
        return self._art_rect(0.282, 0.205, 0.660, 0.505)

    def _reward_bounds(self):
        return self._art_rect(0.282, 0.730, 0.660, 0.185)

    def _reward_title_bounds(self):
        return self._art_rect(0.055, 0.730, 0.218, 0.185)

    def _reward_origin(self):
        x, y, _width, _height = self._reward_bounds()
        return x + 14, y + 14

    def _row_bounds(self):
        list_x, list_y, list_width, _list_height = self._list_bounds()
        return tuple(
            (
                list_x + 8,
                list_y + 44 + index * self.ROW_STEP - self.scroll,
                list_width - 16,
                self.ROW_HEIGHT,
            )
            for index in range(len(self._quests()))
        )

    def _detail_content_height(self, quest):
        if quest is None:
            return 70
        giver_height = 24 if getattr(quest, "giver_npc_id", None) else 0
        branch_height = sum(
            22 + (28 * len(targets) if selected is None else 28)
            for _group, targets, selected in self._branch_groups(quest)
        )
        return 92 + giver_height + branch_height + len(quest.objectives) * 50

    def _branch_groups(self, quest):
        if getattr(quest.state, "value", quest.state) != "completed":
            return ()
        bundle = self.service.application.holder.current
        graph = getattr(bundle, "quest_graph", None)
        progress = getattr(bundle, "quest_graph_progress", None)
        if graph is None or progress is None or quest.quest_id not in graph.quest_ids():
            return ()
        grouped = {}
        for link in graph.outgoing(quest.quest_id):
            if getattr(link.link_type, "value", link.link_type) == "alternative":
                grouped.setdefault(link.branch_group, set()).add(link.target_quest_id)
        result = []
        for group, target_ids in sorted(grouped.items()):
            targets = tuple(sorted(target_ids))
            if len(targets) < 2:
                continue
            result.append((group, targets, progress.selected_branch(quest.quest_id, group)))
        return tuple(result)

    def _render_list(self, renderer, quests):
        rect = renderer.pg.Rect(*self._list_bounds())
        if not quests:
            renderer.text(
                "Bu kategoride görev yok.",
                rect.x + 12, rect.y + 48, MUTED,
                max_width=rect.width - 24,
            )
            return

        self._clamp_scroll()
        row_rects = self._row_bounds()
        category_key = self.CATEGORIES[self.category][0]
        for index, quest in enumerate(quests):
            row = renderer.pg.Rect(row_rects[index])
            if row.y < rect.y + 42 or row.bottom > rect.bottom - 7:
                continue
            selected = index == self.selected
            if selected:
                renderer.panel(row, (48, 35, 43), HIGHLIGHT)
            marker = "●" if category_key == "active" else "✓" if category_key == "completed" else "!"
            marker_color = self.CATEGORY_COLORS[category_key]
            renderer.text(marker, row.x + 7, row.y + 7, marker_color)
            renderer.text(
                renderer.fit_text(quest.title, row.width - 34),
                row.x + 26, row.y + 5,
                GOLD if selected else TEXT,
                max_width=row.width - 34,
            )
            renderer.text(
                self.STATUS_LABELS[category_key],
                row.x + 26, row.y + 24, MUTED,
                max_width=row.width - 34,
            )

    def _giver_name(self, quest):
        giver_id = getattr(quest, "giver_npc_id", None)
        if not giver_id:
            return None
        try:
            npc = self.service.application.holder.current.social.npcs.get(giver_id)
        except (AttributeError, KeyError, RuntimeError):
            npc = None
        name = getattr(npc, "name", None) if npc is not None else None
        return name or "Bilinmeyen görev veren"

    def _render_details(self, renderer, quest):
        rect = renderer.pg.Rect(*self._details_bounds())
        if quest is None:
            renderer.text("Bir görev seçin.", rect.x + 18, rect.y + 20, MUTED)
            return

        category_key = self.CATEGORIES[self.category][0]
        renderer.text(
            renderer.fit_text(quest.title, rect.width - 36),
            rect.x + 18, rect.y + 14,
            self.CATEGORY_COLORS[category_key],
            title=True, max_width=rect.width - 36,
        )
        renderer.text(
            self.STATUS_LABELS[category_key],
            rect.x + 18, rect.y + 48, MUTED,
        )
        giver_name = self._giver_name(quest)
        heading_offset = 0
        if giver_name:
            giver_y = rect.y + 74 - self.detail_scroll
            if rect.y + 62 <= giver_y <= rect.bottom - 24:
                renderer.text(
                    f"Görev veren: {giver_name}",
                    rect.x + 18, giver_y, TEXT_SOFT,
                    max_width=rect.width - 36,
                )
            heading_offset = 24

        self._branch_choice_rects = []
        branch_groups = self._branch_groups(quest)
        branch_offset = 0
        branch_y = rect.y + 78 + heading_offset - self.detail_scroll
        for group, targets, selected in branch_groups:
            if rect.y + 62 <= branch_y <= rect.bottom - 24:
                renderer.text("Görev yolu seçimi", rect.x + 18, branch_y, GOLD)
            branch_y += 22
            branch_offset += 22
            if selected is not None:
                target = self._quest_log().get(selected)
                target_name = target.title if target is not None else selected
                if rect.y + 62 <= branch_y <= rect.bottom - 24:
                    renderer.text(
                        f"Seçilen yol: {target_name}",
                        rect.x + 18, branch_y, GOOD,
                        max_width=rect.width - 36,
                    )
                branch_y += 28
                branch_offset += 28
                continue
            for target_id in targets:
                target = self._quest_log().get(target_id)
                target_name = target.title if target is not None else target_id
                button_rect = (
                    rect.x + 18, branch_y, max(1, rect.width - 36), 24,
                )
                if rect.y + 62 <= branch_y and branch_y + 24 <= rect.bottom - 8:
                    renderer.button(
                        renderer.pg.Rect(button_rect), target_name,
                    )
                    self._branch_choice_rects.append(
                        (button_rect, quest.quest_id, group, target_id)
                    )
                branch_y += 28
                branch_offset += 28

        heading_y = rect.y + 78 + heading_offset + branch_offset - self.detail_scroll
        if rect.y + 62 <= heading_y <= rect.bottom - 24:
            renderer.text("Hedefler", rect.x + 18, heading_y, GOLD)

        y = rect.y + 106 + heading_offset + branch_offset - self.detail_scroll
        for objective in quest.objectives:
            if y >= rect.y + 62 and y + 42 <= rect.bottom - 10:
                marker = "[x]" if objective.completed else "[ ]"
                required_label = "İsteğe bağlı" if objective.optional else "Zorunlu"
                color = GOOD if objective.completed else TEXT_SOFT
                renderer.text(
                    f"{marker} {objective.description}",
                    rect.x + 18, y, color,
                    max_width=rect.width - 36,
                )
                renderer.text(
                    f"{required_label}  {objective.progress}/{objective.required}",
                    rect.x + 18, y + 22, MUTED,
                )
                ratio = (
                    objective.progress / objective.required
                    if objective.required > 0 else 0
                )
                bar_x = rect.x + min(250, rect.width // 3)
                renderer.bar(
                    renderer.pg.Rect(
                        bar_x, y + 26,
                        max(1, rect.right - bar_x - 24), 8,
                    ),
                    ratio,
                    GOOD if objective.completed else WARN,
                )
            y += 50

        self._clamp_detail_scroll()
        if self.detail_scroll:
            renderer.text(
                "Daha fazla hedef...",
                rect.x + 18, rect.bottom - 20, MUTED,
            )

    def _render_rewards(self, renderer, reward):
        x, y = self._reward_origin()
        _rx, _ry, width, height = self._reward_bounds()
        if reward is None:
            renderer.text("Bir görev seçin.", x, y, MUTED)
            return

        lines = []
        if reward.experience:
            lines.append(f"XP  {reward.experience}")
        if reward.currency:
            lines.append(f"Para  {reward.currency}")
        for item_id, amount in reward.items:
            try:
                item = self.service.item(item_id)
            except (KeyError, ValueError, RuntimeError):
                item = None
            name = getattr(item, "name", None) if item is not None else None
            lines.append(f"{name or item_id}  x{amount}")
        for faction_id, amount in reward.reputation:
            lines.append(f"İtibar  {faction_id} {amount:+d}")

        if not lines:
            renderer.text("Bu görev için ödül yok.", x, y, MUTED)
            return
        line_height = max(17, min(21, (height - 16) // 4))
        for index, line in enumerate(lines[:4]):
            renderer.text(
                line, x, y + index * line_height, TEXT_SOFT,
                max_width=width - 28,
            )
