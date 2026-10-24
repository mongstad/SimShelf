"""Reviewed local preservation, isolated from legacy consent and scientific rows."""
from __future__ import annotations

import json
import hashlib
import os
import stat
import tempfile
import re
import uuid
from pathlib import Path

from . import git_archive as archive
from .capture import capture_action, output_inventory, preview as capture_preview
from .common import contained, json_text, match, now
from .config import validate_config
from .git_provenance import workspace_identity
from .git_selection import directory, inventory
from .relocation import source_binding
from .source import blob_path, IGNORED_DIRS
from .workspace_lock import locked_store

PREFIX = 'preservation_v2:'
RECORD_LIMIT = 1024 ** 2
TEXT_LIMIT = 64 * 1024
ANNOTATION_LIMIT = 1000


def get(store, key, default=None):
    return archive.get(store, key, default, namespace=PREFIX)


def put(store, key, value):
    return archive.put(store, key, value, namespace=PREFIX)


def policy_options(value):
    if not isinstance(value, dict) or set(value) != {'enabled', 'all_sources', 'sources', 'extensions', 'process_logs'}:
        raise ValueError('Review all preservation choices explicitly.')
    if any(type(value[k]) is not bool for k in ('enabled', 'all_sources', 'process_logs')):
        raise ValueError('Preservation switches must be booleans.')
    paths, extensions = value['sources'], value['extensions']
    if not isinstance(paths, list) or len(paths) > archive.COUNT_LIMIT or any(
        not isinstance(p, str) or len(p) > 512 or p.startswith('/') or '\\' in p
        or any(ord(c) < 32 for c in p) or any(s in ('', '.', '..', '.git') for s in p.split('/')) for p in paths
    ):
        raise ValueError('Choose bounded relative snapshot paths.')
    if not isinstance(extensions, list) or len(extensions) > 32 or any(
        not isinstance(e, str) or not re.fullmatch(r'\.[A-Za-z0-9_-]{1,20}', e) for e in extensions
    ):
        raise ValueError('Choose at most 32 exact extensions, such as .json, .csv and .log.')
    result = {**value, 'sources': sorted(set(paths)), 'extensions': sorted(set(extensions))}
    if result['enabled'] and not (result['all_sources'] or paths or extensions or result['process_logs']):
        raise ValueError('Select source, output or process-log evidence; an empty preservation policy is not allowed.')
    return result


def location_binding(sim, store):
    with directory(sim['root']) as fd:
        info = os.fstat(fd)
        return {**source_binding(sim), 'device': archive.device_identity(store, Path(sim['root']), info, fd), 'inode': info.st_ino}


@archive.unavailable_errors
@locked_store
def preview(store, ident, config, options):
    sim = store.simulation(ident)
    config = validate_config(config)
    json_text(config)  # Reject nonfinite/unsupported values, never repair them.
    contained(Path(sim['root']), config['output_dir'])
    options = policy_options(options)
    saved = archive.connection(store) if options['enabled'] else archive.get(store, 'connection')
    if options['enabled']:
        archive.validate_repo(store, saved)
        if archive.connection_status(store)['state'] != 'connected':
            raise ValueError('Git preservation is unavailable; disable it to save ordinary capture settings.')
    source, warnings, revision = [], [], None
    try:
        inv = inventory(store, ident, config=config)
        revision = inv['revision']
        for f in inv['files']:
            captured = not any(p in IGNORED_DIRS for p in Path(f['path']).parts[:-1]) and any(match(f['path'], p) for p in config['source_include']) and not any(
                match(f['path'], p) for p in config['source_exclude'])
            source.append({**f, 'captured': captured, 'selected': captured and (
                options['all_sources'] or f['path'] in options['sources'])})
        warnings.extend(inv['blocked'])
    except (OSError, ValueError) as exc:
        if options['enabled']:
            raise
        warnings.append(str(exc))
    outputs = capture_preview({**sim, 'config': config})
    for f in outputs['files']:
        f['git_selected'] = options['enabled'] and f['action'] == 'copy' and Path(f['path']).suffix in options['extensions']
        f['git_reason'] = (f.get('reason') or ('Exceeds Git per-file limit' if f['size'] > archive.FILE_LIMIT else None)
                           if f['git_selected'] else 'Not selected' if f['action'] == 'copy' else f['action'])
    result = {'format': 2, 'simulation': ident, 'config': config, 'options': options,
              'repository': saved, 'workspace': workspace_identity(store), 'binding': location_binding(sim, store) if options['enabled'] else source_binding(sim),
              'source_revision': revision, 'sources': source, 'outputs': outputs, 'warnings': warnings,
              'previous_config': sim['config'], 'previous': get(store, 'settings:' + ident),
              'legacy': archive.get(store, 'settings:' + ident) or archive.get(store, 'paused_settings:' + ident),
              'record_scope': ['exact argv and cwd', 'outcome and simulation version', 'snapshot identities and modes',
                               'recorded parameters and their sources', 'capture result', 'selected evidence and omissions']}
    result['fingerprint'] = archive.hash_bytes(json_text(result).encode())
    archive.checked_review(result)
    return result


@archive.unavailable_errors
@locked_store
def save(store, ident, review, confirmed=False):
    archive.checked_review(review)
    fresh = preview(store, ident, review.get('config'), review.get('options'))
    if confirmed is not True or review.get('fingerprint') != fresh['fingerprint']:
        raise ValueError('Preservation choices or files changed. Review again before confirming.')
    # Browser numbers can round nanosecond timestamps or scientific integers.
    # The digest binds the exact server review; persist only freshly checked values.
    review = fresh
    # Approval stores a preference; the independent global gate is checked when
    # recording starts. Preview still validates the reviewed repository/scope.
    policy = {k: review[k] for k in ('format', 'config', 'options', 'repository', 'workspace', 'binding')}
    policy['revision'] = uuid.uuid4().hex
    # Preserve the previous legacy consent as evidence, while preventing old builds
    # from treating the newly approved policy as legacy automatic permission.
    policy['legacy_settings'] = review['legacy'] or (review['previous'] or {}).get('legacy_settings')
    with store.connection() as db:
        sim = json.loads(db.execute('SELECT data FROM simulations WHERE id=?', (ident,)).fetchone()[0])
        sim['config'] = review['config']
        db.execute('UPDATE simulations SET data=? WHERE id=?', (json_text(sim), ident))
        for key, value in ((PREFIX + 'settings:' + ident, policy), (archive.PREFIX + 'settings:' + ident, None),
                           (archive.PREFIX + 'paused_settings:' + ident, None)):
            db.execute('INSERT OR REPLACE INTO metadata VALUES (?,?)', (key, json_text(value)))
    if policy['options']['enabled']:
        archive.remember_location(store, Path(sim['root']))
    return {'saved': True, 'revision': policy['revision']}


def reviewed_policy(store, ident):
    policy = get(store, 'settings:' + ident)
    legacy = archive.get(store, 'settings:' + ident)
    paused = archive.get(store, 'paused_settings:' + ident)
    return policy, legacy, paused


def validate_participation(store, ident, policy, legacy):
    if policy is not None:
        # A disabled draft may never have been approved for Git. Its location and
        # repository binding must pass the same checks before it can be resumed.
        candidate = {**policy, 'options': {**policy['options'], 'enabled': True}}
        validate_plan(store, store.simulation(ident), candidate)
    elif legacy:
        result = archive.legacy_status(store, ident, legacy)
        if result['state'] != 'enabled':
            raise ValueError(result['reason'] or 'Review the existing archive choices again.')
    else:
        raise ValueError('Review preservation choices before enabling this simulation.')


@locked_store
def status(store, ident):
    """Single effective-state calculation for UI and the recording start boundary."""
    policy, legacy, paused = reviewed_policy(store, ident)
    participating = policy['options']['enabled'] is True if policy is not None else bool(legacy)
    enabled = archive.global_enabled(store)
    connection = archive.connection_status(store)
    valid, reason = False, None
    try:
        validate_participation(store, ident, policy, legacy or paused)
        valid = True
    except (ValueError, OSError, KeyError, TypeError) as exc:
        reason = str(exc)
    result = {'format': 2 if policy is not None else 1, 'legacy': bool(legacy or paused),
              'participating': participating, 'global_enabled': enabled,
              'can_resume': valid, 'connection': connection['state']}
    if not enabled:
        return {**result, 'state': 'disabled', 'reason': 'Master Git Archive is OFF. Local library capture continues.'}
    if connection['state'] != 'connected':
        return {**result, 'state': 'unavailable', 'reason': connection['reason'] or 'The shared repository is disconnected.'}
    if not participating:
        return {**result, 'state': 'disabled', 'reason': None}
    if not valid:
        return {**result, 'state': 'review_required' if policy is None else 'unavailable', 'reason': reason}
    return {**result, 'state': 'enabled', 'reason': None}


@archive.unavailable_errors
@locked_store
def set_participation(store, ident, enabled):
    store.simulation(ident)
    if type(enabled) is not bool:
        raise ValueError('Choose ON or OFF explicitly.')
    policy, legacy, paused = reviewed_policy(store, ident)
    if enabled:
        validate_participation(store, ident, policy, legacy or paused)
    with store.connection() as db:
        if policy is not None:
            policy['options']['enabled'] = enabled
            db.execute('INSERT OR REPLACE INTO metadata VALUES (?,?)',
                       (PREFIX + 'settings:' + ident, json_text(policy)))
        else:
            # Retain exact legacy consent while paused, outside the old active
            # settings key so an older build cannot interpret OFF as permission.
            for key, value in (('settings:', (legacy or paused) if enabled else None),
                               ('paused_settings:', None if enabled else legacy or paused)):
                db.execute('INSERT OR REPLACE INTO metadata VALUES (?,?)',
                           (archive.PREFIX + key + ident, json_text(value)))
    return status(store, ident)


def validate_plan(store, sim, policy):
    policy_options(policy['options'])
    if policy['format'] != 2 or policy['workspace'] != workspace_identity(store) or policy['binding'] != location_binding(sim, store):
        raise ValueError('Library or source location changed; review preservation settings.')
    if policy['config'] != sim['config']:
        raise ValueError('Capture settings changed; review preservation settings.')
    if policy['repository'] != archive.connection(store):
        raise ValueError('Connect the reviewed archive or review preservation settings.')
    archive.validate_repo(store, policy['repository'])
    if archive.connection_status(store)['state'] != 'connected':
        raise ValueError('Git archive unavailable. Recording continues locally.')
    archive.remember_location(store, Path(sim['root']))


def selected_output(name, plan):
    return Path(name).suffix in plan['options']['extensions'] and capture_action(name, plan['config']) == 'copy'


def prepare(recorder):
    policy = get(recorder.store, 'settings:' + recorder.simulation['id'])
    if policy is None:
        return False
    if not policy['options']['enabled']:
        put(recorder.store, 'initial:' + recorder.id, {'state': 'not_enabled'})
        return True
    try:
        validate_plan(recorder.store, {**recorder.simulation, 'config': recorder.base_capture_config}, policy)
        before_inventory, errors = output_inventory(recorder.simulation)
        if errors:
            raise ValueError('Initial output inventory incomplete; no complete preservation claim is possible.')
        plan = {**policy, 'before': archive.fingerprint_outputs(recorder.simulation, policy), 'inventory': before_inventory}
        put(recorder.store, 'initial:' + recorder.id, {'state': 'prepared', 'plan': plan})
    except Exception as exc:
        put(recorder.store, 'initial:' + recorder.id, {'state': 'unavailable'})
        put(recorder.store, 'error:' + recorder.id, str(exc))
    return True


def record_bytes(record):
    if not isinstance(record, dict) or record.get('format') != 2:
        raise ValueError('Unsupported preservation record.')
    raw = json_text(record).encode('utf-8')
    if len(raw) > RECORD_LIMIT:
        raise ValueError('Preservation record exceeds 1 MiB; nothing was truncated or published.')
    annotations = record.get('annotations', [])
    if not isinstance(annotations, list) or len(annotations) > ANNOTATION_LIMIT:
        raise ValueError('Preservation record exceeds 1,000 annotation entries.')
    for annotation in annotations:
        for field in ('notes', 'version_note', 'caption'):
            value = annotation.get('data', {}).get(field)
            if value is not None and (not isinstance(value, str) or len(value.encode('utf-8')) > TEXT_LIMIT):
                raise ValueError('A note or caption exceeds 64 KiB; nothing was truncated.')
    return raw


def budget(store, run_id, files, record):
    raw = record_bytes(record)
    events = archive.entries(store, run_id)
    records = [e['record'] for e in events if e.get('record')]
    total = sum(len(record_bytes(r)) for r in records) + len(raw)
    total += sum(f['size'] for e in events for f in e['files']) + sum(f['size'] for f in files)
    if total > archive.RUN_LIMIT:
        raise ValueError('Cumulative 100 MiB run limit includes preservation records and later additions.')
    if sum(len(r.get('annotations', [])) for r in records) + len(record.get('annotations', [])) > ANNOTATION_LIMIT:
        raise ValueError('Cumulative 1,000 annotation-entry limit exceeded, including revisions.')
    archive.budget(store, run_id, files)


def execution_record(run):
    return {k: run.get(k) for k in ('id', 'simulation_id', 'started_at', 'ended_at', 'status', 'exit_code',
        'error', 'version', 'snapshot_id', 'structure_id', 'command', 'cwd', 'parameters', 'parameter_sources',
        'git', 'source_change', 'launch', 'output_policy', 'output_base')}


def new_record(run, ledger, unknown, *, policy=None, annotations=None):
    return {'format': 2, 'application': 'SimShelf', 'execution': execution_record(run),
            'snapshot': run['snapshot'], 'policy': policy,
            'capture': {k: run.get(k) for k in ('capture_root', 'capture_config', 'capture_status', 'capture_counts', 'capture_errors')},
            'evidence': ledger, 'unknown_coverage': unknown, 'annotations': annotations or [],
            'excluded': ['environment recreation', 'external reference bytes', 'uncaptured outputs', 'unselected annotations'],
            'machine_local_paths': True, 'restores_workspace': False, 'prior_events': []}


@locked_store
def finalize(store, run_id):
    state = get(store, 'initial:' + run_id)
    if not state or state['state'] != 'prepared':
        return
    run = store.run(run_id)
    if run['status'] == 'running':
        return
    plan, files, ledger, skipped = state['plan'], [], [], []
    unknown = list(run.get('capture_errors', [])) + list(run.get('source_warnings', []))
    if run['capture_status'] != 'complete' and not unknown:
        unknown.append('Capture is not complete.')

    def consider(name, blob, size, category, identity=None, reason=None, **extra):
        item = {'name': name, 'category': category, 'artifact_id': identity, 'blob': blob, 'size': size, **extra}
        if reason is None:
            try:
                if category == 'process_log':
                    data = archive.safe_read(store.path / 'logs' / run_id / (extra['stream'] + '.log'))
                    if len(data) != size or archive.hash_bytes(data) != blob:
                        raise ValueError('Process log changed before preservation.')
                else:
                    archive.managed_entry(store, name, blob, size, category, identity)
                archive.budget(store, run_id, files + [item])
                files.append(item)
            except (ValueError, OSError) as exc:
                reason = str(exc)
        ledger.append({**item, 'disposition': 'selected' if reason is None else 'omitted', 'reason': reason})
        if reason:
            skipped.append({'name': name, 'reason': reason})

    for source in run['snapshot']['files']:
        selected = plan['options']['all_sources'] or source['path'] in plan['options']['sources']
        consider(source['path'], source['blob'], source['size'], 'source',
                 reason=None if selected else 'Not selected by reviewed source policy', mode=source['mode'])
    for requested in plan['options']['sources']:
        if requested not in {s['path'] for s in run['snapshot']['files']}:
            consider(requested, None, 0, 'source', reason='Requested source is absent from the captured snapshot')
    sim = {**store.simulation(run['simulation_id']), 'config': run['capture_config']}
    after = archive.fingerprint_outputs(sim, plan)
    artifacts = {a['name']: a for a in run['artifacts'] if a.get('automatic')}
    for name in sorted(set(after) | set(artifacts)):
        a, current = artifacts.get(name), after.get(name)
        reason = None
        if not selected_output(name, plan):
            reason = ('Not selected by reviewed output types' if a and a['policy'] == 'copy'
                      else 'Capture decision: ' + (a['policy'] if a else 'not copied'))
        elif not current or current.get('error'):
            reason = (current or {}).get('error', 'Output missing after execution')
        elif plan['before'].get(name, {}).get('error'):
            reason = 'Initial output bytes could not be verified'
        elif current == plan['before'].get(name):
            reason = 'Unchanged pre-existing output; not attributed to this run'
        elif not a or a['policy'] != 'copy' or a.get('blob') != current['hash']:
            reason = 'No verified matching run-specific managed copy'
        consider(name, a.get('blob') if a else None, a['size'] if a else (current or {}).get('size', 0),
                 'result', a['id'] if a else None, reason=reason)
    # Keep intentional ignored files visible without reading their scientific bytes.
    observed, errors = output_inventory(sim)
    unknown.extend(errors)
    for name, metadata in observed.items():
        if name not in artifacts and name not in after and metadata != plan['inventory'].get(name):
            ledger.append({'name': name, 'category': 'result', 'size': metadata['size'], 'disposition': 'not_retained',
                           'reason': 'Capture decision: ' + capture_action(name, plan['config'])})
    if plan['options']['process_logs']:
        for stream in ('stdout', 'stderr'):
            try:
                data = archive.safe_read(store.path / 'logs' / run_id / (stream + '.log'))
                consider(stream + '.log', archive.hash_bytes(data), len(data), 'process_log', stream=stream)
            except (ValueError, OSError) as exc:
                consider(stream + '.log', None, 0, 'process_log', reason=str(exc), stream=stream)
    record = new_record(run, ledger, unknown, policy={k: v for k, v in plan.items() if k not in ('before', 'inventory', 'legacy_settings')})
    # Deliberate exclusions are not missing requested evidence; coverage remains explicit.
    incomplete = [e for e in ledger if e['disposition'] == 'omitted' and not (
        str(e['reason']).startswith(('Not selected', 'Capture decision:', 'Unchanged pre-existing')))]
    record['completeness'] = 'partial' if unknown or incomplete or not files else 'verified'
    budget(store, run_id, files, record)
    pending = {'id': uuid.uuid4().hex, 'created_at': now(), 'kind': 'initial', 'repository': plan['repository'],
               'simulation': run['simulation_id'], 'run': run_id, 'files': files, 'skipped': skipped, 'record': record}
    with store.connection() as db:
        db.execute('INSERT INTO metadata VALUES (?,?)', (PREFIX + 'pending:' + run_id, json_text(pending)))
        db.execute('UPDATE metadata SET value=? WHERE key=?',
                   (json_text({'state': 'captured', 'policy_revision': plan['revision']}), PREFIX + 'initial:' + run_id))
    archive.publish(store, run_id)


@archive.unavailable_errors
@locked_store
def additions_preview(store, run_id, artifact_ids, include_notes=False):
    run = store.run(run_id)
    if run['status'] == 'running':
        raise ValueError('Finish the run before preserving later evidence.')
    saved = archive.connection(store)
    archive.validate_repo(store, saved)
    if type(include_notes) is not bool or not isinstance(artifact_ids, list) or len(artifact_ids) > archive.COUNT_LIMIT or any(
        not isinstance(i, str) or not re.fullmatch('[0-9a-f]{32}', i) for i in artifact_ids
    ) or len(set(artifact_ids)) != len(artifact_ids) or not (artifact_ids or include_notes):
        raise ValueError('Select distinct manual attachments and/or saved notes for review.')
    files, annotations = [], []
    for ident in artifact_ids:
        a = store.artifact(ident)
        if a['run_id'] != run_id or a.get('automatic') or a['policy'] != 'copy':
            raise ValueError('Select manual managed attachments from this run only.')
        files.append(archive.managed_entry(store, a['name'], a['blob'], a['size'], 'addition', ident))
        annotations.append({'id': 'attachment:' + ident, 'data': {'id': ident, 'caption': a.get('caption', ''), 'created_at': a['created_at'], 'observation': 'current saved attachment metadata at explicit review'}})
    with store.connection() as db:
        rows = db.execute('SELECT event_id,data FROM annotations WHERE run_id=? ORDER BY rowid LIMIT ?', (run_id, ANNOTATION_LIMIT + 1)).fetchall()
    if len(rows) > ANNOTATION_LIMIT:
        raise ValueError('Annotation history exceeds the 1,000-entry review limit; no partial history is exported.')
    for ident, raw in rows:
        value = json.loads(raw)
        if (include_notes and any(k in value for k in ('notes', 'version_note', 'name', 'tags'))) or value.get('id') in artifact_ids:
            annotations.append({'id': ident, 'data': value})
    if include_notes and not any(any(k in a['data'] for k in ('notes', 'version_note', 'name', 'tags')) for a in annotations):
        raise ValueError('No saved note revisions to preserve. Save a note first or select attachments only.')
    record = new_record(run, [{**f, 'disposition': 'selected', 'reason': None} for f in files], [], annotations=annotations)
    record['prior_events'] = [{'id': e['id'], 'commit': e['commit']} for e in archive.entries(store, run_id)]
    record['kind'] = 'annotation_addition'
    record['completeness'] = 'verified'
    budget(store, run_id, files, record)
    review = {'run': run_id, 'simulation': run['simulation_id'], 'repository': saved, 'files': files,
              'artifact_ids': artifact_ids, 'include_notes': include_notes, 'record': record,
              'events': [e['id'] for e in archive.entries(store, run_id)]}
    review['record_json'] = json_text(record)
    review['fingerprint'] = archive.hash_bytes(json_text(review).encode())
    if len(json_text(review).encode()) > 3 * RECORD_LIMIT:
        raise ValueError('Preservation review exceeds its bounded size.')
    return review


@archive.unavailable_errors
@locked_store
def additions(store, run_id, review, operation, confirmed=False):
    if not isinstance(review, dict) or len(json_text(review).encode()) > 3 * RECORD_LIMIT:
        raise ValueError('Invalid or oversized preservation review.')
    if not isinstance(operation, str) or not re.fullmatch('[0-9a-f]{32}', operation) or confirmed is not True:
        raise ValueError('Explicitly confirm the reviewed preservation operation.')
    receipt = {k: review.get(k) for k in ('run', 'simulation', 'fingerprint', 'artifact_ids', 'include_notes')}
    prior = next((e for e in archive.entries(store, run_id) if e['id'] == operation), None)
    if prior:
        if prior.get('review') != receipt:
            raise ValueError('Operation ID belongs to different reviewed evidence.')
        return prior
    pending = get(store, 'pending:' + run_id) or archive.get(store, 'pending:' + run_id)
    if pending:
        if pending['id'] != operation or pending.get('review') != receipt:
            raise ValueError('Resolve the pending preservation operation first.')
        return archive.publish(store, run_id)
    fresh = additions_preview(store, run_id, review.get('artifact_ids'), review.get('include_notes'))
    if review.get('fingerprint') != fresh['fingerprint'] or receipt != {k: fresh[k] for k in receipt}:
        raise ValueError('Evidence, notes or archive changed. Review again.')
    review = fresh
    put(store, 'pending:' + run_id, {'id': operation, 'created_at': now(), 'kind': 'addition', 'review': receipt,
        'repository': review['repository'], 'simulation': review['simulation'], 'run': run_id,
        'files': review['files'], 'skipped': [], 'record': review['record']})
    return archive.publish(store, run_id)


def summary(store, run_id, events, connection):
    run = store.run(run_id)
    initial = next((e for e in events if e['kind'] == 'initial'), None)
    state = get(store, 'initial:' + run_id) or archive.get(store, 'initial:' + run_id)
    pending = get(store, 'pending:' + run_id) or archive.get(store, 'pending:' + run_id)
    error = get(store, 'error:' + run_id) or archive.get(store, 'error:' + run_id)
    source = [f for f in (initial or {}).get('files', []) if f['category'] == 'source']
    results = [f for f in (initial or {}).get('files', []) if f['category'] == 'result']
    copied = [a for a in run['artifacts'] if a.get('automatic') and a['policy'] == 'copy']
    archived_ids = {f['artifact_id'] for f in results if any(a['id'] == f.get('artifact_id') and a.get('blob') == f['blob']
                    and a['size'] == f['size'] for a in copied)}
    if pending:
        label, reason = 'pending', error or 'Approved evidence awaits publication or verified association.'
    elif initial:
        record = initial.get('record')
        label = record['completeness'] if record else 'partial'
        reason = (('Verified for the reviewed scope at publication.' if label == 'verified' else 'Some reviewed evidence is missing or coverage is unknown; inspect omissions.') if record else
                  'Legacy manifest only: no scientific payloads.' if not initial['files'] else
                  'Legacy file selection; complete run-record scope is unknown.')
    elif error:
        label = 'unavailable' if state and state['state'] == 'unavailable' else 'failed'
        reason = error
    elif state and state['state'] == 'prepared':
        label = 'pending' if run['status'] == 'running' else 'partial'
        reason = 'Awaiting finalization.' if run['status'] == 'running' else 'No durable candidate manifest; live outputs will not be recaptured.'
    else:
        label, reason = 'not_enabled', 'No initial Git preservation for this run.'
    return {'state': label, 'reason': reason, 'source_files': len(source), 'output_files': len(archived_ids),
            'copied_outputs': len(copied), 'commit': initial['commit'] if initial else None,
            'record': bool(initial and initial.get('record')), 'connection': connection['state'],
            'events': len(events), 'annotations': sum(len(e.get('record', {}).get('annotations', [])) for e in events)}


@archive.unavailable_errors
@locked_store
def retained_source(store, run_id, name):
    run = store.run(run_id)
    entry = next((f for f in run['snapshot']['files'] if f['path'] == name), None)
    if not entry:
        raise ValueError('Source file not found in this run snapshot.')
    data = archive.safe_read(blob_path(store.path, entry['blob']), 32 * 1024**2)
    if len(data) != entry['size'] or archive.hash_bytes(data) != entry['blob']:
        raise ValueError('Retained source failed integrity verification.')
    return data


@archive.unavailable_errors
@locked_store
def retained_artifact(store, ident):
    """Freeze verified bytes for range/inline serving without unbounded memory."""
    artifact = store.artifact(ident)
    if artifact['policy'] != 'copy':
        raise ValueError('Referenced files are not served; no managed copy exists.')
    path = blob_path(store.path, artifact['blob'])
    result = tempfile.TemporaryFile()
    try:
        with directory(path.parent) as parent:
            fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
            with os.fdopen(fd, 'rb') as stream:
                before = os.fstat(stream.fileno())
                if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_size != artifact['size']:
                    raise ValueError('Managed attachment failed integrity verification.')
                digest, count = hashlib.sha256(), 0
                while chunk := stream.read(min(1024**2, artifact['size'] - count + 1)):
                    count += len(chunk)
                    if count > artifact['size']:
                        raise ValueError('Managed attachment changed during verification.')
                    digest.update(chunk)
                    result.write(chunk)
                after = os.fstat(stream.fileno())
                current = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
                signature = lambda i: (i.st_dev, i.st_ino, i.st_size, i.st_mtime_ns, i.st_ctime_ns)
                if signature(before) != signature(after) or signature(after) != signature(current) or count != artifact['size'] or digest.hexdigest() != artifact['blob']:
                    raise ValueError('Managed attachment failed integrity verification.')
        result.seek(0)
        return result
    except BaseException:
        result.close()
        raise


def pending_blobs(conn):
    """Keep approved bytes through attachment removal and backup until publication."""
    result = set()
    runs = {row[0] for row in conn.execute('SELECT id FROM runs')}
    for row in conn.execute("SELECT value FROM metadata WHERE key LIKE 'preservation_v2:pending:%'"):
        pending = json.loads(row[0])
        if pending and pending['run'] in runs:
            for file in pending['files']:
                if file['category'] != 'process_log':
                    key = file['blob']
                    if not isinstance(key, str) or not re.fullmatch('[0-9a-f]{64}', key):
                        raise ValueError('Invalid pending preservation blob identity.')
                    result.add(key)
    return result
