"""Shared procedural graphics primitives."""

from .cache import CacheStats, ProceduralSurfaceCache
from .canvas import ProceduralCanvas
from .components import draw_circle, draw_ellipse, draw_polygon, draw_polyline
from .geometry import Bounds2D, Point2D, Transform2D
from .palette import ColorRamp, interpolate_rgb, validate_rgb
from .profiles import (
    PROFILE_DEFINITIONS,
    ProceduralProfile,
    build_environment_profile,
    build_environment_profiles,
)
from .variation import create_rng, normalize_seed
from .document_profiles import build_profile_document
from .document_renderer import render_content_definition, render_visual_document

__all__ = [
    "Bounds2D",
    "ColorRamp",
    "CacheStats",
    "PROFILE_DEFINITIONS",
    "Point2D",
    "ProceduralCanvas",
    "ProceduralProfile",
    "ProceduralSurfaceCache",
    "Transform2D",
    "build_environment_profile",
    "build_environment_profiles",
    "build_profile_document",
    "render_content_definition",
    "render_visual_document",
    "create_rng",
    "draw_circle",
    "draw_ellipse",
    "draw_polygon",
    "draw_polyline",
    "interpolate_rgb",
    "normalize_seed",
    "validate_rgb",
]
