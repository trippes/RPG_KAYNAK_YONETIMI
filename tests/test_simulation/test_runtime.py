import unittest

from core.application import GameSession
from core.foundation import EntityId
from core.simulation import SimulationRuntime
from core.time import Tick


class TestSimulationRuntime(unittest.TestCase):
    def test_advance_by_is_deterministic_and_monotonic(self):
        runtime = SimulationRuntime()
        self.assertEqual(runtime.current_tick, Tick(0))
        runtime.advance_by(Tick(4))
        self.assertEqual(runtime.current_tick, Tick(4))
        with self.assertRaises(ValueError):
            runtime.advance_by(-1)

    def test_game_session_exposes_simulation_runtime(self):
        session = GameSession()
        action = session.simulation.actions.create(EntityId("entity_1"), Tick(1))
        session.simulation.actions.schedule(action.action_id, Tick(2))
        events = session.simulation.advance_to(Tick(3))
        self.assertEqual(action.state.value, "completed")
        self.assertEqual(events[-1].event_type, "ActionCompleted")

    def test_world_runtime_boundary_mirrors_canonical_tick(self):
        session = GameSession()
        world = session.worlds.create("Ana Dünya")
        previous, current = session.world_runtime.advance_world(world, Tick(3))
        self.assertEqual(previous, Tick(0))
        self.assertEqual(current, Tick(3))
        self.assertEqual(world.total_ticks, 3)

