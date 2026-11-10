"""Cross-thread and cross-process locking for individual save slots."""

from __future__ import annotations

import os
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

_registry_guard = threading.Lock()
_path_locks: dict[str, threading.RLock] = {}


def _thread_lock_key(path: Path) -> str:
    return os.path.normcase(os.path.abspath(os.fspath(path)))


def _get_thread_lock(path: Path) -> threading.RLock:
    key = _thread_lock_key(path)
    with _registry_guard:
        lock = _path_locks.get(key)
        if lock is None:
            lock = threading.RLock()
            _path_locks[key] = lock
        return lock


@contextmanager
def save_path_lock(path: str | os.PathLike[str]) -> Iterator[None]:
    """Serialize access to one save and its backup across threads and processes.

    The sidecar lock file is intentionally persistent: deleting it after release
    can let different processes lock different file objects for the same slot.
    The operating system releases the actual lock when a process exits.
    """
    target = Path(os.path.abspath(os.fspath(path)))
    target.parent.mkdir(parents=True, exist_ok=True)

    with _get_thread_lock(target):
        lock_path = target.with_name(f".{target.name}.lock")
        with lock_path.open("a+b") as lock_file:
            acquired = False
            try:
                if os.name == "nt":
                    import msvcrt

                    lock_file.seek(0, os.SEEK_END)
                    if lock_file.tell() == 0:
                        lock_file.write(bytes((0,)))
                        lock_file.flush()

                    while not acquired:
                        lock_file.seek(0)
                        try:
                            msvcrt.locking(
                                lock_file.fileno(),
                                msvcrt.LK_NBLCK,
                                1,
                            )
                            acquired = True
                        except OSError:
                            time.sleep(0.05)
                else:
                    import fcntl

                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
                    acquired = True

                yield
            finally:
                if acquired:
                    lock_file.seek(0)
                    if os.name == "nt":
                        import msvcrt

                        msvcrt.locking(
                            lock_file.fileno(),
                            msvcrt.LK_UNLCK,
                            1,
                        )
                    else:
                        import fcntl

                        fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
