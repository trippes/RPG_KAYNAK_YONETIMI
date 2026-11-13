"""Directional, data-driven presentation animation state."""
from game_ui.assets.animation import Animation

class CharacterAnimator:
    DIRECTIONS = {"north", "north_east", "east", "south_east", "south", "south_west", "west", "north_west"}
    STATES = {"idle", "walk", "run", "attack", "interact"}
    def __init__(self, animations=None):
        self.animations = {}
        for direction, states in (animations or {}).items():
            if direction not in self.DIRECTIONS or not isinstance(states, dict):
                raise ValueError("Invalid character animation direction.")
            for state, animation in states.items():
                if state not in self.STATES or not isinstance(animation, Animation):
                    raise ValueError("Character states must map to Animation instances.")
                self.animations[(direction, state)] = animation
        self.direction, self.state = "south", "idle"
    def select(self, *, direction=None, state=None):
        direction = self.direction if direction is None else direction
        state = self.state if state is None else state
        if direction not in self.DIRECTIONS or state not in self.STATES:
            raise ValueError("Unsupported character direction or animation state.")
        self.direction, self.state = direction, state
    def update(self, elapsed_seconds):
        if self.current_animation is not None:
            self.current_animation.update(elapsed_seconds)
    @property
    def current_animation(self):
        return self.animations.get((self.direction, self.state))
    @property
    def current_frame(self):
        animation = self.current_animation
        return None if animation is None else animation.current_frame
