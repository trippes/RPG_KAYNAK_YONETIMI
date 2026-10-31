"""Local landmark map for the actor's current world location."""


class LocalMapScreen:
    def __init__(self, service):
        self.service = service
        self.selected = 0
        self.message = "Bir noktayı seçip Enter ile etkileşime geç."

    def _location(self):
        actors = self.service.state().actors
        if not actors:
            return None
        world_map = self.service.application.holder.current.movement.map_for(actors[0].world_id)
        return world_map.get(actors[0].location_id) if world_map else None

    def handle(self, state):
        location = self._location()
        landmarks = location.landmarks if location else ()
        if landmarks:
            if state.pressed("up") or state.pressed("left"):
                self.selected = (self.selected - 1) % len(landmarks)
            if state.pressed("down") or state.pressed("right"):
                self.selected = (self.selected + 1) % len(landmarks)
            if state.pressed("confirm"):
                landmark = landmarks[self.selected]
                activities = set(landmark[3])
                if "dialogue" in activities:
                    return "dialogue"
                if "market" in activities:
                    return "market"
                if "combat" in activities:
                    return "combat"
                if "gather" in activities:
                    return "world"
                self.message = f"{landmark[1]}: {landmark[4]}"
        if state.pressed("back") or state.pressed("world"):
            return "world"
        return None

    def render(self, renderer):
        snapshot = self.service.state()
        renderer.frame("Yerel Harita", snapshot.simulation_tick)
        renderer.hud(self.service)
        renderer.panel(renderer.pg.Rect(24, 130, 620, 350), (22, 30, 43), (62, 78, 101))
        location = self._location()
        landmarks = location.landmarks if location else ()
        if location:
            renderer.text(location.name, 48, 150, title=True)
        if not landmarks:
            renderer.text("Bu lokasyonda yerel harita noktası yok.", 52, 220, (155, 172, 196))
        else:
            positions = {}
            for index, landmark in enumerate(landmarks):
                raw = landmark[2]
                positions[index] = (40 + raw[0], 130 + raw[1])
            for index in range(len(landmarks) - 1):
                renderer.map_edge(positions[index], positions[index + 1], (62, 78, 101), 3)
            for index, landmark in enumerate(landmarks):
                position = positions[index]
                renderer.map_node(position, selected=index == self.selected)
                renderer.text(landmark[1], position[0] - 42, position[1] + 28, (235, 238, 245))
        renderer.panel(renderer.pg.Rect(670, 130, 250, 350))
        renderer.text("Yerel nokta", 694, 160, title=True)
        if landmarks:
            landmark = landmarks[self.selected]
            renderer.text(landmark[1], 694, 220, (220, 190, 120))
            renderer.wrapped_text(landmark[4], 694, 260, 205, (190, 202, 220), line_height=24)
            renderer.text("Eylemler", 694, 350, title=True)
            renderer.text("  ".join(landmark[3]), 694, 390, (220, 190, 120))
        renderer.text(self.message, 28, 500, (220, 190, 120))
        renderer.footer("↑/↓ Nokta seç   Enter Etkileşim   Esc Dünya")
