import tempfile
import unittest
from pathlib import Path
from unittest import mock

from application.save_storage import SaveStorage, SaveStorageError
from game_ui.game_window import GameWindow
from game_ui.screens.save_slots_screen import SaveSlotsScreen


class TestSaveStorage(unittest.TestCase):
    def test_documents_provider_builds_user_save_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = SaveStorage(documents_path=Path(directory))
            self.assertEqual(
                storage.save_directory,
                Path(directory) / "My Games" / "Eldoria" / "Saves",
            )

    def test_prepare_creates_directory_and_all_ten_slot_names(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = SaveStorage(documents_path=Path(directory))
            storage.prepare()
            self.assertTrue(storage.save_directory.is_dir())
            self.assertEqual(
                [storage.slot_path(index).name for index in range(storage.SLOT_COUNT)],
                [f"slot_{index}.json" for index in range(1, 11)],
            )

    def test_migrates_valid_legacy_slots_without_deleting_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            legacy = root / "save"
            source = legacy / "slot_1.json"
            source.parent.mkdir()
            source.write_text("valid-save", encoding="utf-8")
            storage = SaveStorage(documents_path=root / "documents", legacy_directory=legacy)

            with mock.patch(
                "application.save_storage.GameSaveFileAdapter.load",
                return_value=object(),
            ) as load:
                report = storage.prepare()

            target = storage.slot_path(0)
            self.assertEqual(target.read_text(encoding="utf-8"), "valid-save")
            self.assertTrue(source.exists())
            self.assertEqual(report.copied, (target,))
            self.assertEqual(load.call_count, 2)

    def test_slot_migration_race_preserves_competing_target_and_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            legacy = root / "save"
            legacy.mkdir()
            source = legacy / "slot_1.json"
            source.write_text("legacy-save", encoding="utf-8")
            storage = SaveStorage(documents_path=root / "documents", legacy_directory=legacy)
            target = storage.slot_path(0)

            def create_target_then_fail(_temporary, competing_target):
                competing_target.write_text("competing-save", encoding="utf-8")
                raise FileExistsError("target appeared")

            with mock.patch(
                "application.save_storage.GameSaveFileAdapter.load",
                return_value=object(),
            ), mock.patch(
                "application.save_storage.os.link",
                side_effect=create_target_then_fail,
            ):
                report = storage.prepare()

            self.assertEqual(target.read_text(encoding="utf-8"), "competing-save")
            self.assertEqual(source.read_text(encoding="utf-8"), "legacy-save")
            self.assertEqual(len(report.conflicts), 1)
            self.assertEqual(list(target.parent.glob(".slot_1.json.*.tmp")), [])

    def test_existing_target_is_never_overwritten_and_conflict_is_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            legacy = root / "save"
            legacy.mkdir()
            (legacy / "slot_1.json").write_text("old", encoding="utf-8")
            storage = SaveStorage(documents_path=root / "documents", legacy_directory=legacy)
            target = storage.slot_path(0)
            target.parent.mkdir(parents=True)
            target.write_text("new", encoding="utf-8")

            report = storage.prepare()

            self.assertEqual(target.read_text(encoding="utf-8"), "new")
            self.assertEqual(report.copied, ())
            self.assertEqual(len(report.conflicts), 1)

    def test_identical_existing_target_is_not_copied_again(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            legacy = root / "save"
            legacy.mkdir()
            (legacy / "slot_1.json").write_text("same", encoding="utf-8")
            storage = SaveStorage(documents_path=root / "documents", legacy_directory=legacy)
            target = storage.slot_path(0)
            target.parent.mkdir(parents=True)
            target.write_text("same", encoding="utf-8")

            report = storage.prepare()

            self.assertEqual(report.copied, ())
            self.assertEqual(report.conflicts, ())

    def test_invalid_legacy_json_is_not_copied(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            legacy = root / "save"
            legacy.mkdir()
            source = legacy / "slot_1.json"
            source.write_text("{broken", encoding="utf-8")
            storage = SaveStorage(documents_path=root / "documents", legacy_directory=legacy)

            with mock.patch(
                "application.save_storage.GameSaveFileAdapter.load",
                side_effect=ValueError("invalid JSON"),
            ):
                report = storage.prepare()

            self.assertFalse(storage.slot_path(0).exists())
            self.assertTrue(source.exists())
            self.assertEqual(len(report.invalid_sources), 1)

    def test_unavailable_documents_directory_is_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            blocked = Path(directory) / "not-a-directory"
            blocked.write_text("file", encoding="utf-8")
            storage = SaveStorage(documents_path=blocked)
            with self.assertRaises(SaveStorageError):
                storage.prepare()

    def test_migrates_valid_legacy_single_save_to_first_empty_slot(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            legacy = root / "save"
            legacy.mkdir()
            source = legacy / "eldoria_save.json"
            backup = legacy / "eldoria_save.json.bak"
            source.write_text("single-save", encoding="utf-8")
            backup.write_text("backup-save", encoding="utf-8")
            (legacy / "slot_1.json").write_text("occupied", encoding="utf-8")
            storage = SaveStorage(documents_path=root / "documents", legacy_directory=legacy)

            with mock.patch(
                "application.save_storage.GameSaveFileAdapter.load",
                return_value=object(),
            ) as load:
                report = storage.prepare()

            target = storage.slot_path(1)
            self.assertEqual(target.read_text(encoding="utf-8"), "single-save")
            self.assertEqual(report.copied[-1], target)
            self.assertEqual(source.read_text(encoding="utf-8"), "single-save")
            self.assertEqual(backup.read_text(encoding="utf-8"), "backup-save")
            self.assertEqual(load.call_count, 6)

    def test_single_save_migration_race_preserves_competing_target_and_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            legacy = root / "save"
            legacy.mkdir()
            source = legacy / "eldoria_save.json"
            source.write_text("single-save", encoding="utf-8")
            storage = SaveStorage(documents_path=root / "documents", legacy_directory=legacy)
            target = storage.slot_path(0)

            def create_target_then_fail(_temporary, competing_target):
                competing_target.write_text("competing-save", encoding="utf-8")
                raise FileExistsError("target appeared")

            with mock.patch(
                "application.save_storage.GameSaveFileAdapter.load",
                return_value=object(),
            ), mock.patch(
                "application.save_storage.os.link",
                side_effect=create_target_then_fail,
            ):
                report = storage.prepare()

            self.assertEqual(target.read_text(encoding="utf-8"), "competing-save")
            self.assertEqual(source.read_text(encoding="utf-8"), "single-save")
            self.assertEqual(len(report.conflicts), 1)
            self.assertEqual(list(target.parent.glob(".slot_1.json.*.tmp")), [])

    def test_full_slots_do_not_overwrite_for_legacy_single_save(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            legacy = root / "save"
            legacy.mkdir()
            source = legacy / "eldoria_save.json"
            source.write_text("single-save", encoding="utf-8")
            storage = SaveStorage(documents_path=root / "documents", legacy_directory=legacy)
            for index in range(1, storage.SLOT_COUNT + 1):
                (legacy / f"slot_{index}.json").write_text(
                    f"slot-{index}", encoding="utf-8"
                )

            with mock.patch(
                "application.save_storage.GameSaveFileAdapter.load",
                return_value=object(),
            ):
                report = storage.prepare()

            self.assertFalse(any(
                path.read_text(encoding="utf-8") == "single-save"
                for path in storage.save_directory.glob("slot_*.json")
            ))
            self.assertTrue(source.exists())
            self.assertTrue(any("tüm kayıt yuvaları dolu" in item for item in report.conflicts))

    def test_legacy_single_save_is_not_duplicated_on_repeat(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            legacy = root / "save"
            legacy.mkdir()
            source = legacy / "eldoria_save.json"
            source.write_text("single-save", encoding="utf-8")
            storage = SaveStorage(documents_path=root / "documents", legacy_directory=legacy)

            with mock.patch(
                "application.save_storage.GameSaveFileAdapter.load",
                return_value=object(),
            ):
                first = storage.prepare()
                second = storage.prepare()

            self.assertEqual(len(first.copied), 1)
            self.assertEqual(second.copied, ())
            self.assertEqual(
                [path for path in storage.save_directory.glob("slot_*.json")],
                [storage.slot_path(0)],
            )
            self.assertTrue(source.exists())

    def test_legacy_single_save_with_different_json_format_is_not_duplicated(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            legacy = root / "save"
            legacy.mkdir()
            source = legacy / "eldoria_save.json"
            source.write_text('{"schema": "rpg-game-save", "value": 1}', encoding="utf-8")
            storage = SaveStorage(documents_path=root / "documents", legacy_directory=legacy)
            target = storage.slot_path(0)
            target.parent.mkdir(parents=True)
            target.write_text('{"value":1,"schema":"rpg-game-save"}', encoding="utf-8")

            with mock.patch(
                "application.save_storage.GameSaveFileAdapter.load",
                return_value=object(),
            ):
                report = storage.prepare()

            self.assertEqual(report.copied, ())
            self.assertTrue(target.exists())
            self.assertEqual(target.read_text(encoding="utf-8"), '{"value":1,"schema":"rpg-game-save"}')

    def test_invalid_legacy_single_save_is_preserved_and_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            legacy = root / "save"
            legacy.mkdir()
            source = legacy / "eldoria_save.json"
            backup = legacy / "eldoria_save.json.bak"
            source.write_text("{broken", encoding="utf-8")
            backup.write_text("backup-save", encoding="utf-8")
            storage = SaveStorage(documents_path=root / "documents", legacy_directory=legacy)

            with mock.patch(
                "application.save_storage.GameSaveFileAdapter.load",
                side_effect=ValueError("invalid JSON"),
            ):
                report = storage.prepare()

            self.assertFalse(storage.slot_path(0).exists())
            self.assertTrue(source.exists())
            self.assertEqual(source.read_text(encoding="utf-8"), "{broken")
            self.assertEqual(backup.read_text(encoding="utf-8"), "backup-save")
            self.assertTrue(any("eldoria_save.json" in item for item in report.invalid_sources))

    def test_failed_temporary_validation_creates_no_target(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            legacy = root / "save"
            legacy.mkdir()
            source = legacy / "eldoria_save.json"
            backup = legacy / "eldoria_save.json.bak"
            source.write_text("single-save", encoding="utf-8")
            backup.write_text("backup-save", encoding="utf-8")
            storage = SaveStorage(documents_path=root / "documents", legacy_directory=legacy)

            with mock.patch(
                "application.save_storage.GameSaveFileAdapter.load",
                side_effect=[object(), ValueError("target validation failed")],
            ):
                report = storage.prepare()

            self.assertFalse(storage.slot_path(0).exists())
            self.assertTrue(source.exists())
            self.assertEqual(source.read_text(encoding="utf-8"), "single-save")
            self.assertEqual(backup.read_text(encoding="utf-8"), "backup-save")
            self.assertEqual(len(report.invalid_sources), 1)
            self.assertEqual(list(storage.save_directory.glob(".slot_1.json.*.tmp")), [])

    def test_failed_temporary_validation_preserves_source_and_existing_target(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            legacy = root / "save"
            legacy.mkdir()
            source = legacy / "slot_2.json"
            source.write_text("legacy-save", encoding="utf-8")
            storage = SaveStorage(documents_path=root / "documents", legacy_directory=legacy)
            target = storage.slot_path(0)
            target.parent.mkdir(parents=True)
            target.write_text("existing-save", encoding="utf-8")

            def validate(path):
                if Path(path).suffix == ".tmp":
                    raise ValueError("temporary validation failed")
                return object()

            with mock.patch(
                "application.save_storage.GameSaveFileAdapter.load",
                side_effect=validate,
            ):
                report = storage.prepare()

            self.assertEqual(target.read_text(encoding="utf-8"), "existing-save")
            self.assertEqual(source.read_text(encoding="utf-8"), "legacy-save")
            self.assertEqual(len(report.invalid_sources), 1)
            self.assertEqual(
                list(storage.save_directory.glob(".slot_2.json.*.tmp")),
                [],
            )

    def test_preexisting_target_is_never_removed_after_single_save_error(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            legacy = root / "save"
            legacy.mkdir()
            source = legacy / "eldoria_save.json"
            backup = legacy / "eldoria_save.json.bak"
            source.write_text("single-save", encoding="utf-8")
            backup.write_text("backup-save", encoding="utf-8")
            storage = SaveStorage(documents_path=root / "documents", legacy_directory=legacy)
            existing_target = storage.slot_path(0)
            existing_target.parent.mkdir(parents=True)
            existing_target.write_text("existing-save", encoding="utf-8")

            with mock.patch(
                "application.save_storage.GameSaveFileAdapter.load",
                side_effect=ValueError("source validation failed"),
            ):
                report = storage.prepare()

            self.assertEqual(existing_target.read_text(encoding="utf-8"), "existing-save")
            self.assertEqual(source.read_text(encoding="utf-8"), "single-save")
            self.assertEqual(backup.read_text(encoding="utf-8"), "backup-save")
            self.assertEqual(len(report.invalid_sources), 1)

    def test_unavailable_save_slots_do_not_touch_filesystem(self):
        with tempfile.TemporaryDirectory() as directory:
            blocked_path = Path(directory) / "must-not-be-created"
            screen = SaveSlotsScreen(
                None,
                lambda *_args: self.fail("save callback must not run"),
                save_available=False,
                unavailable_message="Documents kayıt klasörü kullanılamıyor.",
            )
            state = type(
                "State",
                (),
                {
                    "pressed": lambda self, action: action == "confirm",
                    "mouse_pos": None,
                    "mouse_clicked": False,
                },
            )()

            self.assertIsNone(screen.handle(state))
            self.assertEqual(
                screen.message,
                "Documents kayıt klasörü kullanılamıyor.",
            )
            self.assertFalse(blocked_path.exists())

    def test_save_slots_report_directory_creation_failure_without_callback(self):
        with tempfile.TemporaryDirectory() as directory:
            callback = mock.Mock()
            screen = SaveSlotsScreen(
                Path(directory) / "saves",
                callback,
                mode="save",
            )
            state = type(
                "State",
                (),
                {
                    "pressed": lambda self, action: action == "confirm",
                    "mouse_pos": None,
                    "mouse_clicked": False,
                },
            )()

            with mock.patch.object(
                Path,
                "mkdir",
                side_effect=OSError("access denied"),
            ):
                self.assertIsNone(screen.handle(state))

            callback.assert_not_called()
            self.assertIn("Kayıt klasörü hazırlanamadı", screen.message)

    def test_save_slots_report_directory_removed_after_open_without_callback(self):
        with tempfile.TemporaryDirectory() as directory:
            save_dir = Path(directory) / "saves"
            save_dir.mkdir()
            callback = mock.Mock()
            screen = SaveSlotsScreen(save_dir, callback, mode="save")
            save_dir.rmdir()
            save_dir.write_text("not a directory", encoding="utf-8")
            state = type(
                "State",
                (),
                {
                    "pressed": lambda self, action: action == "confirm",
                    "mouse_pos": None,
                    "mouse_clicked": False,
                },
            )()

            self.assertIsNone(screen.handle(state))

            callback.assert_not_called()
            self.assertIn("Kayıt klasörü hazırlanamadı", screen.message)

    def test_game_window_opens_when_storage_preparation_fails(self):
        class Backend:
            FULLSCREEN = 1

            class display:
                @staticmethod
                def set_caption(_title):
                    return None

            class font:
                @staticmethod
                def init():
                    return None

            @staticmethod
            def init():
                return None

        class Screen:
            def get_size(self):
                return (960, 640)

        class FailingStorage:
            def prepare(self):
                raise SaveStorageError("Documents kayıt klasörü kullanılamıyor.")

        with mock.patch.object(GameWindow, "_create_display", return_value=Screen()), \
                mock.patch("game_ui.game_window.Renderer"), \
                mock.patch("game_ui.game_window.InputMapper"), \
                mock.patch("game_ui.game_window.WindowManager") as window_manager, \
                mock.patch("game_ui.game_window.SaveSlotsScreen") as save_slots, \
                mock.patch("game_ui.game_window.CharacterCreationScreen"):
            window = GameWindow(
                service=object(),
                backend=Backend(),
                save_storage=FailingStorage(),
                fullscreen=False,
            )

        self.assertEqual(window.current, "menu")
        self.assertIsNone(window.save_path)
        self.assertIn("kullanılamıyor", window.notice)
        self.assertFalse(save_slots.call_args.kwargs["save_available"])
        window_manager.return_value.register.assert_called()

    def test_save_is_rejected_explicitly_when_storage_is_unavailable(self):
        service = mock.Mock()
        window = object.__new__(GameWindow)
        window.service = service
        window.save_path = None
        window._save_storage_failure = SaveStorageError(
            "Documents kayıt klasörü kullanılamıyor."
        )
        window.notice = ""
        window.notice_level = "info"
        window._notice_frames = 0

        window._save_game()

        self.assertIn("Kaydetme başarısız", window.notice)
        self.assertIn("kullanılamıyor", window.notice)
        service.save.assert_not_called()

    def test_continue_reports_stat_failure_without_loading(self):
        service = mock.Mock()
        window = object.__new__(GameWindow)
        window.service = service
        window.save_path = mock.Mock()
        window.save_path.is_file.return_value = True
        window.save_dir = mock.Mock()
        candidate = mock.Mock()
        candidate.is_file.return_value = True
        candidate.stat.side_effect = OSError("directory became inaccessible")
        window.save_dir.is_dir.return_value = True
        window.save_dir.glob.return_value = [candidate]
        window._save_storage_failure = None
        window.notice = ""
        window.notice_level = "info"
        window._notice_frames = 0

        result = window._continue_latest_save()

        self.assertIsNone(result)
        self.assertIn("kayıt dosyaları taranamadı", window.notice)
        service.load.assert_not_called()

    def test_overwrite_confirmation_rechecks_directory_before_callback(self):
        with tempfile.TemporaryDirectory() as directory:
            save_dir = Path(directory) / "saves"
            save_dir.mkdir()
            (save_dir / "slot_1.json").write_text("existing", encoding="utf-8")
            callback = mock.Mock()
            screen = SaveSlotsScreen(save_dir, callback, mode="save")
            state = type(
                "State",
                (),
                {
                    "pressed": lambda self, action: action == "confirm",
                    "mouse_pos": None,
                    "mouse_clicked": False,
                },
            )()

            self.assertIsNone(screen.handle(state))
            self.assertTrue(screen.pending_overwrite)

            (save_dir / "slot_1.json").unlink()
            save_dir.rmdir()
            save_dir.write_text("not a directory", encoding="utf-8")

            self.assertIsNone(screen.handle(state))

            callback.assert_not_called()
            self.assertTrue(screen.pending_overwrite)
            self.assertIn("Kayıt klasörü hazırlanamadı", screen.message)


    def test_backup_only_slot_is_treated_as_occupied_and_requires_confirmation(self):
        with tempfile.TemporaryDirectory() as directory:
            save_dir = Path(directory)
            backup = save_dir / "slot_1.json.bak"
            backup.write_text("recoverable-save", encoding="utf-8")
            callback = mock.Mock()
            screen = SaveSlotsScreen(save_dir, callback, mode="save")
            state = type(
                "State",
                (),
                {
                    "pressed": lambda self, action: action == "confirm",
                    "mouse_pos": None,
                    "mouse_clicked": False,
                },
            )()

            self.assertIsNone(screen.handle(state))
            self.assertTrue(screen.pending_overwrite)
            callback.assert_not_called()

            self.assertEqual(screen.handle(state), callback.return_value)
            callback.assert_called_once_with(0, save_dir / "slot_1.json", True)

    def test_overwrite_confirmation_is_repeated_when_slot_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            save_dir = Path(directory)
            target = save_dir / "slot_1.json"
            target.write_text("old", encoding="utf-8")
            callback = mock.Mock()
            screen = SaveSlotsScreen(save_dir, callback, mode="save")
            state = type(
                "State",
                (),
                {
                    "pressed": lambda self, action: action == "confirm",
                    "mouse_pos": None,
                    "mouse_clicked": False,
                },
            )()

            screen.handle(state)
            target.write_text("new save contents", encoding="utf-8")
            self.assertIsNone(screen.handle(state))

            self.assertTrue(screen.pending_overwrite)
            self.assertIn("Kayıt değişti", screen.message)
            callback.assert_not_called()

            screen.handle(state)
            callback.assert_called_once_with(0, target, True)

    def test_overwrite_confirmation_is_cancelled_when_slot_disappears(self):
        with tempfile.TemporaryDirectory() as directory:
            save_dir = Path(directory)
            target = save_dir / "slot_1.json"
            target.write_text("existing", encoding="utf-8")
            callback = mock.Mock()
            screen = SaveSlotsScreen(save_dir, callback, mode="save")
            state = type(
                "State",
                (),
                {
                    "pressed": lambda self, action: action == "confirm",
                    "mouse_pos": None,
                    "mouse_clicked": False,
                },
            )()

            screen.handle(state)
            target.unlink()
            self.assertIsNone(screen.handle(state))

            self.assertFalse(screen.pending_overwrite)
            self.assertIn("artık mevcut değil", screen.message)
            callback.assert_not_called()

    def test_confirmed_slot_delete_removes_primary_and_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            save_dir = Path(directory)
            primary = save_dir / "slot_1.json"
            backup = Path(f"{primary}.bak")
            primary.write_text("primary", encoding="utf-8")
            backup.write_text("backup", encoding="utf-8")
            screen = SaveSlotsScreen(save_dir, mock.Mock(), mode="load")
            delete_state = type(
                "State",
                (),
                {
                    "pressed": lambda self, action: action == "delete",
                    "mouse_pos": None,
                    "mouse_clicked": False,
                },
            )()
            confirm_state = type(
                "State",
                (),
                {
                    "pressed": lambda self, action: action == "confirm",
                    "mouse_pos": None,
                    "mouse_clicked": False,
                },
            )()

            screen.handle(delete_state)
            self.assertTrue(screen.pending_delete)
            screen.handle(confirm_state)

            self.assertFalse(primary.exists())
            self.assertFalse(backup.exists())
            self.assertIn("silindi", screen.message)

    def test_latest_save_finds_backup_only_slot(self):
        with tempfile.TemporaryDirectory() as directory:
            save_dir = Path(directory)
            primary = save_dir / "slot_4.json"
            Path(f"{primary}.bak").write_text("recoverable", encoding="utf-8")
            window = object.__new__(GameWindow)
            window.save_path = save_dir / "slot_1.json"
            window.save_dir = save_dir

            self.assertEqual(window._latest_save_path(), primary)


    def test_manual_save_helper_opens_slot_picker_instead_of_writing_directly(self):
        service = mock.Mock()
        slot_screen = mock.Mock()
        window = object.__new__(GameWindow)
        window.service = service
        window._save_storage_failure = None
        window.screens = {"save_slots": slot_screen}
        window.gameplay_active = True

        window._save_game()

        self.assertEqual(window.current, "save_slots")
        self.assertFalse(window.gameplay_active)
        self.assertEqual(slot_screen.mode, "save")
        self.assertEqual(slot_screen.return_target, "main")
        service.save.assert_not_called()

if __name__ == "__main__":
    unittest.main()
