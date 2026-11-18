"""Immutable content library with deterministic identity lookup."""
from dataclasses import dataclass
from types import MappingProxyType
from .definition import ContentDefinition
from .values import non_empty_id

@dataclass(frozen=True, slots=True)
class ContentLibrary:
    library_id: str
    definitions: tuple[ContentDefinition, ...]
    def __post_init__(self):
        non_empty_id(self.library_id, "library_id")
        definitions = tuple(self.definitions)
        if any(not isinstance(item, ContentDefinition) for item in definitions):
            raise TypeError("definitions must contain ContentDefinition values")
        ids = [item.content_id for item in definitions]
        if len(ids) != len(set(ids)):
            raise ValueError("content IDs must be unique")
        object.__setattr__(self, "definitions", tuple(sorted(definitions, key=lambda item: item.content_id)))
    @property
    def by_id(self):
        return MappingProxyType({item.content_id: item for item in self.definitions})
    def resolve(self, content_id: str) -> ContentDefinition:
        try:
            return self.by_id[content_id]
        except KeyError:
            raise KeyError(f"unknown content ID: {content_id}") from None
