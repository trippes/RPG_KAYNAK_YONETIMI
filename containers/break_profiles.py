"""Data-driven physical break profiles for containers."""
from dataclasses import dataclass
from math import isfinite
from types import MappingProxyType
from collections.abc import Mapping


@dataclass(frozen=True)
class BreakProfile:
    profile_id: str
    max_durability: float
    damage_resistances: Mapping[str, float] | None = None
    breakable: bool = True

    def __post_init__(self):
        if not isinstance(self.profile_id, str) or not self.profile_id.strip():
            raise ValueError("profile_id must be a non-empty string.")
        if isinstance(self.max_durability, bool) or not isinstance(self.max_durability, (int, float)) or not isfinite(self.max_durability) or self.max_durability < 0:
            raise ValueError("max_durability must be finite and non-negative.")
        values = dict(self.damage_resistances or {})
        for kind, resistance in values.items():
            if not isinstance(kind, str) or not kind.strip():
                raise ValueError("Damage type keys must be non-empty strings.")
            if isinstance(resistance, bool) or not isinstance(resistance, (int, float)) or not isfinite(resistance) or not 0 <= resistance <= 1:
                raise ValueError("Damage resistance must be between 0 and 1.")
        if not isinstance(self.breakable, bool):
            raise TypeError("breakable must be boolean.")
        object.__setattr__(self, "damage_resistances", MappingProxyType(values))


class BreakProfileRegistry:
    def __init__(self, profiles=()):
        self._profiles = {}
        for profile in profiles:
            self.register(profile)

    def register(self, profile: BreakProfile):
        if not isinstance(profile, BreakProfile):
            raise TypeError("profile must be BreakProfile.")
        if profile.profile_id in self._profiles:
            raise ValueError(f"Duplicate break profile: {profile.profile_id}")
        self._profiles[profile.profile_id] = profile
        return profile

    def get(self, profile_id):
        return self._profiles.get(profile_id)

    def profiles(self):
        return tuple(self._profiles[key] for key in sorted(self._profiles))
