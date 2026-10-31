from ..renderer import MUTED


class CharacterScreen:
    def __init__(self, service):
        self.service = service

    def handle(self, state):
        if state.pressed("world") or state.pressed("back"):
            return "world"
        if state.pressed("inventory"):
            return "inventory"
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
                line = f"{stats['name']} — Lv {stats['level']} — HP {stats['current_hit_points']}/{stats['max_hit_points']}"
                detail = "  ".join(f"{key[:3].upper()} {value}" for key, value in stats["attributes"].items())
                renderer.text(detail, 90, 225 + index * 72, (190, 202, 220))
                skills = "  ".join(
                    f"{key[:3].upper()} {value}"
                    for key, value in stats["skills"].items()
                )
                renderer.text(
                    renderer.fit_text(skills or "Beceri yok", 480),
                    90, 252 + index * 72, MUTED,
                )
            renderer.text(line, 70, 170 + index * 72, title=index == 0)
        renderer.quest_panel(self.service, renderer.pg.Rect(625, 130, 295, 390))
        renderer.footer("W Yerel Harita   I Envanter   Esc Geri")
