"""Read-only explanations of frozen source evidence; never inspect live source."""
from __future__ import annotations

import ast
from pathlib import PurePosixPath

from .common import digest, json_text
from .source import blob_path, read_snapshot
from .removal import deleted_run
from .workspace_lock import workspace_lock

PREVIEW_LIMIT = 1024 * 1024
AST_BUDGET = 8 * PREVIEW_LIMIT


def snapshot(store, key):
    result = read_snapshot(store.path, key)
    if result.get('id') != key or digest(json_text(result['files']).encode()) != key:
        raise ValueError('Source manifest failed integrity verification')
    return result


def comparison_target(store, run, ident):
    with store.connection() as conn:
        removed = deleted_run(conn, ident)
    if removed and ident == run['baseline_run_id']:
        return {**removed, 'deleted': True}, snapshot(store, removed['snapshot_id'])
    other = store.run(ident, detail=False)
    return {**other, 'deleted': False}, snapshot(store, other['snapshot_id'])


def source_bytes(store, entry):
    from .git_archive import safe_read
    if entry['size'] > PREVIEW_LIMIT:
        raise ValueError('Source preview is limited to 1 MB per file, including the baseline')
    data = safe_read(blob_path(store.path, entry['blob']), PREVIEW_LIMIT)
    if len(data) != entry['size'] or digest(data) != entry['blob']:
        raise ValueError('Source bytes failed integrity verification')
    return data


def selection_context(run):
    # Older capture configs retain include/exclude patterns, but not every
    # effective output exclusion. Never reconstruct these from today's settings.
    context = run.get('source_selection')
    if context is not None:
        return context
    config = run.get('capture_config', {})
    return {key: config[key] for key in ('source_include', 'source_exclude') if key in config}


def output_boundary(path, context):
    candidate = PurePosixPath(path)
    return next((root for root in context.get('output_dirs', [])
                 if candidate.is_relative_to(PurePosixPath(root))), None)


def recorded_capture_boundary(path, run):
    root = run.get('capture_config', {}).get('output_dir')
    return root if isinstance(root, str) and PurePosixPath(path).is_relative_to(PurePosixPath(root)) else None


def compare_sources(store, ident, offset=0, limit=100):
    if offset < 0 or not 1 <= limit <= 200:
        raise ValueError('Use a nonnegative offset and a limit from 1 to 200')
    with workspace_lock(store.path):
        run = store.run(ident, detail=False)
        current = snapshot(store, run['snapshot_id'])
        baseline, previous = comparison_target(store, run, run['baseline_run_id'])
        before = {f['path']: f for f in previous['files']}
        after = {f['path']: f for f in current['files']}
        old_context, context = selection_context(baseline), selection_context(run)
        changes, counts = [], {'added': 0, 'removed': 0, 'changed': 0, 'unchanged': 0}
        for path in sorted(before.keys() | after.keys()):
            old, new = before.get(path), after.get(path)
            if old == new:
                counts['unchanged'] += 1
                continue
            change = 'added' if old is None else 'removed' if new is None else 'changed'
            counts[change] += 1
            changes.append({'path': path, 'change': change,
                            'before': old, 'after': new,
                            'permissions_changed': bool(old and new and old['mode'] != new['mode']),
                            'output_boundary': (output_boundary(path, context) if 'source_selection' in run
                                                else recorded_capture_boundary(path, run)) if change == 'removed' else None,
                            'output_boundary_confirmed': 'source_selection' in run})
        budget = AST_BUDGET
        page = changes[offset:offset + limit]
        for item in page:
            old, new = item['before'], item['after']
            kind = 'python' if item['path'].endswith('.py') else 'non-python'
            if item['change'] != 'changed':
                item['classification'] = kind
            elif old['blob'] == new['blob']:
                item['classification'] = 'permissions' if item['permissions_changed'] else 'manifest'
            elif kind != 'python':
                item['classification'] = 'non-python'
            elif max(old['size'], new['size']) > PREVIEW_LIMIT or old['size'] + new['size'] > budget:
                item['classification'] = 'python-unverified'
                item['detail'] = 'AST comparison exceeds the 1 MB/file or 8 MB/page budget.'
            else:
                budget -= old['size'] + new['size']
                try:
                    old_tree = ast.dump(ast.parse(source_bytes(store, old)), include_attributes=False)
                    new_tree = ast.dump(ast.parse(source_bytes(store, new)), include_attributes=False)
                    item['classification'] = 'python-text' if old_tree == new_tree else 'python-structure'
                except (SyntaxError, UnicodeError, RecursionError):
                    item['classification'] = 'python-unverified'
                    item['detail'] = 'Python could not be parsed; exact recorded bytes differ.'
                except (ValueError, OSError) as exc:
                    item['classification'] = 'python-unverified'
                    item['detail'] = str(exc)
        notes = []
        if not changes and run['structure_id'] != baseline['structure_id']:
            notes.append('Recorded structural fingerprints differ despite matching file entries. Algorithm or environment differences may be involved; the recorded classification is unchanged.')
        if 'source_selection' not in run or 'source_selection' not in baseline:
            notes.append('Historical source-selection details are incomplete. Added or removed paths alone do not establish why selection changed or whether a file was generated.')
        excluded = sum(bool(item['output_boundary']) for item in changes)
        if excluded:
            if 'source_selection' in run:
                notes.append(f'The baseline includes {excluded} removed path(s) inside this run’s recorded output exclusions. The original baseline is preserved; no files or versions were rewritten.')
            else:
                notes.append(f'The baseline includes {excluded} removed path(s) under this run’s recorded capture folder. This is consistent with corrected output exclusion, but historical selection details cannot prove the cause. The baseline is unchanged.')
        return {'run_id': ident, 'version': run['version'], 'recorded_change': run['source_change'],
                'snapshot_id': current['id'],
                'baseline': {key: baseline[key] for key in ('id', 'version', 'started_at', 'snapshot_id', 'deleted')},
                'counts': counts, 'total': len(changes), 'offset': offset, 'limit': limit,
                'changes': page, 'notes': notes,
                'selection_changes': [{'field': key, 'before': old_context[key], 'after': context[key]}
                                      for key in sorted(old_context.keys() & context.keys())
                                      if old_context[key] != context[key]]}
