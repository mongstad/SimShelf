"""Short, reentrant, cross-process exclusion for managed file lifetimes."""
from __future__ import annotations

import os
import threading
from contextlib import contextmanager
from functools import wraps
from pathlib import Path

_local = threading.local()


@contextmanager
def workspace_lock(path: Path):
    # Separate open file descriptions conflict even within one process. Nested
    # operations in the same thread reuse the outer lock, including Store copies.
    import fcntl
    key = str(path.resolve())
    held = getattr(_local, "held", None)
    if held is None:
        held = _local.held = set()
    if key in held:
        yield
        return
    fd = os.open(path / ".managed-data.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        held.add(key)
        try:
            yield
        finally:
            held.remove(key)
    finally:
        os.close(fd)


def locked_store(function):
    @wraps(function)
    def wrapped(store, *args, **kwargs):
        with workspace_lock(store.path):
            return function(store, *args, **kwargs)
    return wrapped


def locked_recorder(function):
    @wraps(function)
    def wrapped(recorder, *args, **kwargs):
        with workspace_lock(recorder.store.path):
            return function(recorder, *args, **kwargs)
    return wrapped
