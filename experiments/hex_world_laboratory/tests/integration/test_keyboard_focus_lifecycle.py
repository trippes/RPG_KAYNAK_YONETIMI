"""Focus lifecycle integration tests without a real display window."""

import pygame

from hex_world_lab.input import PygameKeyboardAdapter
from hex_world_lab.movement import MovementIntent, Vector2


class FakeKeys:
    def __init__(self, pressed=()):
        self.pressed = set(pressed)

    def __getitem__(self, key):
        return key in self.pressed


def test_focus_loss_and_gain_follow_event_lifecycle():
    keys = FakeKeys({pygame.K_d})
    adapter = PygameKeyboardAdapter(lambda: keys)

    assert adapter.read_intent().direction == Vector2(1.0, 0.0)

    adapter.handle_event(pygame.event.Event(pygame.WINDOWFOCUSLOST))
    assert adapter.read_intent() == MovementIntent()

    keys.pressed = {pygame.K_w}
    adapter.handle_event(pygame.event.Event(pygame.WINDOWFOCUSGAINED))
    assert adapter.read_intent().direction == Vector2(0.0, 1.0)


def test_repeated_focus_loss_and_gain_are_deterministic():
    adapter = PygameKeyboardAdapter(lambda: FakeKeys({pygame.K_s}))

    for _ in range(2):
        adapter.handle_event(pygame.event.Event(pygame.WINDOWFOCUSLOST))
        assert adapter.read_intent() == MovementIntent()
        adapter.handle_event(pygame.event.Event(pygame.WINDOWFOCUSGAINED))
        assert adapter.read_intent().direction == Vector2(0.0, -1.0)
