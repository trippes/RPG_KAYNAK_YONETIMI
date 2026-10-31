"""World locations used by the application-level movement model."""

from dataclasses import dataclass

@dataclass(frozen=True)
class Location:
    """A named node in a world's movement graph."""

    location_id: str
    name: str
    position: object | None = None
    description: str = ""
    location_type: str = "unknown"
    activities: tuple[str, ...] = ()
    landmarks: tuple = ()

    def __post_init__(self) -> None:
        if not isinstance(self.location_id, str) or not self.location_id.strip():
            raise ValueError("location_id must be a non-empty string.")
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("name must be a non-empty string.")
        if not isinstance(self.description, str):
            raise TypeError("description must be a string.")
        if not isinstance(self.location_type, str) or not self.location_type.strip():
            raise ValueError("location_type must be a non-empty string.")
        if not isinstance(self.activities, tuple) or any(not isinstance(item, str) or not item.strip() for item in self.activities):
            raise TypeError("activities must be a tuple of non-empty strings.")
        if not isinstance(self.landmarks, tuple):
            raise TypeError("landmarks must be a tuple.")
