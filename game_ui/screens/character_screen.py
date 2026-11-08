from ..renderer import (
    GOOD, GOLD, HIGHLIGHT, MUTED, PANEL_BORDER, TEXT, TEXT_SOFT,
    BUTTON_HOVER, BUTTON_SELECTED,
)


class CharacterScreen:
    def __init__(self, service):
        self.service = service
        self.selected_skill = 0
        self.message = ""

    def handle(self, state):
        if state.pressed("world") or state.pressed("back"):
            return "world"
        if state.pressed("inventory"):
            return "inventory"
        character = self.service.actor_character("hero")
        skills = tuple(character.skills.to_dict()) if character is not None else ()
        if skills:
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
        return None

    def render(self, renderer):
        snapshot = self.service.state()
        renderer.frame("Karakter")
        renderer.hud(self.service)
        if not snapshot.actors:
            renderer.panel(renderer.pg.Rect(24, 126, 760, 430), (25, 31, 43), (145, 118, 70))
            renderer.text("Karakter kaydı bulunamadı.", 50, 180, MUTED)
            return

        actor = snapshot.actors[0]
        stats = self.service.actor_stats(actor.actor_id) or {}
        renderer.panel(renderer.pg.Rect(24, 126, 760, 430), (25, 31, 43), (145, 118, 70))

        # Summary card: identity and combat readiness.
        summary = renderer.pg.Rect(40, 146, 246, 166)
        renderer.panel(summary, (32, 40, 54), PANEL_BORDER)
        renderer.text(stats.get("name", actor.actor_id), 56, 160, GOLD, title=True, max_width=210)
        renderer.text(
            f"Seviye {stats.get('level', 1)}   {stats.get('age', 0)} yaş",
            58, 202, TEXT_SOFT,
        )
        current_hp = stats.get("current_hit_points", 0)
        max_hp = stats.get("max_hit_points", 0)
        renderer.text("Can", 58, 234, MUTED)
        renderer.bar(renderer.pg.Rect(96, 238, 140, 13), current_hp / max_hp if max_hp else 0, GOOD)
        renderer.text(f"{current_hp}/{max_hp}", 58, 258, TEXT_SOFT)
        renderer.text(
            f"Saldırı +{stats.get('attack_bonus', 0)}   Savunma +{stats.get('defense_bonus', 0)}",
            58, 280, TEXT_SOFT, max_width=210,
        )

        # Attribute cards preserve the existing values while making them scannable.
        attributes = tuple(stats.get("attributes", {}).items())
        attributes_panel = renderer.pg.Rect(304, 146, 464, 166)
        renderer.panel(attributes_panel, (27, 35, 50), PANEL_BORDER)
        renderer.text("Temel Özellikler", 322, 158, GOLD)
        attribute_labels = {
            "strength": "Güç", "dexterity": "Çeviklik",
            "constitution": "Dayanıklılık", "intelligence": "Zeka",
            "wisdom": "Bilgelik", "charisma": "Karizma",
        }
        for index, (attribute, value) in enumerate(attributes[:6]):
            column, row = index % 3, index // 3
            rect = renderer.pg.Rect(320 + column * 145, 190 + row * 52, 132, 40)
            hovered = renderer.hovered(rect)
            fill = BUTTON_HOVER if hovered else (BUTTON_SELECTED if value >= 14 else (35, 44, 60))
            border = HIGHLIGHT if hovered else PANEL_BORDER
            renderer.panel(rect, fill, border)
            label = attribute_labels.get(str(getattr(attribute, "value", attribute)), str(attribute))
            renderer.text(label, rect.x + 10, rect.y + 6, TEXT_SOFT, max_width=92)
            renderer.text(str(value), rect.right - 28, rect.y + 6, GOLD, max_width=20)

        character = self.service.actor_character("hero")
        skill_values = tuple(character.skills.to_dict().items()) if character is not None else ()
        skill_panel = renderer.pg.Rect(40, 330, 350, 210)
        renderer.panel(skill_panel, (27, 35, 50), PANEL_BORDER)
        renderer.text(
            f"Beceriler   Puan: {character.progression.unspent_points if character else 0}",
            58, 346, GOLD,
        )
        if skill_values:
            for index, (skill, value) in enumerate(skill_values[:6]):
                color = GOOD if index == self.selected_skill else TEXT_SOFT
                row = renderer.pg.Rect(56, 378 + index * 25, 318, 22)
                if index == self.selected_skill:
                    renderer.panel(row, BUTTON_SELECTED, HIGHLIGHT)
                renderer.text(
                    f"{'> ' if index == self.selected_skill else '  '}{skill}",
                    66, 380 + index * 25, color, max_width=230,
                )
                renderer.text(str(value), 342, 380 + index * 25, color)
        else:
            renderer.text("Sınıf becerisi bulunmuyor.", 58, 390, MUTED)
        if self.message:
            renderer.text(renderer.fit_text(self.message, 320), 58, 510, GOOD)
        renderer.quest_panel(self.service, renderer.pg.Rect(410, 330, 358, 210))
        renderer.text("↑/↓ Beceri seç   Enter Puan harca   Esc Kapat", 410, 548, MUTED, max_width=358)
