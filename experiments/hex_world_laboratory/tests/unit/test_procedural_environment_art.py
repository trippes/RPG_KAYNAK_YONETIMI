import pygame

from hex_world_lab.rendering.environment_assets import register_environment_assets
from hex_world_lab.rendering.procedural_environment import EnvironmentArtPalette, build_environment_surfaces
from hex_world_lab.rendering.pygame_world_renderer import PygameWorldRenderer


def _pixels(surface):
    return pygame.image.tostring(surface, "RGBA")


def test_environment_profiles_are_drawn_without_loading_any_raster_file(monkeypatch):
    def reject_file_load(*args, **kwargs):
        raise AssertionError("procedural environment art must not load raster files")

    monkeypatch.setattr(pygame.image, "load", reject_file_load)
    renderer = PygameWorldRenderer()
    sizes = register_environment_assets(renderer)

    assert sizes == {"tree": (132, 168), "rock": (66, 48), "bush": (88, 58)}
    assert set(renderer._sprite_assets) == {"tree", "rock", "bush"}
    assert all(isinstance(asset.surface, pygame.Surface) for asset in renderer._sprite_assets.values())


def test_procedural_environment_art_is_deterministic_and_transparent():
    first = build_environment_surfaces()
    second = build_environment_surfaces()

    assert set(first) == {"tree", "rock", "bush"}
    for key in first:
        assert first[key].get_size() == second[key].get_size()
        assert _pixels(first[key]) == _pixels(second[key])
        assert first[key].get_flags() & pygame.SRCALPHA
        mask = pygame.mask.from_surface(first[key])
        opaque_pixels = mask.count()
        assert opaque_pixels > first[key].get_width() * first[key].get_height() // 5
        assert opaque_pixels < first[key].get_width() * first[key].get_height()

    assert len({_pixels(surface) for surface in first.values()}) == 3


def test_tree_has_tall_visual_profile_and_rock_and_bush_remain_distinct():
    surfaces = build_environment_surfaces()
    tree = surfaces["tree"]
    rock = surfaces["rock"]
    bush = surfaces["bush"]

    assert tree.get_height() > tree.get_width()
    assert rock.get_width() > rock.get_height()
    assert bush.get_width() > bush.get_height()
    assert tree.get_height() >= 2 * rock.get_height()


def test_palette_is_validated_and_can_change_the_generated_art():
    baseline = build_environment_surfaces()
    autumn = EnvironmentArtPalette(
        tree_leaf_shadow=(105, 48, 24),
        tree_leaf_mid=(178, 83, 31),
        tree_leaf_light=(225, 151, 54),
        leaf_glint=(245, 205, 112),
        bush_base=(105, 48, 24),
        bush_light=(225, 151, 54),
    )
    changed = build_environment_surfaces(autumn)
    assert _pixels(changed["tree"]) != _pixels(baseline["tree"])
    assert _pixels(changed["bush"]) != _pixels(baseline["bush"])
    assert _pixels(changed["rock"]) == _pixels(baseline["rock"])

    import pytest
    with pytest.raises(ValueError):
        EnvironmentArtPalette(tree_leaf_mid=(256, 0, 0))
