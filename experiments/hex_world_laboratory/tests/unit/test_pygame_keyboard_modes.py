"""Modifier-key movement mode selection tests."""

import pygame
import pytest

from hex_world_lab.input import PygameKeyboardAdapter
from hex_world_lab.movement import MovementMode


class FakeKeys:
    def __init__(self, pressed=()):
        self.pressed = set(pressed)

    def __getitem__(self, key):
        return key in self.pressed


@pytest.mark.parametrize("key", [pygame.K_LSHIFT, pygame.K_RSHIFT])
def test_either_shift_selects_running(key):
    adapter = PygameKeyboardAdapter(lambda: FakeKeys({key}))
    assert adapter.read_intent().mode is MovementMode.RUNNING


@pytest.mark.parametrize("key", [pygame.K_LALT, pygame.K_RALT])
def test_either_alt_selects_stealth(key):
    adapter = PygameKeyboardAdapter(lambda: FakeKeys({key}))
    assert adapter.read_intent().mode is MovementMode.STEALTH


@pytest.mark.parametrize(
    "keys",
    [
        {pygame.K_LSHIFT, pygame.K_LALT},
        {pygame.K_LSHIFT, pygame.K_RALT},
        {pygame.K_RSHIFT, pygame.K_LALT},
        {pygame.K_RSHIFT, pygame.K_RALT},
    ],
)
def test_alt_has_priority_when_shift_and_alt_are_held(keys):
    adapter = PygameKeyboardAdapter(lambda: FakeKeys(keys))
    assert adapter.read_intent().mode is MovementMode.STEALTH


def test_left_and_right_shift_do_not_stack():
    adapter = PygameKeyboardAdapter(
        lambda: FakeKeys({pygame.K_LSHIFT, pygame.K_RSHIFT})
    )
    assert adapter.read_intent().mode is MovementMode.RUNNING


def test_left_and_right_alt_do_not_stack():
    adapter = PygameKeyboardAdapter(
        lambda: FakeKeys({pygame.K_LALT, pygame.K_RALT})
    )
    assert adapter.read_intent().mode is MovementMode.STEALTH


def test_alt_toggle_stays_stealth_after_release_and_second_press_selects_running():
    keys = FakeKeys({pygame.K_LSHIFT, pygame.K_LALT})
    adapter = PygameKeyboardAdapter(lambda: keys)
    assert adapter.read_intent().mode is MovementMode.STEALTH

    keys.pressed.remove(pygame.K_LALT)
    assert adapter.read_intent().mode is MovementMode.STEALTH

    keys.pressed.add(pygame.K_LALT)
    assert adapter.read_intent().mode is MovementMode.RUNNING


def test_releasing_shift_while_alt_remains_selects_stealth():
    keys = FakeKeys({pygame.K_LSHIFT, pygame.K_LALT})
    adapter = PygameKeyboardAdapter(lambda: keys)
    assert adapter.read_intent().mode is MovementMode.STEALTH

    keys.pressed.remove(pygame.K_LSHIFT)
    assert adapter.read_intent().mode is MovementMode.STEALTH


def test_releasing_all_modifiers_keeps_stealth_until_alt_is_toggled_off():
    keys = FakeKeys({pygame.K_LSHIFT, pygame.K_LALT})
    adapter = PygameKeyboardAdapter(lambda: keys)
    assert adapter.read_intent().mode is MovementMode.STEALTH

    keys.pressed.clear()
    assert adapter.read_intent().mode is MovementMode.STEALTH

    keys.pressed.add(pygame.K_LALT)
    assert adapter.read_intent().mode is MovementMode.NORMAL


def test_modifier_mode_is_sampled_with_direction():
    adapter = PygameKeyboardAdapter(
        lambda: FakeKeys({pygame.K_w, pygame.K_d, pygame.K_RSHIFT})
    )
    intent = adapter.read_intent()
    assert intent.direction.x == 1.0
    assert intent.direction.y == 1.0
    assert intent.mode is MovementMode.RUNNING


def test_focus_loss_clears_direction_and_mode_without_sampling_provider():
    calls = []
    adapter = PygameKeyboardAdapter(
        lambda: calls.append(True)
        or FakeKeys({pygame.K_d, pygame.K_LALT, pygame.K_LSHIFT})
    )
    adapter.handle_event(pygame.event.Event(pygame.WINDOWFOCUSLOST))
    intent = adapter.read_intent()

    assert intent.direction.x == 0.0
    assert intent.direction.y == 0.0
    assert intent.mode is MovementMode.NORMAL
    assert calls == []


def test_focus_gain_requires_alt_release_then_a_fresh_press():
    keys = FakeKeys({pygame.K_RALT})
    adapter = PygameKeyboardAdapter(lambda: keys)
    adapter.handle_event(pygame.event.Event(pygame.WINDOWFOCUSLOST))
    assert adapter.read_intent().mode is MovementMode.NORMAL

    adapter.handle_event(pygame.event.Event(pygame.WINDOWFOCUSGAINED))
    assert adapter.read_intent().mode is MovementMode.NORMAL

    keys.pressed.clear()
    assert adapter.read_intent().mode is MovementMode.NORMAL
    keys.pressed.add(pygame.K_RALT)
    assert adapter.read_intent().mode is MovementMode.STEALTH
