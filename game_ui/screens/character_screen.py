"""Modern, responsive character sheet rendered inside a movable window."""

from ..renderer import (
    GOOD, GOLD, HIGHLIGHT, MUTED, PANEL_BORDER, TEXT_SOFT,
    BUTTON_HOVER, BUTTON_SELECTED,
)


class CharacterScreen:
    """Character overview with responsive panels and skill progression."""

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
        self._last_skill_bounds = (0, 0, 0, 23)

    def _character(self):
        return self.service.actor_character("hero")

    def _skill_rows(self, character=None):
        character = character or self._character()
        return tuple(character.skills.to_dict().items()) if character else ()

    def _equipment_rows(self, character=None):
        character = character or self._character()
        if character is None:
            return ()
        equipped = character.equipment.snapshot()
        return tuple((slot, equipped.get(slot)) for slot in self.EQUIPMENT_LABELS)

    def _layout(self, renderer):
        width = min(self.CONTENT_WIDTH, max(480, renderer.width - 80))
        height = min(self.CONTENT_HEIGHT, max(330, renderer.height - 180))
        gap = 12
        usable = width - 2 * gap
        attribute_width = int(usable * 0.30)
        skill_width = int(usable * 0.36)
        equipment_width = usable - attribute_width - skill_width
        left = self.CONTENT_X + 16
        middle = left + attribute_width + gap
        right = middle + skill_width + gap
        top = self.CONTENT_Y + 140
        return {
            "width": width,
            "height": height,
            "identity": renderer.pg.Rect(left, self.CONTENT_Y + 42, int((width - 32) * 0.39), 82),
            "combat": renderer.pg.Rect(
                left + int((width - 32) * 0.39) + gap,
                self.CONTENT_Y + 42,
                width - 32 - int((width - 32) * 0.39) - gap,
                82,
            ),
            "attributes": renderer.pg.Rect(left, top, attribute_width, height - 158),
            "skills": renderer.pg.Rect(middle, top, skill_width, height - 158),
            "equipment": renderer.pg.Rect(right, top, equipment_width, height - 158),
        }

    def _skill_bounds(self, rect):
        return (rect.x + 8, rect.y + 48, rect.width - 16, 23)

    def handle(self, state):
        character = self._character()
        skills = self._skill_rows(character)
        if not skills:
            self.selected_skill = self.skill_scroll = 0
            return None

        self.selected_skill %= len(skills)
        visible_count = 7
        max_scroll = max(0, len(skills) - visible_count)
        # The same panel geometry is used for mouse selection and rendering.
        # WindowManager translates pointer coordinates into screen coordinates.
        if state.mouse_pos is not None:
            x, y, width, height = self._last_skill_bounds
            if x <= state.mouse_pos[0] < x + width and y <= state.mouse_pos[1] < y + height * visible_count:
                if state.mouse_wheel:
                    self.skill_scroll = max(0, min(max_scroll, self.skill_scroll - state.mouse_wheel))
                elif state.mouse_clicked:
                    index = self.skill_scroll + (state.mouse_pos[1] - y) // height
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
                self.message = f"{skill.replace('_', ' ').title()} becerisi {value} oldu."
            except (KeyError, ValueError, RuntimeError) as error:
                self.message = str(error)
        return None

    def render(self, renderer):
        snapshot = self.service.state()
        if not snapshot.actors:
            renderer.text("Karakter kaydı bulunamadı.", 44, 180, MUTED)
            return
        actor = snapshot.actors[0]
        character = self.service.actor_character(actor.actor_id)
        stats = self.service.actor_stats(actor.actor_id) or {}
        if character is None:
            renderer.text("Karakter profili bulunamadı.", 44, 180, MUTED)
            return

        layout = self._layout(renderer)
        outer = renderer.pg.Rect(self.CONTENT_X, self.CONTENT_Y, layout["width"], layout["height"])
        renderer.panel(outer, (21, 28, 41), (145, 118, 70))
        renderer.text("KARAKTER", outer.x + 16, outer.y + 9, GOLD, title=True, max_width=outer.width - 32)
        renderer.text(
            "Kimlik  /  Savaş  /  Nitelikler  /  Beceriler  /  Ekipman",
            outer.x + 18, outer.y + 76, MUTED, max_width=outer.width - 36,
        )
        self._render_identity(renderer, layout["identity"], character, stats)
        self._render_combat(renderer, layout["combat"], stats)
        self._render_attributes(renderer, layout["attributes"], stats)
        self._render_skills(renderer, layout["skills"], character)
        self._render_equipment(renderer, layout["equipment"], character)

    def _render_identity(self, renderer, rect, character, stats):
        renderer.panel(rect, (31, 40, 56), PANEL_BORDER)
        renderer.text(
            renderer.fit_text(character.name, rect.width - 24, title=True),
            rect.x + 12, rect.y + 8, GOLD, title=True, max_width=rect.width - 24,
        )
        identity = f"{character.race.name} · {character.character_class.name} · {character.age} yaş"
        renderer.wrapped_text(identity, rect.x + 12, rect.y + 42, rect.width - 24, TEXT_SOFT, line_height=19, max_lines=2)
        level = stats.get("level", character.progression.level)
        xp = stats.get("experience", character.progression.experience)
        required = stats.get("experience_to_next_level", character.progression.experience_to_next_level)
        renderer.text(f"SEVİYE {level}", rect.x + 12, rect.bottom - 20, MUTED, max_width=rect.width - 24)
        renderer.bar(renderer.pg.Rect(rect.x + 92, rect.bottom - 17, max(30, rect.width - 106), 8), xp / required if required else 0, GOLD)

    def _render_combat(self, renderer, rect, stats):
        renderer.panel(rect, (27, 35, 50), PANEL_BORDER)
        current = stats.get("current_hit_points", 0) or 0
        maximum = stats.get("max_hit_points", 0) or 0
        renderer.text("CAN", rect.x + 12, rect.y + 10, MUTED)
        renderer.bar(renderer.pg.Rect(rect.x + 52, rect.y + 13, max(60, rect.width - 150), 12), current / maximum if maximum else 0, GOOD)
        renderer.text(f"{current}/{maximum}", rect.right - 78, rect.y + 9, TEXT_SOFT, max_width=66)
        values = (
            ("SALDIRI", stats.get("attack_bonus", 0)),
            ("SAVUNMA", stats.get("defense_bonus", 0)),
            ("İLK HAMLE", stats.get("initiative_bonus", 0)),
            ("SİLAH HASARI", stats.get("weapon_damage", 0)),
        )
        column_width = max(120, (rect.width - 24) // 2)
        for index, (label, value) in enumerate(values):
            x = rect.x + 12 + (index % 2) * column_width
            y = rect.y + 39 + (index // 2) * 20
            renderer.text(label, x, y, MUTED, max_width=column_width - 48)
            rendered = f"{value:+}" if label != "SİLAH HASARI" else str(value)
            renderer.text(rendered, x + column_width - 42, y, GOLD, max_width=38)

    def _render_attributes(self, renderer, rect, stats):
        renderer.panel(rect, (27, 35, 50), PANEL_BORDER)
        renderer.text("NİTELİKLER", rect.x + 10, rect.y + 9, GOLD, max_width=rect.width - 20)
        attributes = stats.get("attributes", {})
        modifiers = stats.get("modifiers", {})
        gap = 6
        cell_width = (rect.width - 24 - gap) // 2
        for index, key in enumerate(self.ATTRIBUTE_LABELS):
            column, row = index % 2, index // 2
            card = renderer.pg.Rect(rect.x + 10 + column * (cell_width + gap), rect.y + 38 + row * 55, cell_width, 47)
            renderer.panel(card, (35, 44, 60), PANEL_BORDER)
            renderer.text(self.ATTRIBUTE_LABELS[key], card.x + 7, card.y + 5, TEXT_SOFT, max_width=card.width - 14)
            renderer.text(str(attributes.get(key, 10)), card.x + 7, card.y + 24, GOLD, max_width=card.width - 44)
            modifier = modifiers.get(key, 0)
            renderer.text(f"{modifier:+}", card.right - 34, card.y + 24, GOOD if modifier >= 0 else MUTED, max_width=28)

    def _render_skills(self, renderer, rect, character):
        renderer.panel(rect, (27, 35, 50), PANEL_BORDER)
        renderer.text("BECERİLER", rect.x + 10, rect.y + 9, GOLD, max_width=rect.width - 20)
        renderer.text(f"Gelişim puanı: {character.progression.unspent_points}", rect.x + 10, rect.y + 28, MUTED, max_width=rect.width - 20)
        skills = self._skill_rows(character)
        visible_count = 7
        x, y, width, height = self._skill_bounds(rect)
        self._last_skill_bounds = (x, y, width, height)
        if not skills:
            renderer.text("Beceri kaydı yok.", x, y + 4, MUTED, max_width=width)
        else:
            self.selected_skill %= len(skills)
            self.skill_scroll = max(0, min(max(0, len(skills) - visible_count), self.skill_scroll))
            for row_index, (skill, value) in enumerate(skills[self.skill_scroll:self.skill_scroll + visible_count]):
                index = self.skill_scroll + row_index
                row = renderer.pg.Rect(x, y + row_index * height, width, height - 3)
                selected = index == self.selected_skill
                if selected:
                    renderer.panel(row, BUTTON_SELECTED, HIGHLIGHT)
                elif renderer.hovered(row):
                    renderer.panel(row, BUTTON_HOVER, PANEL_BORDER)
                renderer.text(skill.replace("_", " ").title(), row.x + 7, row.y + 3, TEXT_SOFT, max_width=row.width - 48)
                renderer.text(str(value), row.right - 34, row.y + 3, GOLD if selected else TEXT_SOFT, max_width=26)
        if self.message:
            renderer.text(renderer.fit_text(self.message, rect.width - 20), rect.x + 10, rect.bottom - 30, GOOD, max_width=rect.width - 20)
        renderer.text("↑ / ↓ seç · Enter: puan harca", rect.x + 10, rect.bottom - 17, MUTED, max_width=rect.width - 20)

    def _render_equipment(self, renderer, rect, character):
        renderer.panel(rect, (27, 35, 50), PANEL_BORDER)
        renderer.text("EKİPMAN", rect.x + 10, rect.y + 9, GOLD, max_width=rect.width - 20)
        rows = self._equipment_rows(character)
        gap = 6
        cell_width = (rect.width - 24 - gap) // 2
        for index, (slot, item_id) in enumerate(rows):
            column, row_index = index % 2, index // 2
            cell = renderer.pg.Rect(rect.x + 10 + column * (cell_width + gap), rect.y + 38 + row_index * 48, cell_width, 42)
            renderer.panel(cell, (35, 44, 60), PANEL_BORDER)
            renderer.text(self.EQUIPMENT_LABELS[slot], cell.x + 6, cell.y + 4, MUTED, max_width=cell.width - 12)
            item = self.service.item(item_id) if item_id else None
            item_name = item.name if item is not None else ("Boş" if item_id is None else "Bilinmiyor")
            renderer.text(renderer.fit_text(item_name, cell.width - 12), cell.x + 6, cell.y + 21, GOLD if item_id else TEXT_SOFT, max_width=cell.width - 12)
