"""Explicit run removal and crash-retryable, reference-aware file reclamation."""
from __future__ import annotations

import json
import os
import re
import sqlite3
import stat

from .common import json_text, now
from .source import read_snapshot
from .workspace_lock import locked_store

ID = re.compile(r"[0-9a-f]{32}\Z")
MANAGED = re.compile(r"(?:blobs/[0-9a-f]{2}/[0-9a-f]{64}|snapshots/[0-9a-f]{64}\.json|logs/[0-9a-f]{32}/(?:stdout|stderr)\.log|journal/[0-9a-f]{32}/[0-9]{20}-[0-9a-f]{32}\.json)\Z")


def deleted_run(conn, ident):
    row = conn.execute("SELECT value FROM metadata WHERE key=?", ("deleted_run:" + ident,)).fetchone()
    return json.loads(row[0]) if row else None


def snapshot_ids(conn):
    runs = [json.loads(row[0]) for row in conn.execute("SELECT data FROM runs")]
    ids = {run["snapshot_id"] for run in runs}
    for run in runs:
        baseline = deleted_run(conn, run.get("baseline_run_id", ""))
        if baseline:
            ids.add(baseline["snapshot_id"])
    return ids


def snapshot_files(store, ident):
    snapshot = read_snapshot(store.path, ident)
    return {f"snapshots/{ident}.json", *(f"blobs/{f['blob'][:2]}/{f['blob']}" for f in snapshot["files"])}


def unlink_managed(root, relative):
    """Descriptor-relative unlink: no path component may traverse a symlink."""
    if not MANAGED.fullmatch(relative):
        raise ValueError("Invalid managed cleanup path")
    parts = relative.split("/")
    fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in parts[:-1]:
            next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        mode = os.stat(parts[-1], dir_fd=fd, follow_symlinks=False).st_mode
        if not stat.S_ISREG(mode):
            raise ValueError("Managed cleanup target is not a regular file")
        os.unlink(parts[-1], dir_fd=fd)
        os.fsync(fd)
    except FileNotFoundError:
        pass  # A previous cleanup may have unlinked before its DB acknowledgement.
    finally:
        os.close(fd)


@locked_store
def cleanup_removed(store):
    errors = []
    with store.connection() as conn:
        pending = [row[0] for row in conn.execute("SELECT key FROM metadata WHERE key LIKE 'cleanup:%'")]
        if not pending:
            return errors
        protected = set()
        # Fail closed if any retained source manifest cannot be read.
        for ident in snapshot_ids(conn):
            protected.update(snapshot_files(store, ident))
        for row in conn.execute("SELECT data FROM artifacts"):
            key = json.loads(row[0]).get("blob")
            if key:
                protected.add(f"blobs/{key[:2]}/{key}")
        for key in pending:
            relative = key[len("cleanup:"):]
            try:
                if relative not in protected:
                    unlink_managed(store.path, relative)
                conn.execute("DELETE FROM metadata WHERE key=?", (key,))
            except (OSError, ValueError) as exc:
                errors.append(f"{relative}: {exc}")
    return errors


@locked_store
def remove_runs(store, identifiers, *, confirmed=False):
    if confirmed is not True:
        raise ValueError("Confirm run removal explicitly")
    if not isinstance(identifiers, list) or not 1 <= len(identifiers) <= 1000 or any(not isinstance(i, str) or not ID.fullmatch(i) for i in identifiers):
        raise ValueError("Select 1–1000 valid run IDs")
    ids = list(dict.fromkeys(identifiers))
    # Replay before calculating references, including pending starts/attachments.
    report = store.reconcile()
    if report["errors"]:
        raise ValueError("Resolve journal or cleanup errors before removing runs: " + "; ".join(report["errors"][:3]))
    with store.connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        runs = []
        for ident in ids:
            row = conn.execute("SELECT data FROM runs WHERE id=?", (ident,)).fetchone()
            if not row:
                if deleted_run(conn, ident):
                    continue
                raise ValueError("A selected run no longer exists in this workspace. Refresh and review your selection.")
            run = json.loads(row[0])
            if run["status"] not in {"completed", "failed", "interrupted"} or run.get("capture_status") == "pending":
                raise ValueError("Running or finalizing runs cannot be removed. Stop them and wait for finalization first.")
            runs.append(run)
        candidates = set()
        for run in runs:
            candidates.update(snapshot_files(store, run["snapshot_id"]))
            baseline = deleted_run(conn, run.get("baseline_run_id", ""))
            if baseline:
                candidates.update(snapshot_files(store, baseline["snapshot_id"]))
            for row in conn.execute("SELECT data FROM artifacts WHERE run_id=?", (run["id"],)):
                key = json.loads(row[0]).get("blob")
                if key:
                    candidates.add(f"blobs/{key[:2]}/{key}")
            candidates.update(f"logs/{run['id']}/{name}.log" for name in ("stdout", "stderr"))
            journal = store.path / "journal" / run["id"]
            # Never enumerate through a substituted journal directory.
            if (store.path / "journal").is_symlink() or journal.is_symlink():
                raise ValueError("Managed journal must not be a symbolic link")
            candidates.update(p.relative_to(store.path).as_posix() for p in journal.glob("*.json"))
            tombstone = {key: run[key] for key in ("id", "simulation_id", "version", "started_at", "snapshot_id", "structure_id")}
            tombstone["deleted_at"] = now()
            conn.execute("INSERT INTO metadata VALUES (?,?)", ("deleted_run:" + run["id"], json_text(tombstone)))
            for table in ("artifacts", "metrics", "annotations"):
                conn.execute(f"DELETE FROM {table} WHERE run_id=?", (run["id"],))
            conn.execute("DELETE FROM runs WHERE id=?", (run["id"],))
        for relative in candidates:
            if not MANAGED.fullmatch(relative):
                raise ValueError("Invalid managed cleanup path; no runs removed")
            conn.execute("INSERT OR IGNORE INTO metadata VALUES (?,?)", ("cleanup:" + relative, "pending"))
        if runs:
            conn.execute("UPDATE metadata SET value='2' WHERE key='schema_version'")
    # After commit failures mean removal succeeded but reclamation needs retry.
    try:
        errors = cleanup_removed(store)
    except (OSError, ValueError, sqlite3.Error) as exc:
        errors = [str(exc)]
    return {"removed_ids": ids, "cleanup_errors": errors}
