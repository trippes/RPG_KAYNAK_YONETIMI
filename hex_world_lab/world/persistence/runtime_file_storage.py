"""UTF-8 runtime snapshot files with safe create and atomic replacement."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from hex_world_lab.world.map_definition import HexMapDefinition
from hex_world_lab.world.runtime import HexWorldRuntime
from .errors import MapFileAccessError, MapFileAlreadyExistsError, MapFileNotFoundError
from .runtime_deserializer import RuntimeMapSnapshot, deserialize_runtime_payload
from .runtime_errors import RuntimeFileWriteError, RuntimeJSONDecodeError
from .runtime_serializer import serialize_runtime


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON numeric constant {value!r} is not allowed")


def load_runtime_file(
    path: str | os.PathLike[str], map_definition: HexMapDefinition
) -> RuntimeMapSnapshot:
    file_path = Path(path)
    try:
        text = file_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise MapFileNotFoundError(f"runtime snapshot not found: {file_path}") from exc
    except (OSError, UnicodeError) as exc:
        raise MapFileAccessError(f"could not read runtime snapshot {file_path}: {exc}") from exc
    try:
        payload = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_constant,
        )
    except (json.JSONDecodeError, ValueError) as exc:
        raise RuntimeJSONDecodeError(f"invalid runtime snapshot JSON: {exc}") from exc
    return deserialize_runtime_payload(payload, map_definition)


def save_runtime_file(
    runtime: HexWorldRuntime,
    map_definition: HexMapDefinition,
    path: str | os.PathLike[str],
    *,
    mode: str = "create",
) -> None:
    if mode not in {"create", "replace"}:
        raise ValueError("mode must be 'create' or 'replace'")
    file_path = Path(path)
    try:
        text = serialize_runtime(runtime, map_definition)
    except Exception:
        raise
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=file_path.parent,
            prefix=f".{file_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())

        if mode == "create":
            # Hard-link publication is atomic and fails if the destination exists.
            os.link(temporary_path, file_path)
            temporary_path.unlink()
            temporary_path = None
        else:
            os.replace(temporary_path, file_path)
            temporary_path = None
    except FileExistsError as exc:
        raise MapFileAlreadyExistsError(f"runtime snapshot already exists: {file_path}") from exc
    except OSError as exc:
        raise RuntimeFileWriteError(f"could not safely write runtime snapshot {file_path}: {exc}") from exc
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass


def restore_runtime_file(
    runtime: HexWorldRuntime,
    map_definition: HexMapDefinition,
    path: str | os.PathLike[str],
) -> RuntimeMapSnapshot:
    if not isinstance(runtime, HexWorldRuntime):
        raise TypeError("runtime must be a HexWorldRuntime")
    if runtime.world_id != map_definition.world_id:
        from .runtime_errors import RuntimeWorldMismatchError
        raise RuntimeWorldMismatchError("runtime and target map belong to different worlds", "$.world_id")
    # Decode and validate everything before the single replacement operation.
    snapshot = load_runtime_file(path, map_definition)
    runtime.replace_map_overrides(map_definition.map_id, snapshot.overrides)
    return snapshot
