"""Immutable, data-driven definitions for physical containers."""
from dataclasses import dataclass
from math import isfinite


def _optional_limit(value, name):
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a number or None.")
    if not isfinite(value) or value < 0:
        raise ValueError(f"{name} must be finite and non-negative.")


def _tags(values, name):
    result = tuple(values)
    if any(not isinstance(tag, str) or not tag.strip() for tag in result):
        raise ValueError(f"{name} must contain non-empty strings.")
    if len(result) != len(set(result)):
        raise ValueError(f"{name} must not contain duplicates.")
    return tuple(sorted(result))


@dataclass(frozen=True)
class ContainerDefinition:
    """Content definition shared by all runtime instances of one container kind."""
    definition_id: str
    name: str
    empty_weight_kg: float = 0.0
    outer_volume_liters: float = 0.0
    max_contents_weight_kg: float | None = None
    max_slots: int | None = None
    max_contents_volume_liters: float | None = None
    nesting_enabled: bool = True
    max_nesting_depth: int = 1
    allowed_item_tags: tuple[str, ...] = ()
    denied_item_tags: tuple[str, ...] = ()
    allowed_resource_tags: tuple[str, ...] = ()
    denied_resource_tags: tuple[str, ...] = ()
    allowed_container_tags: tuple[str, ...] = ()
    denied_container_tags: tuple[str, ...] = ()
    container_tags: tuple[str, ...] = ()
    break_profile_id: str | None = None

    def __post_init__(self):
        for field in ("definition_id", "name"):
            value = getattr(self, field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field} must be a non-empty string.")
        for field in ("empty_weight_kg", "outer_volume_liters"):
            value = getattr(self, field)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise TypeError(f"{field} must be a number.")
            if not isfinite(value) or value < 0:
                raise ValueError(f"{field} must be finite and non-negative.")
        _optional_limit(self.max_contents_weight_kg, "max_contents_weight_kg")
        _optional_limit(self.max_contents_volume_liters, "max_contents_volume_liters")
        if self.max_slots is not None and (isinstance(self.max_slots, bool) or not isinstance(self.max_slots, int) or self.max_slots < 0):
            raise ValueError("max_slots must be a non-negative integer or None.")
        if not isinstance(self.nesting_enabled, bool):
            raise TypeError("nesting_enabled must be boolean.")
        if isinstance(self.max_nesting_depth, bool) or not isinstance(self.max_nesting_depth, int) or self.max_nesting_depth < 0:
            raise ValueError("max_nesting_depth must be a non-negative integer.")
        if not self.nesting_enabled:
            object.__setattr__(self, "max_nesting_depth", 0)
        for field in ("allowed_item_tags", "denied_item_tags", "allowed_resource_tags", "denied_resource_tags", "allowed_container_tags", "denied_container_tags", "container_tags"):
            object.__setattr__(self, field, _tags(getattr(self, field), field))
        for allowed, denied in (("allowed_item_tags", "denied_item_tags"), ("allowed_resource_tags", "denied_resource_tags"), ("allowed_container_tags", "denied_container_tags")):
            if set(getattr(self, allowed)) & set(getattr(self, denied)):
                raise ValueError(f"A tag cannot be both {allowed} and {denied}.")
        if self.break_profile_id is not None and (not isinstance(self.break_profile_id, str) or not self.break_profile_id.strip()):
            raise ValueError("break_profile_id must be a non-empty string or None.")
