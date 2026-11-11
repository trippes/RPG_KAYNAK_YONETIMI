"""Character sheet rendered inside the movable gameplay window."""

from ..renderer import (
    GOOD, GOLD, HIGHLIGHT, MUTED, PANEL_BORDER, TEXT, TEXT_SOFT,
    BUTTON_HOVER, BUTTON_SELECTED, ResponsiveLayout,
)


class CharacterScreen:
    """Read-only character overview with the existing skill progression action."""

    responsive_layout = True
    min_window_width = 600
    min_window_height = 470

    ATTRIBUTE_LABELS = {
        "strength": "Güç",
        "dexterity": "Çeviklik",
        "constitution": "Dayanıklılık",
        "intelligence": "Zekâ",
        "wisdom": "Bilgelik",
        "charisma": "Karizma",
    }

    def __init__(self, service):
        self.service = service
        self.selected_skill = 0
        self.skill_scroll = 0
        self.message = ""
        self.viewport_width = 760
        self.viewport_height = 438

    def set_viewport(self, width, height):
        self.viewport_width = max(1, int(width))
        self.viewport_height = max(1, int(height))

    def _layout(self):
        outer = (
            24, 126,
            max(1, self.viewport_width - 48),
            max(1, self.viewport_height - 16),
        )
        inner = ResponsiveLayout.inset(outer, 16, 48, 16, 14)
        compact = inner[2] < 700
        gap = 10
        top_height = max(104, min(132, int(inner[3] * 0.34)))
        bottom_y = inner[1] + top_height + gap
        bottom_height = max(1, inner[3] - top_height - gap)
        if compact:
            identity = (inner[0], inner[1], inner[2], top_height)
            combat = None
            attribute_height = max(96, (bottom_height - gap) // 2)
            attributes = (inner[0], bottom_y, inner[2], attribute_height)
            skills = (
                inner[0], bottom_y + attribute_height + gap,
                inner[2], max(1, bottom_height - attribute_height - gap),
            )
        else:
            identity, combat = ResponsiveLayout.split_columns(
                (inner[0], inner[1], inner[2], top_height),
                (0.82, 1.18), gap=gap,
            )
            attributes, skills = ResponsiveLayout.split_columns(
                (inner[0], bottom_y, inner[2], bottom_height),
                (0.82, 1.18), gap=gap,
            )
        return {
            "outer": outer, "inner": inner, "compact": compact,
            "identity": identity, "combat": combat,
            "attributes": attributes, "skills": skills,
        }

    def _character(self):
        return self.service.actor_character("hero")

    def _stats(self):
        return self.service.actor_stats("hero") or {}

    def _skill_rows(self, character=None):
        character = character or self._character()
        if character is None:
            return ()
        return tuple(character.skills.to_dict().items())

    def _skill_geometry(self):
        layout = self._layout()
        rect = layout["skills"] or layout["attributes"]
        x, y, width, height = rect
        header_height = 58
        footer_height = 30
        row_height = max(20, min(27, (height - header_height - footer_height) // 3))
        visible_count = max(1, (height - header_height - footer_height) // row_height)
        return (x + 8, y + header_height, max(1, width - 16), row_height), visible_count

    def _skill_bounds(self):
        rect, visible_count = self._skill_geometry()
        return (rect[0], rect[1], rect[2], rect[3] * visible_count)

    def handle(self, state):
        character = self._character()
        skills = self._skill_rows(character)
        if not skills:
            self.selected_skill = 0
            self.skill_scroll = 0
            return None

        self.selected_skill %= len(skills)
        row_rect, visible_count = self._skill_geometry()
        max_scroll = max(0, len(skills) - visible_count)
        if state.mouse_pos is not None:
            x, y, width, height = row_rect
            if x <= state.mouse_pos[0] < x + width and y <= state.mouse_pos[1] < y + height * visible_count:
                if state.mouse_wheel:
                    self.skill_scroll = max(0, min(max_scroll, self.skill_scroll - state.mouse_wheel))
                elif state.mouse_clicked:
                    row = (state.mouse_pos[1] - y) // height
                    index = self.skill_scroll + row
                    if index < len(skills):
                        self.selected_skill = index

        if state.pressed("up"):
            self.selected_skill = (self.selected_skill - 1) % len(skills)
        if state.pressed("down"):
            self.selected_skill = (self.selected_skill + 1) % len(skills)

        if self.selected_skill < self.skill_scroll:
            self.skill_scroll = self.selected_skill
        elif self.selected_skill >= self.skill_scroll + visible_count:
            self.skill_scroll = self.selected_skill - visible_count + 1
        self.skill_scroll = max(0, min(max_scroll, self.skill_scroll))

        if state.pressed("confirm"):
            try:
                skill = skills[self.selected_skill][0]
                value = self.service.improve_skill("hero", skill)
                self.message = f"{skill} becerisi {value} oldu."
            except (KeyError, ValueError, RuntimeError) as error:
                self.message = str(error)
        return None

    def render(self, renderer):
        snapshot = self.service.state()
        layout = self._layout()
        outer = renderer.pg.Rect(layout["outer"])
        renderer.panel(outer, (23, 29, 42), (145, 118, 70))
        renderer.text("KARAKTER", outer.x + 16, outer.y + 9, GOLD)
        renderer.text("Kimlik · nitelikler · gelişim", outer.x + 132, outer.y + 9, MUTED)

        if not snapshot.actors:
            renderer.text("Karakter kaydı bulunamadı.", outer.x + 20, outer.y + 76, MUTED)
            return

        actor = snapshot.actors[0]
        character = self.service.actor_character(actor.actor_id)
        stats = self.service.actor_stats(actor.actor_id) or {}
        if character is None:
            renderer.text("Bu karaktere bağlı bir karakter profili bulunamadı.", outer.x + 20, outer.y + 76, MUTED)
            return

        self._render_identity(renderer, character, stats, layout["identity"])
        if layout["combat"] is not None:
            self._render_combat(renderer, stats, layout["combat"])
        self._render_attributes(renderer, stats, layout["attributes"])
        self._render_skills(renderer, character, layout["skills"])

    def _render_identity(self, renderer, character, stats, bounds):
        rect = renderer.pg.Rect(bounds)
        renderer.panel(rect, (32, 40, 54), PANEL_BORDER)
        portrait_size = max(44, min(64, rect.height - 24))
        portrait = renderer.pg.Rect(rect.x + 10, rect.y + 10, portrait_size, portrait_size)
        renderer.panel(portrait, (20, 27, 40), (145, 118, 70))
        center = (portrait.centerx, portrait.centery - 3)
        renderer.pg.draw.circle(renderer.surface, (82, 100, 126), center, max(12, portrait_size // 3))
        renderer.pg.draw.circle(renderer.surface, GOLD, center, max(12, portrait_size // 3), 2)
        initials = (character.name.strip()[:1] or "?").upper()
        initials_width = renderer.text_width(initials, title=True)
        renderer.text(initials, center[0] - initials_width // 2, center[1] - 15, GOLD, title=True)

        text_x = portrait.right + 10
        text_width = max(30, rect.right - text_x - 10)
        renderer.text(renderer.fit_text(character.name, text_width), text_x, rect.y + 10, GOLD, max_width=text_width)
        identity = f"{character.race.name} · {character.character_class.name} · {character.age} yaş"
        renderer.text(identity, text_x, rect.y + 38, TEXT_SOFT, max_width=text_width)
        level = stats.get("level", character.progression.level)
        experience = stats.get("experience", character.progression.experience)
        required = stats.get("experience_to_next_level", character.progression.experience_to_next_level)
        renderer.text(f"SEVİYE {level}", text_x, rect.y + rect.height - 30, MUTED)
        bar_x = text_x + 78
        bar_width = max(1, rect.right - bar_x - 10)
        renderer.text(f"{experience}/{required} XP", bar_x, rect.y + rect.height - 30, MUTED, max_width=bar_width)
        renderer.bar(renderer.pg.Rect(bar_x, rect.y + rect.height - 10, bar_width, 5),
                     experience / required if required else 0, GOLD)

    def _render_combat(self, renderer, stats, bounds):
        rect = renderer.pg.Rect(bounds)
        renderer.panel(rect, (27, 35, 50), PANEL_BORDER)
        current_hp = stats.get("current_hit_points", 0) or 0
        max_hp = stats.get("max_hit_points", 0) or 0
        renderer.text("CAN", rect.x + 12, rect.y + 10, MUTED)
        bar_x = rect.x + 52
        bar_width = max(1, rect.width - 150)
        renderer.bar(renderer.pg.Rect(bar_x, rect.y + 13, bar_width, 12),
                     current_hp / max_hp if max_hp else 0, GOOD)
        renderer.text(f"{current_hp}/{max_hp}", bar_x + bar_width + 8, rect.y + 9, TEXT_SOFT)
        values = (
            ("SALDIRI", stats.get("attack_bonus", 0)),
            ("SAVUNMA", stats.get("defense_bonus", 0)),
            ("İLK HAMLE", stats.get("initiative_bonus", 0)),
            ("SİLAH HASARI", stats.get("weapon_damage", 0)),
        )
        column_width = max(1, (rect.width - 32) // 2)
        for index, (label, value) in enumerate(values):
            column, row = index % 2, index // 2
            x = rect.x + 12 + column * column_width
            y = rect.y + 40 + row * 26
            renderer.text(label, x, y, MUTED, max_width=max(30, column_width - 48))
            renderer.text(f"{value:+}" if label != "SİLAH HASARI" else str(value),
                          x + column_width - 48, y, GOLD)

    def _render_attributes(self, renderer, stats, bounds):
        rect = renderer.pg.Rect(bounds)
        renderer.panel(rect, (27, 35, 50), PANEL_BORDER)
        renderer.text("NİTELİKLER", rect.x + 12, rect.y + 10, GOLD)
        attributes = stats.get("attributes", {})
        modifiers = stats.get("modifiers", {})
        columns = 2 if rect.width >= 300 else 1
        gap = 6
        cell_width = max(1, (rect.width - 20 - gap * (columns - 1)) // columns)
        row_height = max(24, min(38, (rect.height - 44) // 3))
        for index, key in enumerate(self.ATTRIBUTE_LABELS):
            column, row = index % columns, index // columns
            card = renderer.pg.Rect(
                rect.x + 10 + column * (cell_width + gap),
                rect.y + 36 + row * (row_height + 5),
                cell_width, row_height,
            )
            renderer.panel(card, (35, 44, 60), PANEL_BORDER)
            value = f"{self.ATTRIBUTE_LABELS[key]}: {attributes.get(key, 10)} ({modifiers.get(key, 0):+})"
            renderer.text(renderer.fit_text(value, card.width - 10),
                          card.x + 5, card.y + max(2, (card.height - 20) // 2),
                          TEXT_SOFT, max_width=max(1, card.width - 10))

    def _render_skills(self, renderer, character, bounds):
        rect = renderer.pg.Rect(bounds)
        renderer.panel(rect, (27, 35, 50), PANEL_BORDER)
        points = character.progression.unspent_points
        renderer.text("BECERİLER", rect.x + 12, rect.y + 10, GOLD)
        renderer.text(f"Gelişim puanı: {points}", rect.x + 12, rect.y + 34, MUTED)

        skills = self._skill_rows(character)
        row_rect, visible_count = self._skill_geometry()
        row_x, row_y, row_width, row_height = row_rect
        if not skills:
            renderer.text("Beceri kaydı bulunmuyor.", rect.x + 12, rect.y + 62, MUTED)
        else:
            self.selected_skill %= len(skills)
            self.skill_scroll = max(0, min(max(0, len(skills) - visible_count), self.skill_scroll))
            for row_index, (skill, value) in enumerate(
                skills[self.skill_scroll:self.skill_scroll + visible_count]
            ):
                index = self.skill_scroll + row_index
                row = renderer.pg.Rect(row_x, row_y + row_index * row_height,
                                       row_width, max(1, row_height - 3))
                selected = index == self.selected_skill
                if selected:
                    renderer.panel(row, BUTTON_SELECTED, HIGHLIGHT)
                elif renderer.hovered(row):
                    renderer.panel(row, BUTTON_HOVER, PANEL_BORDER)
                renderer.text(skill.replace("_", " ").title(), row.x + 7, row.y + 1,
                              GOOD if selected else TEXT_SOFT, max_width=max(1, row.width - 45))
                renderer.text(str(value), row.right - 27, row.y + 1,
                              GOLD if selected else TEXT_SOFT)

        footer = self.message or "↑ / ↓ seç · Enter: puan harca"
        renderer.text(renderer.fit_text(footer, rect.width - 20),
                      rect.x + 10, rect.bottom - 24,
                      GOOD if self.message else MUTED, max_width=max(1, rect.width - 20))
