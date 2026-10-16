from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def json_text(value) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":"))


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".pending-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "simulation"


def match(path: str, pattern: str) -> bool:
    return fnmatch.fnmatchcase(path, pattern) or (pattern.startswith("**/") and fnmatch.fnmatchcase(path, pattern[3:]))


def contained(root: Path, relative: str) -> Path:
    root = root.resolve()
    result = (root / relative).resolve()
    if not result.is_relative_to(root):
        raise ValueError("Path must stay inside its registered folder")
    return result


def clean_name(name: str) -> str:
    return Path(name.replace("\\", "/")).name[:200] or "attachment"


def default_workspace() -> Path:
    value = os.environ.get("SIMSHELF_HOME")
    return Path(value).expanduser().resolve() if value else (Path.home() / ".local/share/simshelf").resolve()


def process_identity(pid: int) -> str | None:
    """Linux start ticks distinguish an original recorder from a reused PID."""
    try:
        stat = Path(f"/proc/{pid}/stat").read_text()
        return stat[stat.rfind(")") + 2:].split()[19]
    except (OSError, IndexError):
        return None


def process_alive(pid: int, identity: str | None = None) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    current = process_identity(pid)
    return not (identity and current and current != identity)
