"""Unit tests for the Pygame keyboard movement adapter."""

import pygame
import pytest

from hex_world_lab.input import PygameKeyboardAdapter
from hex_world_lab.movement import MovementIntent, MovementMode, Vector2


class FakeKeys:
    def __init__(self, pressed=()):
        self.pressed = set(pressed)

    def __getitem__(self, key):
        return key in self.pressed


@pytest.mark.parametrize(
    ("key", "expected"),
    [
        (pygame.K_w, Vector2(0.0, 1.0)),
        (pygame.K_UP, Vector2(0.0, 1.0)),
        (pygame.K_s, Vector2(0.0, -1.0)),
        (pygame.K_DOWN, Vector2(0.0, -1.0)),
        (pygame.K_a, Vector2(-1.0, 0.0)),
        (pygame.K_LEFT, Vector2(-1.0, 0.0)),
        (pygame.K_d, Vector2(1.0, 0.0)),
        (pygame.K_RIGHT, Vector2(1.0, 0.0)),
    ],
)
def test_single_key_maps_to_mathematical_world_direction(key, expected):
    adapter = PygameKeyboardAdapter(lambda: FakeKeys({key}))
    assert adapter.read_intent() == MovementIntent(expected)


@pytest.mark.parametrize(
    ("keys", "expected"),
    [
        ({pygame.K_w, pygame.K_d}, Vector2(1.0, 1.0)),
        ({pygame.K_w, pygame.K_a}, Vector2(-1.0, 1.0)),
        ({pygame.K_s, pygame.K_d}, Vector2(1.0, -1.0)),
        ({pygame.K_s, pygame.K_a}, Vector2(-1.0, -1.0)),
        ({pygame.K_w, pygame.K_UP}, Vector2(0.0, 1.0)),
        ({pygame.K_d, pygame.K_RIGHT}, Vector2(1.0, 0.0)),
        ({pygame.K_w, pygame.K_s}, Vector2(0.0, 0.0)),
        ({pygame.K_a, pygame.K_d}, Vector2(0.0, 0.0)),
        ({pygame.K_w, pygame.K_s, pygame.K_d}, Vector2(1.0, 0.0)),
        (set(), Vector2(0.0, 0.0)),
    ],
)
def test_key_combinations_produce_expected_raw_intent(keys, expected):
    adapter = PygameKeyboardAdapter(lambda: FakeKeys(keys))
    assert adapter.read_intent() == MovementIntent(expected)


def test_provider_is_sampled_again_for_every_read():
    snapshots = iter(
        [
            FakeKeys({pygame.K_d}),
            FakeKeys(),
            FakeKeys({pygame.K_w}),
        ]
    )
    calls = []

    def provider():
        calls.append(True)
        return next(snapshots)

    adapter = PygameKeyboardAdapter(provider)
    assert adapter.read_intent().direction == Vector2(1.0, 0.0)
    assert adapter.read_intent().direction == Vector2(0.0, 0.0)
    assert adapter.read_intent().direction == Vector2(0.0, 1.0)
    assert len(calls) == 3


def test_invalid_provider_is_rejected():
    with pytest.raises(TypeError, match="callable"):
        PygameKeyboardAdapter(key_state_provider=object())


def test_incomplete_provider_snapshot_fails_loudly():
    adapter = PygameKeyboardAdapter(lambda: {})
    with pytest.raises(KeyError):
        adapter.read_intent()


def test_focus_loss_returns_neutral_intent_without_sampling_provider():
    calls = []
    adapter = PygameKeyboardAdapter(lambda: calls.append(True) or FakeKeys({pygame.K_d}))
    assert adapter.focused is True

    adapter.handle_event(pygame.event.Event(pygame.WINDOWFOCUSLOST))
    assert adapter.focused is False
    assert adapter.read_intent() == MovementIntent()
    assert calls == []


def test_focus_gain_resumes_sampling_current_keyboard_state():
    adapter = PygameKeyboardAdapter(lambda: FakeKeys({pygame.K_LEFT}))
    adapter.handle_event(pygame.event.Event(pygame.WINDOWFOCUSLOST))
    assert adapter.read_intent() == MovementIntent()

    adapter.handle_event(pygame.event.Event(pygame.WINDOWFOCUSGAINED))
    assert adapter.focused is True
    assert adapter.read_intent().direction == Vector2(-1.0, 0.0)


def test_unknown_events_do_not_change_focus_state():
    adapter = PygameKeyboardAdapter(lambda: FakeKeys())
    adapter.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_w))
    assert adapter.focused is True


def test_alt_toggles_stealth_on_and_off_after_release():
    keys = FakeKeys()
    adapter = PygameKeyboardAdapter(lambda: keys)

    assert adapter.read_intent().mode is MovementMode.NORMAL
    keys.pressed = {pygame.K_LALT}
    assert adapter.read_intent().mode is MovementMode.STEALTH
    assert adapter.read_intent().mode is MovementMode.STEALTH
    keys.pressed.clear()
    assert adapter.read_intent().mode is MovementMode.STEALTH
    keys.pressed = {pygame.K_LALT}
    assert adapter.read_intent().mode is MovementMode.NORMAL


def test_holding_alt_does_not_retrigger_toggle():
    keys = FakeKeys({pygame.K_LALT})
    adapter = PygameKeyboardAdapter(lambda: keys)

    modes = [adapter.read_intent().mode for _ in range(8)]
    assert modes == [MovementMode.STEALTH] * 8


def test_left_and_right_alt_together_are_one_toggle_press():
    keys = FakeKeys({pygame.K_LALT, pygame.K_RALT})
    adapter = PygameKeyboardAdapter(lambda: keys)

    assert adapter.read_intent().mode is MovementMode.STEALTH
    assert adapter.read_intent().mode is MovementMode.STEALTH
    keys.pressed = {pygame.K_RALT}
    assert adapter.read_intent().mode is MovementMode.STEALTH
    keys.pressed.clear()
    adapter.read_intent()
    keys.pressed = {pygame.K_LALT}
    assert adapter.read_intent().mode is MovementMode.NORMAL


def test_shift_is_hold_to_run_and_stealth_has_priority():
    keys = FakeKeys()
    adapter = PygameKeyboardAdapter(lambda: keys)

    keys.pressed = {pygame.K_LSHIFT}
    assert adapter.read_intent().mode is MovementMode.RUNNING
    keys.pressed.clear()
    assert adapter.read_intent().mode is MovementMode.NORMAL

    keys.pressed = {pygame.K_LALT}
    assert adapter.read_intent().mode is MovementMode.STEALTH
    keys.pressed = {pygame.K_LALT, pygame.K_LSHIFT}
    assert adapter.read_intent().mode is MovementMode.STEALTH

    keys.pressed = {pygame.K_LSHIFT}
    assert adapter.read_intent().mode is MovementMode.STEALTH
    keys.pressed = {pygame.K_LSHIFT, pygame.K_LALT}
    assert adapter.read_intent().mode is MovementMode.RUNNING


def test_focus_loss_resets_stealth_and_requires_alt_release_after_regain():
    keys = FakeKeys({pygame.K_LALT})
    adapter = PygameKeyboardAdapter(lambda: keys)
    assert adapter.read_intent().mode is MovementMode.STEALTH

    adapter.handle_event(pygame.event.Event(pygame.WINDOWFOCUSLOST))
    assert adapter.read_intent().mode is MovementMode.NORMAL
    adapter.handle_event(pygame.event.Event(pygame.WINDOWFOCUSGAINED))

    # Alt is still physically held: it must not be interpreted as a new press.
    assert adapter.read_intent().mode is MovementMode.NORMAL
    keys.pressed.clear()
    assert adapter.read_intent().mode is MovementMode.NORMAL
    keys.pressed = {pygame.K_LALT}
    assert adapter.read_intent().mode is MovementMode.STEALTH
