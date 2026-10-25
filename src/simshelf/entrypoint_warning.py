"""Read-only entrypoint warning; whole-snapshot provenance remains immutable."""
from __future__ import annotations

import ast
import json
from functools import lru_cache
from pathlib import PurePosixPath

from .removal import deleted_run
from .source_comparison import snapshot, source_bytes
from .swss import parse
from .workspace_lock import workspace_lock

VERSION_NAMES = {'SIMSHELF_VERSION', 'VERSION', '__version__'}


def python_versions(data):
    """Recognize literal module version declarations, without executing Python."""
    tree = ast.parse(data)
    versions = {}
    for node in tree.body:
        targets = node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(node, ast.AnnAssign) else []
        for target in targets:
            if isinstance(target, ast.Name) and target.id in VERSION_NAMES:
                if target.id in versions or not isinstance(node.value, ast.Constant) or not isinstance(node.value.value, str):
                    raise ValueError('Python version declaration is not one literal string')
                versions[target.id] = node.value.value
    # A conditional/dynamic assignment cannot establish an unchanged declaration.
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store) and node.id in VERSION_NAMES:
            if not any(node is target for item in tree.body
                       for target in (item.targets if isinstance(item, ast.Assign) else [item.target] if isinstance(item, ast.AnnAssign) else [])):
                raise ValueError('Python version declaration is not a module literal')
    return versions


class EntrypointWarnings:
    """Request-local bounded caches; never reuse checks across library mutations."""

    def __init__(self, store):
        self.store = store
        self.facts = lru_cache(maxsize=128)(self._facts)
        self.baseline = lru_cache(maxsize=128)(self._baseline)

    def _baseline(self, ident):
        with self.store.connection() as conn:
            row = conn.execute('SELECT data FROM runs WHERE id=?', (ident,)).fetchone()
            result = json.loads(row[0]) if row else deleted_run(conn, ident)
        if not result:
            raise ValueError('Recorded baseline is unavailable')
        return result

    def _facts(self, snapshot_id, recorded_entrypoint):
        files = {entry['path']: entry for entry in snapshot(self.store, snapshot_id)['files']}
        declaration = files.get('swss.toml')
        swss_version = None
        entrypoint = recorded_entrypoint
        if declaration:
            swss = parse(source_bytes(self.store, declaration))['swss']
            if entrypoint is not None and entrypoint != swss['entrypoint']:
                raise ValueError('Recorded entrypoint and captured SWSS association differ')
            entrypoint = swss['entrypoint']
            swss_version = swss['simulation_version']
            for source in swss.get('source_files', []):
                if source['path'] not in files or files[source['path']]['blob'] != source['sha256']:
                    raise ValueError('Captured SWSS source binding is unavailable or stale')
        if not isinstance(entrypoint, str) or PurePosixPath(entrypoint).suffix != '.py':
            raise ValueError('Historical primary Python entrypoint is not recorded')
        if entrypoint not in files:
            raise ValueError('Primary Python entrypoint was not captured')
        entry = files[entrypoint]
        data = source_bytes(self.store, entry)
        return entrypoint, entry['blob'], swss_version, python_versions(data)

    def check(self, run):
        result = {'warn': False, 'status': 'unavailable', 'baseline_run_id': run.get('baseline_run_id')}
        try:
            with workspace_lock(self.store.path):
                baseline = self.baseline(run['baseline_run_id'])
                if baseline['simulation_id'] != run['simulation_id'] or baseline['version'] != run['version']:
                    raise ValueError('Recorded baseline belongs to a different simulation or version')
                facts = []
                for record in (baseline, run):
                    provenance = (record.get('parameter_metadata') or {}).get('provenance') or {}
                    if provenance.get('binding_reasons'):
                        raise ValueError('Recorded SWSS binding diagnostics require separate review')
                    facts.append(self.facts(record['snapshot_id'], record.get('source_entrypoint', provenance.get('entrypoint'))))
                before, after = facts
                result['entrypoint'] = after[0]
                if before[0] != after[0]:
                    raise ValueError('Primary entrypoint changed; no same-file baseline is established')
                if before[1] == after[1]:
                    result['status'] = 'same'
                elif before[2:] != after[2:]:
                    result['status'] = 'version-changed'
                else:
                    result.update(warn=True, status='changed')
        except (ValueError, OSError, KeyError, TypeError, SyntaxError, UnicodeError, RecursionError) as exc:
            result['detail'] = str(exc)
        return result

    def project(self, run):
        return {**run, 'entrypoint_warning': self.check(run)}
