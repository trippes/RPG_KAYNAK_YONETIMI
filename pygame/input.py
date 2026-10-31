
"""Input mapping for the playable slice."""

from dataclasses import dataclass, field


@dataclass
class InputState:
    """Frame input translated into stable, backend-independent actions."""

    actions: set[str] = field(default_factory=set)
    text: str = ""
    quit_requested: bool = False
    mouse_pos: tuple[int, int] | None = None
    mouse_clicked: bool = False

    def pressed(self, action: str) -> bool:
        return action in self.actions


class InputMapper:
    """Translate keyboard/window events into gameplay actions."""

    def __init__(self, backend=None) -> None:
        self.backend = backend

    def collect(self, events) -> InputState:
        state = InputState()

        for event in events:
            event_type = getattr(event, "type", None)
            quit_type = getattr(self.backend, "QUIT", "QUIT")
            keydown_type = getattr(self.backend, "KEYDOWN", "KEYDOWN")
            mouse_down_type = getattr(self.backend, "MOUSEBUTTONDOWN", "MOUSEBUTTONDOWN")
            mouse_motion_type = getattr(self.backend, "MOUSEMOTION", "MOUSEMOTION")

            if event_type == quit_type or event_type == "QUIT":
                state.quit_requested = True
                continue

            if event_type == mouse_down_type and getattr(event, "button", None) == 1:
                state.mouse_clicked = True
                state.mouse_pos = getattr(event, "pos", None)
                continue

            if event_type == mouse_motion_type:
                state.mouse_pos = getattr(event, "pos", None)
                continue

            if event_type != keydown_type and event_type != "KEYDOWN":
                continue

            key = self._key_name(getattr(event, "key", None))

            actions = {
                "escape": "back",
                "return": "confirm",
                "space": "wait",
                "g": "gather",
                "c": "craft",
                "i": "inventory",
                "p": "character",
                "m": "market",
                "d": "dialogue",
                "b": "combat",
                "n": "character_creation",
                "w": "world",
                "q": "quit",
                "left": "left",
                "right": "right",
                "up": "up",
                "down": "down",
                "backspace": "backspace",
                "delete": "delete",
                "f5": "save",
                "f9": "load",
                "f11": "fullscreen",
                "x": "map",
                "l": "local_map",
            }

            action = actions.get(key)
            if action:
                state.actions.add(action)

            if key.isdigit():
                state.actions.add(f"slot:{key}")

            if key not in {
                "return", "escape", "backspace",
                "left", "right", "up", "down", "f5", "f9",
            }:
                character = getattr(event, "unicode", "")
                if character and character.isprintable():
                    state.text += character

        return state

    def _key_name(self, key) -> str:
        if isinstance(key, str):
            return key.lower()

        names = {
            getattr(self.backend, "K_ESCAPE", object()): "escape",
            getattr(self.backend, "K_RETURN", object()): "return",
            getattr(self.backend, "K_SPACE", object()): "space",
            getattr(self.backend, "K_LEFT", object()): "left",
            getattr(self.backend, "K_RIGHT", object()): "right",
            getattr(self.backend, "K_UP", object()): "up",
            getattr(self.backend, "K_DOWN", object()): "down",
            getattr(self.backend, "K_BACKSPACE", object()): "backspace",
            getattr(self.backend, "K_DELETE", object()): "delete",
        }

        if self.backend is not None:
            for letter in "gcipwqxlmdbn":
                names[getattr(self.backend, f"K_{letter}", object())] = letter
            names[getattr(self.backend, "K_F5", object())] = "f5"
            names[getattr(self.backend, "K_F9", object())] = "f9"
            names[getattr(self.backend, "K_F11", object())] = "f11"
            names[getattr(self.backend, "K_DELETE", object())] = "delete"

        return names.get(key, "")
