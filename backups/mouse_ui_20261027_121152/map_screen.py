"""Interactive location graph view for the playable world."""


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
        if locations:
            if state.pressed("up") or state.pressed("left"):
                self.selected = (self.selected - 1) % len(locations)
            if state.pressed("down") or state.pressed("right"):
                self.selected = (self.selected + 1) % len(locations)
            if state.pressed("confirm") and actor is not None:
                destination = locations[self.selected]
                if destination.location_id == actor.location_id:
                    return "local_map"
                else:
                    try:
                        self.service.move_actor(actor.actor_id, destination.location_id)
                        self.service.advance_by(1)
                        self.message = f"{destination.name} konumuna gidildi."
                    except (KeyError, ValueError, RuntimeError) as error:
                        self.message = f"Seyahat başarısız: {error}"
        if state.pressed("back") or state.pressed("world"):
            return "world"
        return None

    def render(self, renderer):
        snapshot = self.service.state()
        renderer.frame("Harita", snapshot.simulation_tick)
        renderer.hud(self.service)
        renderer.panel(renderer.pg.Rect(24, 130, 620, 350), (22, 30, 43), (62, 78, 101))
        actor, world_map, locations = self._context()
        if not locations or world_map is None:
            renderer.text("Bu dünyada harita bulunamadı.", 52, 190)
        else:
            current_id = actor.location_id if actor else None
            selected_id = locations[self.selected].location_id if locations else None
            renderer.world_map(world_map, current_id, selected_id, renderer.pg.Rect(24, 130, 620, 350))
        renderer.panel(renderer.pg.Rect(670, 130, 250, 350))
        renderer.text("Lokasyon", 694, 160, title=True)
        if locations:
            selected = locations[self.selected]
            renderer.text(selected.name, 694, 220, (220, 190, 120))
            renderer.text(f"{selected.location_type} bölgesi", 694, 248, (155, 172, 196))
            renderer.wrapped_text(selected.description, 694, 278, 205, (190, 202, 220), line_height=24)
            renderer.text("Etkinlikler", 694, 354, title=True)
            for index, activity in enumerate(selected.activities):
                renderer.text(f"• {activity}", 710, 390 + index * 24, (220, 190, 120))
            if world_map is not None:
                neighbors = world_map.neighbors(selected.location_id)
                renderer.text("Bağlantılar", 694, 450, title=True)
                if neighbors:
                    for index, neighbor in enumerate(neighbors):
                        renderer.text(f"• {neighbor.name}", 710, 478 + index * 24, (190, 202, 220))
                else:
                    renderer.text("Bağlantı yok", 710, 478, (155, 172, 196))
        renderer.text(self.message, 28, 500, (220, 190, 120))
        renderer.footer("↑/↓ Hedef seç   Enter Seyahat   Esc Dünya")

