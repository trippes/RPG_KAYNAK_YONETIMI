"""Sprite-sheet slicing helpers independent of a concrete asset file."""
from __future__ import annotations


class SpriteSheet:
    def __init__(self, surface, frame_width: int, frame_height: int):
        if frame_width <= 0 or frame_height <= 0:
            raise ValueError("Frame dimensions must be positive.")
        self.surface = surface
        self.frame_width = int(frame_width)
        self.frame_height = int(frame_height)
        self.columns = surface.get_width() // self.frame_width
        self.rows = surface.get_height() // self.frame_height
        if self.columns < 1 or self.rows < 1:
            raise ValueError("Sprite sheet is smaller than one frame.")
        self.frame_count = self.columns * self.rows

    def frame(self, index: int):
        if index < 0 or index >= self.frame_count:
            raise IndexError("Sprite frame index is outside the sheet.")
        x = (index % self.columns) * self.frame_width
        y = (index // self.columns) * self.frame_height
        return self.surface.subsurface((x, y, self.frame_width, self.frame_height)).copy()
