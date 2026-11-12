"""Time-based sprite animation playback state."""
from __future__ import annotations


class Animation:
    def __init__(self, frames, frame_duration: float = 0.12, *, loop: bool = True):
        if not frames:
            raise ValueError("Animation requires at least one frame.")
        if frame_duration <= 0:
            raise ValueError("frame_duration must be greater than zero.")
        self.frames = tuple(frames)
        self.frame_duration = float(frame_duration)
        self.loop = bool(loop)
        self.elapsed = 0.0
        self.index = 0
        self.finished = False

    @property
    def current_frame(self):
        return self.frames[self.index]

    def update(self, elapsed_seconds: float) -> None:
        if elapsed_seconds < 0:
            raise ValueError("elapsed_seconds cannot be negative.")
        if self.finished or elapsed_seconds == 0:
            return
        self.elapsed += float(elapsed_seconds)
        while self.elapsed >= self.frame_duration and not self.finished:
            self.elapsed -= self.frame_duration
            if self.index + 1 < len(self.frames):
                self.index += 1
            elif self.loop:
                self.index = 0
            else:
                self.index = len(self.frames) - 1
                self.finished = True
                self.elapsed = 0.0
