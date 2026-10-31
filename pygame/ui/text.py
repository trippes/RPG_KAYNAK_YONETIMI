"""Backend-independent text descriptor."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Text:
    value: str
    x: int = 0
    y: int = 0
