"""Content-defined local tile map for movement and NPC positions."""

from ..renderer import GOLD, TEXT_SOFT, duration_label
from resources import Quantity, ResourceUnit
from collections import deque
from pathlib import Path

from world import load_map_definition


class MainScreen:
    TILE_SIZE = 16

    def __init__(self, service):
        self.service = service
        self._map_definition_cache = {}
        self.selected = (16, 16)
        self.selected_npc_id = None
        self.selected_container_id = None
        self.menu_open = False
        self.menu_selected = 0
        self.menu_rects = ()
        self.context_menu_open = False
        self.context_menu_rects = ()
        self.context_menu_actions = ()
        self.context_menu_position = (0, 0)
        self.menu_options = (
            ("main", "Ana Ekrana Dön"),
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

    def _map_definition(self, location=None):
        location = location or self._location()
        if location is None:
            return None
        map_id = location.location_id
        if map_id not in self._map_definition_cache:
            package_root = getattr(self.service, "_content_package_path", None)
            if package_root is None:
                package_root = Path(__file__).resolve().parents[2] / "content" / "demo_eldoria"
            source = Path(package_root) / "maps" / f"{map_id}.json"
            try:
                self._map_definition_cache[map_id] = load_map_definition(source)
            except (OSError, ValueError):
                return None
        return self._map_definition_cache[map_id]

    def _map_width(self):
        definition = self._map_definition()
        return definition.size.width if definition is not None else 32

    def _map_height(self):
        definition = self._map_definition()
        return definition.size.height if definition is not None else 32

    def _gate_tiles(self, definition=None):
        definition = definition or self._map_definition()
        if definition is None:
            return frozenset()
        return frozenset(item.position for item in definition.landmarks if item.visual_type == "gate")

    def _feature_tiles(self, feature_type, definition=None):
        definition = definition or self._map_definition()
        if definition is None:
            return frozenset()
        return frozenset(
            tile for feature in definition.features if feature.feature_type == feature_type
            for tile in feature.tiles
        )

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
        definition = self._map_definition()
        if definition is None:
            return ()
        result = []
        for item in definition.landmarks:
            landmark = (
                item.landmark_id, item.name, item.position, item.activities,
                item.description, item.visual_type, item.resource_node_id,
                item.walkable, item.interactable, item.landmark_type,
            )
            if self._resource_is_available(landmark):
                result.append(landmark)
        return tuple(result)

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

    def _container_placement_at(self, tile):
        actors = self._actors()
        location = self._location()
        if not actors or location is None:
            return None
        for placement in self.service.world_objects_for_location(
            actors[0].world_id, location.location_id,
        ):
            if not (
                placement.x <= tile[0] < placement.x + placement.width
                and placement.y <= tile[1] < placement.y + placement.height
            ):
                continue
            container_id = self.service.container_for_entity(placement.object_id)
            if container_id is not None:
                return container_id, placement
        return None

    def _container_placement(self, container_id):
        actors = self._actors()
        location = self._location()
        if not actors or location is None:
            return None
        for placement in self.service.world_objects_for_location(
            actors[0].world_id, location.location_id,
        ):
            if self.service.container_for_entity(placement.object_id) == container_id:
                return placement
        return None

    def _is_adjacent_to_container(self, placement):
        actors = self._actors()
        if not actors or placement is None:
            return False
        actor_x, actor_y = self._position(actors[0].position)
        dx = max(placement.x - actor_x, 0, actor_x - (placement.x + placement.width - 1))
        dy = max(placement.y - actor_y, 0, actor_y - (placement.y + placement.height - 1))
        return max(dx, dy) <= 1

    def _node_id_for_landmark(self, landmark):
        return landmark[6] if landmark is not None else None

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
        return landmark[9] == "resource" or landmark[6] is not None

    def _resource_is_available(self, landmark):
        if not self._is_resource_landmark(landmark):
            return True
        return self._tree_is_available(landmark)

    def _tile_at(self, mouse_pos):
        origin_x, origin_y = self._grid_origin()
        x = (mouse_pos[0] - origin_x) // self.TILE_SIZE
        y = (mouse_pos[1] - origin_y) // self.TILE_SIZE
        if 0 <= x < self._map_width() and 0 <= y < self._map_height():
            return x, y
        return None

    def _blocked_tiles(self):
        """Return blocked tiles declared by the active map and world objects."""
        blocked = set()
        location = self._location()
        definition = self._map_definition(location)
        if location is None or definition is None:
            return blocked
        blocked.update(definition.blocked_tiles)
        for feature in definition.features:
            if not feature.walkable:
                blocked.update(feature.tiles)
        actors = self._actors()
        if actors:
            blocked.update(
                self.service.blocked_world_object_tiles(
                    actors[0].world_id, location.location_id,
                )
            )
        return blocked

    def _is_walkable(self, tile, target=None):
        x, y = tile
        if not (0 <= x < self._map_width() and 0 <= y < self._map_height()):
            return False
        if tile not in self._blocked_tiles():
            return True
        if tile != target:
            return False
        landmark = self._landmark_at(tile)
        if landmark is None:
            return self._npc_at(tile) is not None
        return bool(landmark[7] or landmark[8])

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
        width = self._map_width() * self.TILE_SIZE
        height = self._map_height() * self.TILE_SIZE
        return ((self.renderer_width - width) // 2, max(54, (self.renderer_height - height) // 2))

    def _tile_size_for(self, renderer):
        available_width = max(320, renderer.width - 48)
        available_height = max(320, renderer.height - 150)
        return max(8, min(available_width // self._map_width(), available_height // self._map_height()))

    def _position(self, position, fallback=None):
        if fallback is None:
            fallback = (self._map_width() // 2, self._map_height() // 2)
        if position is None:
            return fallback
        x, y = int(position.x), int(position.y)
        return (x, y) if 0 <= x < self._map_width() and 0 <= y < self._map_height() else fallback

    def _move_player(self, dx, dy):
        actors = self._actors()
        if not actors:
            return
        actor = actors[0]
        x, y = self._position(actor.position)
        next_x, next_y = x + dx, y + dy
        if not (0 <= next_x < self._map_width() and 0 <= next_y < self._map_height()):
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
        current_gate = self._position(actor.position)
        current_definition = self._map_definition(location)
        current_gates = self._gate_tiles(current_definition)
        if current_gates and current_gate not in current_gates:
            self.message = "Bu bölgeden yalnızca tanımlı geçiş noktalarından çıkabilirsin."
            return True

        candidates = []
        for neighbor in world_map.neighbors(actor.location_id):
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
        destination_definition = self._map_definition(destination)
        destination_gates = self._gate_tiles(destination_definition)
        target = (
            (0 if dx > 0 else self._map_width() - 1, current_gate[1])
            if dx else
            (current_gate[0], 0 if dy > 0 else self._map_height() - 1)
        )
        if destination_gates and destination_definition is not None:
            target_edge = (
                "west" if dx > 0 else "east" if dx < 0 else
                "north" if dy > 0 else "south"
            )
            def on_target_edge(tile):
                if target_edge == "west":
                    return tile[0] == 0
                if target_edge == "east":
                    return tile[0] == destination_definition.size.width - 1
                if target_edge == "north":
                    return tile[1] == 0
                return tile[1] == destination_definition.size.height - 1
            edge_tiles = [tile for tile in destination_gates if on_target_edge(tile)]
            if not edge_tiles:
                self.message = "Hedef haritada bu yönde tanımlı bir geçiş yok."
                return True
            target = min(
                edge_tiles,
                key=lambda tile: abs(tile[0] - current_gate[0]) + abs(tile[1] - current_gate[1]),
            )

        self.service.place_actor(actor.actor_id, destination.location_id)
        self._complete_tile_move(actor.actor_id, target)
        self.selected = target
        self.message = f"{destination.name} bölgesine geçildi. Adım: {self.steps_taken}."
        return True

    def _has_required_key(self, inventory_id, lock):
        if lock is None or not lock.required_key_id:
            return False
        inventory = self.service.inventory(inventory_id)
        return any(
            item_id == lock.required_key_id and quantity > 0
            for item_id, quantity in inventory.items
        )

    def _open_container_context_menu(self, position):
        lock = self.service.container_lock_state(self.selected_container_id)
        actions = []
        if lock is not None and lock.locked:
            actors = self._actors()
            has_key = bool(
                actors
                and actors[0].inventory_id is not None
                and self._has_required_key(actors[0].inventory_id, lock)
            )
            if has_key:
                actions.append(("open", "Aç"))
            elif (
                lock.lockpick_profile_id
                and not lock.jammed
                and not lock.broken
                and actors
                and actors[0].inventory_id is not None
                and (
                    not getattr(lock, "lockpick_requires_tool", False)
                    or self._tool_for_tags(
                        actors[0].inventory_id,
                        lock.lockpick_allowed_tool_tags,
                    ) is not None
                )
            ):
                actions.append(("unlock", "Kilidi Aç"))
            if lock.force_profile_id and not lock.jammed and not lock.broken:
                actions.append(("force", "Kilidi zorla"))
            actions.append(("inspect", "İncele"))
        else:
            actions.extend((("open", "Aç"), ("inspect", "İncele")))
        self.context_menu_actions = tuple(actions)
        self.context_menu_position = position
        self.context_menu_open = True
        self.context_menu_rects = ()

    def _tool_for_tags(self, inventory_id, allowed_tags):
        if not allowed_tags:
            return None
        for item_id, quantity in self.service.inventory(inventory_id).items:
            if quantity < 1:
                continue
            item = self.service.item(item_id)
            if item is not None and set(item.tags).intersection(allowed_tags):
                return item_id
        return None

    def _execute_container_action(self, action):
        actors = self._actors()
        if not actors:
            self.message = "Aktif karakter bulunamadı."
            return
        actor = actors[0]
        lock = self.service.container_lock_state(self.selected_container_id)
        placement = self._container_placement(self.selected_container_id)
        if action == "inspect":
            status = "kilitli" if lock is not None and lock.locked else "kilidi açık"
            self.message = f"Sandık incelendi: {status}."
            return
        if not self._is_adjacent_to_container(placement):
            self.message = "Sandıkla etkileşmek için yanına yaklaşmalısın."
            return
        if actor.inventory_id is None:
            self.message = "Karakter envanteri bulunamadı."
            return
        if action == "open":
            if lock is not None and lock.locked:
                if not lock.required_key_id:
                    self.message = "Bu kilit için uygun anahtar tanımlanmamış."
                    return None
                success = self.service.unlock_with_key(
                    actor.actor_id, actor.inventory_id, lock.lock_id, lock.required_key_id,
                )
                if not success:
                    self.message = "Uygun anahtar bulunamadı."
                    return None
                self.message = "Kilit anahtarla açıldı."
            return f"container:{self.selected_container_id}"
        if action == "unlock" and lock is not None:
            tool_id = self._tool_for_tags(actor.inventory_id, lock.lockpick_allowed_tool_tags)
            result = self.service.resolve_lockpick(actor.actor_id, actor.inventory_id, lock.lock_id, tool_item_id=tool_id)
            self.message = f"{'Başarılı' if result.success else 'Başarısız'} — d20 {result.total} / DC {result.difficulty_class}"
        elif action == "force" and lock is not None:
            tool_id = self._tool_for_tags(actor.inventory_id, lock.force_required_tool_tags)
            result = self.service.resolve_force_lock(actor.actor_id, actor.inventory_id, lock.lock_id, tool_item_id=tool_id)
            self.message = f"{'Başarılı' if result.success else 'Başarısız'} — d20 {result.total} / DC {result.difficulty_class}"

    def render_context_menu(self, renderer):
        if not self.context_menu_open:
            return
        width, row_height = 208, 36
        x, y = self.context_menu_position
        height = 14 + len(self.context_menu_actions) * row_height
        x = max(8, min(x, renderer.width - width - 8))
        y = max(8, min(y, renderer.height - height - 8))
        renderer.panel(renderer.pg.Rect(x, y, width, height), (30, 23, 19), (173, 128, 67))
        rects = []
        for index, (action, label) in enumerate(self.context_menu_actions):
            rect = renderer.pg.Rect(x + 7, y + 7 + index * row_height, width - 14, row_height - 2)
            renderer.panel(rect, (49, 38, 29), (112, 82, 48))
            renderer.text(label, rect.x + 10, rect.y + 8, GOLD)
            rects.append((action, rect))
        self.context_menu_rects = tuple(rects)

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
                        if target == "close" or target == "main":
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
                if target == "close" or target == "main":
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

        if self.context_menu_open:
            if state.mouse_clicked and state.mouse_pos is not None:
                selected_action = next((action for action, rect in self.context_menu_rects if rect.collidepoint(state.mouse_pos)), None)
                if selected_action is not None:
                    self.context_menu_open = False
                    if selected_action in ("open", "unlock", "force", "inspect"):
                        placement = self._container_placement(self.selected_container_id)
                        if not self._is_adjacent_to_container(placement) and selected_action != "inspect":
                            self.message = "Sandıkla etkileşmek için yanına yaklaşmalısın."
                            return None
                        result = self._execute_container_action(selected_action)
                        if result is not None:
                            return result
                    return None
                self.context_menu_open = False
                return None
            if state.mouse_right_clicked:
                self.context_menu_open = False
                return None
            return None

        if state.mouse_right_clicked and state.mouse_pos is not None:
            tile = self._tile_at(state.mouse_pos)
            target = self._container_placement_at(tile) if tile is not None else None
            if target is not None:
                self.selected_container_id = target[0]
                self.selected = tile
                self._open_container_context_menu(state.mouse_pos)
            else:
                self.selected_container_id = None
                self.message = "Burada bağlamsal aksiyon bulunmuyor."
            return None

        if state.mouse_clicked and state.mouse_pos is not None:
            tile = self._tile_at(state.mouse_pos)
            if tile is not None:
                container_target = self._container_placement_at(tile)
                if container_target is not None:
                    self.selected_container_id = container_target[0]
                    self.selected = tile
                else:
                    self.selected_container_id = None
                    self._move_to_tile(tile)

        if state.pressed("confirm"):
            npcs = self._npcs()
            npc = next((item for item in npcs if self._position(item.position) == self.selected), None)
            if npc is not None:
                self.selected_npc_id = npc.npc_id
                self.message = f"{npc.name} ile konuşmak için Enter'a bas."
                return "dialogue"
            if self.selected_container_id is not None:
                placement = self._container_placement(self.selected_container_id)
                if self._is_adjacent_to_container(placement):
                    return f"container:{self.selected_container_id}"
                self.message = "Konteyneri açmak için yanına yaklaşın."
                return None
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

        definition = self._map_definition(location)
        if definition is not None:
            for feature in definition.features:
                if feature.feature_type != "river":
                    continue
                for tile_x, tile_y in feature.tiles:
                    rect = renderer.pg.Rect(
                        origin_x + tile_x * self.TILE_SIZE,
                        origin_y + tile_y * self.TILE_SIZE,
                        self.TILE_SIZE,
                        self.TILE_SIZE,
                    )
                    renderer.pg.draw.rect(renderer.surface, (45, 115, 165), rect)
                    renderer.pg.draw.line(
                        renderer.surface, (115, 190, 220),
                        (rect.x + 3, rect.centery),
                        (rect.right - 3, rect.centery), 1,
                    )

            for feature in definition.features:
                if feature.feature_type != "bridge":
                    continue
                for bridge_x, bridge_y in feature.tiles:
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

            for feature in definition.features:
                if feature.feature_type != "wall":
                    continue
                for wall_x, wall_y in feature.tiles:
                    rect = renderer.pg.Rect(
                        origin_x + wall_x * self.TILE_SIZE,
                        origin_y + wall_y * self.TILE_SIZE,
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
            if not (0 <= x < self._map_width() and 0 <= y < self._map_height()):
                continue
            rect = renderer.pg.Rect(
                origin_x + x * self.TILE_SIZE + 1,
                origin_y + y * self.TILE_SIZE + 1,
                self.TILE_SIZE * 2 - 2,
                self.TILE_SIZE * 2 - 2,
            )
            if landmark[5] == "tree":
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
            elif landmark[5] == "mine":
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
            else:
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
            renderer.pg.draw.rect(renderer.surface, (102, 72, 43), rect, 1)

        if actor is not None and location is not None:
            for placement in self.service.world_objects_for_location(actor.world_id, location.location_id):
                rect = renderer.pg.Rect(origin_x + placement.x * self.TILE_SIZE + 2, origin_y + placement.y * self.TILE_SIZE + 2, max(4, placement.width * self.TILE_SIZE - 4), max(4, placement.height * self.TILE_SIZE - 4))
                container_id = self.service.container_for_entity(placement.object_id)
                selected_container = container_id is not None and container_id == self.selected_container_id
                renderer.pg.draw.rect(renderer.surface, (126, 91, 58), rect, border_radius=2)
                renderer.pg.draw.rect(
                    renderer.surface, (245, 210, 120) if selected_container else (210, 174, 112),
                    rect, 2 if selected_container else 1, border_radius=2,
                )

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
                    f"{'Demir cevheri' if landmark[5] == 'mine' else 'Odun'}: {remaining} kaldı — Enter: topla",
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
        self.render_context_menu(renderer)
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
