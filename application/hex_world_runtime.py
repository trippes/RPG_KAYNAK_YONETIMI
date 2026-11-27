"""Runtime orchestration for player, NPC, and movable-object hex movement."""
from __future__ import annotations

import math
from time import perf_counter
from functools import wraps
from threading import RLock

from dataclasses import dataclass, replace
from types import MappingProxyType
from collections.abc import Mapping

from application.hex_map_definition import HexMapDefinition
from application.world_map_definition import WorldMapDefinition, validate_world_map
from core.foundation import WorldId
from core.domain.spatial import (
    AABB, ConstructionPosition, ContinuousEntityPosition, EntityPosition, HexCoord,
    HexDirection, LocalHexPosition,
    MovementFailureReason, MovementProfile, MovementRequest, MovementResult,
    UniformGridIndex, WorldPoint, axial_to_world_point, world_point_to_hex,
)
from .hex_movement_rules import MovementRules
from .hex_occupancy import HexOccupant, HexOccupancyRegistry
from .hex_pathfinding import HexPathfinder


@dataclass(frozen=True, slots=True)
class _HexEntityState:
    """Non-spatial identity and movement data stored by the runtime."""

    entity_id: str
    kind: str
    profile: MovementProfile
    active: bool
    local_spatial_bounds: AABB | None = None
    broadphase_enabled: bool = True

    def __post_init__(self):
        if not isinstance(self.entity_id, str) or not self.entity_id.strip():
            raise ValueError("entity_id must be a non-empty string.")
        if self.kind not in {"player", "npc", "object"}:
            raise ValueError("kind must be player, npc, or object.")
        if not isinstance(self.profile, MovementProfile):
            raise TypeError("profile must be a MovementProfile.")
        if not isinstance(self.active, bool):
            raise TypeError("active must be boolean.")
        if self.local_spatial_bounds is not None and not isinstance(self.local_spatial_bounds, AABB):
            raise TypeError("local_spatial_bounds must be an AABB or None.")
        if not isinstance(self.broadphase_enabled, bool):
            raise TypeError("broadphase_enabled must be boolean.")


@dataclass(frozen=True, slots=True)
class HexMovableEntity:
    entity_id: str
    kind: str
    position: EntityPosition
    profile: MovementProfile
    active: bool = True
    continuous_position: ContinuousEntityPosition | None = None

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
        if self.continuous_position is not None:
            if not isinstance(self.continuous_position, ContinuousEntityPosition):
                raise TypeError("continuous_position must be a ContinuousEntityPosition or None.")
            if self.continuous_position.map_id != self.position.map_id:
                raise ValueError("continuous position belongs to a different map.")


def _runtime_state_locked(method):
    """Serialize authoritative runtime mutations and construction commits."""
    @wraps(method)
    def locked(self, *args, **kwargs):
        with self._state_lock:
            return method(self, *args, **kwargs)
    return locked


@dataclass(frozen=True, slots=True)
class HexWorldStructurePlacement:
    """One live structure placement owned by the authoritative hex runtime."""

    structure_id: str
    part_definition_id: str
    position: ConstructionPosition
    footprint_cells: tuple[HexCoord, ...]
    created_by_actor_id: str

    def __post_init__(self):
        for name in ("structure_id", "part_definition_id", "created_by_actor_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string.")
        if not isinstance(self.position, ConstructionPosition):
            raise TypeError("position must be a ConstructionPosition.")
        cells = tuple(self.footprint_cells)
        if not cells or any(not isinstance(cell, HexCoord) for cell in cells):
            raise ValueError("footprint_cells must contain HexCoord values.")
        if len(cells) != len(set(cells)):
            raise ValueError("footprint_cells cannot contain duplicates.")
        object.__setattr__(self, "footprint_cells", tuple(sorted(cells, key=lambda c: (c.q, c.r))))


class HexWorldRuntimeOwner:
    """Own one lazily initialized hex runtime for a single gameplay session."""

    def __init__(self, runtime: HexWorldRuntime | None = None) -> None:
        if runtime is not None and not isinstance(runtime, HexWorldRuntime):
            raise TypeError("hex_world_runtime must be HexWorldRuntime or None.")
        self._runtime = runtime

    @property
    def runtime(self) -> HexWorldRuntime | None:
        return self._runtime

    def get_or_create(self, factory) -> HexWorldRuntime:
        """Create the session runtime once; subsequent views reuse the same state."""
        if self._runtime is None:
            candidate = factory()
            if not isinstance(candidate, HexWorldRuntime):
                raise TypeError("runtime factory must return HexWorldRuntime.")
            self._runtime = candidate
        return self._runtime

    def discard_if_empty(self, runtime: HexWorldRuntime) -> bool:
        """Discard only the exact owned runtime when failed initialization left it empty."""
        if runtime is not self._runtime:
            return False
        if runtime.entities():
            raise RuntimeError("Cannot discard a HexWorldRuntime that still has entities.")
        self._runtime = None
        return True


class HexWorldRuntime:
    """Owns continuous world positions and their derived hex occupancy view."""

    HEX_SIZE = 32.0

    def __init__(
        self, map_definitions, occupancy: HexOccupancyRegistry | None = None,
        world_map_definition: WorldMapDefinition | None = None,
        *,
        world_id: WorldId | None = None,
        metrics=None,
    ):
        if world_id is not None and not isinstance(world_id, WorldId):
            raise TypeError("world_id must be a WorldId or None.")
        maps = dict(map_definitions)
        if not maps or any(not isinstance(value, HexMapDefinition) for value in maps.values()):
            raise ValueError("map_definitions must contain at least one HexMapDefinition.")
        if any(key != value.map_id for key, value in maps.items()):
            raise ValueError("map definition keys must match map_id.")
        if world_map_definition is not None:
            validate_world_map(world_map_definition, maps)
        self._maps = maps
        self._world_map = world_map_definition
        self._world_id = world_id
        self.metrics = metrics
        self._occupancy = occupancy or HexOccupancyRegistry()
        self._entities: dict[str, _HexEntityState] = {}
        self._continuous_positions: dict[str, ContinuousEntityPosition] = {}
        self._spatial_index = UniformGridIndex()
        self._patrol_indices: dict[str, int] = {}
        self._state_lock = RLock()
        self._state_revision = 0
        self._structure_placements: dict[str, HexWorldStructurePlacement] = {}
        self._structure_cells: dict[tuple[str, HexCoord], str] = {}
        self._next_structure_id = 1

    @property
    def world_id(self) -> WorldId | None:
        """World scope bound to this runtime, if it is session-integrated."""
        return self._world_id

    @property
    def map_ids(self) -> tuple[str, ...]:
        """Stable IDs of the local maps owned by this runtime."""
        return tuple(sorted(self._maps))

    @property
    def world_map_definition(self) -> WorldMapDefinition | None:
        """Immutable world topology used to connect the local maps."""
        return self._world_map

    @property
    def occupancy(self) -> HexOccupancyRegistry:
        return self._occupancy

    @property
    def state_revision(self) -> int:
        """Monotonic revision for authoritative spatial/runtime state."""
        return self._state_revision

    def structure_placements(self, map_id: str | None = None) -> tuple[HexWorldStructurePlacement, ...]:
        """Return immutable structure placement views in stable ID order."""
        if map_id is not None:
            self.map_definition(map_id)
        return tuple(
            self._structure_placements[key]
            for key in sorted(self._structure_placements)
            if map_id is None or self._structure_placements[key].position.map_id == map_id
        )

    @_runtime_state_locked
    def construction_snapshot(self, map_id: str, *, supported_cells=()):
        """Build placement evidence from this runtime's authoritative map and occupants.

        Support evidence is supplied by its future owning subsystem; this runtime
        deliberately does not infer structural support from terrain walkability.
        """
        from application.construction_placement import ConstructionPlacementSnapshot

        map_definition = self.map_definition(map_id)
        supported = frozenset(supported_cells)
        if any(not isinstance(cell, HexCoord) for cell in supported):
            raise TypeError("supported_cells must contain HexCoord values.")
        occupied: dict[HexCoord, str] = {}
        for occupant in self._occupancy.snapshot():
            if occupant.position.map_id == map_id:
                occupied.setdefault(occupant.position.cell.to_hex_coord(), occupant.entity_id)
        for (placed_map_id, cell), structure_id in self._structure_cells.items():
            if placed_map_id == map_id:
                occupied[cell] = structure_id
        return ConstructionPlacementSnapshot(
            map_definition=map_definition,
            hex_size=self.HEX_SIZE,
            origin=WorldPoint(0.0, 0.0),
            occupied_cells=occupied,
            supported_cells=supported,
            state_revision=self._state_revision,
        )

    @_runtime_state_locked
    def commit_if_revision(self, expected_revision, request, result) -> bool:
        """Commit one placement against the same live state revision.

        The runtime is the single owner of actor occupancy and placed structures.
        The revision check, final overlap/bounds checks, and insertion are kept in
        one serialized operation; a rejected commit never mutates world state.
        """
        from application.construction_placement import ConstructionPlacementRequest, ConstructionPlacementResult

        if type(expected_revision) is not int or expected_revision < 0:
            raise ValueError("expected_revision must be a non-negative integer.")
        if not isinstance(request, ConstructionPlacementRequest):
            raise TypeError("request must be a ConstructionPlacementRequest.")
        if not isinstance(result, ConstructionPlacementResult):
            raise TypeError("result must be a ConstructionPlacementResult.")
        if expected_revision != self._state_revision or result.snapshot_revision != expected_revision:
            return False
        if not result.valid or not result.footprint_cells:
            return False
        map_id = request.position.map_id
        map_definition = self.map_definition(map_id)
        if request.actor_id not in self._entities:
            return False
        actor = self.entity(request.actor_id)
        if actor.position.map_id != map_id:
            return False
        footprint = tuple(result.footprint_cells)
        if len(footprint) != len(set(footprint)):
            return False
        for cell in footprint:
            local = LocalHexPosition.from_hex_coord(cell)
            if not map_definition.has_cell(local) or map_definition.is_blocked(local):
                return False
            if any(
                occupant.position.map_id == map_id and occupant.position.cell == local
                for occupant in self._occupancy.snapshot()
            ):
                return False
            if (map_id, cell) in self._structure_cells:
                return False
        structure_id = f"structure-{self._next_structure_id:08d}"
        placement = HexWorldStructurePlacement(
            structure_id,
            request.part_definition_id,
            request.position,
            footprint,
            request.actor_id,
        )
        self._structure_placements[structure_id] = placement
        for cell in footprint:
            self._structure_cells[(map_id, cell)] = structure_id
        self._next_structure_id += 1
        self._state_revision += 1
        return True

    def map_definition(self, map_id: str) -> HexMapDefinition:
        try:
            return self._maps[map_id]
        except KeyError as error:
            raise KeyError(f"Unknown hex map: {map_id}") from error

    @_runtime_state_locked
    def register_entity(
        self, entity_id: str, kind: str, position: EntityPosition,
        profile: MovementProfile | None = None, *, active: bool = True,
        blocks_movement: bool = True, blocks_occupancy: bool = True,
        continuous_position: ContinuousEntityPosition | None = None,
        local_spatial_bounds: AABB | None = None,
        broadphase_enabled: bool = True,
    ) -> HexMovableEntity:
        if entity_id in self._entities:
            raise ValueError(f"Duplicate hex entity: {entity_id}")
        if not isinstance(position, EntityPosition):
            raise TypeError("position must be an EntityPosition.")
        if local_spatial_bounds is not None and not isinstance(local_spatial_bounds, AABB):
            raise TypeError("local_spatial_bounds must be an AABB or None.")
        if not isinstance(broadphase_enabled, bool):
            raise TypeError("broadphase_enabled must be boolean.")
        map_definition = self.map_definition(position.map_id)
        if not map_definition.has_cell(position.cell):
            raise ValueError("Entity position is outside the map valid_cells mask.")
        if profile is None:
            profile = MovementProfile(can_move=(kind != "object"))
        if not isinstance(profile, MovementProfile):
            raise TypeError("profile must be a MovementProfile.")
        if map_definition.is_blocked(position.cell) and not profile.can_traverse_blocked_cells:
            raise ValueError("Entity cannot be placed on a blocked cell.")
        if continuous_position is None:
            center = axial_to_world_point(position.cell.to_hex_coord(), self.HEX_SIZE)
            continuous_position = ContinuousEntityPosition(position.map_id, center)
        if not isinstance(continuous_position, ContinuousEntityPosition):
            raise TypeError("continuous_position must be a ContinuousEntityPosition or None.")
        if continuous_position.map_id != position.map_id:
            raise ValueError("continuous position belongs to a different map.")
        resolved_cell = LocalHexPosition.from_hex_coord(
            world_point_to_hex(
                continuous_position.point, self.HEX_SIZE,
                previous_cell=position.cell.to_hex_coord(),
            )
        )
        if resolved_cell != position.cell:
            raise ValueError("continuous position does not resolve to the supplied map cell.")
        state = _HexEntityState(entity_id, kind, profile, active, local_spatial_bounds, broadphase_enabled)
        occupant = HexOccupant(
            entity_id, position, blocks_movement, blocks_occupancy, kind,
        )
        self._occupancy.add(
            occupant, ignore_blockers=profile.ignores_occupancy
        )
        try:
            self._spatial_index.insert(
                entity_id,
                continuous_position.map_id,
                self._bounds_at(state, continuous_position.point),
            )
        except Exception:
            self._occupancy.remove(entity_id)
            raise
        self._entities[entity_id] = state
        self._continuous_positions[entity_id] = continuous_position
        self._state_revision += 1
        return self.entity(entity_id)

    def _entity_state(self, entity_id: str) -> _HexEntityState:
        try:
            return self._entities[entity_id]
        except KeyError as error:
            raise KeyError(f"Unknown hex entity: {entity_id}") from error

    @staticmethod
    def _bounds_at(state: _HexEntityState, point: WorldPoint) -> AABB:
        """Translate immutable local collider bounds to the authoritative world point."""
        local = state.local_spatial_bounds
        if local is None:
            return AABB.at_point(point)
        return AABB(
            point.x + local.min_x, point.y + local.min_y,
            point.x + local.max_x, point.y + local.max_y,
        )

    def entity(self, entity_id: str) -> HexMovableEntity:
        """Return a read-only entity view with position derived from occupancy."""
        if self.metrics is not None:
            self.metrics.increment("runtime_entity_validation_queries")
        state = self._entity_state(entity_id)
        occupant = self._occupancy.get(entity_id)
        if occupant is None:
            raise RuntimeError(
                f"Hex entity has no authoritative occupancy record: {entity_id}"
            )
        if occupant.kind != state.kind:
            raise RuntimeError(
                f"Hex entity and occupancy kind mismatch: {entity_id}"
            )
        continuous_position = self._continuous_positions.get(entity_id)
        if continuous_position is None:
            raise RuntimeError(
                f"Hex entity has no authoritative continuous position: {entity_id}"
            )
        if continuous_position.map_id != occupant.position.map_id:
            raise RuntimeError(f"Hex entity continuous position map mismatch: {entity_id}")
        resolved_cell = LocalHexPosition.from_hex_coord(
            world_point_to_hex(
                continuous_position.point, self.HEX_SIZE,
                previous_cell=occupant.position.cell.to_hex_coord(),
            )
        )
        if resolved_cell != occupant.position.cell:
            raise RuntimeError(f"Hex entity continuous position and occupancy diverged: {entity_id}")
        if entity_id not in self._spatial_index.query(
            continuous_position.map_id, self._bounds_at(state, continuous_position.point)
        ):
            raise RuntimeError(f"Hex entity spatial index is inconsistent: {entity_id}")
        return HexMovableEntity(
            state.entity_id, state.kind, occupant.position,
            state.profile, state.active, continuous_position,
        )

    def entities(self) -> tuple[HexMovableEntity, ...]:
        return tuple(self.entity(key) for key in sorted(self._entities))

    @_runtime_state_locked
    def remove_entity(self, entity_id: str) -> HexMovableEntity:
        """Remove one spatial registration and its authoritative occupancy."""
        previous = self.entity(entity_id)
        self._occupancy.remove(entity_id)
        self._spatial_index.remove(entity_id)
        del self._entities[entity_id]
        del self._continuous_positions[entity_id]
        self._patrol_indices.pop(entity_id, None)
        self._state_revision += 1
        return previous

    @_runtime_state_locked
    def set_active(self, entity_id: str, active: bool) -> HexMovableEntity:
        if not isinstance(active, bool):
            raise TypeError("active must be boolean.")
        state = self._entity_state(entity_id)
        self._entities[entity_id] = replace(state, active=active)
        self._state_revision += 1
        return self.entity(entity_id)

    def move(self, entity_id: str, direction: HexDirection) -> MovementResult:
        entity = self.entity(entity_id)
        if not entity.active or not entity.profile.can_move:
            return MovementResult(False, entity.position, MovementFailureReason.MOVEMENT_NOT_ALLOWED, "Entity cannot move.")
        if not isinstance(direction, HexDirection):
            raise TypeError("direction must be a HexDirection.")
        target_cell = LocalHexPosition.from_hex_coord(entity.position.cell.to_hex_coord().neighbor(direction))
        return self.move_to(entity_id, target_cell)

    def validate_move_to(
        self,
        entity_id: str,
        target: LocalHexPosition,
    ) -> MovementResult:
        """Validate a cell move without mutating occupancy or entity state."""
        entity = self.entity(entity_id)
        if not isinstance(target, LocalHexPosition):
            raise TypeError("target must be a LocalHexPosition.")
        if not entity.active or not entity.profile.can_move:
            return MovementResult(
                False,
                entity.position,
                MovementFailureReason.MOVEMENT_NOT_ALLOWED,
                "Entity cannot move.",
            )
        destination = EntityPosition(entity.position.map_id, target)
        request = MovementRequest(
            entity_id,
            entity.position,
            destination,
            entity.profile,
        )
        result = MovementRules.evaluate(
            request,
            self.map_definition(entity.position.map_id),
        )
        if not result.success:
            return result
        if (
            not entity.profile.ignores_occupancy
            and not self._occupancy.can_enter(destination, excluding=entity_id)
        ):
            return MovementResult(
                False,
                entity.position,
                MovementFailureReason.OCCUPIED_CELL,
                "Target cell is occupied or movement-blocked.",
            )
        return MovementResult(True, destination)

    @_runtime_state_locked
    def _commit_position(
        self,
        entity_id: str,
        target: EntityPosition,
        continuous_position: ContinuousEntityPosition,
    ) -> None:
        """Commit occupancy, broadphase bounds, and position as one operation.

        The spatial index is updated first because its update validates all new
        bucket keys before replacing the old entry. If occupancy rejects the
        relocation, the previous broadphase entry is restored before re-raising.
        The authoritative continuous position is assigned only after both
        derived registries have accepted the move.
        """
        state = self._entity_state(entity_id)
        if self._occupancy.get(entity_id) is None:
            raise RuntimeError(f"Hex entity has no occupancy record: {entity_id}")
        previous_position = self._continuous_positions[entity_id]
        previous_bounds = self._bounds_at(state, previous_position.point)
        next_bounds = self._bounds_at(state, continuous_position.point)

        self._spatial_index.update(
            entity_id, continuous_position.map_id, next_bounds,
        )
        try:
            self._occupancy.move(
                entity_id,
                target,
                ignore_blockers=state.profile.ignores_occupancy,
            )
        except Exception:
            self._spatial_index.update(
                entity_id, previous_position.map_id, previous_bounds,
            )
            raise
        self._continuous_positions[entity_id] = continuous_position
        self._state_revision += 1

    def move_to(self, entity_id: str, target: LocalHexPosition) -> MovementResult:
        """Validate then atomically commit one map-local cell movement."""
        result = self.validate_move_to(entity_id, target)
        if not result.success:
            return result
        center = axial_to_world_point(result.position.cell.to_hex_coord(), self.HEX_SIZE)
        continuous_position = ContinuousEntityPosition(result.position.map_id, center)
        self._commit_position(entity_id, result.position, continuous_position)
        return result

    def continuous_position(self, entity_id: str) -> ContinuousEntityPosition:
        """Return the authoritative map-scoped continuous world position."""
        self.entity(entity_id)
        return self._continuous_positions[entity_id]

    @_runtime_state_locked
    def set_continuous_position(self, entity_id: str, point: WorldPoint) -> MovementResult:
        """Apply one continuous update and atomically refresh occupancy and broadphase."""
        if not isinstance(point, WorldPoint):
            raise TypeError("point must be a WorldPoint.")
        entity = self.entity(entity_id)
        if not entity.active or not entity.profile.can_move:
            return MovementResult(
                False, entity.position, MovementFailureReason.MOVEMENT_NOT_ALLOWED,
                "Entity cannot move.",
            )
        target_coord = world_point_to_hex(
            point, self.HEX_SIZE,
            previous_cell=entity.position.cell.to_hex_coord(),
        )
        target_cell = LocalHexPosition.from_hex_coord(target_coord)
        target = EntityPosition(entity.position.map_id, target_cell)
        map_definition = self.map_definition(target.map_id)
        if not map_definition.has_cell(target_cell):
            return MovementResult(
                False, entity.position, MovementFailureReason.INVALID_TARGET,
                "Continuous position resolves outside the map valid_cells mask.",
            )
        if target_cell == entity.position.cell:
            next_position = ContinuousEntityPosition(entity.position.map_id, point)
            state = self._entity_state(entity_id)
            self._spatial_index.update(
                entity_id, next_position.map_id,
                self._bounds_at(state, next_position.point),
            )
            self._continuous_positions[entity_id] = next_position
            self._state_revision += 1
            return MovementResult(True, entity.position)
        request = MovementRequest(entity_id, entity.position, target, entity.profile)
        validation = MovementRules.evaluate(request, map_definition)
        if not validation.success:
            return validation
        if (
            not entity.profile.ignores_occupancy
            and not self._occupancy.can_enter(target, excluding=entity_id)
        ):
            return MovementResult(
                False, entity.position, MovementFailureReason.OCCUPIED_CELL,
                "Target cell is occupied or movement-blocked.",
            )
        next_position = ContinuousEntityPosition(entity.position.map_id, point)
        self._commit_position(entity_id, target, next_position)
        return MovementResult(True, target)

    def query_spatial_candidates(self, map_id: str, bounds: AABB) -> tuple[str, ...]:
        """Return enabled broadphase actors near a map-scoped world-space AABB."""
        candidates = tuple(
            entity_id
            for entity_id in self._spatial_index.query(map_id, bounds)
            if self._entity_state(entity_id).broadphase_enabled
        )
        if self.metrics is not None:
            self.metrics.increment("runtime_spatial_queries")
            self.metrics.increment("runtime_spatial_candidates", len(candidates))
        return candidates

    def path_to(self, entity_id: str, goal: LocalHexPosition, *, edge_validator=None):
        if self.metrics is not None:
            self.metrics.increment("runtime_path_queries")
        entity = self.entity(entity_id)
        if not entity.active or not entity.profile.can_move:
            return None
        map_definition = self.map_definition(entity.position.map_id)
        blocked = (
            frozenset() if entity.profile.ignores_occupancy
            else self._occupancy.blocked_cells(map_definition.map_id, excluding=entity_id)
        )
        if self.metrics is None:
            return HexPathfinder.find_path(
                map_definition, entity.position.cell, goal, entity.profile, blocked,
                edge_validator=edge_validator,
            )
        started = perf_counter()
        try:
            return HexPathfinder.find_path(
                map_definition, entity.position.cell, goal, entity.profile, blocked,
                edge_validator=edge_validator,
            )
        finally:
            self.metrics.record_duration(
                "runtime_pathfinder_search", perf_counter() - started,
            )

    def move_toward(self, entity_id: str, goal: LocalHexPosition, *, edge_validator=None) -> MovementResult:
        entity = self.entity(entity_id)
        if not entity.active or not entity.profile.can_move:
            return MovementResult(
                False, entity.position, MovementFailureReason.MOVEMENT_NOT_ALLOWED,
                "Entity cannot move.",
            )
        path = self.path_to(entity_id, goal, edge_validator=edge_validator)
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

    def patrol(self, entity_id: str, route, *, edge_validator=None) -> MovementResult:
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
        result = self.move_toward(entity_id, points[index], edge_validator=edge_validator)
        if result.success and result.position.cell == points[index]:
            self._patrol_indices[entity_id] = (index + 1) % len(points)
        else:
            self._patrol_indices[entity_id] = index
        return result

    def patrol_target(self, entity_id: str, route) -> LocalHexPosition:
        """Return the current patrol waypoint, advancing progress on waypoint arrival."""
        entity = self.entity(entity_id)
        if entity.kind != "npc":
            raise ValueError("Patrol behavior is reserved for NPC entities.")
        points = tuple(route)
        if len(points) < 2 or any(not isinstance(point, LocalHexPosition) for point in points):
            raise ValueError("route must contain at least two LocalHexPosition waypoints.")
        map_definition = self.map_definition(entity.position.map_id)
        if any(not map_definition.has_cell(point) for point in points):
            raise ValueError("Patrol route leaves the map valid_cells mask.")
        index = self._patrol_indices.get(entity_id, 0) % len(points)
        waypoint_center = axial_to_world_point(
            points[index].to_hex_coord(), self.HEX_SIZE,
        )
        current_point = entity.continuous_position.point
        if (
            math.hypot(
                current_point.x - waypoint_center.x,
                current_point.y - waypoint_center.y,
            ) <= 1e-5
        ):
            index = (index + 1) % len(points)
            self._patrol_indices[entity_id] = index
        return points[index]

    def transfer_entity(self, entity_id: str, target: EntityPosition) -> MovementResult:
        entity = self.entity(entity_id)
        if not isinstance(target, EntityPosition):
            raise TypeError("target must be an EntityPosition.")
        if not entity.active or not entity.profile.can_move:
            return MovementResult(False, entity.position, MovementFailureReason.MOVEMENT_NOT_ALLOWED, "Entity cannot change maps.")
        if target.map_id not in self._maps or not self.map_definition(target.map_id).has_cell(target.cell):
            return MovementResult(False, entity.position, MovementFailureReason.INVALID_TARGET, "Destination map cell is unavailable.")
        if self.map_definition(target.map_id).is_blocked(target.cell) and not entity.profile.can_traverse_blocked_cells:
            return MovementResult(False, entity.position, MovementFailureReason.BLOCKED_CELL, "Destination cell is blocked.")
        if not entity.profile.ignores_occupancy and not self._occupancy.can_enter(target, excluding=entity_id):
            return MovementResult(False, entity.position, MovementFailureReason.OCCUPIED_CELL, "Destination cell is occupied or movement-blocked.")
        center = axial_to_world_point(target.cell.to_hex_coord(), self.HEX_SIZE)
        next_continuous_position = ContinuousEntityPosition(target.map_id, center)
        self._commit_position(entity_id, target, next_continuous_position)
        return MovementResult(True, target)

    @property
    def patrol_indices(self) -> Mapping[str, int]:
        """Read-only copy of deterministic NPC patrol progress."""
        return MappingProxyType(dict(self._patrol_indices))

    def restore_patrol_indices(self, indices: Mapping[str, int]) -> None:
        """Restore patrol progress after entity registrations are complete."""
        if not isinstance(indices, Mapping):
            raise TypeError("indices must be a mapping.")
        normalized = {}
        for entity_id, index in indices.items():
            if not isinstance(entity_id, str) or not entity_id.strip():
                raise ValueError("patrol entity IDs must be non-empty strings.")
            state = self._entity_state(entity_id)
            if state.kind != "npc":
                raise ValueError("Patrol progress can only belong to NPC entities.")
            if type(index) is not int or index < 0:
                raise ValueError("patrol indices must be non-negative integers.")
            normalized[entity_id] = index
        self._patrol_indices = normalized

    def transition(self, entity_id: str, transition_id: str) -> MovementResult:
        from .hex_transition_service import HexMapTransitionService
        return HexMapTransitionService(self, self._world_map).transition(entity_id, transition_id)


__all__ = ["HexMovableEntity", "HexWorldStructurePlacement", "HexWorldRuntime", "HexWorldRuntimeOwner"]
