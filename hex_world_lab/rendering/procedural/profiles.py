"""Deterministic Surface builders backed by editable vector profile documents."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

import pygame

from .._procedural_environment_legacy import DEFAULT_PALETTE, EnvironmentArtPalette
from .cache import ProceduralSurfaceCache
from .document_profiles import build_profile_document
from .document_renderer import render_visual_document
from .variation import normalize_seed


@dataclass(frozen=True, slots=True)
class ProceduralProfile:
    """Visual metadata for one generated environmental profile."""

    key: str
    logical_size: tuple[int, int]
    anchor: tuple[float, float]

    def __post_init__(self) -> None:
        if not self.key or not isinstance(self.key, str):
            raise ValueError("profile key must be a non-empty string")
        if (
            not isinstance(self.logical_size, tuple)
            or len(self.logical_size) != 2
            or any(
                isinstance(value, bool) or not isinstance(value, int) or value <= 0
                for value in self.logical_size
            )
        ):
            raise ValueError("logical_size must contain two positive integers")
        if (
            not isinstance(self.anchor, tuple)
            or len(self.anchor) != 2
            or any(
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not 0.0 <= value <= 1.0
                for value in self.anchor
            )
        ):
            raise ValueError("anchor values must be between 0 and 1")


PROFILE_DEFINITIONS: Mapping[str, ProceduralProfile] = MappingProxyType(
    {
        "tree": ProceduralProfile("tree", (132, 168), (0.50, 0.94)),
        "rock": ProceduralProfile("rock", (66, 48), (0.50, 0.92)),
        "bush": ProceduralProfile("bush", (88, 58), (0.50, 0.92)),
        "grass": ProceduralProfile("grass", (64, 36), (0.50, 0.94)),
        "flower": ProceduralProfile("flower", (56, 48), (0.50, 0.94)),
    }
)


def build_environment_profile(
    profile_key: str,
    palette=None,
    seed: int | str = 0,
    supersampling: int = 3,
    cache: ProceduralSurfaceCache | None = None,
) -> pygame.Surface:
    """Build one profile, optionally reusing a bounded cached Surface."""
    if profile_key not in PROFILE_DEFINITIONS:
        raise KeyError(f"unknown procedural profile: {profile_key}")
    normalized_seed = normalize_seed(seed)
    if isinstance(supersampling, bool) or not isinstance(supersampling, int):
        raise TypeError("supersampling must be an integer")
    if supersampling <= 0:
        raise ValueError("supersampling must be positive")
    if cache is not None and not isinstance(cache, ProceduralSurfaceCache):
        raise TypeError("cache must be a ProceduralSurfaceCache or None")

    selected_palette = DEFAULT_PALETTE if palette is None else palette
    if not isinstance(selected_palette, EnvironmentArtPalette):
        raise TypeError("palette must be an EnvironmentArtPalette")

    profile_seed = normalized_seed if profile_key in ("grass", "flower") else 0

    def factory() -> pygame.Surface:
        document = build_profile_document(profile_key, seed=profile_seed, palette=selected_palette)
        scale = 3 if profile_key in ("tree", "rock", "bush") else supersampling
        return render_visual_document(document, supersampling=scale)

    key = (profile_key, "profile-v1", selected_palette, profile_seed, supersampling)
    return factory() if cache is None else cache.get_or_create(key, factory)


def build_environment_profiles(
    palette=None,
    seed: int | str = 0,
    supersampling: int = 3,
    cache: ProceduralSurfaceCache | None = None,
) -> dict[str, pygame.Surface]:
    """Build all five profiles, preserving Phase 12 legacy pixels."""
    normalized_seed = normalize_seed(seed)
    if isinstance(supersampling, bool) or not isinstance(supersampling, int):
        raise TypeError("supersampling must be an integer")
    if supersampling <= 0:
        raise ValueError("supersampling must be positive")
    return {
        key: build_environment_profile(key, palette, normalized_seed, supersampling, cache)
        for key in PROFILE_DEFINITIONS
    }
