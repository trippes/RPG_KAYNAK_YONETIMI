"""Directional, data-driven presentation animation state."""
from __future__ import annotations

from game_ui.assets.animation import Animation


class CharacterAnimator:
    DIRECTIONS = {
        "north", "north_east", "east", "south_east",
        "south", "south_west", "west", "north_west",
    }
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
        next_direction = self.direction if direction is None else direction
        next_state = self.state if state is None else state
        if next_direction not in self.DIRECTIONS or next_state not in self.STATES:
            raise ValueError("Unsupported character direction or animation state.")

        direction_changed = next_direction != self.direction
        state_changed = next_state != self.state
        previous_animation = self.current_animation
        self.direction, self.state = next_direction, next_state
        animation = self.current_animation
        if animation is None:
            return

        if state_changed:
            animation.elapsed = 0.0
            animation.index = 0
            animation.finished = False
        elif direction_changed and previous_animation is not None:
            # Keep the gait phase when turning so the legs do not snap back
            # to the first pose on every direction change.
            phase = (
                previous_animation.index
                + previous_animation.elapsed / previous_animation.frame_duration
            ) / len(previous_animation.frames)
            frame_position = phase * len(animation.frames)
            animation.index = min(int(frame_position), len(animation.frames) - 1)
            animation.elapsed = (
                frame_position - animation.index
            ) * animation.frame_duration
            animation.finished = False

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
