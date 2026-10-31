from core.entity.entity import Entity


class EntityRepository:
    """Authoritative registry for Entity objects.

    The repository owns entity registration and lookup only. World membership
    is intentionally managed by WorldMembershipService.
    """

    def __init__(self) -> None:
        self._entities: dict[str, Entity] = {}

    def add(self, entity: Entity) -> Entity:
        if not isinstance(entity, Entity):
            raise TypeError("Only Entity objects can be registered.")
        if entity.entity_id in self._entities:
            raise ValueError(f"Entity ID already exists: {entity.entity_id}")
        self._entities[entity.entity_id] = entity
        return entity

    def remove(self, entity_id: str) -> Entity:
        if entity_id not in self._entities:
            raise KeyError(f"Entity not found: {entity_id}")
        entity = self._entities[entity_id]
        if entity.has_world():
            raise RuntimeError(
                "Owned entities must be removed through WorldMembershipService."
            )
        return self._entities.pop(entity_id)

    def get(self, entity_id: str) -> Entity | None:
        return self._entities.get(entity_id)

    def exists(self, entity_id: str) -> bool:
        return entity_id in self._entities

    def get_all(self) -> tuple[Entity, ...]:
        """Return entities in deterministic insertion order."""

        return tuple(self._entities.values())

    def count(self) -> int:
        return len(self._entities)

    def clear(self) -> None:
        self._entities.clear()

    # Read/query helpers retained for the 1.x Game.entities compatibility
    # surface. They do not own or modify World membership.
    def activate(self, entity_id: str) -> None:
        self._require(entity_id).activate()

    def deactivate(self, entity_id: str) -> None:
        self._require(entity_id).deactivate()

    def kill(self, entity_id: str) -> None:
        self._require(entity_id).kill()

    def revive(self, entity_id: str) -> None:
        self._require(entity_id).revive()

    def get_by_type(self, entity_type):
        return [entity for entity in self._entities.values()
                if entity.entity_type == entity_type]

    def get_by_status(self, status):
        return [entity for entity in self._entities.values()
                if entity.state.get_status() == status]

    def get_alive(self):
        return [entity for entity in self._entities.values() if entity.is_alive()]

    def get_active(self):
        return [entity for entity in self._entities.values() if entity.is_active()]

    def get_by_name(self, name):
        return [entity for entity in self._entities.values() if entity.name == name]

    def _require(self, entity_id: str) -> Entity:
        entity = self.get(entity_id)
        if entity is None:
            raise KeyError(f"Entity not found: {entity_id}")
        return entity
