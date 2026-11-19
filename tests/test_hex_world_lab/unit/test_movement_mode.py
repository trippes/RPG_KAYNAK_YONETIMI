import pytest

from hex_world_lab.movement import MovementMode


@pytest.mark.parametrize(
    ("mode", "value"),
    [
        (MovementMode.NORMAL, "normal"),
        (MovementMode.RUNNING, "running"),
        (MovementMode.STEALTH, "stealth"),
    ],
)
def test_movement_mode_values_are_stable(mode, value):
    assert mode.value == value


def test_movement_modes_are_distinct():
    assert len(set(MovementMode)) == 3
