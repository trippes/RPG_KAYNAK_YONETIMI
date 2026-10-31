from ..renderer import GOOD, MUTED, TEXT_SOFT, WARN


class QuestLogScreen:
    """Full quest journal with separate active and completed sections."""

    def __init__(self, service):
        self.service = service

    def handle(self, state):
        if state.pressed("world") or state.pressed("back"):
            return "world"
        if state.pressed("character"):
            return "character"
        return None

    def render(self, renderer):
        renderer.frame("Görev Günlüğü")
        renderer.hud(self.service)
        log = self.service.application.holder.current.quest_log
        active = log.active()
        completed = log.completed()

        left = renderer.pg.Rect(32, 132, renderer.width // 2 - 48, 390)
        right = renderer.pg.Rect(renderer.width // 2 + 16, 132, renderer.width // 2 - 48, 390)
        self._render_section(renderer, left, "Devam Eden Görevler", active, WARN)
        self._render_section(renderer, right, "Tamamlanan Görevler", completed, GOOD)
        renderer.footer("W Yerel Harita   P Karakter   Esc Geri")

    @staticmethod
    def _render_section(renderer, rect, title, quests, title_color):
        renderer.panel(rect)
        renderer.text(title, rect.x + 18, rect.y + 16, title_color)
        if not quests:
            renderer.text("Henüz görev yok.", rect.x + 18, rect.y + 60, MUTED)
            return
        y = rect.y + 58
        for quest in quests:
            renderer.text(
                renderer.fit_text(quest.title, rect.width - 36),
                rect.x + 18, y, title_color,
            )
            y += 28
            for objective in quest.objectives:
                marker = "[x]" if objective.completed else "[ ]"
                line = f"{marker} {objective.description} ({objective.progress}/{objective.required})"
                y = renderer.wrapped_text(
                    line, rect.x + 22, y, rect.width - 44,
                    TEXT_SOFT if not objective.completed else GOOD,
                    line_height=20, max_lines=1,
                ) + 4
            y += 12
            if y > rect.bottom - 42:
                renderer.text("Daha fazla görev için kayıt günlüğünü açın.", rect.x + 18, rect.bottom - 30, MUTED)
                break
