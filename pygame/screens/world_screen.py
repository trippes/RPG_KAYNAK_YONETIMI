from resources import Quantity, ResourceUnit

from ..renderer import GOLD, MUTED, TEXT_SOFT, duration_label, resource_name, unit_label
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

    NODE_ROW_X, NODE_ROW_Y, NODE_ROW_W, NODE_ROW_H = 686, 376, 218, 26
    NODE_ROWS = 3

    @staticmethod
    def _local_nodes(nodes, actor):
        """Gather nodes the actor can reach from the current location."""
        if actor is None:
            return []
        return [
            node for node in nodes
            if node.location_id is None or node.location_id == actor.location_id
        ]

    def _node_window(self, local_nodes):
        """Index of the first visible node row so the selection stays in view."""
        return max(0, min(self.selected - self.NODE_ROWS + 1, len(local_nodes) - self.NODE_ROWS))

    @staticmethod
    def _node_amount(node):
        try:
            return f"{node.quantity[0]} {unit_label(node.quantity[1])}"
        except (TypeError, IndexError, AttributeError):
            return ""

    def _has_activity(self, location, activity):
        return location is not None and activity in location.activities

    def _action_specs(self):
        return (
            ("dialogue", "D", "Diyalog"),
            ("market", "M", "Pazar"),
            ("gather", "G", "Topla"),
            ("combat", "B", "Savaş"),
            ("map", "X", "Harita"),
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
        _current_map, current_location = self._current_location(actors)

        if state.mouse_clicked and state.mouse_pos is not None:
            x, y = state.mouse_pos
            if 522 <= y <= 560 and 32 <= x <= 920:
                index = (x - 32) // 148
                if 0 <= index < len(self._action_specs()):
                    state.actions.add(self._action_specs()[index][0])

        if actors and (state.pressed("right") or state.pressed("left")):
            actor = actors[0]
            world_map = self.service.application.holder.current.movement.map_for(actor.world_id)
            if world_map is not None:
                locations = world_map.locations()
                if locations:
                    current = next(
                        (
                            index
                            for index, location in enumerate(locations)
                            if location.location_id == actor.location_id
                        ),
                        0,
                    )
                    direction = 1 if state.pressed("right") else -1
                    destination = locations[(current + direction) % len(locations)]
                    try:
                        self.service.move_actor(actor.actor_id, destination.location_id)
                        self.service.advance_by(1)
                        self.message = f"{destination.name} konumuna gidildi."
                    except (KeyError, ValueError, RuntimeError) as error:
                        self.message = f"Seyahat başarısız: {error}"
       # Hareket sonrasında güncel oyuncu konumunu ve kaynak listesini al.
        snapshot = self.service.state()
        nodes = snapshot.nodes
        actors = snapshot.actors
        _current_map, current_location = self._current_location(actors)

        actor = actors[0] if actors else None
        local_nodes = self._local_nodes(nodes, actor)

        if local_nodes:
            # Mouse: click a row in the "Kaynak noktaları" list.
            if state.mouse_clicked and state.mouse_pos is not None:
                mx, my = state.mouse_pos
                first = self._node_window(local_nodes)
                if self.NODE_ROW_X <= mx <= self.NODE_ROW_X + self.NODE_ROW_W:
                    row = (my - self.NODE_ROW_Y) // self.NODE_ROW_H
                    if (
                        0 <= row < self.NODE_ROWS
                        and my >= self.NODE_ROW_Y
                        and first + row < len(local_nodes)
                    ):
                        self.selected = first + row

            if state.pressed("up"):
                self.selected = (self.selected - 1) % len(local_nodes)
            if state.pressed("down"):
                self.selected = (self.selected + 1) % len(local_nodes)
            self.selected %= len(local_nodes)
        else:
            self.selected = 0

        if state.pressed("gather"):
            if not self._has_activity(current_location, "gather"):
                self.message = "Bu lokasyonda toplanacak kaynak yok."
                return None
            if actor is None:
                self.message = "Toplama yapacak bir aktör bulunamadı."
                return None
            if not local_nodes:
                self.message = "Bu lokasyonda toplanacak kaynak noktası yok."
                return None

            node = local_nodes[self.selected]
            try:
                self.service.start_gathering_at_location(
                    actor.actor_id,
                    actor.location_id,
                    node.node_id,
                    self.inventory_id,
                    Quantity(1, ResourceUnit(node.quantity[1])),
                )
                self.message = (
                    f"{resource_name(node.resource_type)} toplama başladı. "
                    f"{duration_label(self.service.gathering_duration(actor.actor_id))} sürecek."
                )
            except (KeyError, ValueError, RuntimeError) as error:
                self.message = f"Toplama başarısız: {error}"

        # C: Üretim ekranını aç. Üretim bu ekranda Enter ile başlatılır.
        if state.pressed("craft"):
            return "production"

        if state.pressed("wait"):
            try:
                self.service.advance_by(1)
                self.message = "Zaman ilerletildi."
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
            world_map = self.service.application.holder.current.movement.map_for(
                actors[0].world_id
            )
            location = world_map.get(current_location) if world_map and current_location else None

        map_rect = renderer.pg.Rect(24, 130, 620, 350)
        renderer.panel(map_rect, (22, 30, 43), (62, 78, 101))
        renderer.text("Dünya haritası", 48, 150, title=True)

        if world_map is not None:
            renderer.world_map(
                world_map,
                current_location_id=current_location,
                rect=map_rect,
            )
        else:
            renderer.text("Bu dünyada harita bulunamadı.", 52, 220, (155, 172, 196))

        renderer.panel(renderer.pg.Rect(670, 130, 250, 350))
        if location:
            renderer.text(renderer.fit_text(location.name, 214), 686, 144, GOLD)
            renderer.text(f"{location.location_type} bölgesi", 686, 168, MUTED)
            renderer.wrapped_text(
                location.description, 686, 196, 218, TEXT_SOFT, line_height=22, max_lines=2,
            )

            labels = {
                "dialogue": "Diyalog",
                "market": "Pazar",
                "gather": "Toplama",
                "combat": "Savaş",
                "travel": "Seyahat",
            }
            renderer.text("Burada yapılabilir", 686, 246, MUTED)
            chip_x, chip_y = 686, 270
            for item in location.activities:
                label = labels.get(item, item)
                width = renderer.text_width(label) + 16
                if chip_x + width > 904:
                    chip_x, chip_y = 686, chip_y + 25
                chip_x += renderer.chip(chip_x, chip_y, label) + 6

            node_list = self._local_nodes(snapshot.nodes, actors[0] if actors else None)
            renderer.text("Kaynak noktaları", 686, 350, MUTED)
            if not node_list:
                renderer.text("Burada kaynak yok", 692, 380, (110, 120, 135))
            first = self._node_window(node_list)
            for row, node in enumerate(node_list[first:first + self.NODE_ROWS]):
                index = first + row
                rect = renderer.pg.Rect(
                    self.NODE_ROW_X, self.NODE_ROW_Y + row * self.NODE_ROW_H,
                    self.NODE_ROW_W, self.NODE_ROW_H - 2,
                )
                chosen = index == self.selected
                renderer.panel(
                    rect,
                    (55, 75, 105) if chosen or renderer.hovered(rect) else (38, 49, 69),
                    (245, 210, 120) if chosen else (62, 78, 101),
                )
                renderer.resource_icon(rect.x + 6, rect.y + 4, node.resource_type, 14)
                label = renderer.fit_text(resource_name(node.resource_type), 110)
                renderer.text(label, rect.x + 26, rect.y + 3, (220, 225, 235))
                amount = self._node_amount(node)
                renderer.text(amount, rect.right - 8 - renderer.text_width(amount), rect.y + 3, GOLD)
            if len(node_list) > self.NODE_ROWS:
                renderer.text(f"{self.selected + 1}/{len(node_list)}", 856, 350, MUTED)
        else:
            renderer.text("Konum bilgisi yok", 686, 150, MUTED)

        renderer.text(self.message, 28, 500, (220, 190, 120))

        activities = set(location.activities) if location else set()
        for action, key, label in self._action_specs():
            enabled = action in activities or action in {"map", "local_map"}
            rect = self._action_rects(renderer)[action]
            renderer.action_button(rect, key, label, enabled=enabled)

        renderer.footer(
            "G Topla   ↑/↓ Kaynak seç   C Üretim   I Envanter   "
            "P Karakter   F5 Kaydet   F9 Yükle"
        )
