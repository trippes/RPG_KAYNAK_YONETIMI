from ..renderer import GOOD, GOLD, MUTED, TEXT_SOFT


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
        renderer.panel(renderer.pg.Rect(40, 130, 560, 390))
        if not snapshot.actors:
            renderer.text("Karakter kaydı bulunamadı.", 100, 190)
        for index, actor in enumerate(snapshot.actors):
            stats = self.service.actor_stats(actor.actor_id)
            if stats is None:
                line = f"{actor.actor_id} — {actor.role} — {'aktif' if actor.active else 'pasif'}"
            else:
                line = (
                    f"{stats['name']} ({stats['age']} yaş) — Lv {stats['level']} — "
                    f"XP {stats['experience']}/{stats['experience_to_next_level']} — "
                    f"HP {stats['current_hit_points']}/{stats['max_hit_points']}"
                )
                detail = "  ".join(f"{key[:3].upper()} {value}" for key, value in stats["attributes"].items())
                renderer.text(detail, 90, 225 + index * 72, (190, 202, 220))
                renderer.text(
                    f"Saldırı +{stats['attack_bonus']}  Savunma +{stats['defense_bonus']}  "
                    f"İnisiyatif +{stats['initiative_bonus']}",
                    90, 279 + index * 72, (170, 185, 205),
                )
                skills = "  ".join(f"{key[:3].upper()} {value}" for key, value in stats["skills"].items())
                renderer.text(renderer.fit_text(skills or "Beceri yok", 480), 90, 306 + index * 72, MUTED)
            renderer.text(line, 70, 170 + index * 72, title=index == 0)
        character = self.service.actor_character("hero")
        skill_values = tuple(character.skills.to_dict().items()) if character is not None else ()
        skill_panel = renderer.pg.Rect(40, 390, 560, 130)
        renderer.panel(skill_panel, (27, 35, 50), (86, 105, 135))
        renderer.text(
            f"Beceri geliştirme  (puan: {character.progression.unspent_points if character else 0})",
            58, 404, GOLD,
        )
        if skill_values:
            for index, (skill, value) in enumerate(skill_values[:3]):
                color = GOOD if index == self.selected_skill else TEXT_SOFT
                renderer.text(
                    f"{'> ' if index == self.selected_skill else '  '}{skill}: {value}",
                    62, 438 + index * 24, color,
                )
        else:
            renderer.text("Sınıf becerisi bulunmuyor.", 62, 444, MUTED)
        if self.message:
            renderer.text(renderer.fit_text(self.message, 540), 58, 508, GOOD)
        renderer.quest_panel(self.service, renderer.pg.Rect(625, 130, 295, 390))
        renderer.footer("↑/↓ Beceri seç   Enter Puan harca   W Yerel Harita   I Envanter   Esc Geri")
