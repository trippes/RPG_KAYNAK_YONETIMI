"""Backend-independent panel descriptor."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Panel:
    x: int
    y: int
    width: int
    height: int

    @property
    def bounds(self) -> tuple[int, int, int, int]:
        return self.x, self.y, self.width, self.height
