"""Three-session Phase 11 tick and render snapshot benchmark."""
from __future__ import annotations

import json
import platform
import statistics
import sys
from pathlib import Path

import pygame

# Make the laboratory root importable when this script is run by file path.
LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT))

from benchmarks.benchmark_simulation_tick import (  # noqa: E402
    MEASURED_BATCHES,
    WARMUP_BATCHES,
    measure_snapshot_cost,
    measure_tick_cost,
)


SESSION_COUNT = 3


def median_metric(sessions: list[dict[str, object]], group: str, metric: str) -> float:
    values = [float(session[group][metric]) for session in sessions]  # type: ignore[index]
    return round(statistics.median(values), 4)


def main() -> int:
    pygame.init()
    try:
        sessions: list[dict[str, object]] = []
        for session_number in range(1, SESSION_COUNT + 1):
            sessions.append({
                "session": session_number,
                "simulation_tick": measure_tick_cost(),
                "render_snapshot": measure_snapshot_cost(),
            })

        report = {
            "python": sys.version,
            "platform": platform.platform(),
            "processor": platform.processor() or "unavailable",
            "session_count": SESSION_COUNT,
            "warmup_batches_per_session": WARMUP_BATCHES,
            "measured_batches_per_session": MEASURED_BATCHES,
            "measurement_note": "Median across three independent sessions. Compare only runs on the same runner and Python environment; no cross-machine absolute threshold is implied.",
            "sessions": sessions,
            "median_across_sessions": {
                "simulation_tick_mean_us": median_metric(sessions, "simulation_tick", "mean_tick_us"),
                "simulation_tick_p95_batch_ms": median_metric(sessions, "simulation_tick", "p95_batch_ms"),
                "render_snapshot_mean_us": median_metric(sessions, "render_snapshot", "mean_snapshot_us"),
                "render_snapshot_p95_batch_ms": median_metric(sessions, "render_snapshot", "p95_batch_ms"),
            },
        }
        output = Path("artifacts/phase-11")
        output.mkdir(parents=True, exist_ok=True)
        (output / "phase-11-simulation-performance.json").write_text(
            json.dumps(report, indent=2), encoding="utf-8"
        )
        print(json.dumps(report, indent=2))
        return 0
    finally:
        pygame.quit()


if __name__ == "__main__":
    raise SystemExit(main())
