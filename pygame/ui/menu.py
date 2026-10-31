"""Keyboard-independent menu model."""
from .button import Button

class Menu:
    def __init__(self, buttons=()):
        self.buttons = list(buttons)
        self.selected = 0

    def move(self, delta: int) -> None:
        if self.buttons: self.selected = (self.selected + delta) % len(self.buttons)

    def confirm(self) -> str | None:
        return self.buttons[self.selected].activate() if self.buttons else None
