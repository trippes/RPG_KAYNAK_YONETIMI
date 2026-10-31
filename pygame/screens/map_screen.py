"""Interactive location graph view for the playable world."""

from ..renderer import ACTIVITY_LABELS, GOLD, MUTED, TEXT_SOFT


class MapScreen:
    def __init__(self, service):
        self.service = service
        self.selected = 0
        self._selection_initialized = False
        self.message = "Bir lokasyon seçip Enter ile seyahat et."

    def _context(self):
        actors = self.service.state().actors
        if not actors:
            return None, None, ()
        actor = actors[0]
        world_map = self.service.application.holder.current.movement.map_for(actor.world_id)
        if world_map is None:
            return actor, None, ()
        locations = world_map.locations()
        if not self._selection_initialized and locations:
            self.selected = next(
                (index for index, location in enumerate(locations) if location.location_id == actor.location_id),
                0,
            )
            self._selection_initialized = True
        return actor, world_map, locations


    def handle(self, state):
        actor, world_map, locations = self._context()

        if locations and state.mouse_clicked and state.mouse_pos is not None:
            mx, my = state.mouse_pos
            for index, location in enumerate(locations):
                raw = location.position or (150 + index * 180, 220)
                x, y = 40 + raw[0], 112 + raw[1]
                if (mx - x) ** 2 + (my - y) ** 2 <= 28 ** 2:
                    self.selected = index
                    break

        if locations:
            if state.pressed("up") or state.pressed("left"):
                self.selected = (self.selected - 1) % len(locations)
            if state.pressed("down") or state.pressed("right"):
                self.selected = (self.selected + 1) % len(locations)
            if state.pressed("confirm") and actor is not None:
                destination = locations[self.selected]
                if destination.location_id == actor.location_id:
                    return "local_map"
                self.message = (
                    "Dünya haritası yalnızca konumları gösterir. "
                    "Konum değiştirmek için Yerel Harita'yı kullanın."
                )

        if state.pressed("back") or state.pressed("world"):
            return "local_map"
        return None

    def render(self, renderer):
        snapshot = self.service.state()
        renderer.frame("Harita", snapshot.simulation_tick)
        renderer.hud(self.service)
        renderer.panel(renderer.pg.Rect(24, 110, 912, 410), (22, 30, 43), (62, 78, 101))
        actor, world_map, locations = self._context()
        if not locations or world_map is None:
            renderer.text("Bu dünyada harita bulunamadı.", 52, 190)
        else:
            current_id = actor.location_id if actor else None
            selected_id = locations[self.selected].location_id if locations else None
            renderer.world_map(world_map, current_id, selected_id, renderer.pg.Rect(24, 110, 912, 410))
        renderer.panel(renderer.pg.Rect(24, 530, 912, 32), (22, 30, 43), (62, 78, 101))
        if locations:
            selected = locations[self.selected]
            neighbors = world_map.neighbors(selected.location_id) if world_map is not None else ()
            detail = f"{selected.name} — {selected.location_type} — Komşular: "
            detail += ", ".join(item.name for item in neighbors) if neighbors else "yok"
            renderer.text(renderer.fit_text(detail, 880), 40, 536, TEXT_SOFT)
        renderer.text(self.message, 28, 500, (220, 190, 120))
        renderer.footer("↑/↓ Hedef seç   Enter Seyahat   Esc Yerel Harita")
