"""Pygame keyboard adapter for Eldoria's device-independent movement intent."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from core.domain.movement import MovementIntent, MovementMode
from core.domain.physics import Vector2


class PygameMovementInput:
    """Translate held keyboard state into native movement intent.

    WASD and arrow keys control direction, Shift is hold-to-run, and Alt
    toggles stealth on a press edge. Focus loss clears all transient input.
    """

    __slots__ = (
        "_backend",
        "_key_state_provider",
        "_focused",
        "_alt_was_pressed",
        "_stealth_enabled",
        "_require_alt_release",
    )

    def __init__(
        self,
        backend: Any,
        key_state_provider: Callable[[], Any] | None = None,
    ) -> None:
        if backend is None:
            raise TypeError("backend is required")
        if key_state_provider is not None and not callable(key_state_provider):
            raise TypeError("key_state_provider must be callable")
        key_module = getattr(backend, "key", None)
        provider = key_state_provider or getattr(key_module, "get_pressed", None)
        if not callable(provider):
            raise TypeError("backend must provide key.get_pressed()")
        self._backend = backend
        self._key_state_provider = provider
        self._focused = True
        self._alt_was_pressed = False
        self._stealth_enabled = False
        self._require_alt_release = False

    @property
    def focused(self) -> bool:
        return self._focused

    def handle_events(self, events) -> None:
        focus_lost = getattr(self._backend, "WINDOWFOCUSLOST", object())
        focus_gained = getattr(self._backend, "WINDOWFOCUSGAINED", object())
        for event in events:
            event_type = getattr(event, "type", None)
            if event_type == focus_lost:
                self._focused = False
                self._alt_was_pressed = False
                self._stealth_enabled = False
                self._require_alt_release = True
            elif event_type == focus_gained:
                self._focused = True

    def read_intent(self) -> MovementIntent:
        if not self._focused:
            return MovementIntent()

        keys = self._key_state_provider()
        right = self._held(keys, "K_d", "K_RIGHT")
        left = self._held(keys, "K_a", "K_LEFT")
        up = self._held(keys, "K_w", "K_UP")
        down = self._held(keys, "K_s", "K_DOWN")
        alt_pressed = self._held(keys, "K_LALT", "K_RALT")
        shift_pressed = self._held(keys, "K_LSHIFT", "K_RSHIFT")

        if self._require_alt_release:
            if not alt_pressed:
                self._require_alt_release = False
        elif alt_pressed and not self._alt_was_pressed:
            self._stealth_enabled = not self._stealth_enabled
        self._alt_was_pressed = alt_pressed

        if self._stealth_enabled:
            mode = MovementMode.STEALTH
        elif shift_pressed:
            mode = MovementMode.RUNNING
        else:
            mode = MovementMode.NORMAL

        return MovementIntent(
            Vector2(
                float(int(right) - int(left)),
                float(int(down) - int(up)),
            ),
            mode,
        )

    def _held(self, keys, *constant_names: str) -> bool:
        for name in constant_names:
            key_code = getattr(self._backend, name, None)
            if key_code is not None and bool(keys[key_code]):
                return True
        return False


__all__ = ["PygameMovementInput"]
