"""Pygame keyboard state adapter for device-independent movement intents."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pygame

from hex_world_lab.movement import MovementIntent, Vector2


class PygameKeyboardAdapter:
    """Translate the current Pygame keyboard snapshot into a MovementIntent."""

    __slots__ = ("_key_state_provider", "_focused")

    def __init__(
        self,
        key_state_provider: Callable[[], Any] | None = None,
    ) -> None:
        if key_state_provider is not None and not callable(key_state_provider):
            raise TypeError("key_state_provider must be callable")
        self._key_state_provider = key_state_provider or pygame.key.get_pressed
        self._focused = True

    @property
    def focused(self) -> bool:
        """Whether the application window currently owns keyboard focus."""
        return self._focused

    def handle_event(self, event: pygame.event.Event) -> None:
        """Update focus state from Pygame window-focus events."""
        event_type = getattr(event, "type", None)
        if event_type == pygame.WINDOWFOCUSLOST:
            self._focused = False
        elif event_type == pygame.WINDOWFOCUSGAINED:
            self._focused = True

    def read_intent(self) -> MovementIntent:
        """Read the latest keyboard state and return a normalized-axis intent.

        The returned vector is intentionally not length-normalized; diagonal
        normalization belongs to the movement integrator.
        """
        if not self._focused:
            return MovementIntent()

        keys = self._key_state_provider()

        right = bool(keys[pygame.K_d]) or bool(keys[pygame.K_RIGHT])
        left = bool(keys[pygame.K_a]) or bool(keys[pygame.K_LEFT])
        up = bool(keys[pygame.K_w]) or bool(keys[pygame.K_UP])
        down = bool(keys[pygame.K_s]) or bool(keys[pygame.K_DOWN])

        return MovementIntent(
            Vector2(
                x=float(int(right) - int(left)),
                y=float(int(up) - int(down)),
            )
        )
