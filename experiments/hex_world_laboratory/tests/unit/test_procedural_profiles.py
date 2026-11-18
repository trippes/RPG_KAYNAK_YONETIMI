import pygame
import pytest

from hex_world_lab.rendering.procedural.profiles import (
    PROFILE_DEFINITIONS,
    ProceduralProfile,
    build_environment_profiles,
)
from hex_world_lab.rendering.procedural_environment import build_environment_surfaces


def _pixels(surface):
    return pygame.image.tostring(surface, "RGBA")


def test_five_profile_definitions_have_expected_sizes_and_anchors():
    assert set(PROFILE_DEFINITIONS) == {"tree", "rock", "bush", "grass", "flower"}
    assert PROFILE_DEFINITIONS["tree"].logical_size == (132, 168)
    assert PROFILE_DEFINITIONS["grass"].anchor == (0.5, 0.94)
    with pytest.raises(TypeError):
        PROFILE_DEFINITIONS["tree"] = ProceduralProfile("bad", (1, 1), (0.5, 0.5))


def test_profile_builder_preserves_legacy_three_visuals_exactly():
    legacy = build_environment_surfaces()
    profiles = build_environment_profiles()
    for key in ("tree", "rock", "bush"):
        assert _pixels(profiles[key]) == _pixels(legacy[key])


def test_new_profiles_are_distinct_and_deterministic_for_same_seed():
    first = build_environment_profiles(seed=42)
    second = build_environment_profiles(seed=42)
    assert set(first) == {"tree", "rock", "bush", "grass", "flower"}
    for key in first:
        assert _pixels(first[key]) == _pixels(second[key])
    assert _pixels(first["grass"]) != _pixels(first["flower"])


def test_new_profiles_change_with_seed_without_changing_legacy_art():
    first = build_environment_profiles(seed=1)
    second = build_environment_profiles(seed=2)
    assert _pixels(first["grass"]) != _pixels(second["grass"])
    assert _pixels(first["flower"]) != _pixels(second["flower"])
    for key in ("tree", "rock", "bush"):
        assert _pixels(first[key]) == _pixels(second[key])


def test_all_profiles_are_alpha_surfaces_with_positive_coverage():
    profiles = build_environment_profiles(seed=5)
    for surface in profiles.values():
        assert surface.get_flags() & pygame.SRCALPHA
        assert pygame.mask.from_surface(surface).count() > 0


def test_profile_builder_rejects_invalid_seed_and_supersampling():
    with pytest.raises(TypeError):
        build_environment_profiles(seed="not-an-integer")
    with pytest.raises(ValueError):
        build_environment_profiles(supersampling=0)
