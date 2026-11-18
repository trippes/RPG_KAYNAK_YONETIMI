"""Immutable map-local content placement records."""

from dataclasses import dataclass

from .values import finite_number, non_empty_id


@dataclass(frozen=True, slots=True)
class ContentPlacement:
    instance_id: str
    content_id: str
    x: float
    y: float

    def __post_init__(self):
        non_empty_id(self.instance_id, "instance_id")
        non_empty_id(self.content_id, "content_id")
        object.__setattr__(self, "x", finite_number(self.x, "placement.x"))
        object.__setattr__(self, "y", finite_number(self.y, "placement.y"))
