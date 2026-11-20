"""Low-overhead, opt-in runtime performance telemetry for Eldoria."""

from __future__ import annotations

from collections import defaultdict, deque
from math import ceil
from os import environ


def _percentile(values, percentile):
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, ceil(percentile * len(ordered)) - 1))
    return ordered[index]


class PerformanceMonitor:
    """Keep a bounded rolling window of frame and phase timings."""

    __slots__ = ("enabled", "sample_limit", "_frames", "_phases", "_counters")

    def __init__(self, *, enabled=None, sample_limit=600):
        if enabled is None:
            enabled = environ.get("ELDORIA_PERF", "").strip().lower() in {
                "1", "true", "yes", "on",
            }
        self.enabled = bool(enabled)
        self.sample_limit = max(1, int(sample_limit))
        self._frames = deque(maxlen=self.sample_limit)
        self._phases = defaultdict(lambda: deque(maxlen=self.sample_limit))
        self._counters = {}

    def record_frame(self, frame_ms, *, phases=None, counters=None):
        if not self.enabled:
            return
        self._frames.append(max(0.0, float(frame_ms)))
        for name, duration in (phases or {}).items():
            self._phases[str(name)].append(max(0.0, float(duration)))
        self._counters = {
            str(name): value for name, value in (counters or {}).items()
        }

    @staticmethod
    def _summary(values):
        if not values:
            return {"count": 0, "avg_ms": 0.0, "min_ms": 0.0,
                    "p50_ms": 0.0, "p95_ms": 0.0, "p99_ms": 0.0,
                    "max_ms": 0.0}
        return {
            "count": len(values),
            "avg_ms": sum(values) / len(values),
            "avg_fps": 1000.0 / (sum(values) / len(values)) if sum(values) > 0 else 0.0,
            "min_ms": min(values),
            "p50_ms": _percentile(values, 0.50),
            "p95_ms": _percentile(values, 0.95),
            "p99_ms": _percentile(values, 0.99),
            "max_ms": max(values),
            "over_16_67_ms": sum(value > 16.67 for value in values),
            "over_25_ms": sum(value > 25.0 for value in values),
        }

    @property
    def stats(self):
        if not self.enabled:
            return {"enabled": False, "frames": 0, "phases": {}, "counters": {}}
        return {
            "enabled": True,
            "frames": self._summary(self._frames),
            "phases": {
                name: self._summary(values)
                for name, values in sorted(self._phases.items())
            },
            "counters": dict(self._counters),
        }

    def reset(self):
        self._frames.clear()
        self._phases.clear()
        self._counters.clear()


__all__ = ["PerformanceMonitor"]
