from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import stat
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

from .common import json_text, now
from .source import blob_path, read_snapshot
from .store import Store


def file_digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def create_backup(store: Store, destination: Path) -> Path:
    destination = destination.expanduser().resolve()
    if destination.exists():
        raise ValueError("Backup destination already exists; choose a new filename")
    destination.parent.mkdir(parents=True, exist_ok=True)
    report = store.reconcile()
    if report["errors"]:
        raise ValueError("Resolve pending journal errors before backing up: " + "; ".join(report["errors"][:3]))
    with tempfile.TemporaryDirectory(prefix="simshelf-backup-") as temp:
        temp = Path(temp)
        snapshot_db = temp / "simshelf.sqlite3"
        with store.connection() as source, sqlite3.connect(snapshot_db) as target:
            source.backup(target)
        with sqlite3.connect(snapshot_db) as conn:
            runs = [json.loads(r[0]) for r in conn.execute("SELECT data FROM runs")]
            artifacts = [json.loads(r[0]) for r in conn.execute("SELECT data FROM artifacts")]
        files = {"simshelf.sqlite3": snapshot_db}
        keys = {a["blob"] for a in artifacts if a.get("blob")}
        for run in runs:
            snapshot = read_snapshot(store.path, run["snapshot_id"])
            files[f"snapshots/{snapshot['id']}.json"] = store.path / "snapshots" / f"{snapshot['id']}.json"
            keys.update(f["blob"] for f in snapshot["files"])
            for name in ("stdout.log", "stderr.log"):
                source = store.path / "logs" / run["id"] / name
                if source.is_file():
                    # Freeze the log before checksumming; recording may continue during backup.
                    frozen = temp / run["id"] / name
                    frozen.parent.mkdir(exist_ok=True)
                    shutil.copyfile(source, frozen)
                    files[f"logs/{run['id']}/{name}"] = frozen
        for key in keys:
            files[f"blobs/{key[:2]}/{key}"] = blob_path(store.path, key)
        for name, file in files.items():
            if not file.is_file():
                raise ValueError(f"Cannot back up a missing retained file: {name}")
        manifest = {"format": "simshelf-backup", "version": 1, "created_at": now(), "run_count": len(runs), "references_included": False, "files": {name: file_digest(path) for name, path in files.items()}}
        staged = temp / "archive.zip"
        with zipfile.ZipFile(staged, "w", zipfile.ZIP_DEFLATED, compresslevel=3) as archive:
            archive.writestr("manifest.json", json_text(manifest))
            for name, file in files.items():
                archive.write(file, name)
        # Exclusive creation preserves existing backups even if another caller races us.
        with destination.open("xb") as target, staged.open("rb") as source:
            shutil.copyfileobj(source, target)
    return destination


def restore_backup(archive_path: Path, target: Path) -> Store:
    target = target.expanduser().resolve()
    if target.exists() and any(target.iterdir()):
        raise ValueError("Restore requires a new or empty workspace folder")
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".simshelf-restore-", dir=target.parent) as temporary:
        temporary = Path(temporary)
        with zipfile.ZipFile(archive_path) as archive:
            entries = archive.infolist()
            names = [entry.filename for entry in entries]
            if len(names) != len(set(names)) or len(names) > 100000:
                raise ValueError("Backup contains duplicate paths or too many files")
            if sum(e.file_size for e in entries) > 10 * 1024**3:
                raise ValueError("Backup exceeds the 10 GB restore limit")
            if "manifest.json" not in names or archive.getinfo("manifest.json").file_size > 16 * 1024**2:
                raise ValueError("Missing or oversized backup manifest")
            manifest = json.loads(archive.read("manifest.json"))
            if manifest.get("format") != "simshelf-backup" or manifest.get("version") != 1:
                raise ValueError("Unsupported backup format")
            expected = manifest.get("files", {})
            if set(expected) != set(names) - {"manifest.json"} or "simshelf.sqlite3" not in expected:
                raise ValueError("Backup manifest does not match archive contents")
            for entry in entries:
                if entry.filename == "manifest.json":
                    continue
                relative = PurePosixPath(entry.filename)
                if relative.is_absolute() or ".." in relative.parts or "\\" in entry.filename or not relative.parts or (relative.parts[0] not in {"blobs", "snapshots", "logs"} and entry.filename != "simshelf.sqlite3"):
                    raise ValueError("Unsafe path in backup")
                if stat.S_ISLNK(entry.external_attr >> 16):
                    raise ValueError("Symbolic links are not permitted in backups")
                destination = temporary / entry.filename
                destination.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(entry) as source, destination.open("wb") as out:
                    shutil.copyfileobj(source, out)
                if file_digest(destination) != expected[entry.filename]:
                    raise ValueError(f"Backup checksum mismatch: {entry.filename}")
        with sqlite3.connect(temporary / "simshelf.sqlite3") as conn:
            if conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("Backup database failed its integrity check")
            version = conn.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()
            if not version or version[0] != "1":
                raise ValueError("Unsupported backup database schema")
            for ident, raw in conn.execute("SELECT id,data FROM runs WHERE status='running'").fetchall():
                run = json.loads(raw)
                run.update(status="interrupted", ended_at=manifest["created_at"], capture_status="incomplete", capture_errors=["This run was still active when the backup was taken."], owner={})
                conn.execute("UPDATE runs SET status='interrupted',data=? WHERE id=?", (json_text(run), ident))
        if target.exists():
            target.rmdir()
        shutil.move(str(temporary), str(target))
    return Store(target)
