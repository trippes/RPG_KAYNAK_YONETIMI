"""Configuration for the standalone laboratory application."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Window and runtime settings for the laboratory shell."""

    window_title: str = "Eldoria — Hex World Laboratory"
    window_width: int = 960
    window_height: int = 640
    target_fps: int = 60
