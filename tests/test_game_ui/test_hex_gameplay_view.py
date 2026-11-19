from types import SimpleNamespace

from core.domain.spatial import HexDirection
from game_ui.input import InputState
from game_ui.world_rendering.hex_gameplay_view import HexGameplayView


class RecordingActorBinding:
    def __init__(self):
        self.moves = []

    def move(self, actor_id, direction):
        self.moves.append((actor_id, direction))
        return SimpleNamespace(success=True)


class FakeService:
    def __init__(self):
        self.hex_world_runtime = object()
        self.hex_actor_binding = RecordingActorBinding()
        self.player_actor_id = "hero"


def test_hex_gameplay_view_maps_six_keyboard_actions_to_axial_directions():
    service = FakeService()
    view = HexGameplayView(service)
    state = InputState(actions={
        "right", "left", "up", "down",
        "hex_north_west", "hex_south_west",
    })

    view.handle(state)

    assert service.hex_actor_binding.moves == [
        ("hero", HexDirection.EAST),
        ("hero", HexDirection.WEST),
        ("hero", HexDirection.NORTH_EAST),
        ("hero", HexDirection.SOUTH_EAST),
        ("hero", HexDirection.NORTH_WEST),
        ("hero", HexDirection.SOUTH_WEST),
    ]


def test_hex_gameplay_view_mouse_wheel_changes_only_presentation_zoom():
    service = FakeService()
    view = HexGameplayView(service)

    view.handle(InputState(mouse_wheel=2, mouse_pos=(100, 120)))

    assert view.zoom == 1.16
    assert view.mouse_position == (100, 120)
    assert service.hex_actor_binding.moves == []


def test_hex_gameplay_view_zoom_is_clamped():
    service = FakeService()
    view = HexGameplayView(service)

    view.handle(InputState(mouse_wheel=100))
    assert view.zoom == view.MAX_ZOOM

    view.handle(InputState(mouse_wheel=-1000))
    assert view.zoom == view.MIN_ZOOM


def test_hex_gameplay_view_does_not_issue_moves_without_runtime():
    service = FakeService()
    service.hex_world_runtime = None
    view = HexGameplayView(service)

    view.handle(InputState(actions={"right"}))

    assert service.hex_actor_binding.moves == []
