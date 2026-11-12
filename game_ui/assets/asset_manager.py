"""Shared, lazy-loading image asset cache for Pygame presentation."""
from __future__ import annotations

from pathlib import Path


class AssetManager:
    """Load each image once and reuse its converted surface."""

    def __init__(self, pygame_module):
        self._pygame = pygame_module
        self._images = {}

    def load_image(self, key: str, path: str | Path, *, alpha: bool = True):
        if key in self._images:
            return self._images[key]
        image = self._pygame.image.load(str(path))
        converter = getattr(image, "convert_alpha" if alpha else "convert", None)
        if converter is not None:
            image = converter()
        self._images[key] = image
        return image

    def get_image(self, key: str):
        return self._images.get(key)

    def clear(self) -> None:
        self._images.clear()

    @property
    def image_count(self) -> int:
        return len(self._images)
