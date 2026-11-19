"""UTF-8 map file storage with duplicate-key rejection and atomic replacement."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from hex_world_lab.world.map_definition import HexMapDefinition
from .errors import (
    MapFileAccessError,
    MapFileAlreadyExistsError,
    MapFileNotFoundError,
    MapFileWriteError,
    MapJSONDecodeError,
)
from .map_deserializer import deserialize_map_payload
from .map_serializer import serialize_map


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON numeric constant {value!r} is not allowed")


def load_map_file(path: str | os.PathLike[str]) -> HexMapDefinition:
    """Read, parse, validate, and construct a map without registry side effects."""
    file_path = Path(path)
    try:
        text = file_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise MapFileNotFoundError(f"map file not found: {file_path}") from exc
    except (OSError, UnicodeError) as exc:
        raise MapFileAccessError(f"could not read map file {file_path}: {exc}") from exc
    try:
        payload = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_constant,
        )
    except (json.JSONDecodeError, ValueError) as exc:
        raise MapJSONDecodeError(f"invalid JSON in {file_path}: {exc}") from exc
    return deserialize_map_payload(payload)


def save_map_file(
    map_definition: HexMapDefinition,
    path: str | os.PathLike[str],
    *,
    mode: str = "create",
) -> Path:
    """Atomically save a map; mode is explicitly 'create' or 'replace'."""
    if mode not in {"create", "replace"}:
        raise ValueError("mode must be 'create' or 'replace'")
    if not isinstance(map_definition, HexMapDefinition):
        raise TypeError("map_definition must be a HexMapDefinition")
    target = Path(path)
    parent = target.parent
    if not parent.exists() or not parent.is_dir():
        raise MapFileWriteError(f"target directory does not exist: {parent}")
    if mode == "create" and target.exists():
        raise MapFileAlreadyExistsError(f"map file already exists: {target}")

    content = serialize_map(map_definition)
    temporary_path: Path | None = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{target.name}.", suffix=".tmp", dir=parent
        )
        temporary_path = Path(temporary_name)
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        if mode == "create":
            # Hard-link creation is atomic and fails if another writer won the race.
            try:
                os.link(temporary_path, target)
            except FileExistsError as exc:
                raise MapFileAlreadyExistsError(f"map file already exists: {target}") from exc
            temporary_path.unlink()
            temporary_path = None
        else:
            os.replace(temporary_path, target)
            temporary_path = None
        return target
    except MapFileAlreadyExistsError:
        raise
    except OSError as exc:
        raise MapFileWriteError(f"could not safely write map file {target}: {exc}") from exc
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass
