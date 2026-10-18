"""Explicit library-only unregistering. Never open source paths or Git archives."""
from __future__ import annotations

import hashlib
import json
import sqlite3

from .common import json_text, now
from . import removal
from .git_archive import PREFIX as ARCHIVE
from .git_provenance import KEY as GIT
from .git_selection import KEY as SELECTION
from .workspace_lock import locked_store

AUDIT = 'deleted_simulation:'


def schema(conn):
    version = conn.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()[0]
    if version not in {'2', '3', '4'}:
        raise ValueError('Simulation removal is unavailable in schema-1 libraries. This action will not upgrade the library.')
    return version


def state(conn, ident):
    version = schema(conn)
    row = conn.execute('SELECT data FROM simulations WHERE id=?', (ident,)).fetchone()
    if not row:
        raise ValueError('Simulation no longer exists. Refresh the library.')
    simulation = json.loads(row[0])
    runs = [json.loads(r[0]) for r in conn.execute('SELECT data FROM runs WHERE simulation_id=? ORDER BY id', (ident,))]
    ids = {r['id'] for r in runs}
    old_runs = [json.loads(r[0]) for r in conn.execute("SELECT value FROM metadata WHERE key LIKE 'deleted_run:%'")]
    old_ids = {r['id'] for r in old_runs if r['simulation_id'] == ident}
    all_ids = ids | old_ids
    snapshots = {r['snapshot_id'] for r in runs}
    baselines = {r.get('baseline_run_id') for r in runs}
    snapshots.update(r['snapshot_id'] for r in old_runs if r['id'] in baselines)
    records = {}
    for table in ('artifacts', 'metrics', 'annotations'):
        records[table] = [list(r) for r in conn.execute(
            f'SELECT t.* FROM {table} t JOIN runs r ON t.run_id=r.id WHERE r.simulation_id=? ORDER BY t.rowid', (ident,))]
    metadata = []
    for key, value in conn.execute('SELECT key,value FROM metadata ORDER BY key'):
        suffix = key[len(ARCHIVE):] if key.startswith(ARCHIVE) else ''
        parts = suffix.split(':')
        if key in {SELECTION + ident, ARCHIVE + 'settings:' + ident} or (
            len(parts) >= 2 and parts[0] in {'event', 'initial', 'pending', 'error'} and parts[1] in all_ids
        ):
            metadata.append([key, value])
    git_row = conn.execute('SELECT value FROM metadata WHERE key=?', (GIT,)).fetchone()
    mapping = json.loads(git_row[0]).get('mappings', {}).get(ident) if git_row else None
    artifacts = [json.loads(r[-1]) for r in records['artifacts']]
    counts = {
        'runs': len(runs), 'snapshots': len(snapshots),
        'screenshots': sum(a.get('media_type') in {'image/png', 'image/jpeg', 'image/webp', 'image/gif'} for a in artifacts),
        'annotations': len(records['annotations']), 'measurements': len(records['metrics']),
        'copies': sum(bool(a.get('blob')) for a in artifacts),
        'references': sum(a.get('policy') == 'reference' for a in artifacts),
        'archive_events': sum(k.startswith(ARCHIVE + 'event:') for k, _ in metadata),
        'archive_pending': sum(k.startswith(ARCHIVE + 'pending:') for k, _ in metadata),
    }
    active = any(r['status'] not in {'completed', 'failed', 'interrupted'} or r.get('capture_status') == 'pending' for r in runs)
    revision = hashlib.sha256(json_text([version, simulation, runs, records, metadata, mapping]).encode()).hexdigest()
    return {'simulation_id': ident, 'name': simulation['name'], 'revision': revision,
            'counts': counts, 'active': active}, runs, metadata


@locked_store
def preview(store, ident):
    with store.connection() as conn:
        conn.execute('BEGIN IMMEDIATE')
        return state(conn, ident)[0]


@locked_store
def remove(store, ident, *, typed_name, revision, confirmed=False):
    if confirmed is not True or not isinstance(typed_name, str) or not isinstance(revision, str):
        raise ValueError('Type the exact simulation name and explicitly confirm removal')
    with store.connection() as conn:
        schema(conn)  # Refuse before recovery or any writes, including zero-run libraries.
        audit = conn.execute('SELECT value FROM metadata WHERE key=?', (AUDIT + ident,)).fetchone()
        if audit:
            previous = json.loads(audit[0])
            if previous['name'] != typed_name or previous['revision'] != revision:
                raise ValueError('Simulation was removed; this confirmation does not match')
            return cleanup_result(store, ident, True)
        current, _, _ = state(conn, ident)
        if current['name'] != typed_name or current['revision'] != revision:
            raise ValueError('Simulation or records changed. Reopen removal and type the exact current name.')
        if current['active']:
            raise ValueError('Running or finalizing runs prevent simulation removal. Stop them and wait first.')
    report = store.reconcile()
    if report['errors']:
        raise ValueError('Resolve journal or cleanup errors before removing the simulation: ' + '; '.join(report['errors'][:3]))
    with store.connection() as conn:
        conn.execute('BEGIN IMMEDIATE')
        current, runs, metadata = state(conn, ident)
        if current['name'] != typed_name or current['revision'] != revision or current['active']:
            raise ValueError('Simulation or records changed. Reopen removal and review again.')
        removal.remove_records(store, conn, runs)
        for key, _ in metadata:
            conn.execute('DELETE FROM metadata WHERE key=?', (key,))
        row = conn.execute('SELECT value FROM metadata WHERE key=?', (GIT,)).fetchone()
        if row:
            saved = json.loads(row[0])
            saved.get('mappings', {}).pop(ident, None)
            conn.execute('UPDATE metadata SET value=? WHERE key=?', (json_text(saved), GIT))
        conn.execute('INSERT INTO metadata VALUES (?,?)', (AUDIT + ident, json_text({
            'id': ident, 'name': typed_name, 'revision': revision, 'deleted_at': now()})))
        conn.execute('DELETE FROM simulations WHERE id=?', (ident,))
    return cleanup_result(store, ident, False)


def cleanup_result(store, ident, already_removed):
    try:
        errors = removal.cleanup_removed(store)
    except (OSError, ValueError, sqlite3.Error) as exc:
        errors = [str(exc)]
    return {'simulation_id': ident, 'already_removed': already_removed, 'cleanup_errors': errors}
