from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class Identifier:
    """Stable, immutable and serializable identifier value object."""

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise TypeError("Identifier value must be a string.")
        if not self.value.strip():
            raise ValueError("Identifier value cannot be empty.")

    def __str__(self) -> str:
        return self.value

    def to_dict(self) -> dict[str, str]:
        return {"value": self.value}

    def to_persistence(self) -> str:
        """Canonical persistence representation: stable primitive string."""
        return self.value

    @classmethod
    def from_persistence(cls, value: str):
        return cls(value)


@dataclass(frozen=True, order=True)
class EntityId(Identifier):
    """Canonical identifier for an entity."""


@dataclass(frozen=True, order=True)
class WorldId(Identifier):
    """Canonical identifier for a world."""


@dataclass(frozen=True, order=True)
class EventId(Identifier):
    """Canonical identifier for an event."""


@dataclass(frozen=True, order=True)
class ActionId(Identifier):
    """Canonical identifier for an action."""
