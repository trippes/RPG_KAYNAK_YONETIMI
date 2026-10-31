"""Small user-facing logging boundary for the desktop application."""

from __future__ import annotations

import logging
from pathlib import Path


def configure_logging(log_path: str | Path = "logs/eldoria.log") -> logging.Logger:
    """Configure one rotating-friendly file logger without touching Core."""
    target = Path(log_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("rpg_kaynak_yonetimi")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if not any(getattr(handler, "_rpg_log_path", None) == str(target) for handler in logger.handlers):
        handler = logging.FileHandler(target, encoding="utf-8")
        handler._rpg_log_path = str(target)
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)
    return logger


__all__ = ["configure_logging"]
