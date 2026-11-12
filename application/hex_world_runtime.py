"""Runtime orchestration for player, NPC, and movable-object hex movement."""
from __future__ import annotations

from dataclasses import dataclass, replace

from application.hex_map_definition import HexMapDefinition
from application.world_map_definition import WorldMapDefinition, validate_world_map
from core.domain.spatial import (
    EntityPosition, HexDirection, LocalHexPosition, MovementFailureReason,
    MovementProfile, MovementRequest, MovementResult,
)
from .hex_movement_rules import MovementRules
from .hex_occupancy import HexOccupant, HexOccupancyRegistry
from .hex_pathfinding import HexPathfinder


@dataclass(frozen=True, slots=True)
class HexMovableEntity:
    entity_id: str
    kind: str
    position: EntityPosition
    profile: MovementProfile
    active: bool = True

    def __post_init__(self):
        if not isinstance(self.entity_id, str) or not self.entity_id.strip():
            raise ValueError("entity_id must be a non-empty string.")
        if self.kind not in {"player", "npc", "object"}:
            raise ValueError("kind must be player, npc, or object.")
        if not isinstance(self.position, EntityPosition):
            raise TypeError("position must be an EntityPosition.")
        if not isinstance(self.profile, MovementProfile):
            raise TypeError("profile must be a MovementProfile.")
        if not isinstance(self.active, bool):
            raise TypeError("active must be boolean.")


class HexWorldRuntime:
    """Owns live hex positions without changing legacy square-map actors."""

    def __init__(
        self, map_definitions, occupancy: HexOccupancyRegistry | None = None,
        world_map_definition: WorldMapDefinition | None = None,
    ):
        maps = dict(map_definitions)
        if not maps or any(not isinstance(value, HexMapDefinition) for value in maps.values()):
            raise ValueError("map_definitions must contain at least one HexMapDefinition.")
        if any(key != value.map_id for key, value in maps.items()):
            raise ValueError("map definition keys must match map_id.")
        if world_map_definition is not None:
            validate_world_map(world_map_definition, maps)
        self._maps = maps
        self._world_map = world_map_definition
        self._occupancy = occupancy or HexOccupancyRegistry()
        self._entities: dict[str, HexMovableEntity] = {}
        self._patrol_indices: dict[str, int] = {}

    @property
    def occupancy(self) -> HexOccupancyRegistry:
        return self._occupancy

    def map_definition(self, map_id: str) -> HexMapDefinition:
        try:
            return self._maps[map_id]
        except KeyError as error:
            raise KeyError(f"Unknown hex map: {map_id}") from error

    def register_entity(
        self, entity_id: str, kind: str, position: EntityPosition,
        profile: MovementProfile | None = None, *, active: bool = True,
        blocks_movement: bool = True, blocks_occupancy: bool = True,
    ) -> HexMovableEntity:
        if entity_id in self._entities:
            raise ValueError(f"Duplicate hex entity: {entity_id}")
        if not isinstance(position, EntityPosition):
            raise TypeError("position must be an EntityPosition.")
        map_definition = self.map_definition(position.map_id)
        if not map_definition.has_cell(position.cell):
            raise ValueError("Entity position is outside the map valid_cells mask.")
        if profile is None:
            profile = MovementProfile(can_move=(kind != "object"))
        if not isinstance(profile, MovementProfile):
            raise TypeError("profile must be a MovementProfile.")
        if map_definition.is_blocked(position.cell) and not profile.can_traverse_blocked_cells:
            raise ValueError("Entity cannot be placed on a blocked cell.")
        entity = HexMovableEntity(entity_id, kind, position, profile, active)
        self._occupancy.add(HexOccupant(
            entity_id, position, blocks_movement, blocks_occupancy, kind,
        ), ignore_blockers=profile.ignores_occupancy)
        self._entities[entity_id] = entity
        return entity

    def entity(self, entity_id: str) -> HexMovableEntity:
        try:
            return self._entities[entity_id]
        except KeyError as error:
            raise KeyError(f"Unknown hex entity: {entity_id}") from error

    def entities(self) -> tuple[HexMovableEntity, ...]:
        return tuple(self._entities[key] for key in sorted(self._entities))

    def set_active(self, entity_id: str, active: bool) -> HexMovableEntity:
        if not isinstance(active, bool):
            raise TypeError("active must be boolean.")
        updated = replace(self.entity(entity_id), active=active)
        self._entities[entity_id] = updated
        return updated

    def move(self, entity_id: str, direction: HexDirection) -> MovementResult:
        entity = self.entity(entity_id)
        if not entity.active or not entity.profile.can_move:
            return MovementResult(False, entity.position, MovementFailureReason.MOVEMENT_NOT_ALLOWED, "Entity cannot move.")
        if not isinstance(direction, HexDirection):
            raise TypeError("direction must be a HexDirection.")
        target_cell = LocalHexPosition.from_hex_coord(entity.position.cell.to_hex_coord().neighbor(direction))
        return self.move_to(entity_id, target_cell)

    def move_to(self, entity_id: str, target: LocalHexPosition) -> MovementResult:
        entity = self.entity(entity_id)
        if not isinstance(target, LocalHexPosition):
            raise TypeError("target must be a LocalHexPosition.")
        if not entity.active or not entity.profile.can_move:
            return MovementResult(False, entity.position, MovementFailureReason.MOVEMENT_NOT_ALLOWED, "Entity cannot move.")
        destination = EntityPosition(entity.position.map_id, target)
        request = MovementRequest(entity_id, entity.position, destination, entity.profile)
        result = MovementRules.evaluate(request, self.map_definition(entity.position.map_id))
        if not result.success:
            return result
        if not entity.profile.ignores_occupancy and not self._occupancy.can_enter(destination, excluding=entity_id):
            return MovementResult(False, entity.position, MovementFailureReason.OCCUPIED_CELL, "Target cell is occupied or movement-blocked.")
        self._occupancy.move(entity_id, destination, ignore_blockers=entity.profile.ignores_occupancy)
        self._entities[entity_id] = replace(entity, position=destination)
        return MovementResult(True, destination)

    def path_to(self, entity_id: str, goal: LocalHexPosition):
        entity = self.entity(entity_id)
        if not entity.active or not entity.profile.can_move:
            return None
        map_definition = self.map_definition(entity.position.map_id)
        blocked = (
            frozenset() if entity.profile.ignores_occupancy
            else self._occupancy.blocked_cells(map_definition.map_id, excluding=entity_id)
        )
        return HexPathfinder.find_path(map_definition, entity.position.cell, goal, entity.profile, blocked)

    def move_toward(self, entity_id: str, goal: LocalHexPosition) -> MovementResult:
        entity = self.entity(entity_id)
        path = self.path_to(entity_id, goal)
        if path is None or len(path) < 2:
            return MovementResult(False, entity.position, MovementFailureReason.INVALID_TARGET, "No path to target.")
        return self.move_to(entity_id, path[1])

    def move_away(self, entity_id: str, threat: LocalHexPosition) -> MovementResult:
        entity = self.entity(entity_id)
        if entity.kind != "npc":
            raise ValueError("Avoidance movement is reserved for NPC entities.")
        if not isinstance(threat, LocalHexPosition):
            raise TypeError("threat must be a LocalHexPosition.")
        map_definition = self.map_definition(entity.position.map_id)
        candidates = []
        for direction in HexDirection:
            cell = LocalHexPosition.from_hex_coord(entity.position.cell.to_hex_coord().neighbor(direction))
            target = EntityPosition(entity.position.map_id, cell)
            request = MovementRequest(entity_id, entity.position, target, entity.profile)
            result = MovementRules.evaluate(request, map_definition)
            if result.success and (
                entity.profile.ignores_occupancy
                or self._occupancy.can_enter(target, excluding=entity_id)
            ):
                distance = cell.to_hex_coord().distance_to(threat.to_hex_coord())
                candidates.append((distance, -direction.value[0], -direction.value[1], cell))
        if not candidates:
            return MovementResult(False, entity.position, MovementFailureReason.INVALID_TARGET, "No safe adjacent cell is available.")
        destination = max(candidates)[-1]
        return self.move_to(entity_id, destination)

    def patrol(self, entity_id: str, route) -> MovementResult:
        entity = self.entity(entity_id)
        if entity.kind != "npc":
            raise ValueError("Patrol behavior is reserved for NPC entities.")
        points = tuple(route)
        if not points or any(not isinstance(point, LocalHexPosition) for point in points):
            raise ValueError("route must contain LocalHexPosition values.")
        if any(not self.map_definition(entity.position.map_id).has_cell(point) for point in points):
            raise ValueError("Patrol route leaves the map valid_cells mask.")
        index = self._patrol_indices.get(entity_id, 0) % len(points)
        if entity.position.cell == points[index]:
            index = (index + 1) % len(points)
        result = self.move_toward(entity_id, points[index])
        if result.success and result.position.cell == points[index]:
            self._patrol_indices[entity_id] = (index + 1) % len(points)
        else:
            self._patrol_indices[entity_id] = index
        return result

    def transfer_entity(self, entity_id: str, target: EntityPosition) -> MovementResult:
        """Apply a validated cross-map relocation as one atomic occupancy update."""
        entity = self.entity(entity_id)
        if not isinstance(target, EntityPosition):
            raise TypeError("target must be an EntityPosition.")
        if target.map_id not in self._maps or not self.map_definition(target.map_id).has_cell(target.cell):
            return MovementResult(False, entity.position, MovementFailureReason.INVALID_TARGET, "Destination map cell is unavailable.")
        if self.map_definition(target.map_id).is_blocked(target.cell) and not entity.profile.can_traverse_blocked_cells:
            return MovementResult(False, entity.position, MovementFailureReason.BLOCKED_CELL, "Destination cell is blocked.")
        if not entity.profile.ignores_occupancy and not self._occupancy.can_enter(target, excluding=entity_id):
            return MovementResult(False, entity.position, MovementFailureReason.OCCUPIED_CELL, "Destination cell is occupied or movement-blocked.")
        self._occupancy.move(entity_id, target, ignore_blockers=entity.profile.ignores_occupancy)
        self._entities[entity_id] = replace(entity, position=target)
        return MovementResult(True, target)

    def transition(self, entity_id: str, transition_id: str) -> MovementResult:
        from .hex_transition_service import HexMapTransitionService
        return HexMapTransitionService(self, self._world_map).transition(entity_id, transition_id)


__all__ = ["HexMovableEntity", "HexWorldRuntime"]
