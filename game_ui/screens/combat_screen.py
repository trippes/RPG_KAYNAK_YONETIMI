class CombatScreen:
    def __init__(self, service):
        self.service = service
        self.message = "Enter ile ilk combatant ikinciye saldırır."

    def handle(self, state):
        if state.pressed("confirm"):
            combatants = self.service.application.holder.current.combat.all()
            if len(combatants) >= 2:
                try:
                    attacker, defender = combatants[0], combatants[1]
                    result = self.service.combat_attack(attacker.combatant_id, defender.combatant_id)
                    self.message = f"{result.attacker_id} {result.damage} hasar verdi."
                except (KeyError, ValueError) as error:
                    self.message = str(error)
        if state.pressed("wait"):
            encounters = self.service.application.holder.current.combat.encounters()
            if encounters:
                active = self.service.next_combat_turn(encounters[0].encounter_id)
                self.message = f"Sıra {active} karakterine geçti."
            else:
                self.service.advance_combat_round()
                self.message = "Combat turu ilerletildi."
        if state.pressed("back") or state.pressed("world"):
            return "world"
        return None

    def render(self, renderer):
        renderer.frame("Savaş")
        renderer.hud(self.service)
        renderer.panel(renderer.pg.Rect(70, 130, 820, 350))
        renderer.text("Karşılaşma", 100, 160, title=True)
        combatants = self.service.application.holder.current.combat.all()
        if not combatants:
            renderer.text("Aktif combatant yok.", 100, 190)
        for index, combatant in enumerate(combatants):
            status = ", ".join(combatant.statuses) or "status yok"
            renderer.text(f"{combatant.combatant_id} — HP {combatant.hit_points}/{combatant.max_hit_points} — {status}", 100, 220 + index * 56, title=index == 0)
        encounters = self.service.application.holder.current.combat.encounters()
        if encounters:
            encounter = encounters[0]
            renderer.text(f"Tur {encounter.round_number} — Sıra: {encounter.active_combatant_id}", 100, 360, (190, 202, 220))
        renderer.text(self.message, 70, 500, (220, 190, 120))
        renderer.footer("Enter Saldır   Space Tur geçir   Esc Dünya")
