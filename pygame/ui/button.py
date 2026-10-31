"""Backend-independent button value object."""
from dataclasses import dataclass

@dataclass
class Button:
    label: str
    action: str
    enabled: bool = True

    def activate(self) -> str | None:
        return self.action if self.enabled else None
