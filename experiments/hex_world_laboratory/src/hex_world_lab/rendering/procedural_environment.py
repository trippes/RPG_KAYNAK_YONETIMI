"""Backward-compatible facade for Phase 12 procedural environment art."""

from __future__ import annotations

import pygame

from ._procedural_environment_legacy import (
    DEFAULT_PALETTE,
    EnvironmentArtPalette,
)
from .procedural.profiles import build_environment_profile


def build_environment_surfaces(
    palette: EnvironmentArtPalette = DEFAULT_PALETTE,
) -> dict[str, pygame.Surface]:
    """Build the original tree, rock and bush profiles through the new API."""
    return {
        key: build_environment_profile(key, palette=palette)
        for key in ("tree", "rock", "bush")
    }


__all__ = ["DEFAULT_PALETTE", "EnvironmentArtPalette", "build_environment_surfaces"]
