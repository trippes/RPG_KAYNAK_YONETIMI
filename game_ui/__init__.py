"""Game UI package and pygame-ce backend adapter."""

import importlib

from .game_window import GameWindow, launch
from .input import InputMapper, InputState
from .renderer import Renderer
from .window_manager import WindowManager


def load_backend():
    """Load the third-party pygame-ce backend."""
    try:
        return importlib.import_module("pygame")
    except ImportError as error:
        raise RuntimeError("Third-party pygame backend is not installed.") from error

__all__ = [
    "GameWindow", "InputMapper", "InputState", "Renderer",
    "WindowManager", "launch", "load_backend",
]
