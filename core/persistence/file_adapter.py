"""Filesystem boundary for persistence documents.

The adapter owns only UTF-8 file access and atomic replacement. JSON parsing
and persistence schema validation remain in ``JsonPersistenceCodec`` and
``PersistenceDocument`` respectively.
"""

import os
import tempfile
from pathlib import Path
from typing import Union

from .contracts import PersistenceDocument
from .json_codec import JsonPersistenceCodec


PathLike = Union[str, os.PathLike[str]]


class PersistenceFileError(OSError):
    """Base error for filesystem access failures."""


class PersistenceFileReadError(PersistenceFileError):
    """The persistence document could not be read from the filesystem."""


class PersistenceFileWriteError(PersistenceFileError):
    """The persistence document could not be written atomically."""


class FilePersistenceAdapter:
    """Read and atomically write ``PersistenceDocument`` JSON files."""

    @staticmethod
    def save(document: PersistenceDocument, path: PathLike) -> Path:
        if not isinstance(document, PersistenceDocument):
            raise TypeError("document must be PersistenceDocument.")

        target = Path(path)
        payload = JsonPersistenceCodec.encode(document)
        temporary_path: Path | None = None

        try:
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
            raise PersistenceFileWriteError(
                f"Could not atomically write persistence file: {target}"
            ) from error
        finally:
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    pass

    @staticmethod
    def load(path: PathLike) -> PersistenceDocument:
        target = Path(path)
        try:
            payload = target.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            raise PersistenceFileReadError(
                f"Could not read persistence file: {target}"
            ) from error
        return JsonPersistenceCodec.decode(payload)
