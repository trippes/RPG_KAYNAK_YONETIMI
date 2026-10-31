from resources import Quantity, ResourceUnit


class WorldScreen:
    def __init__(self, service, inventory_id="player"):
        self.service = service
        self.inventory_id = inventory_id
        self.selected = 0
        self.message = "Bir eylem seç veya haritada ilerle."

    def _current_location(self, actors):
        if not actors:
            return None, None
        world_map = self.service.application.holder.current.movement.map_for(actors[0].world_id)
        if world_map is None:
            return None, None
        return world_map, world_map.get(actors[0].location_id)

    def _has_activity(self, location, activity):
        return location is not None and activity in location.activities

    def _action_specs(self):
        return (
            ("dialogue", "D", "Diyalog"),
            ("market", "M", "Pazar"),
            ("gather", "G", "Topla"),
            ("combat", "B", "Savaş"),
            ("map", "X", "Dünya haritası"),
            ("local_map", "L", "Yerel harita"),
        )

    def _action_rects(self, renderer):
        left = 32
        top = 522
        width = 140
        gap = 8
        return {
            action: renderer.pg.Rect(left + index * (width + gap), top, width, 38)
            for index, (action, _key, _label) in enumerate(self._action_specs())
        }

    def _inject_mouse_action(self, state, renderer):
        if not state.mouse_clicked or state.mouse_pos is None:
            return

        snapshot = self.service.state()
        actors = snapshot.actors
        _, location = self._current_location(actors)
        activities = set(location.activities) if location else set()

        for action, rect in self._action_rects(renderer).items():
            if not rect.collidepoint(state.mouse_pos):
                continue

            enabled = action in activities or action in {"map", "local_map"}
            if enabled:
                state.actions.add(action)
            else:
                self.message = "Bu eylem mevcut lokasyonda kullanılamıyor."
            return

    def handle(self, state):
        snapshot = self.service.state()
        nodes = snapshot.nodes
        actors = snapshot.actors
        current_map, current_location = self._current_location(actors)



        if actors and (state.pressed("right") or state.pressed("left")):
            actor = actors[0]
            world_map = self.service.application.holder.current.movement.map_for(actor.world_id)
            if world_map is not None:
                locations = world_map.locations()
                current = next(
                    (index for index, location in enumerate(locations)
                     if location.location_id == actor.location_id),
                    0,
                )
                destination = locations[(current + (1 if state.pressed("right") else -1)) % len(locations)]
                try:
                    self.service.move_actor(actor.actor_id, destination.location_id)
                    self.service.advance_by(1)
                    self.message = f"{destination.name} konumuna gidildi."
                except (KeyError, ValueError, RuntimeError) as error:
                    self.message = f"Seyahat başarısız: {error}"

        if nodes:
            if state.pressed("up"):
                self.selected = (self.selected - 1) % len(nodes)
            if state.pressed("down"):
                self.selected = (self.selected + 1) % len(nodes)

            node = nodes[self.selected]

            if state.pressed("gather"):
                if not self._has_activity(current_location, "gather"):
                    self.message = "Bu lokasyonda toplanacak kaynak yok."
                    return None
                try:
                    actor = actors[0] if actors else None
                    if actor is not None and node.location_id is not None:
                        self.service.start_gathering_at_location(
                            actor.actor_id,
                            node.location_id,
                            node.node_id,
                            self.inventory_id,
                            Quantity(1, ResourceUnit(node.quantity[1])),
                        )
                    else:
                        self.service.collect(
                            node.node_id,
                            self.inventory_id,
                            Quantity(1, ResourceUnit(node.quantity[1])),
                        )
                    self.message = f"{node.resource_type} toplandı."
                except (KeyError, ValueError, RuntimeError) as error:
                    self.message = f"Toplama başarısız: {error}"

            if state.pressed("craft"):
                try:
                    self.service.start_production("campfire", self.inventory_id, "campfire")
                    self.message = "Üretim başladı; Space ile zamanı ilerlet."
                except (KeyError, ValueError, RuntimeError) as error:
                    self.message = f"Üretim başarısız: {error}"

        if state.pressed("wait"):
            try:
                self.service.advance_by(1)
                self.message = "Bir tick ilerletildi."
            except RuntimeError as error:
                self.message = str(error)

        if state.pressed("market"):
            if not self._has_activity(current_location, "market"):
                self.message = "Pazar yalnızca yerleşim yerlerinde kullanılabilir."
                return None
            return "market"

        if state.pressed("dialogue"):
            if not self._has_activity(current_location, "dialogue"):
                self.message = "Bu lokasyonda konuşulacak NPC yok."
                return None
            return "dialogue"

        if state.pressed("combat"):
            if not self._has_activity(current_location, "combat"):
                self.message = "Bu lokasyonda karşılaşma yok."
                return None
            return "combat"

        if state.pressed("inventory"):
            return "inventory"
        if state.pressed("character"):
            return "character"
        if state.pressed("map"):
            return "map"
        if state.pressed("local_map"):
            return "local_map"
        if state.pressed("character_creation"):
            return "character_creation"
        if state.pressed("back"):
            return "menu"
        return None

    def render(self, renderer):
        snapshot = self.service.state()
        renderer.frame(f"Dünya — {snapshot.world_id}", snapshot.simulation_tick)
        renderer.hud(self.service)

        actors = snapshot.actors
        current_location = actors[0].location_id if actors else None
        world_map = None
        location = None

        if actors:
            world_map = self.service.application.holder.current.movement.map_for(actors[0].world_id)
            location = world_map.get(current_location) if world_map and current_location else None

        map_rect = renderer.pg.Rect(24, 130, 620, 350)
        renderer.panel(map_rect, (22, 30, 43), (62, 78, 101))
        renderer.text("Dünya haritası", 48, 150, title=True)

        if world_map is not None:
            renderer.world_map(world_map, current_location_id=current_location, rect=map_rect)
        else:
            renderer.text("Bu dünyada harita bulunamadı.", 52, 220, (155, 172, 196))

        renderer.panel(renderer.pg.Rect(670, 130, 250, 350))
        renderer.text("Lokasyon özeti", 694, 150, title=True)

        if location:
            renderer.text(location.name, 694, 204, (220, 190, 120))
            renderer.text(f"{location.location_type} bölgesi", 694, 232, (155, 172, 196))
            renderer.wrapped_text(location.description, 694, 260, 205, (190, 202, 220), line_height=24)

            renderer.text("Burada yapılabilir", 694, 330, title=True)
            labels = {
                "dialogue": "Diyalog",
                "market": "Pazar",
                "gather": "Toplama",
                "combat": "Combat",
                "travel": "Seyahat",
            }
            renderer.text(
                "  ".join(labels.get(item, item) for item in location.activities),
                694,
                364,
                (220, 190, 120),
            )

        renderer.text(self.message, 28, 500, (220, 190, 120))

        activities = set(location.activities) if location else set()
        for action, key, label in self._action_specs():
            enabled = action in activities or action in {"map", "local_map"}
            rect = self._action_rects(renderer)[action]
            renderer.action_button(rect, key, label, enabled=enabled)

        renderer.footer("Butona tıkla veya kısayolu kullan   I Envanter   P Karakter   F5 Kaydet   F9 Yükle")
