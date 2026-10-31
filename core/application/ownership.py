from core.application.entity_repository import EntityRepository
from core.entity.entity import Entity
from core.foundation import EntityId, WorldId


class WorldMembershipService:
    """Single writer for canonical Entity-to-World membership."""

    def __init__(self, entity_repository, world_registry) -> None:
        if not isinstance(entity_repository, EntityRepository):
            raise TypeError("entity_repository must be an EntityRepository.")
        if not callable(getattr(world_registry, "get", None)):
            raise TypeError("world_registry must provide get().")

        self._entity_repository = entity_repository
        self._world_registry = world_registry
        self._entity_to_world: dict[str, str] = {}
        self._world_to_entities: dict[str, dict[str, None]] = {}

    @property
    def entity_repository(self) -> EntityRepository:
        return self._entity_repository

    @property
    def world_registry(self):
        return self._world_registry

    @staticmethod
    def _entity_id_value(entity_id) -> str:
        if isinstance(entity_id, EntityId):
            return entity_id.value
        if isinstance(entity_id, str) and entity_id.strip():
            return entity_id
        raise TypeError("entity_id must be an EntityId or non-empty string.")

    @staticmethod
    def _world_id_value(world_id) -> str:
        if isinstance(world_id, WorldId):
            return world_id.value
        if isinstance(world_id, str) and world_id.strip():
            return world_id
        raise TypeError("world_id must be a WorldId or non-empty string.")

    def add(self, entity_id: str, world_id: str) -> Entity:
        entity_id = self._entity_id_value(entity_id)
        world_id = self._world_id_value(world_id)
        entity = self._require_entity(entity_id)
        world = self._require_world(world_id)

        if entity_id in self._entity_to_world:
            current_world_id = self._entity_to_world[entity_id]
            if current_world_id == world_id:
                raise ValueError("Entity is already a member of this World.")
            raise ValueError("Entity already belongs to another World.")

        # Update the 1.x projection first. If it fails, no canonical mapping
        # has been committed yet.
        world._compat_attach_entity(entity)
        try:
            self._entity_to_world[entity_id] = world_id
            self._world_to_entities.setdefault(world_id, {})[entity_id] = None
        except Exception:
            world._compat_remove_entity(entity_id)
            raise

        return entity

    def remove(self, entity_id: str, world_id: str | None = None) -> Entity:
        entity_id = self._entity_id_value(entity_id)
        if world_id is not None:
            world_id = self._world_id_value(world_id)
        entity = self._require_entity(entity_id)
        current_world_id = self._entity_to_world.get(entity_id)
        if current_world_id is None:
            raise KeyError(f"Entity has no canonical World membership: {entity_id}")
        if world_id is not None and world_id != current_world_id:
            raise ValueError("Entity does not belong to the specified World.")

        world = self._require_world(current_world_id)
        world._compat_detach_entity(entity)
        removed = entity
        try:
            del self._entity_to_world[entity_id]
            members = self._world_to_entities[current_world_id]
            del members[entity_id]
            if not members:
                del self._world_to_entities[current_world_id]
        except Exception:
            # Restore the projection and canonical mapping if commit fails.
            world._compat_attach_entity(removed)
            self._entity_to_world[entity_id] = current_world_id
            self._world_to_entities.setdefault(current_world_id, {})[entity_id] = None
            raise

        return removed

    def transfer(self, entity_id: str, target_world_id: str) -> Entity:
        entity_id = self._entity_id_value(entity_id)
        target_world_id = self._world_id_value(target_world_id)
        entity = self._require_entity(entity_id)
        current_world_id = self._entity_to_world.get(entity_id)
        if current_world_id is None:
            raise KeyError(f"Entity has no canonical World membership: {entity_id}")
        if current_world_id == target_world_id:
            raise ValueError("Entity is already a member of the target World.")

        source_world = self._require_world(current_world_id)
        target_world = self._require_world(target_world_id)
        if target_world.has_entity(entity_id) and target_world.get_entity(entity_id) is not entity:
            raise ValueError("Target World already contains this Entity.")

        source_world._compat_detach_entity(entity)
        removed = entity
        try:
            target_world._compat_attach_entity(entity)
        except Exception:
            source_world._compat_attach_entity(removed)
            raise

        try:
            del self._world_to_entities[current_world_id][entity_id]
            if not self._world_to_entities[current_world_id]:
                del self._world_to_entities[current_world_id]
            self._world_to_entities.setdefault(target_world_id, {})[entity_id] = None
            self._entity_to_world[entity_id] = target_world_id
        except Exception:
            target_world._compat_detach_entity(entity)
            source_world._compat_attach_entity(entity)
            self._world_to_entities.setdefault(current_world_id, {})[entity_id] = None
            self._entity_to_world[entity_id] = current_world_id
            raise

        return entity

    def world_id_for(self, entity_id: str) -> str | None:
        return self._entity_to_world.get(self._entity_id_value(entity_id))

    def entity_ids_for(self, world_id: str) -> tuple[str, ...]:
        return tuple(self._world_to_entities.get(self._world_id_value(world_id), {}).keys())

    def is_member(self, entity_id: str, world_id: str) -> bool:
        return self.world_id_for(entity_id) == self._world_id_value(world_id)

    def _require_entity(self, entity_id: str) -> Entity:
        entity = self._entity_repository.get(entity_id)
        if entity is None:
            raise KeyError(f"Entity not found: {entity_id}")
        return entity

    def _require_world(self, world_id: str):
        world = self._world_registry.get(world_id)
        if world is None:
            raise KeyError(f"World not found: {world_id}")
        return world
