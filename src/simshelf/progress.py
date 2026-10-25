"""Bounded, opt-in progress input parsing; independent of scientific measurements."""
from __future__ import annotations

import json
import math
import os
import re
import sqlite3
import threading
import time
import warnings
from datetime import datetime
from decimal import Decimal

from .common import atomic_write, json_text, now
from .workspace_lock import locked_store
from .removal import ID, deleted_run

TEXT_MODES = {"off", "auto", "step", "percent"}
MAX_LINE = 256
NUMBER = rb"(?:[0-9]{1,3}(?:,[0-9]{3}){1,5}|[0-9]{1,16})(?:\.[0-9]{1,12})?"
PCT_NUMBER = rb"[0-9]{1,3}(?:\.[0-9]{1,12})?"
WS = rb"[ \t]*"
GAP = rb"[ \t]+"
COUNTS = rb"(?P<current>" + NUMBER + rb")" + WS + rb"/" + WS + rb"(?P<total>" + NUMBER + rb")"
SUFFIX = rb"(?:" + WS + rb"\(" + WS + rb"(?P<percent>" + PCT_NUMBER + rb")" + WS + rb"%" + WS + rb"\))?"
STEP_PATTERNS = tuple(re.compile(pattern + SUFFIX, re.IGNORECASE) for pattern in (
    rb"step" + GAP + COUNTS,
    COUNTS + GAP + rb"steps",
    rb"step" + GAP + rb"(?P<current>" + NUMBER + rb")" + GAP + rb"of" + GAP + rb"(?P<total>" + NUMBER + rb")",
))
PERCENT = re.compile(rb"(?:progress" + WS + rb":" + WS + rb"(?P<label>" + PCT_NUMBER + rb")" + WS + rb"%|(?P<bare>" + PCT_NUMBER + rb")" + WS + rb"%(?:" + GAP + rb"complete)?)", re.IGNORECASE)


def progress_report(current=None, total=None, *, stage=None):
    """Validate a report without inventing a total or claiming completion."""
    def number(value, name):
        if value is None:
            return None
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"Progress {name} must be a finite number")
        if not 0 <= value <= 1e15 or not math.isfinite(value):
            raise ValueError(f"Progress {name} must be between 0 and 1e15")
        return float(value)

    current = number(current, "current")
    total = number(total, "total")
    if total is not None and (total == 0 or current is None or current > total):
        raise ValueError("Progress needs a positive total and current between zero and total")
    if stage is not None and (not isinstance(stage, str) or len(stage) > 160 or any(ord(c) < 32 for c in stage)):
        raise ValueError("Progress stage must be at most 160 characters without control characters")
    return {"current": current, "total": total, "stage": stage or None}


class TextProgressParser:
    """Consume one stream, recognizing supported whole-line formats.

    CR, LF and CRLF terminate reports. Overlong lines are discarded until the next
    delimiter, so a suffix of an arbitrary log line can never become a report.
    Parsing does not modify the original bytes retained by the recorder.
    """
    def __init__(self, mode):
        if mode not in TEXT_MODES:
            raise ValueError("Choose off, auto, step or percent progress parsing")
        self.mode = mode
        self.pending = bytearray()
        self.overflow = False

    def _line(self):
        result = None
        if not self.overflow:
            line = bytes(self.pending).strip(b" \t")
            mode = self.mode
            match = (next((m for pattern in STEP_PATTERNS if (m := pattern.fullmatch(line))), None)
                     if mode in {"step", "auto"} else None)
            if mode == "auto":
                mode = "step" if match else "percent"
            if mode == "percent":
                match = PERCENT.fullmatch(line)
                # Bare percentages can be scientific values. Auto accepts only
                # the existing labeled Progress: or % complete forms.
                if self.mode == "auto" and match and match['label'] is None and not line.lower().endswith(b'complete'):
                    match = None
            if match:
                try:
                    if mode == "step":
                        current = Decimal(match['current'].replace(b',', b'').decode('ascii'))
                        total = Decimal(match['total'].replace(b',', b'').decode('ascii'))
                        result = progress_report(float(current), float(total))
                        if match['percent'] is not None:
                            percent = Decimal(match['percent'].decode('ascii'))
                            # Half a unit of the printed precision: 2.0% allows
                            # 0.05 percentage points; integer 2% allows 0.5.
                            tolerance = Decimal(5).scaleb(percent.as_tuple().exponent - 1)
                            if percent > 100 or abs(current * 100 / total - percent) > tolerance:
                                result = None
                    else:
                        result = progress_report(float(match['label'] or match['bare']), 100)
                except ValueError:
                    result = None
            if result is not None and self.mode == "auto":
                result['text_mode'] = mode
        self.pending.clear()
        self.overflow = False
        return result

    def feed(self, chunk):
        if self.mode == "off":
            return
        for byte in chunk:
            if byte in (10, 13):
                report = self._line()
                if report is not None:
                    yield report
            elif not self.overflow:
                if len(self.pending) == MAX_LINE:
                    self.pending.clear()
                    self.overflow = True
                else:
                    self.pending.append(byte)

    def finish(self):
        return self._line() if self.mode != "off" else None


class AutoProgressSelection:
    """First valid report owns the format and stream for one recorder lifetime.

    Selection precedes coalescing and is shared by both stream reader threads.
    Cross-stream ordering is observational, not the child's emission order.
    """
    def __init__(self):
        self.owner = None
        self.lock = threading.Lock()

    def select(self, report, source):
        with self.lock:
            candidate = (source, report['text_mode'])
            if self.owner is None:
                self.owner = candidate
            return report if candidate == self.owner else None

# Progress is a replaceable latest-state checkpoint, never a scientific event.

def enabled(conn):
    return conn.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()[0] == "4"


@locked_store
def enable_progress(store, *, confirmed=False):
    if confirmed is not True:
        raise ValueError("Explicitly confirm enabling schema 4; older SimShelf versions cannot open this library. Back up and verify restore first; stop older servers/recorders.")
    with store.connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        if enabled(conn):
            return {"schema_version": 4}
        if conn.execute("SELECT 1 FROM runs WHERE status='running' LIMIT 1").fetchone():
            raise ValueError("Stop and finalize all runs before enabling progress reporting")
        conn.execute("CREATE TABLE progress (run_id TEXT PRIMARY KEY, sequence INTEGER NOT NULL, data TEXT NOT NULL)")
        conn.execute("UPDATE metadata SET value='4' WHERE key='schema_version'")
    return {"schema_version": 4}


def checkpoint_path(store, run_id):
    if not isinstance(run_id, str) or not ID.fullmatch(run_id):
        raise ValueError("Invalid run identifier")
    path = store.path / "journal" / run_id / "progress.json"
    if any(p.is_symlink() for p in (path, path.parent, path.parent.parent)):
        raise ValueError("Progress checkpoint must not be a symbolic link")
    return path


def validate_saved_report(report):
    if not isinstance(report, dict):
        raise ValueError("Invalid progress report")
    progress_report(report.get('current'), report.get('total'), stage=report.get('stage'))
    if 'text_mode' in report and (report['text_mode'] not in ('step', 'percent')
            or report.get('source') not in ('text:stdout', 'text:stderr')
            or (report['text_mode'] == 'percent' and report.get('total') != 100)):
        raise ValueError("Invalid detected progress format")
    if (report.get('source') not in {'structured', 'text:stdout', 'text:stderr'}
            or not isinstance(report.get('reported_at'), str) or len(report['reported_at']) > 64
            or type(report.get('written_at')) not in (int, float)
            or not 0 <= report['written_at'] <= 1e15):
        raise ValueError("Invalid progress report metadata")
    if datetime.fromisoformat(report['reported_at']).tzinfo is None:
        raise ValueError("Progress report time needs a timezone")


@locked_store
def recover_progress(store, run_id):
    path = checkpoint_path(store, run_id)
    if not path.exists():
        return
    with path.open('rb') as stream:
        raw = stream.read(4097)
    if len(raw) > 4096:
        raise ValueError("Oversized progress checkpoint")
    event = json.loads(raw)
    report = event["data"]
    validate_saved_report(report)
    if (event.get('run_id') != run_id or type(event.get('sequence')) is not int
            or event['sequence'] < 1):
        raise ValueError("Invalid progress checkpoint")
    with store.connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        if not enabled(conn):
            raise ValueError("Enable progress reporting explicitly before recovery")
        if deleted_run(conn, run_id):
            return
        run = conn.execute("SELECT status FROM runs WHERE id=?", (run_id,)).fetchone()
        # Finalization flushes/replays first. Never mutate finalized execution or
        # accept delayed external writes after finalization.
        if not run or run[0] != 'running':
            return
        conn.execute("INSERT INTO progress VALUES (?,?,?) ON CONFLICT(run_id) DO UPDATE SET sequence=excluded.sequence,data=excluded.data WHERE excluded.sequence > progress.sequence",
                     (run_id, event['sequence'], json_text(report)))


@locked_store
def write_progress(store, run_id, report, source, *, force=False):
    path = checkpoint_path(store, run_id)
    recover_progress(store, run_id)
    with store.connection() as conn:
        if not enabled(conn):
            raise ValueError("Enable progress reporting for this library before calling run.progress or selecting a text adapter")
        run = conn.execute("SELECT status FROM runs WHERE id=?", (run_id,)).fetchone()
        if not run or run[0] != 'running' or deleted_run(conn, run_id):
            raise ValueError("Progress can only be reported for an active run")
        row = conn.execute("SELECT sequence,data FROM progress WHERE run_id=?", (run_id,)).fetchone()
        previous = json.loads(row['data']) if row else None
        if previous and previous['source'] == 'structured' and source != 'structured':
            return True  # Structured reports retain priority over parsed log text.
        if previous and source == previous["source"] and report["reported_at"] < previous["reported_at"]:
            return True  # A delayed coalesced report must not replace newer telemetry.
        if previous and not force and 0 <= time.time() - previous['written_at'] < 1:
            return False
        event = {"run_id": run_id, "sequence": row['sequence'] + 1 if row else 1,
                 "data": {**report, "source": source, "written_at": time.time()}}
    atomic_write(path, json_text(event).encode())
    fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
    recover_progress(store, run_id)
    return True


class ProgressWriter:
    """Coalesce in memory, persist at most once/second, flush on normal exit.

    A single short-lived timer flushes coalesced reports even if reporting stops.
    Unexpected process death can lose the unflushed second; the UI labels data
    as last reported. No per-update journal growth.
    """
    def __init__(self, store, run_id):
        self.store, self.run_id = store, run_id
        self.pending = None
        self.next_write = 0.0
        self.lock = threading.RLock()
        self.error = None
        self.timer = None
        self.closed = False

    def report(self, report, source='structured'):
        with self.lock:
            if self.closed:
                return
            if self.pending and self.pending[1] == 'structured' and source != 'structured':
                return
            self.pending = ({**report, 'reported_at': now()}, source)
            if time.monotonic() >= self.next_write:
                self.flush(force=False)
            if self.pending is not None and self.timer is None:
                self.timer = threading.Timer(max(.01, self.next_write - time.monotonic()), self._tick)
                self.timer.daemon = True
                self.timer.start()

    def _tick(self):
        with self.lock:
            self.timer = None
            if not self.closed:
                self.flush(force=False)
                # If another writer won the per-run rate limit, retry once/second.
                if self.pending is not None and self.error is None:
                    self.timer = threading.Timer(1, self._tick)
                    self.timer.daemon = True
                    self.timer.start()

    def close(self):
        with self.lock:
            self.closed = True
            if self.timer:
                self.timer.cancel()
                self.timer = None
            self.flush()

    def flush(self, *, force=True):
        with self.lock:
            if self.pending is None:
                return
            report, source = self.pending
            try:
                if write_progress(self.store, self.run_id, report, source, force=force):
                    self.pending = None
            except (ValueError, OSError, sqlite3.Error, KeyError, TypeError) as exc:
                if self.error is None:
                    warnings.warn(f"Progress could not be saved: {exc}", RuntimeWarning, stacklevel=2)
                self.error = str(exc)
            self.next_write = time.monotonic() + 1
