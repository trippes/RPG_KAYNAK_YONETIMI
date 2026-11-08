"""User-owned save storage and migration from the legacy project directory."""

from __future__ import annotations

import ctypes
import json
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .save_file_adapter import GameSaveFileAdapter


class _Guid(ctypes.Structure):
    _fields_ = (
        ("data1", ctypes.c_uint32),
        ("data2", ctypes.c_uint16),
        ("data3", ctypes.c_uint16),
        ("data4", ctypes.c_ubyte * 8),
    )


class SaveStorageError(OSError):
    """The user save directory could not be prepared."""


class SaveTargetExistsError(FileExistsError):
    """A migration target appeared before the atomic placement completed."""


def documents_directory() -> Path:
    """Return the actual Windows Documents directory, including OneDrive moves."""
    if os.name == "nt":
        folder_id = _Guid(
            0xFDD39AD0,
            0x238F,
            0x46AF,
            (ctypes.c_ubyte * 8)(0xAD, 0xB4, 0x6C, 0x85, 0x48, 0x03, 0x69, 0xC7),
        )
        path_pointer = ctypes.c_wchar_p()
        result = ctypes.windll.shell32.SHGetKnownFolderPath(
            ctypes.byref(folder_id),
            0,
            None,
            ctypes.byref(path_pointer),
        )
        if result != 0:
            raise SaveStorageError(
                f"Windows Belgelerim klasörü bulunamadı (hata kodu: {result})."
            )
        try:
            return Path(path_pointer.value)
        finally:
            ctypes.windll.ole32.CoTaskMemFree(path_pointer)
    return Path.home() / "Documents"


@dataclass(frozen=True)
class MigrationReport:
    copied: tuple[Path, ...] = ()
    conflicts: tuple[str, ...] = ()
    invalid_sources: tuple[str, ...] = ()


class SaveStorage:
    """Own the ten user save slots and perform a safe, repeatable migration."""

    SLOT_COUNT = 10

    def __init__(
        self,
        documents_path: Path | None = None,
        legacy_directory: Path | None = None,
        *,
        documents_provider: Callable[[], Path] = documents_directory,
    ) -> None:
        self.documents_path = Path(documents_path) if documents_path is not None else None
        self.legacy_directory = (
            Path(legacy_directory)
            if legacy_directory is not None
            else Path(__file__).resolve().parents[1] / "save"
        )
        self._documents_provider = documents_provider
        self.migration_report = MigrationReport()

    @property
    def save_directory(self) -> Path:
        documents = self.documents_path
        if documents is None:
            documents = Path(self._documents_provider())
        return documents / "My Games" / "Eldoria" / "Saves"

    def prepare(self) -> MigrationReport:
        target_directory = self.save_directory
        try:
            target_directory.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            raise SaveStorageError(
                f"Kayıt klasörü oluşturulamadı: {target_directory}"
            ) from error

        copied: list[Path] = []
        conflicts: list[str] = []
        invalid_sources: list[str] = []
        for index in range(1, self.SLOT_COUNT + 1):
            source = self.legacy_directory / f"slot_{index}.json"
            target = target_directory / source.name
            if not source.is_file() or target.exists():
                if source.is_file() and target.exists() and not _same_file(source, target):
                    conflicts.append(
                        f"Slot {index}: eski ve yeni konumda farklı kayıtlar var; "
                        "yeni kayıt korunmuştur."
                    )
                continue
            try:
                GameSaveFileAdapter.load(source)
                _copy_atomically(source, target)
            except SaveTargetExistsError:
                conflicts.append(
                    f"Slot {index}: taşıma sırasında hedef kayıt oluşturuldu; "
                    "mevcut kayıt korunmuştur."
                )
                continue
            except (OSError, UnicodeError, ValueError, TypeError) as error:
                invalid_sources.append(
                    f"Slot {index}: eski kayıt taşınamadı veya doğrulanamadı ({error})."
                )
                continue
            copied.append(target)

        legacy_single = self.legacy_directory / "eldoria_save.json"
        if legacy_single.is_file():
            empty_target: Path | None = None
            try:
                GameSaveFileAdapter.load(legacy_single)
                if not any(
                    target.is_file() and _same_save_document(legacy_single, target)
                    for target in self._slot_paths(target_directory)
                ):
                    empty_target = next(
                        (
                            target
                            for target in self._slot_paths(target_directory)
                            if not target.exists()
                        ),
                        None,
                    )
                    if empty_target is None:
                        conflicts.append(
                            "eldoria_save.json: tüm kayıt yuvaları dolu; "
                            "hiçbir kayıt değiştirilmedi."
                        )
                    else:
                        _copy_atomically(legacy_single, empty_target)
                        copied.append(empty_target)
            except SaveTargetExistsError:
                conflicts.append(
                    "eldoria_save.json: taşıma sırasında hedef kayıt oluşturuldu; "
                    "mevcut kayıt korunmuştur."
                )
            except (OSError, UnicodeError, ValueError, TypeError) as error:
                invalid_sources.append(
                    f"eldoria_save.json: eski tekil kayıt taşınamadı veya "
                    f"doğrulanamadı ({error})."
                )

        self.migration_report = MigrationReport(
            copied=tuple(copied),
            conflicts=tuple(conflicts),
            invalid_sources=tuple(invalid_sources),
        )
        return self.migration_report

    def slot_path(self, index: int) -> Path:
        if not 0 <= index < self.SLOT_COUNT:
            raise ValueError(f"Geçersiz kayıt yuvası: {index + 1}")
        return self.save_directory / f"slot_{index + 1}.json"

    def _slot_paths(self, directory: Path) -> tuple[Path, ...]:
        return tuple(directory / f"slot_{index}.json" for index in range(1, self.SLOT_COUNT + 1))


def _same_file(first: Path, second: Path) -> bool:
    try:
        return first.read_bytes() == second.read_bytes()
    except OSError:
        return False


def _same_save_document(first: Path, second: Path) -> bool:
    try:
        GameSaveFileAdapter.load(first)
        GameSaveFileAdapter.load(second)
        return _canonical_json(first) == _canonical_json(second)
    except (OSError, UnicodeError, ValueError, TypeError):
        return False


def _canonical_json(path: Path) -> str:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return path.read_bytes().decode("utf-8", errors="surrogateescape")
    return json.dumps(
        data,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


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
        GameSaveFileAdapter.load(temporary_path)
        try:
            os.link(temporary_path, target)
        except FileExistsError as error:
            raise SaveTargetExistsError(
                f"Migration target already exists: {target}"
            ) from error
        temporary_path.unlink()
        temporary_path = None
    except SaveTargetExistsError:
        raise
    except OSError as error:
        raise SaveStorageError(
            f"Kayıt slotu güvenli biçimde taşınamadı: {source}"
        ) from error
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass
