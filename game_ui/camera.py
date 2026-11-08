"""Small deterministic 2D camera helper."""
from dataclasses import dataclass

@dataclass
class Camera:
    x: int = 0
    y: int = 0

    def move_to(self, x: int, y: int) -> None:
        self.x, self.y = x, y

    def world_to_screen(self, x: int, y: int) -> tuple[int, int]:
        return x - self.x, y - self.y
