import pygame
import pytest
from hex_world_lab.rendering.procedural.cache import ProceduralSurfaceCache


def _surface(size=(8, 8)):
    return pygame.Surface(size, pygame.SRCALPHA, 32)


def test_cache_reuses_surface_and_tracks_hits_and_misses():
    cache = ProceduralSurfaceCache(max_entries=4, max_bytes=4096)
    calls = []
    def factory():
        calls.append(True)
        return _surface()

    first = cache.get_or_create(("tree", 1), factory)
    second = cache.get_or_create(("tree", 1), factory)
    assert first is second
    assert len(calls) == 1
    assert cache.stats().hits == 1
    assert cache.stats().misses == 1
    assert cache.stats().entries == 1


def test_cache_evicts_least_recently_used_entry_when_entry_limit_is_reached():
    cache = ProceduralSurfaceCache(max_entries=2, max_bytes=4096)
    cache.get_or_create("a", _surface)
    cache.get_or_create("b", _surface)
    cache.get_or_create("a", _surface)
    cache.get_or_create("c", _surface)
    assert cache.stats().evictions == 1
    assert cache.get_or_create("a", lambda: pytest.fail("a should remain cached"))


def test_cache_obeys_byte_limit_and_skips_oversized_surfaces():
    cache = ProceduralSurfaceCache(max_entries=10, max_bytes=256)
    large = cache.get_or_create("large", lambda: _surface((20, 20)))
    assert large.get_size() == (20, 20)
    assert cache.stats().entries == 0
    assert cache.stats().estimated_bytes == 0


def test_cache_clear_resets_entries_and_counters():
    cache = ProceduralSurfaceCache()
    cache.get_or_create("a", _surface)
    cache.get_or_create("a", _surface)
    cache.clear()
    assert cache.stats().hits == 0
    assert cache.stats().misses == 0
    assert cache.stats().entries == 0


@pytest.mark.parametrize("limit", [0, -1, True, 1.5])
def test_cache_rejects_invalid_limits(limit):
    with pytest.raises((TypeError, ValueError)):
        ProceduralSurfaceCache(max_entries=limit)


def test_cache_rejects_invalid_key_and_factory_result():
    cache = ProceduralSurfaceCache()
    with pytest.raises(TypeError):
        cache.get_or_create([], _surface)
    with pytest.raises(TypeError):
        cache.get_or_create("bad", lambda: object())
