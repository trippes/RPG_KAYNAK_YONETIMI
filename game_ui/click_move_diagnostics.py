"""Temporary, opt-in diagnostics for the click-to-move runtime chain.

Enable with ELDORIA_CLICK_MOVE_DIAGNOSTICS=1. The log is written to the
current working directory unless ELDORIA_CLICK_MOVE_LOG supplies a path.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from time import monotonic_ns


def record_click_move_event(stage: str, **values) -> None:
    """Append one structured diagnostic event without affecting gameplay."""
    if os.environ.get("ELDORIA_CLICK_MOVE_DIAGNOSTICS") != "1":
        return
    destination = Path(
        os.environ.get("ELDORIA_CLICK_MOVE_LOG", "click_move_diagnostics.log")
    )
    event = {"time_ns": monotonic_ns(), "stage": stage, **values}
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, ensure_ascii=False, default=repr) + "\\n")
    except OSError:
        # Diagnostics must never interrupt or alter the game loop.
        return
