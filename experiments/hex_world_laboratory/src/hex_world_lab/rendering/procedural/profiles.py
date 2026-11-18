"""Deterministic builders and visual metadata for environmental object profiles."""

from __future__ import annotations

import math
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

import pygame

from .cache import ProceduralSurfaceCache
from .canvas import ProceduralCanvas
from .components import draw_circle, draw_ellipse, draw_polygon, draw_polyline
from .geometry import Point2D
from .variation import create_rng, normalize_seed


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


def _build_grass(seed: int, supersampling: int, palette) -> pygame.Surface:
    rng = create_rng(f"grass:{seed}")
    canvas = ProceduralCanvas((64, 36), supersampling)
    draw_ellipse(canvas, palette.ground_shadow, (7, 27, 50, 8))
    base = palette.tree_leaf_shadow
    mid = palette.tree_leaf_mid
    light = palette.tree_leaf_light
    for _ in range(17):
        x = rng.uniform(5, 59)
        height = rng.uniform(9, 24)
        lean = rng.uniform(-5, 5)
        blade_width = rng.uniform(1.0, 2.8)
        root = Point2D(x, 31)
        tip = Point2D(x + lean, 31 - height)
        left = Point2D(x - blade_width, 31 - height * 0.42)
        right = Point2D(x + blade_width, 31 - height * 0.42)
        color = rng.choice((base, mid, light))
        draw_polygon(canvas, color, (root, left, tip, right))
    return canvas.finish()


def _build_flower(seed: int, supersampling: int, palette) -> pygame.Surface:
    rng = create_rng(f"flower:{seed}")
    canvas = ProceduralCanvas((56, 48), supersampling)
    draw_ellipse(canvas, palette.ground_shadow, (5, 38, 46, 8))
    stem_color = (55, 112, 59)
    leaf_color = palette.tree_leaf_mid
    flower_colors = ((225, 125, 115), (238, 190, 90), (178, 145, 218))
    for index, x in enumerate((14.0, 28.0, 42.0)):
        height = rng.uniform(20, 29)
        top = Point2D(x + rng.uniform(-2, 2), 39 - height)
        root = Point2D(x, 41)
        bend = Point2D((x + top.x) / 2 + rng.uniform(-2, 2), 28)
        draw_polyline(canvas, stem_color, (root, bend, top), width=1)
        leaf_y = rng.uniform(29, 34)
        draw_ellipse(
            canvas,
            leaf_color,
            (x - 7 if index % 2 == 0 else x + 1, leaf_y, 7, 3),
        )
        color = flower_colors[index]
        petal_count = 5
        for petal in range(petal_count):
            angle = petal * 6.283185307179586 / petal_count
            center = Point2D(
                top.x + 3.2 * math.cos(angle),
                top.y + 3.2 * math.sin(angle),
            )
            draw_circle(canvas, color, center, 2.2)
        draw_circle(canvas, (245, 215, 105), top, 1.5)
    return canvas.finish()


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

    from .._procedural_environment_legacy import (
        DEFAULT_PALETTE,
        EnvironmentArtPalette,
        _bush,
        _rock,
        _tree,
    )

    selected_palette = DEFAULT_PALETTE if palette is None else palette
    if not isinstance(selected_palette, EnvironmentArtPalette):
        raise TypeError("palette must be an EnvironmentArtPalette")

    def factory() -> pygame.Surface:
        if profile_key == "tree":
            return _tree(selected_palette)
        if profile_key == "rock":
            return _rock(selected_palette)
        if profile_key == "bush":
            return _bush(selected_palette)
        if profile_key == "grass":
            return _build_grass(normalized_seed, supersampling, selected_palette)
        return _build_flower(normalized_seed, supersampling, selected_palette)

    profile_seed = normalized_seed if profile_key in ("grass", "flower") else 0
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
