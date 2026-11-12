"""Pure application rules for validating one local axial-hex movement."""
from __future__ import annotations

from application.hex_map_definition import HexMapDefinition
from core.domain.spatial import (
    EntityPosition,
    MovementFailureReason,
    MovementRequest,
    MovementResult,
)


class MovementRules:
    """Validate movement intents without mutating entities, maps, or runtime state.

    Occupancy and multi-entity collision resolution are intentionally left to
    the later collision stage. Cross-map movement is handled by map-transition
    services, not by a local movement request.
    """

    @staticmethod
    def evaluate(
        request: MovementRequest,
        map_definition: HexMapDefinition,
    ) -> MovementResult:
        if not isinstance(request, MovementRequest):
            raise TypeError("request must be a MovementRequest.")
        if not isinstance(map_definition, HexMapDefinition):
            raise TypeError("map_definition must be a HexMapDefinition.")

        source = request.source
        target = request.target

        def reject(reason: MovementFailureReason, detail: str) -> MovementResult:
            return MovementResult(False, source, reason, detail)

        if source.map_id != map_definition.map_id:
            return reject(
                MovementFailureReason.INVALID_SOURCE,
                "Source map does not match the supplied map definition.",
            )
        if target.map_id != source.map_id:
            return reject(
                MovementFailureReason.INVALID_TRANSITION,
                "A local movement request cannot change maps.",
            )
        if not map_definition.has_cell(source.cell):
            return reject(
                MovementFailureReason.INVALID_SOURCE,
                "Source position is outside the map valid_cells mask.",
            )
        if not map_definition.has_cell(target.cell):
            return reject(
                MovementFailureReason.INVALID_TARGET,
                "Target position is outside the map valid_cells mask.",
            )
        if not request.profile.can_move:
            return reject(
                MovementFailureReason.MOVEMENT_NOT_ALLOWED,
                "The movement profile does not permit movement.",
            )
        if source.cell == target.cell or source.cell.to_hex_coord().distance_to(
            target.cell.to_hex_coord()
        ) != 1:
            return reject(
                MovementFailureReason.NON_ADJACENT_TARGET,
                "Target must be exactly one axial hex step from source.",
            )

        target_cell = map_definition.get_cell(target.cell)
        if target_cell is None:
            return reject(
                MovementFailureReason.INVALID_TARGET,
                "Target cell has no cell definition.",
            )
        if target_cell.blocked and not request.profile.can_traverse_blocked_cells:
            return reject(
                MovementFailureReason.BLOCKED_CELL,
                "Target cell is blocked.",
            )
        allowed = request.profile.allowed_terrain_ids
        if allowed is not None and target_cell.terrain_id not in allowed:
            return reject(
                MovementFailureReason.TERRAIN_NOT_ALLOWED,
                f"Terrain '{target_cell.terrain_id}' is not allowed by the movement profile.",
            )

        return MovementResult(True, target)
