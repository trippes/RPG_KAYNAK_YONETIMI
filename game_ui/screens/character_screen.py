from ..renderer import (
    GOOD, GOLD, HIGHLIGHT, MUTED, PANEL_BORDER, TEXT, TEXT_SOFT,
    BUTTON_HOVER, BUTTON_SELECTED,
)


class CharacterScreen:
    """Character-sheet content rendered inside the movable gameplay window."""

    CONTENT_X = 24
    CONTENT_Y = 126
    CONTENT_WIDTH = 760
    CONTENT_HEIGHT = 430
    PADDING = 16
    HEADER_HEIGHT = 42
    GAP = 12

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
        self.message = ""

    def handle(self, state):
        character = self.service.actor_character("hero")
        skills = tuple(character.skills.to_dict()) if character is not None else ()
        if skills:
            self.selected_skill %= len(skills)
            if state.pressed("up"):
                self.selected_skill = (self.selected_skill - 1) % len(skills)
            if state.pressed("down"):
                self.selected_skill = (self.selected_skill + 1) % len(skills)
            if state.pressed("confirm"):
                try:
                    value = self.service.improve_skill("hero", skills[self.selected_skill])
                    self.message = f"{skills[self.selected_skill]} becerisi {value} oldu."
                except (KeyError, ValueError, RuntimeError) as error:
                    self.message = str(error)
        else:
            self.selected_skill = 0
        return None

    def _layout(self):
        x, y = self.CONTENT_X, self.CONTENT_Y
        width, height = self.CONTENT_WIDTH, self.CONTENT_HEIGHT
        pad, gap = self.PADDING, self.GAP
        inner_width = width - pad * 2
        top_height = 126
        lower_y = y + self.HEADER_HEIGHT + top_height + gap
        lower_height = height - self.HEADER_HEIGHT - top_height - gap - pad
        left_width = 344
        return {
            "outer": (x, y, width, height),
            "summary": (x + pad, y + self.HEADER_HEIGHT, 242, top_height - 10),
            "attributes": (x + pad + 242 + gap, y + self.HEADER_HEIGHT,
                           inner_width - 242 - gap, top_height - 10),
            "skills": (x + pad, lower_y, left_width, lower_height),
            "quests": (x + pad + left_width + gap, lower_y,
                       inner_width - left_width - gap, lower_height),
        }

    def render(self, renderer):
        # The WindowManager draws the title bar and owns the outer window frame.
        snapshot = self.service.state()
        layout = self._layout()
        outer = renderer.pg.Rect(*layout["outer"])
        renderer.panel(outer, (25, 31, 43), (145, 118, 70))
        renderer.text("KARAKTER PROFİLİ", outer.x + 18, outer.y + 10, GOLD)
        renderer.text(
            "Özellikler, gelişim ve macera durumu",
            outer.x + 18, outer.y + 26, MUTED,
        )

        if not snapshot.actors:
            renderer.text(
                "Karakter kaydı bulunamadı.",
                outer.x + 24, outer.y + 92, MUTED,
            )
            return

        actor = snapshot.actors[0]
        stats = self.service.actor_stats(actor.actor_id) or {}
        character = self.service.actor_character("hero")
        self._render_summary(renderer, renderer.pg.Rect(*layout["summary"]), stats)
        self._render_attributes(
            renderer, renderer.pg.Rect(*layout["attributes"]), stats.get("attributes", {})
        )
        self._render_skills(renderer, renderer.pg.Rect(*layout["skills"]), character)
        quest_rect = renderer.pg.Rect(*layout["quests"])
        renderer.panel(quest_rect, (27, 35, 50), PANEL_BORDER)
        renderer.text("GÖREV DURUMU", quest_rect.x + 14, quest_rect.y + 12, GOLD)
        renderer.quest_panel(
            self.service,
            renderer.pg.Rect(
                quest_rect.x + 8, quest_rect.y + 34,
                quest_rect.width - 16, quest_rect.height - 42,
            ),
        )

    def _render_summary(self, renderer, rect, stats):
        renderer.panel(rect, (32, 40, 54), PANEL_BORDER)
        name = stats.get("name") or "Gezgin"
        renderer.text(
            renderer.fit_text(name, rect.width - 28),
            rect.x + 14, rect.y + 12, GOLD, title=True,
            max_width=rect.width - 28,
        )
        renderer.text(
            f"SEVİYE {stats.get('level', 1)}  ·  {stats.get('age', 0)} yaş",
            rect.x + 14, rect.y + 42, TEXT_SOFT,
        )
        current_hp = stats.get("current_hit_points", 0)
        max_hp = stats.get("max_hit_points", 0)
        renderer.text("CAN", rect.x + 14, rect.y + 70, MUTED)
        renderer.bar(
            renderer.pg.Rect(rect.x + 54, rect.y + 73, rect.width - 126, 12),
            current_hp / max_hp if max_hp else 0,
            GOOD,
        )
        renderer.text(
            f"{current_hp}/{max_hp}",
            rect.right - 62, rect.y + 68, TEXT_SOFT,
        )
        renderer.text(
            f"Saldırı +{stats.get('attack_bonus', 0)}   Savunma +{stats.get('defense_bonus', 0)}",
            rect.x + 14, rect.y + 94, TEXT_SOFT,
            max_width=rect.width - 28,
        )

    def _render_attributes(self, renderer, rect, attributes):
        renderer.panel(rect, (27, 35, 50), PANEL_BORDER)
        renderer.text("TEMEL ÖZELLİKLER", rect.x + 14, rect.y + 12, GOLD)
        values = tuple(attributes.items())[:6]
        columns = 3
        gap = 7
        card_width = (rect.width - 28 - gap * (columns - 1)) // columns
        for index, (attribute, value) in enumerate(values):
            column, row = index % columns, index // columns
            card = renderer.pg.Rect(
                rect.x + 14 + column * (card_width + gap),
                rect.y + 42 + row * 34,
                card_width, 29,
            )
            hovered = renderer.hovered(card)
            renderer.panel(
                card,
                BUTTON_HOVER if hovered else (35, 44, 60),
                HIGHLIGHT if hovered else PANEL_BORDER,
            )
            key = str(getattr(attribute, "value", attribute))
            label = self.ATTRIBUTE_LABELS.get(key, key.replace("_", " ").title())
            renderer.text(label, card.x + 7, card.y + 6, TEXT_SOFT,
                          max_width=card.width - 35)
            renderer.text(str(value), card.right - 25, card.y + 6, GOLD)

    def _render_skills(self, renderer, rect, character):
        renderer.panel(rect, (27, 35, 50), PANEL_BORDER)
        points = character.progression.unspent_points if character else 0
        renderer.text("BECERİ GELİŞİMİ", rect.x + 14, rect.y + 12, GOLD)
        renderer.text(f"Kullanılabilir puan: {points}",
                      rect.x + 14, rect.y + 31, MUTED)

        skills = tuple(character.skills.to_dict().items()) if character else ()
        if not skills:
            renderer.text("Geliştirilebilir beceri bulunmuyor.",
                          rect.x + 14, rect.y + 66, MUTED)
        else:
            visible = skills[:6]
            for index, (skill, value) in enumerate(visible):
                row = renderer.pg.Rect(
                    rect.x + 12, rect.y + 56 + index * 25,
                    rect.width - 24, 22,
                )
                selected = index == self.selected_skill
                if selected:
                    renderer.panel(row, BUTTON_SELECTED, HIGHLIGHT)
                renderer.text(
                    f"{'› ' if selected else '  '}{skill}",
                    row.x + 8, row.y + 3,
                    GOOD if selected else TEXT_SOFT,
                    max_width=row.width - 56,
                )
                renderer.text(str(value), row.right - 26, row.y + 3,
                              GOLD if selected else TEXT_SOFT)

        if self.message:
            renderer.text(
                renderer.fit_text(self.message, rect.width - 28),
                rect.x + 14, rect.bottom - 42, GOOD,
                max_width=rect.width - 28,
            )
        renderer.text(
            "↑ / ↓ Seç   Enter: Puan harca",
            rect.x + 14, rect.bottom - 22, MUTED,
        )
