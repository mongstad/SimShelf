"""Explicit removal of manual screenshots; execution evidence stays immutable."""
from __future__ import annotations

import json
import re
import sqlite3
import time
import uuid

from .common import json_text, now
from .removal import ID, cleanup_removed
from .workspace_lock import locked_store

IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif"}


def deleted_screenshot(conn, ident):
    row = conn.execute("SELECT value FROM metadata WHERE key=?", ("deleted_screenshot:" + ident,)).fetchone()
    return json.loads(row[0]) if row else None


def deletion_reason(artifact, run):
    if run["status"] not in {"completed", "failed", "interrupted"} or run.get("capture_status") == "pending":
        return "Wait until this run has finished recording and capturing outputs."
    if artifact.get("policy") != "copy":
        return "External references are preserved; their files are not owned by SimShelf."
    if artifact.get("media_type") not in IMAGE_TYPES:
        return "Only PNG, JPEG, WebP and GIF screenshots can be deleted here."
    if artifact.get("automatic") is not False:
        return "Captured outputs and attachments with unknown ownership are preserved as execution evidence."
    if not re.fullmatch(r"[0-9a-f]{64}", artifact.get("blob", "")):
        return "This attachment has no valid managed image blob."
    return None


@locked_store
def delete_screenshot(store, run_id, ident, *, confirmed=False):
    if confirmed is not True:
        raise ValueError("Confirm screenshot deletion explicitly")
    if any(not isinstance(i, str) or not ID.fullmatch(i) for i in (run_id, ident)):
        raise ValueError("Invalid run or screenshot identifier")
    # Resolve pending attachments before making any reference-aware cleanup decision.
    report = store.reconcile()
    if report["errors"]:
        raise ValueError("Resolve journal or cleanup errors before deleting screenshots: " + "; ".join(report["errors"][:3]))
    with store.connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute("SELECT data FROM runs WHERE id=?", (run_id,)).fetchone()
        if not row:
            raise ValueError("Run not found in this workspace")
        previous = deleted_screenshot(conn, ident)
        if previous:
            if previous["run_id"] != run_id:
                raise ValueError("Screenshot does not belong to this run")
            return {"deleted_id": ident, "already_deleted": True, "cleanup_errors": []}
        row_artifact = conn.execute("SELECT data FROM artifacts WHERE id=? AND run_id=?", (ident, run_id)).fetchone()
        if not row_artifact:
            raise ValueError("Screenshot not found in this run. Refresh and review your selection.")
        artifact = json.loads(row_artifact[0])
        reason = deletion_reason(artifact, json.loads(row[0]))
        if reason:
            raise ValueError(reason)
        # Retain original attachment metadata and all journal/annotation history.
        # This separate tombstone suppresses replay without rewriting the run record.
        record = {"kind": "screenshot_deleted", "id": ident, "run_id": run_id,
                  "at": now(), "attachment": artifact}
        conn.execute("INSERT INTO metadata VALUES (?,?)", ("deleted_screenshot:" + ident, json_text(record)))
        conn.execute("INSERT INTO annotations VALUES (?,?,?)", (f"{time.time_ns():020d}-{uuid.uuid4().hex}", run_id, json_text(record)))
        conn.execute("DELETE FROM artifacts WHERE id=? AND run_id=?", (ident, run_id))
        blob = artifact["blob"]
        conn.execute("INSERT OR IGNORE INTO metadata VALUES (?,?)", (f"cleanup:blobs/{blob[:2]}/{blob}", "pending"))
        conn.execute("UPDATE metadata SET value='3' WHERE key='schema_version'")
    try:
        errors = cleanup_removed(store)
    except (OSError, ValueError, sqlite3.Error) as exc:
        errors = [str(exc)]
    return {"deleted_id": ident, "already_deleted": False, "cleanup_errors": errors}
