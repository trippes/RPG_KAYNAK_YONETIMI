"""Low-overhead, opt-in NPC simulation diagnostics."""
from __future__ import annotations

from collections import Counter, defaultdict
from functools import wraps
import math
from statistics import median
from time import perf_counter


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = max(1, math.ceil(percentile / 100.0 * len(ordered)))
    return ordered[rank - 1]


class NPCSimulationMetrics:
    """Counters and duration samples for one controlled measurement run."""

    def __init__(self) -> None:
        self._counts: Counter[str] = Counter()
        self._durations: dict[str, list[float]] = defaultdict(list)

    def increment(self, name: str, amount: int = 1) -> None:
        if not isinstance(name, str) or not name:
            raise ValueError("metric name must be non-empty")
        if type(amount) is not int or amount < 0:
            raise ValueError("amount must be a non-negative integer")
        self._counts[name] += amount

    def record_duration(self, name: str, seconds: float) -> None:
        if not isinstance(name, str) or not name:
            raise ValueError("metric name must be non-empty")
        if not math.isfinite(seconds) or seconds < 0:
            raise ValueError("duration must be finite and non-negative")
        self._durations[name].append(float(seconds))

    def reset(self) -> None:
        self._counts.clear()
        self._durations.clear()

    def snapshot(self) -> dict:
        """Return a detached JSON-serializable copy of all collected metrics."""
        return {
            "counts": dict(sorted(self._counts.items())),
            "durations_seconds": {
                name: {
                    "samples": len(values),
                    "total": sum(values),
                    "median": median(values),
                    "p50": _percentile(values, 50),
                    "p95": _percentile(values, 95),
                    "p99": _percentile(values, 99),
                    "max": max(values),
                }
                for name, values in sorted(self._durations.items())
                if values
            },
        }


def timed_npc_step(name: str):
    """Time a system step only when metrics are attached to its runtime."""

    def decorate(method):
        @wraps(method)
        def wrapped(self, *args, **kwargs):
            runtime = getattr(self, "_runtime", None)
            if runtime is None:
                runtime = getattr(self, "runtime", None)
            metrics = getattr(runtime, "metrics", None)
            if metrics is None:
                return method(self, *args, **kwargs)
            started = perf_counter()
            try:
                return method(self, *args, **kwargs)
            finally:
                metrics.record_duration(name, perf_counter() - started)

        return wrapped

    return decorate


__all__ = ["NPCSimulationMetrics", "timed_npc_step"]
