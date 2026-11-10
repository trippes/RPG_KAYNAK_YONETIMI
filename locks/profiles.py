"""Immutable, data-driven lockpicking and forced-opening profiles."""
from dataclasses import dataclass


def _identifier(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string.")


def _tags(values, name):
    result = tuple(values)
    if any(not isinstance(value, str) or not value.strip() for value in result):
        raise ValueError(f"{name} must contain non-empty strings.")
    if len(result) != len(set(result)):
        raise ValueError(f"{name} must not contain duplicates.")
    return tuple(sorted(result))


@dataclass(frozen=True)
class LockpickProfile:
    profile_id: str
    allowed_tool_tags: tuple[str, ...] = ()
    require_skill: bool = True
    require_tool: bool = False
    minimum_skill: int = 0

    def __post_init__(self):
        _identifier(self.profile_id, "profile_id")
        object.__setattr__(self, "allowed_tool_tags", _tags(self.allowed_tool_tags, "allowed_tool_tags"))
        if not isinstance(self.require_skill, bool) or not isinstance(self.require_tool, bool):
            raise TypeError("require_skill and require_tool must be boolean.")
        if not self.require_skill and not self.require_tool:
            raise ValueError("A lockpick profile must require skill, a tool, or both.")
        if self.require_tool and not self.allowed_tool_tags:
            raise ValueError("A tool-required profile must define allowed_tool_tags.")
        if isinstance(self.minimum_skill, bool) or not isinstance(self.minimum_skill, int) or self.minimum_skill < 0:
            raise ValueError("minimum_skill must be a non-negative integer.")


@dataclass(frozen=True)
class ForceProfile:
    profile_id: str
    allowed: bool = True
    minimum_strength: int = 0
    required_tool_tags: tuple[str, ...] = ()
    success_effect: str = "unlock"

    def __post_init__(self):
        _identifier(self.profile_id, "profile_id")
        if not isinstance(self.allowed, bool):
            raise TypeError("allowed must be boolean.")
        if isinstance(self.minimum_strength, bool) or not isinstance(self.minimum_strength, int) or self.minimum_strength < 0:
            raise ValueError("minimum_strength must be a non-negative integer.")
        object.__setattr__(self, "required_tool_tags", _tags(self.required_tool_tags, "required_tool_tags"))
        if self.success_effect not in {"unlock", "break"}:
            raise ValueError("success_effect must be 'unlock' or 'break'.")
