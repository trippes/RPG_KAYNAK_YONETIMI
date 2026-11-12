"""Data-driven local tile map for movement and local NPC positions."""

from ..renderer import GOLD, TEXT_SOFT, duration_label
from resources import Quantity, ResourceUnit
from collections import deque


class LocalMapScreen:
    TILE_SIZE = 16

    def __init__(self, service):
        self.service = service
        self.selected = self._map_center()
        self.selected_npc_id = None
        self.menu_open = False
        self.menu_selected = 0
        self.menu_rects = ()
        self.menu_options = (
            ("local_map", "Yerel Haritaya Dön"),
            ("inventory", "Çanta"),
            ("production", "Üretim"),
            ("character", "Karakter"),
            ("market", "Han / Pazar"),
            ("map", "Dünya Haritası"),
            ("close", "Oyuna Dön"),
            ("menu", "Ana Menüye Dön"),
        )
        self.renderer_width = 960
        self.renderer_height = 640
        self.steps_taken = 0
        self.message = "Ok tuşlarıyla tile üzerinde hareket et. Enter ile etkileş."

    def _location(self):
        actors = self.service.state().actors
        if not actors:
            return None
        world_map = self.service.application.holder.current.movement.map_for(actors[0].world_id)
        return world_map.get(actors[0].location_id) if world_map else None

    def _map_definition(self):
        location = self._location()
        return getattr(location, "local_map", None) or {}

    def _map_width(self):
        return max(1, int(self._map_definition().get("width", 1)))

    def _map_height(self):
        return max(1, int(self._map_definition().get("height", 1)))

    def _map_center(self):
        return self._map_width() // 2, self._map_height() // 2

    def _in_bounds(self, tile):
        x, y = tile
        return 0 <= x < self._map_width() and 0 <= y < self._map_height()

    def _river_tiles(self):
        river = self._map_definition().get("river", {})
        return {(int(x), y) for x in river.get("columns", ()) for y in range(self._map_height())}

    def _bridge_tiles(self):
        return {tuple(tile) for tile in self._map_definition().get("bridges", ())}

    def _gate_tiles(self):
        boundaries = self._map_definition().get("boundaries", {})
        return {tuple(tile) for tile in boundaries.get("gates", ())}

    def _wall_tiles(self):
        boundaries = self._map_definition().get("boundaries", {})
        edges = set(boundaries.get("walls", {}).get("edges", ()))
        tiles = set()
        if "north" in edges:
            tiles.update((x, 0) for x in range(self._map_width()))
        if "south" in edges:
            tiles.update((x, self._map_height() - 1) for x in range(self._map_width()))
        if "west" in edges:
            tiles.update((0, y) for y in range(self._map_height()))
        if "east" in edges:
            tiles.update((self._map_width() - 1, y) for y in range(self._map_height()))
        return tiles - self._gate_tiles()

    @staticmethod
    def _landmark_metadata(landmark):
        return landmark[5] if len(landmark) > 5 and isinstance(landmark[5], dict) else {}

    def _actors(self):
        return self.service.state().actors

    def _npcs(self):
        bundle = self.service.application.holder.current
        location = self._location()
        return tuple(
            npc for npc in bundle.social.npcs.all()
            if npc.active and npc.location_id == getattr(location, "location_id", None)
        )

    def _landmarks(self):
        location = self._location()
        return tuple(
            landmark for landmark in (location.landmarks if location else ())
            if self._resource_is_available(landmark)
        )

    def _landmark_at(self, tile):
        return next(
            (landmark for landmark in self._landmarks() if tuple(landmark[2]) == tile),
            None,
        )

    def _npc_at(self, tile):
        return next(
            (npc for npc in self._npcs() if self._position(npc.position) == tile),
            None,
        )

    def _node_id_for_landmark(self, landmark):
        if landmark is None:
            return None
        return self._landmark_metadata(landmark).get("resource_node_id")

    def _gather_at_selected_tree(self):
        landmark = self._landmark_at(self.selected)
        actors = self._actors()
        location = self._location()
        if landmark is None or "gather" not in landmark[3]:
            return False
        if not actors or location is None:
            self.message = "Kaynak toplayacak bir karakter bulunamadı."
            return True
        node_id = self._node_id_for_landmark(landmark)
        if node_id is None:
            self.message = "Bu bölgede kaynak bulunamadı."
            return True
        try:
            self.service.start_gathering_at_location(
                actors[0].actor_id,
                location.location_id,
                node_id,
                "player",
                Quantity(1, ResourceUnit.ITEM),
            )
            duration = self.service.gathering_duration(actors[0].actor_id)
            self.message = (
                f"{landmark[1]} toplama başladı. "
                f"{duration_label(duration)} sonra envantere eklenecek."
            )
        except (KeyError, ValueError, RuntimeError) as error:
            self.message = f"Odun toplanamadı: {error}"
        return True

    def _tree_is_available(self, landmark):
        if not self._is_resource_landmark(landmark):
            return True
        node = self.service.application.holder.current.resource_nodes.get(
            self._node_id_for_landmark(landmark),
        )
        return node is not None and node.current_quantity.value > 0

    def _is_resource_landmark(self, landmark):
        metadata = self._landmark_metadata(landmark)
        return metadata.get("visual_type") in {"tree", "mine"} or bool(metadata.get("resource_node_id"))

    def _resource_is_available(self, landmark):
        if not self._is_resource_landmark(landmark):
            return True
        return self._tree_is_available(landmark)

    def _tile_at(self, mouse_pos):
        origin_x, origin_y = self._grid_origin()
        x = (mouse_pos[0] - origin_x) // self.TILE_SIZE
        y = (mouse_pos[1] - origin_y) // self.TILE_SIZE
        if self._in_bounds((x, y)):
            return x, y
        return None

    def _blocked_tiles(self):
        """Return tiles that cannot be crossed by local movement."""
        blocked = set()
        location = self._location()
        if location is None:
            return blocked
        for landmark in location.landmarks:
            metadata = self._landmark_metadata(landmark)
            if not metadata.get("blocks_movement", False):
                continue
            x, y = tuple(landmark[2])
            width, height = metadata.get("footprint", (2, 2))
            blocked.update(
                (tile_x, tile_y)
                for tile_x in range(x, min(self._map_width(), x + width))
                for tile_y in range(y, min(self._map_height(), y + height))
            )
        blocked.update(self._river_tiles() - self._bridge_tiles())
        blocked.update(self._wall_tiles())
        return blocked

    def _is_walkable(self, tile, target=None):
        x, y = tile
        if not self._in_bounds(tile):
            return False
        if tile not in self._blocked_tiles():
            return True
        if tile != target:
            return False
        landmark = next(
            (
                item for item in (self._location().landmarks if self._location() else ())
                if tuple(item[2]) == tile
            ),
            None,
        )
        if landmark is None:
            return self._npc_at(tile) is not None
        return bool(landmark[3]) or self._landmark_metadata(landmark).get("visual_type") == "tree"

    def _path_to(self, start, target):
        if start == target:
            return (start,)
        if not self._is_walkable(target, target=target):
            return ()
        queue = deque([start])
        previous = {start: None}
        while queue:
            current = queue.popleft()
            neighbors = (
                (current[0] + 1, current[1]),
                (current[0] - 1, current[1]),
                (current[0], current[1] + 1),
                (current[0], current[1] - 1),
            )
            for neighbor in neighbors:
                if neighbor in previous or not self._is_walkable(neighbor, target=target):
                    continue
                previous[neighbor] = current
                if neighbor == target:
                    path = [target]
                    while path[-1] != start:
                        path.append(previous[path[-1]])
                    return tuple(reversed(path))
                queue.append(neighbor)
        return ()

    def _move_to_tile(self, target):
        actors = self._actors()
        if not actors:
            return
        actor = actors[0]
        start = self._position(actor.position)
        path = self._path_to(start, target)
        if not path:
            self.message = "Bu tile'a güvenli bir yol bulunamadı."
            return
        for step in path[1:]:
            self._complete_tile_move(actor.actor_id, step)
        self.selected = target

    def _grid_origin(self):
        size = self._map_width() * self.TILE_SIZE
        return ((self.renderer_width - size) // 2, 54)

    def _tile_size_for(self, renderer):
        available_width = max(320, renderer.width - 48)
        available_height = max(320, renderer.height - 150)
        return max(8, min(
            available_width // self._map_width(),
            available_height // self._map_height(),
        ))

    def _position(self, position, fallback=None):
        fallback = self._map_center() if fallback is None else fallback
        if position is None:
            return fallback
        x, y = int(position.x), int(position.y)
        return (x, y) if self._in_bounds((x, y)) else fallback

    def _move_player(self, dx, dy):
        actors = self._actors()
        if not actors:
            return
        actor = actors[0]
        x, y = self._position(actor.position)
        next_x, next_y = x + dx, y + dy
        if not self._in_bounds((next_x, next_y)):
            if self._cross_boundary(actor, dx, dy):
                return
            next_x = max(0, min(self._map_width() - 1, next_x))
            next_y = max(0, min(self._map_height() - 1, next_y))
        target = (next_x, next_y)
        if not self._is_walkable(target, target=target):
            self.message = "Bu yoldan geçemezsin. Nehirden yalnızca köprüden geçilebilir."
            return
        self._complete_tile_move(actor.actor_id, target)
        self.selected = target

    def _complete_tile_move(self, actor_id, target):
        self.service.set_actor_tile_position(actor_id, *target)
        try:
            self.service.advance_by(1)
            self.steps_taken += 1
            self.message = (
                f"Hareket tamamlandı: ({target[0]}, {target[1]}) "
                f"— adım: {self.steps_taken}, süre: 1 sn."
            )
        except RuntimeError as error:
            self.message = f"Hareket tamamlanamadı: {error}"

    def _cross_boundary(self, actor, dx, dy):
        world_map = self.service.application.holder.current.movement.map_for(actor.world_id)
        location = world_map.get(actor.location_id) if world_map else None
        if location is None or location.position is None:
            return False
        x, y = self._position(actor.position)
        gate_tile = (x, y)
        if self._wall_tiles() and gate_tile not in self._gate_tiles():
            self.message = "Bu haritadan yalnızca tanımlı kapılardan çıkabilirsin."
            return True
        neighbors = world_map.neighbors(actor.location_id)
        candidates = []
        for neighbor in neighbors:
            if neighbor.position is None:
                continue
            offset_x = neighbor.position[0] - location.position[0]
            offset_y = neighbor.position[1] - location.position[1]
            if dx and offset_x * dx > 0 and abs(offset_x) >= abs(offset_y):
                candidates.append(neighbor)
            if dy and offset_y * dy > 0 and abs(offset_y) >= abs(offset_x):
                candidates.append(neighbor)
        if not candidates:
            self.message = "Bu yönde başka bir yerel harita yok."
            return True
        destination = sorted(candidates, key=lambda item: item.location_id)[0]
        destination_map = destination.local_map or {}
        destination_width = max(1, int(destination_map.get("width", 1)))
        destination_height = max(1, int(destination_map.get("height", 1)))
        target = (
            0 if dx > 0 else destination_width - 1 if dx < 0 else self._position(actor.position)[0],
            0 if dy > 0 else destination_height - 1 if dy < 0 else self._position(actor.position)[1],
        )
        destination_gates = {
            tuple(tile)
            for tile in destination_map.get("boundaries", {}).get("gates", ())
        }
        if destination_gates:
            if dx > 0:
                entry_gates = [gate for gate in destination_gates if gate[0] == 0]
            elif dx < 0:
                entry_gates = [gate for gate in destination_gates if gate[0] == destination_width - 1]
            elif dy > 0:
                entry_gates = [gate for gate in destination_gates if gate[1] == 0]
            else:
                entry_gates = [gate for gate in destination_gates if gate[1] == destination_height - 1]
            if not entry_gates:
                self.message = "Hedef haritada bu yönde kullanılabilir bir kapı yok."
                return True
            reference = self._position(actor.position)
            target = min(
                entry_gates,
                key=lambda gate: abs(gate[0] - reference[0]) + abs(gate[1] - reference[1]),
            )
        self.service.place_actor(actor.actor_id, destination.location_id)
        self._complete_tile_move(actor.actor_id, target)
        self.selected = target
        self.message = (
            f"{destination.name} bölgesine geçildi. "
            f"Adım: {self.steps_taken}."
        )
        return True

    def handle(self, state):
        if state.pressed("back"):
            if self.menu_open:
                self.menu_open = False
            else:
                self.menu_open = True
                self.menu_selected = 0
            return None
        if self.menu_open:
            if state.mouse_clicked and state.mouse_pos is not None:
                for index, rect in enumerate(self.menu_rects):
                    if rect.collidepoint(state.mouse_pos):
                        self.menu_selected = index
                        target, _label = self.menu_options[index]
                        if target == "market" and "market" not in getattr(
                            self._location(), "activities", (),
                        ):
                            self.message = "Han ve pazar yalnızca köyde kullanılabilir."
                            return None
                        if target == "close" or target == "local_map":
                            self.menu_open = False
                            return None
                        if target == "menu":
                            self.menu_open = False
                            return "menu"
                        self.menu_open = False
                        return target
            if state.pressed("up"):
                self.menu_selected = (self.menu_selected - 1) % len(self.menu_options)
            if state.pressed("down"):
                self.menu_selected = (self.menu_selected + 1) % len(self.menu_options)
            if state.pressed("confirm"):
                target, _label = self.menu_options[self.menu_selected]
                if target == "market" and "market" not in getattr(
                    self._location(), "activities", (),
                ):
                    self.message = "Han ve pazar yalnızca köyde kullanılabilir."
                    return None
                if target == "close" or target == "local_map":
                    self.menu_open = False
                    return None
                if target == "menu":
                    self.menu_open = False
                    return "menu"
                self.menu_open = False
                return target
            return None

        if state.pressed("up"):
            self._move_player(0, -1)
        if state.pressed("down"):
            self._move_player(0, 1)
        if state.pressed("left"):
            self._move_player(-1, 0)
        if state.pressed("right"):
            self._move_player(1, 0)

        if state.mouse_clicked and state.mouse_pos is not None:
            tile = self._tile_at(state.mouse_pos)
            if tile is not None:
                self._move_to_tile(tile)

        if state.pressed("confirm"):
            npcs = self._npcs()
            npc = next((item for item in npcs if self._position(item.position) == self.selected), None)
            if npc is not None:
                self.selected_npc_id = npc.npc_id
                self.message = f"{npc.name} ile konuşmak için Enter'a bas."
                return "dialogue"
            landmark = self._landmark_at(self.selected)
            if self._gather_at_selected_tree():
                return None
            self.message = (
                f"{landmark[1]}: {landmark[4]}"
                if landmark is not None
                else f"Tile ({self.selected[0]}, {self.selected[1]}) boş."
            )

        return None

    def render(self, renderer):
        self.renderer_width = renderer.width
        self.renderer_height = renderer.height
        self.TILE_SIZE = self._tile_size_for(renderer)
        snapshot = self.service.state()
        actor = snapshot.actors[0] if snapshot.actors else None
        active = self.service.actor_activity(actor.actor_id) if actor else None
        if active is not None and active.state == "running" and active.end_tick is not None:
            remaining = max(0, active.end_tick - snapshot.simulation_tick)
            self.message = f"Toplama sürüyor: {duration_label(remaining)} kaldı. Space ile zamanı ilerlet."
        renderer.frame("Yerel Harita", snapshot.simulation_tick)
        location = self._location()
        origin_x, origin_y = self._grid_origin()
        if location:
            renderer.text(location.name, 28, 72, title=True)
        for y in range(self._map_height()):
            for x in range(self._map_width()):
                rect = renderer.pg.Rect(
                    origin_x + x * self.TILE_SIZE,
                    origin_y + y * self.TILE_SIZE,
                    self.TILE_SIZE,
                    self.TILE_SIZE,
                )
                color = (74, 145, 72) if (x + y) % 2 else (67, 133, 66)
                if (x, y) == self.selected:
                    color = (112, 177, 82)
                renderer.pg.draw.rect(renderer.surface, color, rect)
                renderer.pg.draw.rect(renderer.surface, (54, 112, 57), rect, 1)

        for river_x, river_y in self._river_tiles():
            rect = renderer.pg.Rect(
                origin_x + river_x * self.TILE_SIZE,
                origin_y + river_y * self.TILE_SIZE,
                self.TILE_SIZE,
                self.TILE_SIZE,
            )
            renderer.pg.draw.rect(renderer.surface, (45, 115, 165), rect)
            renderer.pg.draw.line(
                renderer.surface, (115, 190, 220),
                (rect.x + 3, rect.centery), (rect.right - 3, rect.centery), 1,
            )

        for bridge_x, bridge_y in self._bridge_tiles():
            rect = renderer.pg.Rect(
                origin_x + bridge_x * self.TILE_SIZE,
                origin_y + bridge_y * self.TILE_SIZE,
                self.TILE_SIZE,
                self.TILE_SIZE,
            )
            renderer.pg.draw.rect(renderer.surface, (151, 99, 53), rect)
            renderer.pg.draw.line(
                renderer.surface, (224, 172, 92),
                (rect.x + 2, rect.y + self.TILE_SIZE // 3),
                (rect.right - 2, rect.y + self.TILE_SIZE // 3), 2,
            )
            renderer.pg.draw.line(
                renderer.surface, (224, 172, 92),
                (rect.x + 2, rect.y + self.TILE_SIZE * 2 // 3),
                (rect.right - 2, rect.y + self.TILE_SIZE * 2 // 3), 2,
            )

        if location and self._wall_tiles():
            for x, y in self._wall_tiles():
                    rect = renderer.pg.Rect(
                        origin_x + x * self.TILE_SIZE,
                        origin_y + y * self.TILE_SIZE,
                        self.TILE_SIZE,
                        self.TILE_SIZE,
                    )
                    renderer.pg.draw.rect(renderer.surface, (125, 125, 122), rect)
                    renderer.pg.draw.rect(renderer.surface, (82, 87, 81), rect, 1)
                    renderer.pg.draw.line(
                        renderer.surface, (175, 172, 156),
                        (rect.x + 2, rect.y + 3),
                        (rect.right - 3, rect.y + 3), 2,
                    )

        for landmark in self._landmarks():
            x, y = tuple(landmark[2])
            if not self._in_bounds((x, y)):
                continue
            metadata = self._landmark_metadata(landmark)
            footprint_width, footprint_height = metadata.get("footprint", (2, 2))
            rect = renderer.pg.Rect(
                origin_x + x * self.TILE_SIZE + 1,
                origin_y + y * self.TILE_SIZE + 1,
                footprint_width * self.TILE_SIZE - 2,
                footprint_height * self.TILE_SIZE - 2,
            )
            visual_type = metadata.get("visual_type", "landmark")
            if visual_type == "tree":
                renderer.pg.draw.rect(
                    renderer.surface, (105, 70, 38),
                    renderer.pg.Rect(
                        rect.centerx - max(2, self.TILE_SIZE // 6),
                        rect.bottom - self.TILE_SIZE,
                        max(4, self.TILE_SIZE // 3),
                        self.TILE_SIZE,
                    ),
                )
                renderer.pg.draw.circle(
                    renderer.surface, (48, 125, 68),
                    (rect.centerx, rect.y + self.TILE_SIZE // 2),
                    max(5, self.TILE_SIZE // 2),
                )
            elif visual_type == "mine":
                renderer.pg.draw.polygon(
                    renderer.surface,
                    (112, 108, 104),
                    (
                        (rect.x + 2, rect.bottom - 2),
                        (rect.centerx, rect.y + 3),
                        (rect.right - 2, rect.bottom - 2),
                    ),
                )
                renderer.pg.draw.ellipse(
                    renderer.surface,
                    (35, 38, 42),
                    renderer.pg.Rect(
                        rect.centerx - self.TILE_SIZE // 2,
                        rect.centery - 2,
                        self.TILE_SIZE,
                        self.TILE_SIZE // 2,
                    ),
                )
            elif visual_type == "building":
                house_body = renderer.pg.Rect(
                    rect.x + 2,
                    rect.y + self.TILE_SIZE // 2,
                    rect.width - 4,
                    rect.height - self.TILE_SIZE // 2 - 2,
                )
                renderer.pg.draw.rect(renderer.surface, (210, 170, 105), house_body)
                renderer.pg.draw.polygon(
                    renderer.surface,
                    (150, 55, 45),
                    (
                        (rect.x, house_body.y + 2),
                        (rect.centerx, rect.y + 1),
                        (rect.right, house_body.y + 2),
                    ),
                )
                renderer.pg.draw.rect(
                    renderer.surface,
                    (92, 59, 39),
                    renderer.pg.Rect(
                        rect.centerx - max(2, self.TILE_SIZE // 6),
                        house_body.bottom - self.TILE_SIZE // 2,
                        max(4, self.TILE_SIZE // 3),
                        self.TILE_SIZE // 2,
                    ),
                )
                window_size = max(3, self.TILE_SIZE // 4)
                for window_x in (house_body.x + self.TILE_SIZE // 3, house_body.right - self.TILE_SIZE // 3 - window_size):
                    renderer.pg.draw.rect(
                        renderer.surface,
                        (105, 190, 205),
                        renderer.pg.Rect(window_x, house_body.y + 3, window_size, window_size),
                    )
            else:
                renderer.pg.draw.circle(
                    renderer.surface, (185, 170, 120), rect.center,
                    max(3, self.TILE_SIZE // 3),
                )
            renderer.pg.draw.rect(renderer.surface, (102, 72, 43), rect, 1)

        for npc in self._npcs():
            x, y = self._position(npc.position)
            renderer.pg.draw.rect(
                renderer.surface,
                (220, 150, 100),
                renderer.pg.Rect(origin_x + x * self.TILE_SIZE + 2, origin_y + y * self.TILE_SIZE + 2, 6, 6),
            )
            renderer.text(
                npc.name[:1].upper(),
                origin_x + x * self.TILE_SIZE + 1,
                origin_y + y * self.TILE_SIZE - 2,
                (255, 235, 190),
            )

        actors = self._actors()
        if actors:
            x, y = self._position(actors[0].position)
            renderer.pg.draw.rect(
                renderer.surface,
                (100, 210, 150),
                renderer.pg.Rect(origin_x + x * self.TILE_SIZE + 1, origin_y + y * self.TILE_SIZE + 1, 8, 8),
            )
            self.selected = (x, y)

        renderer.text(f"Tile: {self.selected[0]}, {self.selected[1]}", 28, 108, TEXT_SOFT)
        npc = self._npc_at(self.selected)
        if npc is not None:
            renderer.text(renderer.fit_text(npc.name, 360), 28, 132, GOLD)
            renderer.text(
                f"{npc.role} — Enter: konuş",
                28, 160, (255, 220, 150), max_width=360,
            )
        landmark = self._landmark_at(self.selected)
        if landmark is not None and npc is None:
            renderer.text(renderer.fit_text(landmark[1], 360), 28, 132, GOLD)
            renderer.wrapped_text(landmark[4], 28, 160, 360, TEXT_SOFT, line_height=22, max_lines=3)
            if "gather" in landmark[3]:
                node = self.service.application.holder.current.resource_nodes.get(
                    self._node_id_for_landmark(landmark),
                )
                remaining = node.current_quantity.value if node is not None else 0
                renderer.text(
                    f"{'Demir cevheri' if self._landmark_metadata(landmark).get('visual_type') == 'mine' else 'Odun'}: {remaining} kaldı — Enter: topla",
                    28, 232, (140, 220, 160), max_width=360,
                )
        renderer.wrapped_text(
            "Yeşil: karakter   Turuncu: NPC   Kahverengi: yapı   Mavi: nehir",
            28, renderer.height - 70, 900, TEXT_SOFT, line_height=24, max_lines=2,
        )
        renderer.text(
            self.message, 28, renderer.height - 64, (220, 190, 120),
            max_width=renderer.width - 56,
        )
        renderer.footer("Oklar: Tile hareketi   Enter: etkileşim   Esc: Menü")
        if self.menu_open:
            renderer.pg.draw.rect(
                renderer.surface, (11, 15, 24),
                renderer.pg.Rect(0, 0, renderer.width, renderer.height),
            )
            self.menu_rects = renderer.vertical_menu(
                "OYUN MENÜSÜ",
                [label for _target, label in self.menu_options],
                self.menu_selected,
                width=min(420, renderer.width - 48),
                row_height=46,
            )
            renderer.text(
                "Yukarı/Aşağı seç   Enter onayla   Esc kapat",
                0, self.menu_rects[-1].bottom + 18, TEXT_SOFT,
                max_width=renderer.width,
            )
