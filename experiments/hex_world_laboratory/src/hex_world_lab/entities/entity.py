"""Immutable common entity record."""
from dataclasses import dataclass, replace
from hex_world_lab.world.identity import WorldId, MapId
from .identity import EntityId
from .kind import EntityKind
from .transform import EntityTransform
@dataclass(frozen=True, slots=True)
class EntityRecord:
    entity_id: EntityId
    kind: EntityKind
    transform: EntityTransform
    body: object | None = None
    interaction_profile: object | None = None
    is_active: bool = True
    def __post_init__(self) -> None:
        if not isinstance(self.entity_id, EntityId): raise TypeError("entity_id must be an EntityId")
        if not isinstance(self.kind, EntityKind): raise TypeError("kind must be an EntityKind")
        if not isinstance(self.transform, EntityTransform): raise TypeError("transform must be an EntityTransform")
        if not isinstance(self.is_active, bool): raise TypeError("is_active must be a bool")
        if self.body is not None:
            from hex_world_lab.physics.body import BodyDefinition
            if not isinstance(self.body, BodyDefinition): raise TypeError("body must be a BodyDefinition or None")
    @property
    def world_id(self) -> WorldId: return self.transform.location.world_id
    @property
    def map_id(self) -> MapId: return self.transform.location.map_id
    def with_transform(self, transform: EntityTransform) -> "EntityRecord": return replace(self, transform=transform)
    def with_active(self, active: bool) -> "EntityRecord": return replace(self, is_active=active)
