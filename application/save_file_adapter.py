"""Atomic filesystem boundary for application-level game saves."""

import os
import shutil
import stat
import tempfile
import time
from pathlib import Path
from typing import Union

from .save_codec import SaveJsonCodec
from .save_document import GameSaveDocument, SaveDocumentError, UnsupportedSaveSchemaError
from .save_lock import save_path_lock


PathLike = Union[str, os.PathLike[str]]
ORPHAN_TEMP_MAX_AGE_SECONDS = 7 * 24 * 60 * 60

from core.errors import RPGError

class SaveFileError(OSError, RPGError):
    """Base error for unified save filesystem operations."""


class SaveFileReadError(SaveFileError):
    """The unified save file and its recovery copy could not be read."""


class SaveFileWriteError(SaveFileError):
    """The unified save file could not be written atomically."""


class GameSaveFileAdapter:
    """Read, recover and atomically replace one unified game save file."""

    @staticmethod
    def save(document: GameSaveDocument, path: PathLike) -> Path:
        if not isinstance(document, GameSaveDocument):
            raise TypeError("document must be GameSaveDocument.")

        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with save_path_lock(target):
            return GameSaveFileAdapter._save_locked(document, target)

    @staticmethod
    def _save_locked(document: GameSaveDocument, target: Path) -> Path:
        payload = SaveJsonCodec.encode(document)
        temporary_path: Path | None = None
        try:
            GameSaveFileAdapter._cleanup_orphaned_temporary_files(
                target,
                older_than_seconds=ORPHAN_TEMP_MAX_AGE_SECONDS,
                now=None,
            )
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=target.parent,
                prefix=f".{target.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary:
                temporary_path = Path(temporary.name)
                temporary.write(payload)
                temporary.flush()
                os.fsync(temporary.fileno())

            # Validate the staged bytes before touching either the primary save
            # or its recovery copy.
            GameSaveFileAdapter._read_document(temporary_path)

            if target.exists():
                try:
                    GameSaveFileAdapter._read_document(target)
                except (OSError, ValueError, TypeError):
                    # Never replace a potentially good backup with a corrupt
                    # primary file. The new staged document can still replace it.
                    pass
                else:
                    GameSaveFileAdapter._copy_atomically(
                        target,
                        GameSaveFileAdapter.backup_path(target),
                    )

            os.replace(temporary_path, target)
            temporary_path = None
            GameSaveFileAdapter._fsync_directory(target.parent)
            return target
        except OSError as error:
            raise SaveFileWriteError(
                f"Could not atomically write game save file: {target}"
            ) from error
        finally:
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    pass

    @staticmethod
    def backup_path(path: PathLike) -> Path:
        """Return the recoverable backup path for a save slot."""
        target = Path(path)
        return target.with_name(f"{target.name}.bak")

    @staticmethod
    def cleanup_orphaned_temporary_files(
        path: PathLike,
        *,
        older_than_seconds: int = ORPHAN_TEMP_MAX_AGE_SECONDS,
        now: float | None = None,
    ) -> tuple[Path, ...]:
        """Remove only old regular temp files belonging to this save and backup.

        Cleanup shares the slot lock with save/load so it cannot remove staging
        files while another process is actively replacing the same slot.
        """
        if older_than_seconds < 1:
            raise ValueError("older_than_seconds must be at least 1.")

        target = Path(path)
        with save_path_lock(target):
            return GameSaveFileAdapter._cleanup_orphaned_temporary_files(
                target,
                older_than_seconds=older_than_seconds,
                now=now,
            )

    @staticmethod
    def _cleanup_orphaned_temporary_files(
        target: Path,
        *,
        older_than_seconds: int,
        now: float | None,
    ) -> tuple[Path, ...]:
        directory = target.parent
        if not directory.is_dir():
            return ()

        backup = GameSaveFileAdapter.backup_path(target)
        prefixes = (f".{target.name}.", f".{backup.name}.")
        cutoff = (time.time() if now is None else now) - older_than_seconds
        removed: list[Path] = []

        for candidate in directory.iterdir():
            name = candidate.name
            if not name.endswith(".tmp") or not name.startswith(prefixes):
                continue
            try:
                metadata = candidate.lstat()
                if not stat.S_ISREG(metadata.st_mode):
                    continue
                if metadata.st_mtime > cutoff:
                    continue
                candidate.unlink()
                removed.append(candidate)
            except FileNotFoundError:
                # Another cleanup or process already removed the candidate.
                continue

        if removed:
            GameSaveFileAdapter._fsync_directory(directory)
        return tuple(removed)

    @staticmethod
    def load(path: PathLike) -> GameSaveDocument:
        target = Path(path)
        with save_path_lock(target):
            return GameSaveFileAdapter._load_locked(target)

    @staticmethod
    def _load_locked(target: Path) -> GameSaveDocument:
        primary_error = None
        try:
            return GameSaveFileAdapter._read_document(target)
        except SaveFileReadError as error:
            primary_error = error
        except UnsupportedSaveSchemaError:
            # A future save version is not corruption; never load an older backup.
            raise
        except SaveDocumentError as error:
            primary_error = error

        backup = GameSaveFileAdapter.backup_path(target)
        try:
            document = GameSaveFileAdapter._read_document(backup)
        except (OSError, ValueError, TypeError):
            raise primary_error

        # A valid backup can be loaded even if repairing the primary fails.
        try:
            GameSaveFileAdapter._copy_atomically(backup, target)
        except OSError:
            pass
        return document

    @staticmethod
    def _read_document(path: PathLike) -> GameSaveDocument:
        target = Path(path)
        try:
            payload = target.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            raise SaveFileReadError(
                f"Could not read game save file: {target}"
            ) from error
        return SaveJsonCodec.decode(payload)

    @staticmethod
    def _fsync_directory(directory: Path) -> None:
        """Persist directory-entry changes where directory fsync is supported."""
        if os.name != "posix":
            return

        flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        descriptor = os.open(directory, flags)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)

    @staticmethod
    def _copy_atomically(source: Path, target: Path) -> None:
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb",
                dir=target.parent,
                prefix=f".{target.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary:
                temporary_path = Path(temporary.name)
                with source.open("rb") as source_file:
                    shutil.copyfileobj(source_file, temporary)
                temporary.flush()
                os.fsync(temporary.fileno())

            GameSaveFileAdapter._read_document(temporary_path)
            os.replace(temporary_path, target)
            temporary_path = None
            GameSaveFileAdapter._fsync_directory(target.parent)
        finally:
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    pass
