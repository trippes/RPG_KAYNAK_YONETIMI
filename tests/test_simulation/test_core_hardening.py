import unittest
from pathlib import Path

from core.application import GameSession
from core.compatibility import reset_runtime_usage, usage_report
from core.foundation import EntityId
from core.simulation import SimulationReplay, SimulationRuntime
from core.time import Tick


class TestCoreHardening(unittest.TestCase):
    def _run_scenario(self):
        runtime = SimulationRuntime()
        first = runtime.actions.create(EntityId("actor_1"), Tick(2), {"kind": "gather"})
        second = runtime.actions.create(EntityId("actor_1"), Tick(0), {"kind": "scout"})
        runtime.actions.schedule(first.action_id, Tick(1))
        runtime.actions.schedule(second.action_id, Tick(1))
        return runtime, runtime.advance_to(Tick(3))

    def test_same_action_schedule_produces_identical_event_stream(self):
        _, first_events = self._run_scenario()
        _, second_events = self._run_scenario()
        self.assertEqual(
            [event.to_dict() for event in first_events],
            [event.to_dict() for event in second_events],
        )

    def test_replay_contract_matches_canonical_event_stream(self):
        _, events = self._run_scenario()
        replay = SimulationReplay.from_events(events)
        replay.assert_matches(events)
        self.assertEqual(len(replay.to_dict()["events"]), len(events))
        with self.assertRaises(AssertionError):
            replay.assert_matches(events[:-1])

    def test_migration_report_is_sorted_and_contains_canonical_targets(self):
        reset_runtime_usage()
        report = usage_report(Path(__file__).parents[2])
        self.assertEqual(
            [entry.legacy_name for entry in report],
            sorted(entry.legacy_name for entry in report),
        )
        self.assertTrue(all(entry.canonical_replacement for entry in report))

    def test_session_restore_keeps_canonical_simulation_tick(self):
        session = GameSession()
        session.simulation.advance_to(Tick(7))
        from core.persistence import CanonicalSessionState, RestoreContract

        plan = RestoreContract.prepare(CanonicalSessionState.from_session(session))
        restored = GameSession()
        restored.activate_restore(plan)
        self.assertEqual(restored.simulation.current_tick, Tick(7))


if __name__ == "__main__":
    unittest.main()
