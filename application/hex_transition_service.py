"""Runtime execution of validated local-map exits and cross-map entry placement."""
from __future__ import annotations

from core.domain.spatial import EntityPosition, MovementFailureReason, MovementResult
from .hex_world_runtime import HexWorldRuntime
from .world_map_definition import WorldMapDefinition, validate_world_map


class HexMapTransitionService:
    """Resolve a map's authored transition and atomically move an entity."""

    def __init__(
        self, runtime: HexWorldRuntime,
        world_map_definition: WorldMapDefinition | None = None,
    ):
        if not isinstance(runtime, HexWorldRuntime):
            raise TypeError("runtime must be a HexWorldRuntime.")
        if world_map_definition is not None:
            validate_world_map(world_map_definition, {
                map_id: runtime.map_definition(map_id)
                for map_id in world_map_definition.placements_by_map_id
            })
        self._runtime = runtime
        self._world_map = world_map_definition

    def transition(self, entity_id: str, transition_id: str) -> MovementResult:
        entity = self._runtime.entity(entity_id)
        source_map = self._runtime.map_definition(entity.position.map_id)
        transition = next(
            (item for item in source_map.transitions if item.transition_id == transition_id),
            None,
        )
        if transition is None or not transition.active:
            return MovementResult(
                False, entity.position, MovementFailureReason.INVALID_TRANSITION,
                "Transition is missing or inactive.",
            )
        if entity.position.cell not in transition.source_cells:
            return MovementResult(
                False, entity.position, MovementFailureReason.INVALID_TRANSITION,
                "Entity is not on a transition source cell.",
            )
        try:
            target_map = self._runtime.map_definition(transition.target_map_id)
        except KeyError:
            return MovementResult(
                False, entity.position, MovementFailureReason.INVALID_TRANSITION,
                "Transition target map is unavailable.",
            )
        if not transition.target_cells:
            return MovementResult(
                False, entity.position, MovementFailureReason.INVALID_TRANSITION,
                "Transition has no destination entry cells.",
            )
        for cell in transition.target_cells:
            if not target_map.has_cell(cell):
                continue
            destination = EntityPosition(target_map.map_id, cell)
            result = self._runtime.transfer_entity(entity_id, destination)
            if result.success:
                return result
            if result.reason not in {
                MovementFailureReason.OCCUPIED_CELL,
                MovementFailureReason.BLOCKED_CELL,
            }:
                return result
        return MovementResult(
            False, entity.position, MovementFailureReason.OCCUPIED_CELL,
            "No valid unoccupied transition entry cell is available.",
        )


__all__ = ["HexMapTransitionService"]
