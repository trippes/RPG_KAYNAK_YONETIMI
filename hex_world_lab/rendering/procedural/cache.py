"""Bounded LRU cache for generated Pygame surfaces."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from typing import Callable, Hashable

import pygame


def _positive_limit(value: int, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if value <= 0:
        raise ValueError(f"{name} must be positive")
    return value


@dataclass(frozen=True, slots=True)
class CacheStats:
    hits: int
    misses: int
    evictions: int
    entries: int
    estimated_bytes: int


class ProceduralSurfaceCache:
    """LRU cache bounded by both entry count and estimated Surface bytes.

    Surfaces returned by the cache are shared objects and must be treated as
    read-only by callers after insertion.
    """

    def __init__(self, max_entries: int = 64, max_bytes: int = 32 * 1024 * 1024) -> None:
        self.max_entries = _positive_limit(max_entries, "max_entries")
        self.max_bytes = _positive_limit(max_bytes, "max_bytes")
        self._items: OrderedDict[Hashable, tuple[pygame.Surface, int]] = OrderedDict()
        self._estimated_bytes = 0
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def get_or_create(self, key: Hashable, factory: Callable[[], pygame.Surface]) -> pygame.Surface:
        try:
            hash(key)
        except TypeError as error:
            raise TypeError("cache key must be hashable") from error
        if not callable(factory):
            raise TypeError("factory must be callable")

        cached = self._items.get(key)
        if cached is not None:
            self._hits += 1
            self._items.move_to_end(key)
            return cached[0]

        self._misses += 1
        surface = factory()
        if not isinstance(surface, pygame.Surface):
            raise TypeError("factory must return a pygame.Surface")
        estimated_bytes = surface.get_pitch() * surface.get_height()
        if estimated_bytes > self.max_bytes:
            return surface

        while (
            len(self._items) >= self.max_entries
            or self._estimated_bytes + estimated_bytes > self.max_bytes
        ):
            _, (_, removed_bytes) = self._items.popitem(last=False)
            self._estimated_bytes -= removed_bytes
            self._evictions += 1

        self._items[key] = (surface, estimated_bytes)
        self._estimated_bytes += estimated_bytes
        return surface

    def clear(self) -> None:
        self._items.clear()
        self._estimated_bytes = 0
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def stats(self) -> CacheStats:
        return CacheStats(
            hits=self._hits,
            misses=self._misses,
            evictions=self._evictions,
            entries=len(self._items),
            estimated_bytes=self._estimated_bytes,
        )
