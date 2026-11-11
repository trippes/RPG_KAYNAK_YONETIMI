"""Character sheet rendered inside the movable gameplay window."""

from ..renderer import (
    GOOD, GOLD, HIGHLIGHT, MUTED, PANEL_BORDER, TEXT, TEXT_SOFT,
    BUTTON_HOVER, BUTTON_SELECTED,
)


class CharacterScreen:
    """Read-only character overview with the existing skill progression action."""

    CONTENT_X = 24
    CONTENT_Y = 126
    CONTENT_WIDTH = 760
    CONTENT_HEIGHT = 430

    ATTRIBUTE_LABELS = {
        "strength": "Güç",
        "dexterity": "Çeviklik",
        "constitution": "Dayanıklılık",
        "intelligence": "Zekâ",
        "wisdom": "Bilgelik",
        "charisma": "Karizma",
    }
    EQUIPMENT_LABELS = {
        "head": "Baş",
        "chest": "Gövde",
        "hands": "Eller",
        "legs": "Bacak",
        "feet": "Ayak",
        "main_hand": "Ana el",
        "off_hand": "Diğer el",
        "accessory": "Aksesuar",
    }

    def __init__(self, service):
        self.service = service
        self.selected_skill = 0
        self.skill_scroll = 0
        self.message = ""

    def _character(self):
        return self.service.actor_character("hero")

    def _stats(self):
        return self.service.actor_stats("hero") or {}

    def _skill_rows(self, character=None):
        character = character or self._character()
        if character is None:
            return ()
        return tuple(character.skills.to_dict().items())

    def _equipment_rows(self, character=None):
        character = character or self._character()
        if character is None:
            return ()
        equipped = character.equipment.snapshot()
        return tuple(
            (slot, equipped.get(slot))
            for slot in self.EQUIPMENT_LABELS
        )

    def _skill_bounds(self):
        return (280, 320, 244, 21)

    def handle(self, state):
        character = self._character()
        skills = self._skill_rows(character)
        if not skills:
            self.selected_skill = 0
            self.skill_scroll = 0
            return None

        self.selected_skill %= len(skills)
        visible_count = 5
        max_scroll = max(0, len(skills) - visible_count)
        if state.mouse_pos is not None:
            x, y, width, height = self._skill_bounds()
            if x <= state.mouse_pos[0] < x + width and y <= state.mouse_pos[1] < y + height * visible_count:
                if state.mouse_wheel:
                    self.skill_scroll = max(
                        0, min(max_scroll, self.skill_scroll - state.mouse_wheel)
                    )
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
        outer = renderer.pg.Rect(
            self.CONTENT_X, self.CONTENT_Y,
            self.CONTENT_WIDTH, self.CONTENT_HEIGHT,
        )
        renderer.panel(outer, (23, 29, 42), (145, 118, 70))
        renderer.text("KARAKTER", outer.x + 16, outer.y + 9, GOLD, title=True)
        renderer.text(
            "Kimlik · nitelikler · gelişim · ekipman",
            outer.x + 132, outer.y + 13, MUTED,
        )

        if not snapshot.actors:
            renderer.text(
                "Karakter kaydı bulunamadı.",
                outer.x + 20, outer.y + 76, MUTED,
            )
            return

        actor = snapshot.actors[0]
        character = self.service.actor_character(actor.actor_id)
        stats = self.service.actor_stats(actor.actor_id) or {}
        if character is None:
            renderer.text(
                "Bu karaktere bağlı bir karakter profili bulunamadı.",
                outer.x + 20, outer.y + 76, MUTED,
            )
            return

        self._render_identity(renderer, character, stats)
        self._render_combat(renderer, stats)
        self._render_attributes(renderer, stats)
        self._render_skills(renderer, character)
        self._render_equipment(renderer, character)

    def _render_identity(self, renderer, character, stats):
        """Render the character identity as a compact RPG profile card."""
        rect = renderer.pg.Rect(40, 168, 316, 88)
        renderer.panel(rect, (32, 40, 54), PANEL_BORDER)

        portrait = renderer.pg.Rect(rect.x + 10, rect.y + 10, 64, 68)
        renderer.panel(portrait, (20, 27, 40), (145, 118, 70))
        center = (portrait.centerx, portrait.centery - 3)
        renderer.pg.draw.circle(renderer.surface, (82, 100, 126), center, 21)
        renderer.pg.draw.circle(renderer.surface, GOLD, center, 21, 2)
        initials = (character.name.strip()[:1] or "?").upper()
        initials_width = renderer.text_width(initials, title=True)
        renderer.text(
            initials,
            center[0] - initials_width // 2,
            center[1] - 15,
            GOLD,
            title=True,
        )

        text_x = portrait.right + 10
        text_width = rect.right - text_x - 10
        renderer.text(
            renderer.fit_text(character.name, text_width, title=True),
            text_x, rect.y + 7, GOLD, title=True,
            max_width=text_width,
        )
        identity = (
            f"{character.race.name} · {character.character_class.name} · "
            f"{character.age} yaş"
        )
        renderer.text(
            identity, text_x, rect.y + 36, TEXT_SOFT,
            max_width=text_width,
        )
        level = stats.get("level", character.progression.level)
        experience = stats.get("experience", character.progression.experience)
        required = stats.get(
            "experience_to_next_level",
            character.progression.experience_to_next_level,
        )
        renderer.text(f"SEVİYE {level}", text_x, rect.y + 60, MUTED)
        bar_x = text_x + 78
        bar_width = max(30, rect.right - bar_x - 10)
        renderer.bar(
            renderer.pg.Rect(bar_x, rect.y + 64, bar_width, 8),
            experience / required if required else 0,
            GOLD,
        )
        renderer.text(
            f"{experience}/{required} XP",
            bar_x, rect.y + 73, MUTED,
            max_width=bar_width,
        )

    def _render_combat(self, renderer, stats):
        rect = renderer.pg.Rect(368, 168, 400, 88)
        renderer.panel(rect, (27, 35, 50), PANEL_BORDER)
        current_hp = stats.get("current_hit_points", 0) or 0
        max_hp = stats.get("max_hit_points", 0) or 0
        renderer.text("CAN", rect.x + 12, rect.y + 10, MUTED)
        renderer.bar(
            renderer.pg.Rect(rect.x + 52, rect.y + 13, 230, 12),
            current_hp / max_hp if max_hp else 0,
            GOOD,
        )
        renderer.text(
            f"{current_hp}/{max_hp}",
            rect.x + 292, rect.y + 9, TEXT_SOFT,
        )
        values = (
            ("SALDIRI", stats.get("attack_bonus", 0)),
            ("SAVUNMA", stats.get("defense_bonus", 0)),
            ("İLK HAMLE", stats.get("initiative_bonus", 0)),
            ("SİLAH HASARI", stats.get("weapon_damage", 0)),
        )
        for index, (label, value) in enumerate(values):
            column = index % 2
            row = index // 2
            x = rect.x + 12 + column * 190
            y = rect.y + 38 + row * 22
            renderer.text(label, x, y, MUTED)
            renderer.text(f"{value:+}" if label != "SİLAH HASARI" else str(value),
                          x + 112, y, GOLD)

    def _render_attributes(self, renderer, stats):
        rect = renderer.pg.Rect(40, 268, 220, 174)
        renderer.panel(rect, (27, 35, 50), PANEL_BORDER)
        renderer.text("NİTELİKLER", rect.x + 12, rect.y + 10, GOLD)
        attributes = stats.get("attributes", {})
        modifiers = stats.get("modifiers", {})
        for index, key in enumerate(self.ATTRIBUTE_LABELS):
            column, row = index % 2, index // 2
            card = renderer.pg.Rect(
                rect.x + 10 + column * 100,
                rect.y + 36 + row * 42,
                94, 34,
            )
            renderer.panel(card, (35, 44, 60), PANEL_BORDER)
            renderer.text(
                self.ATTRIBUTE_LABELS[key], card.x + 6, card.y + 4,
                TEXT_SOFT, max_width=card.width - 12,
            )
            renderer.text(
                str(attributes.get(key, 10)),
                card.x + 6, card.y + 19, GOLD,
            )
            modifier = modifiers.get(key, 0)
            renderer.text(
                f"{modifier:+}",
                card.right - 30, card.y + 19, GOOD if modifier >= 0 else MUTED,
            )

    def _render_skills(self, renderer, character):
        rect = renderer.pg.Rect(272, 268, 260, 174)
        renderer.panel(rect, (27, 35, 50), PANEL_BORDER)
        points = character.progression.unspent_points
        renderer.text("BECERİLER", rect.x + 12, rect.y + 10, GOLD)
        renderer.text(f"Gelişim puanı: {points}", rect.x + 12, rect.y + 29, MUTED)

        skills = self._skill_rows(character)
        visible_count = 5
        if not skills:
            renderer.text("Beceri kaydı bulunmuyor.", rect.x + 12, rect.y + 62, MUTED)
        else:
            self.selected_skill %= len(skills)
            self.skill_scroll = max(
                0, min(max(0, len(skills) - visible_count), self.skill_scroll)
            )
            for row_index, (skill, value) in enumerate(
                skills[self.skill_scroll:self.skill_scroll + visible_count]
            ):
                index = self.skill_scroll + row_index
                row = renderer.pg.Rect(
                    rect.x + 8, rect.y + 52 + row_index * 21,
                    rect.width - 16, 19,
                )
                selected = index == self.selected_skill
                if selected:
                    renderer.panel(row, BUTTON_SELECTED, HIGHLIGHT)
                elif renderer.hovered(row):
                    renderer.panel(row, BUTTON_HOVER, PANEL_BORDER)
                renderer.text(
                    skill.replace("_", " ").title(),
                    row.x + 7, row.y + 2,
                    GOOD if selected else TEXT_SOFT,
                    max_width=row.width - 45,
                )
                renderer.text(
                    str(value), row.right - 27, row.y + 2,
                    GOLD if selected else TEXT_SOFT,
                )

        if self.message:
            renderer.text(
                renderer.fit_text(self.message, rect.width - 20),
                rect.x + 10, rect.bottom - 28, GOOD,
                max_width=rect.width - 20,
            )
        renderer.text(
            "↑ / ↓ seç · Enter: puan harca",
            rect.x + 10, rect.bottom - 14, MUTED,
        )

    def _render_equipment(self, renderer, character):
        rect = renderer.pg.Rect(544, 268, 224, 174)
        renderer.panel(rect, (27, 35, 50), PANEL_BORDER)
        renderer.text("EKİPMAN", rect.x + 12, rect.y + 10, GOLD)
        for index, (slot, item_id) in enumerate(self._equipment_rows(character)):
            column, row = index % 2, index // 2
            cell = renderer.pg.Rect(
                rect.x + 8 + column * 106,
                rect.y + 36 + row * 32,
                102, 27,
            )
            renderer.panel(cell, (35, 44, 60), PANEL_BORDER)
            renderer.text(
                self.EQUIPMENT_LABELS[slot],
                cell.x + 5, cell.y + 3, MUTED,
                max_width=cell.width - 10,
            )
            item = self.service.item(item_id) if item_id else None
            item_name = item.name if item is not None else (
                "Boş" if item_id is None else "Bilinmiyor"
            )
            renderer.text(
                renderer.fit_text(item_name, cell.width - 10),
                cell.x + 5, cell.y + 15, GOLD if item_id else TEXT_SOFT,
                max_width=cell.width - 10,
            )
