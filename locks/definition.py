"""Immutable content definitions for locks and keys."""
from dataclasses import dataclass


def _identifier(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string.")


@dataclass(frozen=True)
class LockDefinition:
    definition_id: str
    name: str
    required_key_id: str | None = None
    lockpick_profile_id: str | None = None
    force_profile_id: str | None = None
    tags: tuple[str, ...] = ()

    def __post_init__(self):
        _identifier(self.definition_id, "definition_id")
        _identifier(self.name, "name")
        for field in ("required_key_id", "lockpick_profile_id", "force_profile_id"):
            value = getattr(self, field)
            if value is not None:
                _identifier(value, field)
        tags = tuple(self.tags)
        if any(not isinstance(tag, str) or not tag.strip() for tag in tags):
            raise ValueError("tags must contain non-empty strings.")
        if len(tags) != len(set(tags)):
            raise ValueError("tags must not contain duplicates.")
        object.__setattr__(self, "tags", tuple(sorted(tags)))


@dataclass(frozen=True)
class KeyDefinition:
    key_id: str
    name: str
    lock_definition_id: str
    owner_bound: bool = False

    def __post_init__(self):
        _identifier(self.key_id, "key_id")
        _identifier(self.name, "name")
        _identifier(self.lock_definition_id, "lock_definition_id")
        if not isinstance(self.owner_bound, bool):
            raise TypeError("owner_bound must be boolean.")
