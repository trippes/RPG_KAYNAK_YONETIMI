"""Concurrency regression tests for unified save-slot operations."""

import multiprocessing
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from application import GameSaveDocument, GameSaveFileAdapter
from application.save_codec import SaveJsonCodec
from application.save_lock import save_path_lock
from core.application import GameSession
from core.persistence import CanonicalSessionState, PersistenceDocument
from core.simulation import SimulationRuntime
from resources import Inventory, ProductionJobManager, Quantity, ResourceType, ResourceUnit, GameplaySnapshot, WorldResourceNodeManager


def _acquire_save_lock_in_child(path: str, started, acquired) -> None:
    started.set()
    with save_path_lock(path):
        acquired.set()


class TestSaveConcurrency(unittest.TestCase):
    def _document(self, marker: str) -> GameSaveDocument:
        session = GameSession()
        session.simulation.advance_to(3)
        core = PersistenceDocument.from_state(CanonicalSessionState.from_session(session))
        inventory = Inventory()
        inventory.add(ResourceType("wood"), Quantity(2 if marker == "first" else 3, ResourceUnit.ITEM))
        jobs = ProductionJobManager(SimulationRuntime(start_tick=3))
        gameplay = GameplaySnapshot.from_runtime(
            {"main": inventory},
            WorldResourceNodeManager(),
            jobs,
        )
        return GameSaveDocument(core=core, gameplay=gameplay)

    def test_simultaneous_thread_saves_keep_primary_and_backup_valid(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "slot_1.json"
            documents = (self._document("first"), self._document("second"))
            barrier = threading.Barrier(3)

            def save_after_barrier(document):
                barrier.wait(timeout=5)
                GameSaveFileAdapter.save(document, path)

            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = [
                    executor.submit(save_after_barrier, document)
                    for document in documents
                ]
                barrier.wait(timeout=5)
                for future in futures:
                    future.result(timeout=10)

            primary = GameSaveFileAdapter.load(path)
            backup = GameSaveFileAdapter.load(GameSaveFileAdapter.backup_path(path))
            encoded_documents = {SaveJsonCodec.encode(item) for item in documents}
            self.assertIn(SaveJsonCodec.encode(primary), encoded_documents)
            self.assertIn(SaveJsonCodec.encode(backup), encoded_documents)
            self.assertNotEqual(SaveJsonCodec.encode(primary), SaveJsonCodec.encode(backup))

    def test_save_waits_until_an_in_progress_load_finishes(self):
        from unittest import mock

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "slot_1.json"
            first = self._document("first")
            second = self._document("second")
            GameSaveFileAdapter.save(first, path)

            read_entered = threading.Event()
            release_read = threading.Event()
            save_finished = threading.Event()
            original_read = GameSaveFileAdapter._read_document

            def pause_primary_read(candidate):
                if Path(candidate) == path:
                    read_entered.set()
                    if not release_read.wait(5):
                        raise TimeoutError("test did not release the load")
                return original_read(candidate)

            with mock.patch.object(
                GameSaveFileAdapter,
                "_read_document",
                side_effect=pause_primary_read,
            ):
                loader = threading.Thread(target=lambda: GameSaveFileAdapter.load(path))
                loader.start()
                self.assertTrue(read_entered.wait(5))

                def save_second():
                    GameSaveFileAdapter.save(second, path)
                    save_finished.set()

                saver = threading.Thread(target=save_second)
                saver.start()
                self.assertFalse(save_finished.wait(0.25))
                release_read.set()
                loader.join(5)
                saver.join(5)

            self.assertFalse(loader.is_alive())
            self.assertFalse(saver.is_alive())
            self.assertTrue(save_finished.is_set())
            self.assertEqual(
                SaveJsonCodec.encode(GameSaveFileAdapter.load(path)),
                SaveJsonCodec.encode(second),
            )
            self.assertEqual(
                SaveJsonCodec.encode(
                    GameSaveFileAdapter.load(GameSaveFileAdapter.backup_path(path))
                ),
                SaveJsonCodec.encode(first),
            )

    def test_processes_cannot_hold_the_same_slot_lock_at_once(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "slot_1.json"
            context = multiprocessing.get_context("spawn")
            started = context.Event()
            acquired = context.Event()
            process = context.Process(
                target=_acquire_save_lock_in_child,
                args=(str(path), started, acquired),
            )

            with save_path_lock(path):
                process.start()
                self.assertTrue(started.wait(5))
                self.assertFalse(acquired.wait(0.25))

            self.assertTrue(acquired.wait(5))
            process.join(5)
            self.assertEqual(process.exitcode, 0)

    def test_lock_is_released_after_an_exception(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "slot_1.json"
            with self.assertRaisesRegex(RuntimeError, "injected"):
                with save_path_lock(path):
                    raise RuntimeError("injected")

            acquired = threading.Event()

            def acquire():
                with save_path_lock(path):
                    acquired.set()

            thread = threading.Thread(target=acquire)
            thread.start()
            thread.join(5)
            self.assertFalse(thread.is_alive())
            self.assertTrue(acquired.is_set())

    def test_different_slots_use_independent_locks(self):
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "slot_1.json"
            second = Path(directory) / "slot_2.json"
            acquired = threading.Event()

            with save_path_lock(first):
                thread = threading.Thread(
                    target=lambda: self._acquire_and_signal(second, acquired)
                )
                thread.start()
                thread.join(5)
                self.assertFalse(thread.is_alive())

            self.assertTrue(acquired.is_set())

    @staticmethod
    def _acquire_and_signal(path: Path, signal) -> None:
        with save_path_lock(path):
            signal.set()


if __name__ == "__main__":
    unittest.main()
