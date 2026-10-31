"""Pygame adapter package (kept free of a hard import-time dependency)."""

import importlib
import sys
from pathlib import Path

from .game_window import GameWindow, launch
from .input import InputMapper, InputState
from .renderer import Renderer


def load_backend():
    """Load third-party pygame despite this adapter package's legacy name."""
    adapter_module = sys.modules.get(__name__)
    local_modules = {
        name: module for name, module in sys.modules.items()
        if name == "pygame" or name.startswith("pygame.")
    }
    for name in local_modules:
        sys.modules.pop(name, None)
    root = str(Path(__file__).resolve().parent.parent)
    working_directory = str(Path.cwd().resolve())
    site_package_roots = {
        str(Path(entry).resolve())
        for entry in sys.path
        if entry and "site-packages" in str(Path(entry).resolve()).lower()
    }
    blocked_roots = {working_directory}
    if root not in site_package_roots:
        blocked_roots.add(root)
    original_path = list(sys.path)
    if root in site_package_roots:
        # In an installed wheel, this adapter and pygame-ce share the
        # ``pygame`` directory.  Importing the top-level package again would
        # only reload this adapter, so bind the extension modules directly.
        if adapter_module is None:
            raise RuntimeError("Pygame adapter module is unavailable.")
        sys.modules["pygame"] = adapter_module
        return _load_installed_backend(adapter_module)
    try:
        sys.path[:] = [
            entry for entry in sys.path
            if str(Path(entry or ".").resolve()) not in blocked_roots
        ]
        backend = importlib.import_module("pygame")
        if not hasattr(backend, "display") and hasattr(backend, "_load_installed_backend"):
            return backend._load_installed_backend(backend)
        return backend
    except ImportError as error:
        raise RuntimeError("Third-party pygame backend is not installed.") from error
    finally:
        sys.path[:] = original_path
        # Keep the external package and its submodules registered. Pygame's
        # lazy imports (pygame.time, pygame.font, ...) rely on that package
        # identity after the loader returns.


def _load_installed_backend(adapter_module):
    """Expose pygame-ce extension modules through the installed adapter."""
    import importlib

    base = importlib.import_module("pygame.base")
    constants = importlib.import_module("pygame.constants")
    rect = importlib.import_module("pygame.rect")
    adapter_module.version = importlib.import_module("pygame.version")
    for name in ("display", "draw", "event", "font", "time"):
        setattr(adapter_module, name, importlib.import_module(f"pygame.{name}"))
    adapter_module.init = base.init
    adapter_module.quit = base.quit
    adapter_module.Rect = rect.Rect
    for name in dir(constants):
        if name.startswith("K_") or name in {"QUIT", "KEYDOWN"}:
            setattr(adapter_module, name, getattr(constants, name))
    return adapter_module

__all__ = ["GameWindow", "InputMapper", "InputState", "Renderer", "launch", "load_backend"]
