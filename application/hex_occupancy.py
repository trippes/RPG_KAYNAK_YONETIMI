"""Map-scoped occupancy registry with distinct movement and stacking rules."""
from __future__ import annotations

from dataclasses import dataclass

from core.domain.spatial import EntityPosition


@dataclass(frozen=True, slots=True)
class HexOccupant:
    entity_id: str
    position: EntityPosition
    blocks_movement: bool = True
    blocks_occupancy: bool = True
    kind: str = "entity"

    def __post_init__(self):
        if not isinstance(self.entity_id, str) or not self.entity_id.strip():
            raise ValueError("entity_id must be a non-empty string.")
        if not isinstance(self.position, EntityPosition):
            raise TypeError("position must be an EntityPosition.")
        if not isinstance(self.blocks_movement, bool) or not isinstance(self.blocks_occupancy, bool):
            raise TypeError("occupancy flags must be booleans.")
        if not isinstance(self.kind, str) or not self.kind.strip():
            raise ValueError("kind must be a non-empty string.")


class HexOccupancyRegistry:
    """Own entity placement and atomic movement reservations across local maps."""

    def __init__(self):
        self._occupants: dict[str, HexOccupant] = {}

    def add(self, occupant: HexOccupant, *, ignore_blockers: bool = False) -> None:
        if not isinstance(occupant, HexOccupant):
            raise TypeError("occupant must be a HexOccupant.")
        if occupant.entity_id in self._occupants:
            raise ValueError(f"Duplicate hex occupant: {occupant.entity_id}")
        if not ignore_blockers and not self.can_enter(occupant.position):
            raise ValueError("The target hex is occupied or movement-blocked.")
        self._occupants[occupant.entity_id] = occupant

    def get(self, entity_id: str) -> HexOccupant | None:
        return self._occupants.get(entity_id)

    def remove(self, entity_id: str) -> HexOccupant:
        try:
            return self._occupants.pop(entity_id)
        except KeyError as error:
            raise KeyError(f"Unknown hex occupant: {entity_id}") from error

    def snapshot(self) -> tuple[HexOccupant, ...]:
        return tuple(self._occupants[key] for key in sorted(self._occupants))

    def at(self, position: EntityPosition, excluding: str | None = None) -> tuple[HexOccupant, ...]:
        if not isinstance(position, EntityPosition):
            raise TypeError("position must be an EntityPosition.")
        return tuple(
            item for item in self.snapshot()
            if item.entity_id != excluding and item.position == position
        )

    def is_occupied(self, position: EntityPosition, excluding: str | None = None) -> bool:
        return any(item.blocks_occupancy for item in self.at(position, excluding))

    def is_movement_blocked(self, position: EntityPosition, excluding: str | None = None) -> bool:
        return any(item.blocks_movement for item in self.at(position, excluding))

    def blocked_cells(self, map_id: str, excluding: str | None = None) -> frozenset:
        return frozenset(
            item.position.cell for item in self.snapshot()
            if item.entity_id != excluding
            and item.position.map_id == map_id
            and item.blocks_movement
        )

    def can_enter(self, position: EntityPosition, excluding: str | None = None) -> bool:
        return not self.is_occupied(position, excluding) and not self.is_movement_blocked(position, excluding)

    def move(self, entity_id: str, target: EntityPosition, *, ignore_blockers: bool = False) -> HexOccupant:
        """Atomically relocate an occupant after checking all other blockers."""
        current = self.get(entity_id)
        if current is None:
            raise KeyError(f"Unknown hex occupant: {entity_id}")
        if not isinstance(target, EntityPosition):
            raise TypeError("target must be an EntityPosition.")
        if not ignore_blockers and not self.can_enter(target, excluding=entity_id):
            raise ValueError("The target hex is occupied or movement-blocked.")
        updated = HexOccupant(
            current.entity_id, target, current.blocks_movement,
            current.blocks_occupancy, current.kind,
        )
        self._occupants[entity_id] = updated
        return updated


__all__ = ["HexOccupant", "HexOccupancyRegistry"]
