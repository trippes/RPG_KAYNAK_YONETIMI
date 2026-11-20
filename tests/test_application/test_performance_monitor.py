import unittest

from application.performance_monitor import PerformanceMonitor


class PerformanceMonitorTests(unittest.TestCase):
    def test_disabled_monitor_does_not_collect_samples(self):
        monitor = PerformanceMonitor(enabled=False)
        monitor.record_frame(16.0, phases={"render": 4.0}, counters={"cells": 10})
        self.assertEqual(
            monitor.stats,
            {"enabled": False, "frames": 0, "phases": {}, "counters": {}},
        )

    def test_frame_and_phase_percentiles_are_reported(self):
        monitor = PerformanceMonitor(enabled=True, sample_limit=10)
        for frame_ms in (10.0, 20.0, 30.0, 40.0):
            monitor.record_frame(
                frame_ms,
                phases={"render": frame_ms / 2},
                counters={"visible_cells": 12},
            )
        stats = monitor.stats
        self.assertEqual(stats["frames"]["count"], 4)
        self.assertEqual(stats["frames"]["min_ms"], 10.0)
        self.assertEqual(stats["frames"]["max_ms"], 40.0)
        self.assertEqual(stats["frames"]["avg_fps"], 40.0)
        self.assertEqual(stats["frames"]["over_16_67_ms"], 3)
        self.assertEqual(stats["frames"]["p50_ms"], 20.0)
        self.assertEqual(stats["frames"]["p95_ms"], 40.0)
        self.assertEqual(stats["phases"]["render"]["avg_ms"], 12.5)
        self.assertEqual(stats["counters"]["visible_cells"], 12)

    def test_samples_are_bounded_and_resettable(self):
        monitor = PerformanceMonitor(enabled=True, sample_limit=3)
        for frame_ms in (1.0, 2.0, 3.0, 4.0):
            monitor.record_frame(frame_ms)
        self.assertEqual(monitor.stats["frames"]["count"], 3)
        self.assertEqual(monitor.stats["frames"]["min_ms"], 2.0)
        monitor.reset()
        self.assertEqual(monitor.stats["frames"]["count"], 0)


if __name__ == "__main__":
    unittest.main()
