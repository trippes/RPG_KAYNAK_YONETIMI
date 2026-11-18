"""Reusable content definitions and categories."""
from dataclasses import dataclass
from enum import Enum
from .drawing import VisualDocument
from .values import freeze_json, non_empty_id

class ContentCategory(str, Enum):
    ENVIRONMENTAL_OBJECT = "environmental_object"
    STRUCTURE = "structure"

@dataclass(frozen=True, slots=True)
class ContentDefinition:
    content_id: str
    name: str
    category: ContentCategory
    visual_document: VisualDocument
    collider: object | None = None
    metadata: object | None = None
    def __post_init__(self):
        non_empty_id(self.content_id, "content_id")
        non_empty_id(self.name, "name")
        if not isinstance(self.category, ContentCategory):
            object.__setattr__(self, "category", ContentCategory(self.category))
        if not isinstance(self.visual_document, VisualDocument):
            raise TypeError("visual_document must be VisualDocument")
        if self.collider is not None:
            from .collision import ColliderDefinition
            if not isinstance(self.collider, ColliderDefinition):
                raise TypeError("collider must be ColliderDefinition or None")
        object.__setattr__(self, "metadata", freeze_json({} if self.metadata is None else self.metadata))
