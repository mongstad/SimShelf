from __future__ import annotations

import hashlib
import mimetypes
import os
import socket
import tempfile
import uuid
from pathlib import Path

from .common import clean_name, contained, match, now
from .source import blob_path

MAX_SCAN_FILES = 20000


def output_inventory(simulation: dict) -> tuple[dict, list[str]]:
    root = contained(Path(simulation["root"]), simulation["config"]["output_dir"])
    result, errors = {}, []
    if not root.exists():
        return result, errors
    for directory, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if not (Path(directory) / d).is_symlink())
        for name in sorted(files):
            path = Path(directory) / name
            if path.is_symlink() or not path.is_file():
                continue
            if len(result) >= MAX_SCAN_FILES:
                return result, [f"Stopped after {MAX_SCAN_FILES:,} files. Narrow the output folder."]
            try:
                s = path.stat()
                result[path.relative_to(root).as_posix()] = {"size": s.st_size, "mtime_ns": s.st_mtime_ns}
            except OSError as exc:
                errors.append(f"{name}: {exc}")
    return result, errors


def capture_action(relative: str, config: dict) -> str:
    return next((r["action"] for r in config["rules"] if match(relative, r["pattern"])), "ignore")


def preview(simulation: dict) -> dict:
    inventory, errors = output_inventory(simulation)
    files, copied = [], 0
    for name, metadata in inventory.items():
        action = capture_action(name, simulation["config"])
        reason = None
        if action == "copy":
            if metadata["size"] > simulation["config"]["max_file_mb"] * 1024**2:
                reason = "Exceeds per-file copy limit"
            elif copied + metadata["size"] > simulation["config"]["max_run_mb"] * 1024**2:
                reason = "Exceeds per-run copy budget"
            else:
                copied += metadata["size"]
        files.append({"path": name, **metadata, "action": action, "reason": reason})
    return {"files": files[:1000], "total_files": len(files), "copy_bytes": copied, "errors": errors, "truncated": len(files) > 1000, "counts": {action: sum(f["action"] == action for f in files) for action in ("copy", "reference", "ignore")}}


def save_file(store, run_id: str, path: Path, *, policy="copy", name=None, caption="", limit=25 * 1024**2, automatic=False) -> dict:
    path = path.expanduser().absolute()
    if path.is_symlink() or not path.is_file():
        raise ValueError("Only regular files can be attached; symbolic links are excluded")
    before = path.stat()
    artifact = {"id": uuid.uuid4().hex, "run_id": run_id, "name": name or path.name, "policy": policy, "size": before.st_size, "mtime_ns": before.st_mtime_ns, "original_path": str(path), "host": socket.gethostname(), "created_at": now(), "caption": caption, "media_type": mimetypes.guess_type(name or path.name)[0] or "application/octet-stream", "automatic": automatic}
    if policy == "copy":
        if before.st_size > limit:
            raise ValueError(f"{path.name} exceeds the copy limit ({limit // 1024**2} MB)")
        temporary_dir = store.path / "staging"
        temporary_dir.mkdir(exist_ok=True)
        fd, temporary_name = tempfile.mkstemp(dir=temporary_dir)
        temporary = Path(temporary_name)
        total, digest = 0, hashlib.sha256()
        try:
            with path.open("rb") as source, os.fdopen(fd, "wb") as target:
                while block := source.read(1024 * 1024):
                    total += len(block)
                    if total > limit:
                        raise ValueError("File grew beyond the copy limit")
                    digest.update(block)
                    target.write(block)
                target.flush()
                os.fsync(target.fileno())
            after = path.stat()
            if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                raise ValueError("File changed during capture; write final files atomically or attach after closing them")
            key = digest.hexdigest()
            destination = blob_path(store.path, key)
            destination.parent.mkdir(parents=True, exist_ok=True)
            os.replace(temporary, destination)
            artifact["blob"] = key
        finally:
            temporary.unlink(missing_ok=True)
    if automatic:
        identity = f"{run_id}:{artifact['original_path']}:{artifact.get('blob', str(before.st_mtime_ns))}:{policy}"
        artifact["id"] = hashlib.sha256(identity.encode()).hexdigest()[:32]
    store.emit(run_id, "artifact", artifact)
    return artifact


def capture_outputs(store, run_id: str, simulation: dict, before: dict | None = None) -> dict:
    inventory, errors = output_inventory(simulation)
    root = contained(Path(simulation["root"]), simulation["config"]["output_dir"])
    counts = {"copied": 0, "referenced": 0, "ignored": 0, "unchanged": 0, "skipped": 0}
    copied = 0
    for name, metadata in inventory.items():
        if before is not None and before.get(name) == metadata:
            counts["unchanged"] += 1
            continue
        action = capture_action(name, simulation["config"])
        if action == "ignore":
            counts["ignored"] += 1
            continue
        try:
            if action == "copy" and copied + metadata["size"] > simulation["config"]["max_run_mb"] * 1024**2:
                raise ValueError("Per-run copy budget exceeded")
            artifact = save_file(store, run_id, contained(root, name), policy=action, name=name, limit=int(simulation["config"]["max_file_mb"] * 1024**2), automatic=True)
            counts["copied" if action == "copy" else "referenced"] += 1
            if action == "copy":
                copied += artifact["size"]
        except (OSError, ValueError) as exc:
            counts["skipped"] += 1
            errors.append(f"{name}: {exc}")
            store.emit(run_id, "artifact", {"id": uuid.uuid4().hex, "run_id": run_id, "name": name, "policy": "skipped", "size": metadata["size"], "reason": str(exc), "created_at": now(), "media_type": mimetypes.guess_type(name)[0] or "application/octet-stream", "caption": ""})
    return {"capture_status": "partial" if errors else "complete", "capture_errors": errors, "capture_counts": counts, "capture_bytes": copied}
