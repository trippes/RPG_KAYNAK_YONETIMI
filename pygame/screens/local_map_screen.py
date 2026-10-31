"""32x32 tile map for movement and local NPC positions."""

from ..renderer import GOLD, TEXT_SOFT
from resources import Quantity, ResourceUnit
from collections import deque


class LocalMapScreen:
    GRID_SIZE = 32
    TILE_SIZE = 16
    RIVER_TILES = frozenset((18, 19))
    BRIDGE_TILES = frozenset(((18, 16), (19, 16)))
    VILLAGE_GATES = frozenset(((16, 0), (16, 31), (0, 16), (31, 16)))

    def __init__(self, service):
        self.service = service
        self.selected = (16, 16)
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

    def _wood_node_id(self):
        location = self._location()
        if location is None:
            return None
        return "forest_wood" if location.location_id == "forest" else f"{location.location_id}_wood"

    def _node_id_for_landmark(self, landmark):
        if landmark is None:
            return self._wood_node_id()
        if "tree" in str(landmark[0]).lower() or "ağaç" in str(landmark[1]).lower():
            return (
                "forest_wood"
                if landmark[0] == "forest_tree_01"
                else f"{landmark[0]}_wood"
            )
        if "mine" in str(landmark[0]).lower() or "maden" in str(landmark[1]).lower():
            return (
                "north_iron_mine"
                if self._location().location_id == "forest"
                else str(landmark[0])
            )
        return self._wood_node_id()

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
            self.service.advance_by(1)
            resource_name = "demir cevheri" if "mine" in str(landmark[0]).lower() else "odun"
            self.message = f"{landmark[1]} toplandı: +1 {resource_name}."
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
        landmark_id = str(landmark[0]).lower()
        landmark_name = str(landmark[1]).lower()
        return (
            "tree" in landmark_id
            or "ağaç" in landmark_name
            or "mine" in landmark_id
            or "maden" in landmark_name
        )

    def _resource_is_available(self, landmark):
        if not self._is_resource_landmark(landmark):
            return True
        return self._tree_is_available(landmark)

    def _tile_at(self, mouse_pos):
        origin_x, origin_y = self._grid_origin()
        x = (mouse_pos[0] - origin_x) // self.TILE_SIZE
        y = (mouse_pos[1] - origin_y) // self.TILE_SIZE
        if 0 <= x < self.GRID_SIZE and 0 <= y < self.GRID_SIZE:
            return x, y
        return None

    def _blocked_tiles(self):
        """Return tiles that cannot be crossed by local movement."""
        blocked = set()
        location = self._location()
        if location is None:
            return blocked
        for landmark in location.landmarks:
            landmark_id = str(landmark[0]).lower()
            name = str(landmark[1]).lower()
            if "river" not in landmark_id and "nehir" not in name:
                if landmark[3]:
                    continue
                x, y = tuple(landmark[2])
                blocked.update(
                    (tile_x, tile_y)
                    for tile_x in range(x, min(self.GRID_SIZE, x + 2))
                    for tile_y in range(y, min(self.GRID_SIZE, y + 2))
                )
        blocked.update(
            (x, y)
            for x in self.RIVER_TILES
            for y in range(self.GRID_SIZE)
            if (x, y) not in self.BRIDGE_TILES
        )
        if location.location_id == "village":
            blocked.update(
                (x, y)
                for x in range(self.GRID_SIZE)
                for y in range(self.GRID_SIZE)
                if (
                    x in (0, self.GRID_SIZE - 1)
                    or y in (0, self.GRID_SIZE - 1)
                )
                and (x, y) not in self.VILLAGE_GATES
            )
        return blocked

    def _is_walkable(self, tile, target=None):
        x, y = tile
        if not (0 <= x < self.GRID_SIZE and 0 <= y < self.GRID_SIZE):
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
        landmark_id = str(landmark[0]).lower()
        landmark_name = str(landmark[1]).lower()
        return bool(landmark[3]) or "tree" in landmark_id or "ağaç" in landmark_name

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
        size = self.GRID_SIZE * self.TILE_SIZE
        return ((self.renderer_width - size) // 2, 54)

    def _tile_size_for(self, renderer):
        available_width = max(320, renderer.width - 48)
        available_height = max(320, renderer.height - 150)
        return max(8, min(available_width // self.GRID_SIZE, available_height // self.GRID_SIZE))

    @staticmethod
    def _position(position, fallback=(16, 16)):
        if position is None:
            return fallback
        x, y = int(position.x), int(position.y)
        return (x, y) if 0 <= x < 32 and 0 <= y < 32 else fallback

    def _move_player(self, dx, dy):
        actors = self._actors()
        if not actors:
            return
        actor = actors[0]
        x, y = self._position(actor.position)
        next_x, next_y = x + dx, y + dy
        if not (0 <= next_x < self.GRID_SIZE and 0 <= next_y < self.GRID_SIZE):
            if self._cross_boundary(actor, dx, dy):
                return
            next_x = max(0, min(self.GRID_SIZE - 1, next_x))
            next_y = max(0, min(self.GRID_SIZE - 1, next_y))
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
                f"— adım: {self.steps_taken}, süre: 1 tick."
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
        if location.location_id == "village" and gate_tile not in self.VILLAGE_GATES:
            self.message = "Köyden yalnızca kapılardan çıkabilirsin."
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
        if destination.location_id == "village":
            target_gate = (
                (16, 31) if dy < 0 else
                (16, 0) if dy > 0 else
                (31, 16) if dx < 0 else
                (0, 16)
            )
            if target_gate not in self.VILLAGE_GATES:
                self.message = "Köye yalnızca kapılardan girebilirsin."
                return True
        self.service.place_actor(actor.actor_id, destination.location_id)
        target = (
            0 if dx > 0 else self.GRID_SIZE - 1 if dx < 0 else self._position(actor.position)[0],
            0 if dy > 0 else self.GRID_SIZE - 1 if dy < 0 else self._position(actor.position)[1],
        )
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
        renderer.frame("Yerel Harita", snapshot.simulation_tick)
        location = self._location()
        origin_x, origin_y = self._grid_origin()
        if location:
            renderer.text(location.name, 28, 72, title=True)
        for y in range(self.GRID_SIZE):
            for x in range(self.GRID_SIZE):
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

        for y in range(self.GRID_SIZE):
            rect = renderer.pg.Rect(
                origin_x + 18 * self.TILE_SIZE,
                origin_y + y * self.TILE_SIZE,
                self.TILE_SIZE * 2,
                self.TILE_SIZE,
            )
            renderer.pg.draw.rect(renderer.surface, (45, 115, 165), rect)
            renderer.pg.draw.line(
                renderer.surface,
                (115, 190, 220),
                (rect.x + 3, rect.centery),
                (rect.right - 3, rect.centery),
                1,
            )

        for bridge_x, bridge_y in self.BRIDGE_TILES:
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

        if location and location.location_id == "village":
            for x in range(self.GRID_SIZE):
                for y in range(self.GRID_SIZE):
                    if (
                        x not in (0, self.GRID_SIZE - 1)
                        and y not in (0, self.GRID_SIZE - 1)
                    ) or (x, y) in self.VILLAGE_GATES:
                        continue
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
            if not (0 <= x < self.GRID_SIZE and 0 <= y < self.GRID_SIZE):
                continue
            rect = renderer.pg.Rect(
                origin_x + x * self.TILE_SIZE + 1,
                origin_y + y * self.TILE_SIZE + 1,
                self.TILE_SIZE * 2 - 2,
                self.TILE_SIZE * 2 - 2,
            )
            is_tree = (
                "tree" in str(landmark[0]).lower()
                or "ağaç" in str(landmark[1]).lower()
            )
            if is_tree:
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
            elif "mine" in str(landmark[0]).lower() or "maden" in str(landmark[1]).lower():
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
                    f"{'Demir cevheri' if 'mine' in str(landmark[0]).lower() else 'Odun'}: {remaining} kaldı — Enter: topla",
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
