"""Safe UTF-8 file storage for content libraries and map-content documents."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from .codec import (
    deserialize_library,
    deserialize_map_content,
    serialize_library,
    serialize_map_content,
)
from .errors import ContentPersistenceError


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def _constant(value):
    raise ValueError(f"non-standard JSON constant {value!r} is not allowed")


def _load(path, decoder):
    target = Path(path)
    try:
        raw = json.loads(
            target.read_text(encoding="utf-8"), object_pairs_hook=_pairs, parse_constant=_constant
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise ContentPersistenceError(f"could not read or parse {target}: {exc}") from exc
    return decoder(raw)


def load_library_file(path):
    return _load(path, deserialize_library)


def load_map_content_file(path):
    return _load(path, deserialize_map_content)


def _save(value, path, serializer, mode):
    if mode not in {"create", "replace"}:
        raise ValueError("mode must be 'create' or 'replace'")
    target = Path(path)
    if not target.parent.is_dir():
        raise ContentPersistenceError(f"target directory does not exist: {target.parent}")
    if mode == "create" and target.exists():
        raise FileExistsError(target)
    content = serializer(value)
    temp = None
    try:
        fd, name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
        temp = Path(name)
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        if mode == "create":
            try:
                os.link(temp, target)
            except FileExistsError:
                raise
            temp.unlink()
        else:
            os.replace(temp, target)
        temp = None
        return target
    except OSError as exc:
        raise ContentPersistenceError(f"could not safely save {target}: {exc}") from exc
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)


def save_library_file(library, path, *, mode="create"):
    return _save(library, path, serialize_library, mode)


def save_map_content_file(document, path, *, mode="create"):
    return _save(document, path, serialize_map_content, mode)
