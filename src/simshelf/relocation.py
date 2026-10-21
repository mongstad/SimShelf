"""Explicit registration remapping; never move files or rewrite run history."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat
import uuid

from .common import json_text
from .git_selection import directory, KEY as SELECTION_KEY
from .git_provenance import KEY as GIT_KEY
from .git_archive import PREFIX as ARCHIVE_PREFIX
from .workspace_lock import locked_store


def source_binding(simulation):
    return {"root": simulation["root"], "revision": simulation.get("location_revision")}


def relative_metadata(root, value, *, file=False, prospective=False):
    if not isinstance(value, str) or not value or '\0' in value or Path(value).is_absolute() or '..' in Path(value).parts:
        raise ValueError('Registered paths must be relative and contain no parent traversal')
    signatures = []
    with directory(root) as rootfd:
        fd = os.dup(rootfd)
        try:
            parts = Path(value).parts
            if not parts and file:
                raise ValueError('Expected a relative file path')
            for index, part in enumerate(parts):
                try:
                    info = os.stat(part, dir_fd=fd, follow_symlinks=False)
                except FileNotFoundError:
                    if prospective:
                        return signatures
                    raise ValueError(f'Required path is missing at the new location: {value}') from None
                if stat.S_ISLNK(info.st_mode):
                    raise ValueError(f'Symlinks are not permitted in relocated paths: {value}')
                is_directory = index < len(parts) - 1 or not file
                if is_directory:
                    child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                    os.close(fd)
                    fd = child
                    info = os.fstat(fd)
                elif not stat.S_ISREG(info.st_mode):
                    raise ValueError(f'Expected a regular file: {value}')
                signatures.append([index, info.st_dev, info.st_ino, info.st_mode])
        finally:
            os.close(fd)
    return signatures


def review_state(store, conn, ident, path):
    row = conn.execute('SELECT data FROM simulations WHERE id=?', (ident,)).fetchone()
    if row is None:
        raise ValueError('Simulation not found')
    simulation = json.loads(row[0])
    if conn.execute("SELECT 1 FROM runs WHERE simulation_id=? AND status='running'", (ident,)).fetchone():
        raise ValueError('Stop or finish this simulation’s active runs before changing its source location')
    if not isinstance(path, str) or not path or len(path) > 4096 or '\0' in path:
        raise ValueError('Enter an absolute source folder path')
    root = Path(path)
    if not root.is_absolute() or '..' in root.parts:
        raise ValueError('Enter an absolute source folder path without parent traversal')
    if str(root) == simulation['root']:
        raise ValueError('Choose a different source location')
    if root.is_relative_to(store.path) or store.path.is_relative_to(root):
        raise ValueError('Source and managed workspace folders must not overlap')
    for other in conn.execute('SELECT id,data FROM simulations WHERE id != ?', (ident,)):
        other_root = Path(json.loads(other['data'])['root']).resolve()
        if root.is_relative_to(other_root) or other_root.is_relative_to(root):
            raise ValueError('New source folder overlaps another registered simulation')
    for key in ('connection', 'last_connection'):
        archive = conn.execute('SELECT value FROM metadata WHERE key=?', (ARCHIVE_PREFIX + key,)).fetchone()
        saved = json.loads(archive[0]) if archive else None
        if saved and saved.get('path'):
            archive_root = Path(saved['path']).resolve()
            if root.is_relative_to(archive_root) or archive_root.is_relative_to(root):
                raise ValueError('Source folder must not overlap the master archive')
    signatures = []
    # Reject links in all ancestors, including the chosen root. No source writes.
    with directory(root) as fd:
        info = os.fstat(fd)
        signatures.append([info.st_dev, info.st_ino])
        for field in ('entrypoint', 'version_file'):
            if simulation.get(field):
                signatures.extend(relative_metadata(root, simulation[field], file=True))
        signatures.extend(relative_metadata(root, simulation['config']['output_dir'], prospective=True))
        execution = simulation.get('execution')
        warnings = []
        if execution:
            # Preserve preferences; invalid environment/cwd/mappings are repaired
            # through the existing launch validation, never executed in a preview.
            from .portal import execution_settings
            try:
                execution_settings({**simulation, 'root': str(root)}, execution)
            except ValueError as exc:
                warnings.append(f'Before launching, review saved execution settings: {exc}')
    keys = [GIT_KEY, SELECTION_KEY + ident, ARCHIVE_PREFIX + 'settings:' + ident, ARCHIVE_PREFIX + 'paused_settings:' + ident]
    settings = [list(row) for row in conn.execute(
        'SELECT key,value FROM metadata WHERE key IN (?,?,?,?) ORDER BY key', keys)]
    revision = hashlib.sha256(json_text([simulation, signatures, settings]).encode()).hexdigest()
    return {'simulation_id': ident, 'old_path': simulation['root'], 'new_path': str(root),
            'revision': revision, 'warnings': warnings}


def checked_review(store, conn, ident, path):
    try:
        return review_state(store, conn, ident, path)
    except (OSError, RuntimeError) as exc:
        raise ValueError('Source folder is missing, inaccessible or contains unsafe links. Check the path and review again.') from exc


@locked_store
def preview(store, ident, path):
    with store.connection() as conn:
        conn.execute('BEGIN IMMEDIATE')
        return checked_review(store, conn, ident, path)


@locked_store
def relocate(store, ident, review, confirmed=False):
    if confirmed is not True or not isinstance(review, dict):
        raise ValueError('Preview and explicitly confirm the source location change')
    with store.connection() as conn:
        conn.execute('BEGIN IMMEDIATE')
        current = checked_review(store, conn, ident, review.get('new_path'))
        if current != review:
            raise ValueError('Registration or source location changed. Preview and confirm again')
        simulation = json.loads(conn.execute('SELECT data FROM simulations WHERE id=?', (ident,)).fetchone()[0])
        simulation.update(root=current['new_path'], location_revision=uuid.uuid4().hex)
        conn.execute('UPDATE simulations SET data=? WHERE id=?', (json_text(simulation), ident))
        # Only current location-bound preferences. Historical archive events and
        # the independent master connection remain untouched, even after return.
        conn.execute('DELETE FROM metadata WHERE key IN (?,?,?)',
                     (SELECTION_KEY + ident, ARCHIVE_PREFIX + 'settings:' + ident, ARCHIVE_PREFIX + 'paused_settings:' + ident))
        row = conn.execute('SELECT value FROM metadata WHERE key=?', (GIT_KEY,)).fetchone()
        if row:
            connection = json.loads(row[0])
            connection.get('mappings', {}).pop(ident, None)
            conn.execute('UPDATE metadata SET value=? WHERE key=?', (json_text(connection), GIT_KEY))
    return simulation
