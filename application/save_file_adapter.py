"""Atomic filesystem boundary for application-level game saves."""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Union

from .save_codec import SaveJsonCodec
from .save_document import GameSaveDocument


PathLike = Union[str, os.PathLike[str]]


class SaveFileError(OSError):
    """Base error for unified save filesystem operations."""


class SaveFileReadError(SaveFileError):
    """The unified save file could not be read."""


class SaveFileWriteError(SaveFileError):
    """The unified save file could not be written atomically."""


class GameSaveFileAdapter:
    """Read and atomically replace one unified game save file."""

    @staticmethod
    def save(document: GameSaveDocument, path: PathLike) -> Path:
        if not isinstance(document, GameSaveDocument):
            raise TypeError("document must be GameSaveDocument.")

        target = Path(path)
        payload = SaveJsonCodec.encode(document)
        temporary_path: Path | None = None
        try:
            if target.exists():
                shutil.copy2(target, GameSaveFileAdapter.backup_path(target))
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
            os.replace(temporary_path, target)
            temporary_path = None
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
    def load(path: PathLike) -> GameSaveDocument:
        target = Path(path)
        try:
            payload = target.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            raise SaveFileReadError(
                f"Could not read game save file: {target}"
            ) from error
        return SaveJsonCodec.decode(payload)
