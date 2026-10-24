"""Explicit local archive; independent of scientific records and source Git state."""
from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import re
import shutil
import selectors
import signal
import time
import stat
import subprocess
import tempfile
import uuid
from contextlib import contextmanager, nullcontext
from functools import wraps
from pathlib import Path, PurePosixPath

from .common import clean_name, json_text, now
from .git_provenance import workspace_identity
from .location_identity import device_identity, remember_location
from .git_selection import directory, inventory, matches
from .source import blob_path
from .workspace_lock import locked_store

PREFIX = 'archive_v1:'
PRESERVATION_PREFIX = 'preservation_v2:'
NAMESPACES = (PREFIX, PRESERVATION_PREFIX)
FILE_LIMIT = 25 * 1024**2
RUN_LIMIT = 100 * 1024**2
COUNT_LIMIT = 1000
CONFIG = b'[core]\n\trepositoryformatversion = 0\n\tfilemode = true\n\tbare = true\n'


def unavailable_errors(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except (OSError, UnicodeError) as exc:
            raise ValueError('Archive files are unavailable or unsafe. Check the dedicated repository and managed copies; no substitute bytes will be served.') from exc
    return wrapped


def checked_review(review):
    if not isinstance(review, dict) or len(json_text(review)) > 512 * 1024:
        raise ValueError('Invalid or oversized archive review. Refresh and review again.')


def get(store, key, default=None, *, namespace=PREFIX):
    with store.connection() as conn:
        row = conn.execute('SELECT value FROM metadata WHERE key=?', (namespace + key,)).fetchone()
    return json.loads(row[0]) if row else default


@locked_store
def put(store, key, value, *, namespace=PREFIX):
    with store.connection() as conn:
        # A late optional finalizer must not recreate associations after removal.
        from .removal import deleted_run
        parts = key.split(':')
        if len(parts) >= 2 and parts[0] in {'initial', 'pending', 'event', 'error'} and deleted_run(conn, parts[1]):
            return
        conn.execute('INSERT OR REPLACE INTO metadata VALUES (?,?)', (namespace + key, json_text(value)))


def save_connection(store, active, remembered):
    """Commit connection and its last successful identity together, or neither."""
    with store.connection() as conn:
        for key, value in (('connection', active), ('last_connection', remembered)):
            conn.execute('INSERT OR REPLACE INTO metadata VALUES (?,?)', (PREFIX + key, json_text(value)))


@locked_store
def disconnect(store):
    saved = get(store, 'connection') or get(store, 'last_connection')
    save_connection(store, None, saved)


def global_enabled(store):
    # Missing/invalid state fails closed, including libraries from older builds.
    return get(store, 'automatic_enabled') is True


@locked_store
def set_global_enabled(store, enabled):
    if type(enabled) is not bool:
        raise ValueError('Choose ON or OFF explicitly.')
    if enabled:
        status = connection_status(store)
        if status['state'] != 'connected':
            raise ValueError(status['reason'] or 'Connect the shared repository before enabling Master Git Archive.')
    put(store, 'automatic_enabled', enabled)
    return {'enabled': global_enabled(store), 'status': connection_status(store)}


def hash_bytes(data):
    return hashlib.sha256(data).hexdigest()


def safe_read(path, limit=FILE_LIMIT):
    """Pin every parent, reject links/special files and detect concurrent writes."""
    path = Path(path).absolute()
    with directory(path.parent) as parent:
        fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        with os.fdopen(fd, 'rb') as stream:
            before = os.fstat(stream.fileno())
            if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_size > limit:
                raise ValueError('Not an eligible bounded, singly linked regular file.')
            data = stream.read(limit + 1)
            after = os.fstat(stream.fileno())
            current = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
            signature = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
            if len(data) > limit or signature(before) != signature(after) or signature(after) != signature(current):
                raise ValueError('File changed during reading; no archive copy accepted.')
            return data


def git(root, *args, data=None, index=None, limit=FILE_LIMIT + 1024):
    executable = shutil.which('git')
    if not executable:
        raise ValueError('Git unavailable. Simulation recording is unaffected.')
    env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null', GIT_NO_REPLACE_OBJECTS='1',
               GIT_NO_LAZY_FETCH='1', GIT_TERMINAL_PROMPT='0', LC_ALL='C',
               GIT_AUTHOR_NAME='SimShelf Archive', GIT_AUTHOR_EMAIL='archive@localhost',
               GIT_COMMITTER_NAME='SimShelf Archive', GIT_COMMITTER_EMAIL='archive@localhost')
    if index:
        env['GIT_INDEX_FILE'] = str(index)
    with (nullcontext(root) if isinstance(root, int) else directory(Path(root))) as fd, tempfile.TemporaryFile() as incoming:
        if data is not None:
            incoming.write(data)
        incoming.seek(0)
        command = [executable, '-c', 'core.hooksPath=/dev/null', '-c', 'core.fsmonitor=false',
                   '-c', 'protocol.allow=never', '-c', 'commit.gpgSign=false', '-c', 'gc.auto=0',
                   '-c', 'core.fsync=all', '--git-dir=/proc/self/fd/' + str(fd), *args]
        try:
            with subprocess.Popen(command, stdin=incoming, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                  env=env, pass_fds=(fd,), start_new_session=True) as process:
                chunks, size, deadline = [], 0, time.monotonic() + 15
                try:
                    with selectors.DefaultSelector() as selector:
                        selector.register(process.stdout, selectors.EVENT_READ)
                        while selector.get_map():
                            if time.monotonic() >= deadline:
                                raise ValueError('Archive Git operation timed out.')
                            for key, _ in selector.select(.1):
                                chunk = os.read(key.fileobj.fileno(), 65536)
                                if not chunk:
                                    selector.unregister(key.fileobj)
                                    continue
                                size += len(chunk)
                                if size > limit:
                                    raise ValueError('Archive Git result exceeded its size bound.')
                                chunks.append(chunk)
                    process.wait(timeout=max(.01, deadline-time.monotonic()))
                    if process.returncode:
                        raise ValueError('Archive Git operation failed; check repository access and integrity.')
                    return b''.join(chunks)
                finally:
                    if process.poll() is None:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait()
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ValueError('Archive Git operation unavailable or timed out; retry after inspection.') from exc


def boundaries(store, path):
    root = Path(path).expanduser().absolute()
    with directory(root):
        pass
    root = Path(os.path.abspath(root))
    protected = [store.path, Path(__file__).resolve().parents[2], *[Path(s['root']) for s in store.simulations()]]
    if any(root.is_relative_to(p) or p.is_relative_to(root) for p in protected):
        raise ValueError('Archive must be separate from the application, library and all simulation sources.')
    return root


def validate_repo(store, saved):
    root = boundaries(store, saved['path'])
    # Dedicated bare format only. Refuse imported repositories, config helpers,
    # alternates, links and shallow/promisor storage rather than invoking them.
    if safe_read(root / 'config', 4096) != CONFIG:
        raise ValueError('Archive configuration changed or is not a dedicated SimShelf archive.')
    if safe_read(root / 'simshelf-archive-id', 64).decode() != saved['identity']:
        raise ValueError('Archive identity changed; reconnect the original archive explicitly.')
    count = 0
    for base, dirs, files in os.walk(root, followlinks=False):
        for name in dirs + files:
            count += 1
            p = Path(base) / name
            st = p.lstat()
            if count > 100000 or stat.S_ISLNK(st.st_mode) or (not stat.S_ISDIR(st.st_mode) and (not stat.S_ISREG(st.st_mode) or st.st_nlink != 1)):
                raise ValueError('Unsafe or oversized archive repository layout.')
    for forbidden in ('objects/info/alternates', 'objects/info/http-alternates', 'shallow'):
        if (root / forbidden).exists():
            raise ValueError('Alternate or shallow object storage is unsupported.')
    return root


@contextmanager
def repo_lock(store, saved):
    import fcntl
    root = validate_repo(store, saved)
    with directory(root) as parent:
        fd = os.open('simshelf.lock', os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600, dir_fd=parent)
        try:
            if os.fstat(fd).st_nlink != 1:
                raise ValueError('Unsafe archive lock.')
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise ValueError('Archive is busy. Retry after the other operation finishes.') from exc
            # Hold the repository directory descriptor throughout all Git calls.
            validate_repo(store, saved)
            yield parent
        finally:
            os.close(fd)


@unavailable_errors
@locked_store
def connect(store, path, initialize=False, confirmed=False, expected_connection=None, remap=False):
    if confirmed is not True:
        raise ValueError('Explicitly confirm local archive setup.')
    if get(store, 'connection') is not None:
        raise ValueError('Disconnect the current archive before confirming another connection.')
    root = boundaries(store, path)
    remembered = get(store, 'last_connection')
    if remembered and remembered.get('path') == str(root):
        if initialize:
            raise ValueError('The remembered archive cannot be reinitialized. Restore it or choose another empty directory.')
        # Manual path confirmation must not bypass the remembered identity.
        validate_repo(store, remembered)
        if remap is not True and expected_connection is None:
            expected_connection = remembered
    if expected_connection is not None:
        # A quick reconnect must never adopt a replacement repository or move
        # an old library binding. Deliberate setup remains a separate action.
        if (not isinstance(expected_connection, dict)
                or set(expected_connection) != {'path', 'identity', 'workspace'}
                or initialize or expected_connection.get('workspace') != workspace_identity(store)):
            raise ValueError('Review the archive location and setup for this library.')
        if not shutil.which('git'):
            raise ValueError('Git unavailable. Install or restore Git before reconnecting.')
        if get(store, 'connection') not in (None, expected_connection):
            raise ValueError('Archive connection changed. Refresh before reconnecting.')
        if str(root) != expected_connection.get('path'):
            raise ValueError('Archive location changed. Review archive location and setup.')
        validate_repo(store, expected_connection)
    if initialize:
        if any(root.iterdir()):
            raise ValueError('Initialize only an existing empty dedicated directory.')
        # Explicit init, no user template. Failure leaves a disclosed partial repo.
        with directory(root) as fd:
            git(fd, 'init', '--bare', '--template=', '--initial-branch=main')
            if safe_read(root / 'config', 4096) != CONFIG:
                raise ValueError('Unexpected initialized archive configuration; inspect before retrying.')
            marker = os.open('simshelf-archive-id', os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=fd)
            with os.fdopen(marker, 'w') as stream:
                stream.write(uuid.uuid4().hex)
                stream.flush()
                os.fsync(stream.fileno())
            os.fsync(fd)
    saved = {'path': str(root), 'identity': safe_read(root / 'simshelf-archive-id', 64).decode(), 'workspace': workspace_identity(store)}
    if not re.fullmatch('[0-9a-f]{32}', saved['identity']):
        raise ValueError('Invalid archive identity.')
    validate_repo(store, saved)
    if expected_connection is not None and saved != expected_connection:
        raise ValueError('Archive identity changed. Restore the original archive or review archive location and setup.')
    remember_location(store, store.path)
    save_connection(store, saved, saved)
    return saved


def connection(store):
    saved = get(store, 'connection')
    if not saved:
        raise ValueError('Connect the master archive for this library first.')
    if saved['workspace'] != workspace_identity(store):
        raise ValueError('Library binding changed (host, path or filesystem identity). Restore the original library location or explicitly review archive setup; refreshing cannot authorize a remap.')
    return saved


def connection_status(store):
    """Availability hint; downloads still verify exact objects."""
    saved = get(store, 'connection')
    if not saved:
        return {'state': 'disconnected', 'reason': None, 'identity': None}
    try:
        saved = connection(store)
        validate_repo(store, saved)
        if not shutil.which('git'):
            raise ValueError('Git unavailable. Workspace copies remain downloadable.')
        remember_location(store, store.path)
        return {'state': 'connected', 'reason': None, 'identity': saved['identity']}
    except (ValueError, OSError, KeyError, TypeError) as exc:
        if isinstance(exc, FileNotFoundError):
            reason = 'Archive path or required repository file is missing. Restore the mount/path, then refresh archive status.'
        elif isinstance(exc, PermissionError):
            reason = 'Archive access denied. Restore directory/file permissions, then refresh archive status.'
        elif isinstance(exc, OSError):
            reason = f'Archive filesystem access failed ({exc.strerror}). Check the mount, then refresh archive status.'
        else:
            reason = str(exc)
        return {'state': 'unavailable', 'reason': reason, 'identity': None}


@locked_store
def legacy_status(store, ident, plan=None):
    """Mirror start-time consent checks without creating a plan or writing data."""
    plan = plan if plan is not None else get(store, 'settings:' + ident)
    if not plan:
        return {'state': 'disabled', 'reason': None}
    try:
        saved = connection(store)
        sim = store.simulation(ident)
        if (plan['workspace'] != workspace_identity(store) or plan['repository'] != saved
                or plan['capture_config'] != sim['config'] or plan['source'] != sim['root']):
            raise ValueError('Source, capture settings or archive connection changed. Review consent again.')
        inv = inventory(store, ident)
        if inv['rules'] != plan['rules'] or inv['binding'] != plan['binding']:
            raise ValueError('File selection changed. Review consent again.')
        status = connection_status(store)
        if status['state'] != 'connected':
            raise ValueError(status['reason'] or 'Connect the master archive first.')
        return {'state': 'enabled', 'reason': None}
    except (ValueError, OSError, KeyError, TypeError) as exc:
        return {'state': 'review_required', 'reason': str(exc)}


def automatic_status(store, ident):
    # Compatibility entry point; UI and recording share the same effective gate.
    from .preservation import status
    return status(store, ident)


def future_rules(values):
    if not isinstance(values, list) or len(values) > 100:
        raise ValueError('Use at most 100 future output rules.')
    for value in values:
        if not isinstance(value, str) or len(value) > 240 or not re.fullmatch(r'[A-Za-z0-9_. /\-*]+', value) or '**' in value:
            raise ValueError('Use relative filenames or a single-level * pattern such as logs/*.csv.')
        parts = value.split('/')
        if any(p in ('', '.', '..', '.git') for p in parts) or any('*' in p for p in parts[:-1]):
            raise ValueError('Future rules must stay inside the capture directory; * is allowed only in the filename.')
    return sorted(set(values))


def future_match(path, rules):
    return any(PurePosixPath(path).parent == PurePosixPath(r).parent and fnmatch.fnmatchcase(PurePosixPath(path).name, PurePosixPath(r).name) for r in rules)


@unavailable_errors
@locked_store
def settings_preview(store, ident, future):
    saved = connection(store)
    validate_repo(store, saved)
    sim = store.simulation(ident)
    inv = inventory(store, ident)
    return {'simulation': ident, 'repository': saved, 'selection_revision': inv['revision'], 'rules': inv['rules'],
            'future': future_rules(future), 'capture_config': sim['config'], 'source': sim['root'],
            'workspace': workspace_identity(store), 'binding': inv['binding'], 'previous': get(store, 'settings:' + ident)}


@unavailable_errors
@locked_store
def enable(store, ident, review, confirmed=False):
    from .preservation import get as preservation_get
    if preservation_get(store, 'settings:' + ident) is not None:
        raise ValueError('Use Preservation settings to review this simulation’s policy.')
    checked_review(review)
    if confirmed is not True or review != settings_preview(store, ident, review.get('future')):
        raise ValueError('Settings changed. Preview and explicitly confirm archive consent again.')
    put(store, 'settings:' + ident, {k: v for k, v in review.items() if k != 'previous'})
    put(store, 'paused_settings:' + ident, None)
    return {'enabled': True}


def entries(store, run_id):
    store.run(run_id, False)
    with store.connection() as conn:
        rows = conn.execute('SELECT value FROM metadata WHERE key LIKE ? OR key LIKE ?',
                            tuple(prefix + 'event:' + run_id + ':%' for prefix in NAMESPACES)).fetchall()
    return sorted([json.loads(row[0]) for row in rows], key=lambda e: (e['created_at'], e['id']))


def view(store, run_id):
    from . import preservation
    events = entries(store, run_id)
    status = connection_status(store)
    return {'events': events, 'connection_status': status,
            'initial': preservation.get(store, 'initial:' + run_id) or get(store, 'initial:' + run_id),
            'pending': preservation.get(store, 'pending:' + run_id) or get(store, 'pending:' + run_id),
            'error': preservation.get(store, 'error:' + run_id) or get(store, 'error:' + run_id),
            'preservation': preservation.summary(store, run_id, events, status)}


def managed_entry(store, name, blob, size, category, artifact_id=None):
    data = safe_read(blob_path(store.path, blob))
    if len(data) != size or hash_bytes(data) != blob:
        raise ValueError('Managed bytes failed integrity verification.')
    return {'name': name, 'blob': blob, 'size': size, 'category': category, 'artifact_id': artifact_id}


@unavailable_errors
@locked_store
def additions_preview(store, run_id, artifact_ids):
    run = store.run(run_id)
    if run['status'] == 'running':
        raise ValueError('Finish the run before archiving attachments.')
    saved = connection(store)
    validate_repo(store, saved)
    if not isinstance(artifact_ids, list) or not 1 <= len(artifact_ids) <= COUNT_LIMIT or not all(isinstance(i, str) and re.fullmatch('[0-9a-f]{32}', i) for i in artifact_ids) or len(set(artifact_ids)) != len(artifact_ids):
        raise ValueError('Select distinct managed attachments.')
    result = []
    archived = {f.get('artifact_id') for e in entries(store, run_id) for f in e['files']}
    for ident in artifact_ids:
        a = store.artifact(ident)
        if a['run_id'] != run_id or a.get('automatic') or a['policy'] != 'copy' or ident in archived:
            raise ValueError('Select unarchived manual managed attachments belonging to this run.')
        result.append(managed_entry(store, a['name'], a['blob'], a['size'], 'addition', ident))
    budget(store, run_id, result)
    return {'run': run_id, 'simulation': run['simulation_id'], 'repository': saved, 'files': result,
            'artifact_ids': artifact_ids, 'events': [e['id'] for e in entries(store, run_id)]}


def budget(store, run_id, files):
    events = entries(store, run_id)
    existing = [f for e in events for f in e['files']]
    record_total = sum(len(json_text(e['record']).encode()) for e in events if e.get('record'))
    if len(existing) + len(files) > COUNT_LIMIT or sum(f['size'] for f in existing + files) + record_total > RUN_LIMIT or any(f['size'] > FILE_LIMIT for f in files):
        raise ValueError('Cumulative run archive limit: 1,000 files, 25 MiB each, 100 MiB total, including additions.')


@unavailable_errors
@locked_store
def additions(store, run_id, review, operation, confirmed=False):
    checked_review(review)
    if not isinstance(operation, str) or not re.fullmatch('[0-9a-f]{32}', operation):
        raise ValueError('Invalid archive operation ID.')
    if confirmed is not True:
        raise ValueError('Explicitly confirm the reviewed attachments.')
    prior = next((e for e in entries(store, run_id) if e['id'] == operation), None)
    if prior:
        if prior.get('review') != review:
            raise ValueError('Operation ID already belongs to another request.')
        return prior
    pending = get(store, 'pending:' + run_id) or get(store, 'pending:' + run_id, namespace=PRESERVATION_PREFIX)
    if pending:
        if pending['id'] != operation or pending.get('review') != review:
            raise ValueError('Resolve the pending archive operation first.')
        return publish(store, run_id)
    if review != additions_preview(store, run_id, review.get('artifact_ids')):
        raise ValueError('Attachments or archive changed. Preview again.')
    put(store, 'pending:' + run_id, {'id': operation, 'created_at': now(), 'kind': 'addition', 'review': review,
        'repository': review['repository'], 'simulation': review['simulation'], 'run': run_id, 'files': review['files'], 'skipped': []})
    return publish(store, run_id)


def candidate_bytes(store, run_id, file):
    if file.get('category') == 'process_log':
        if file.get('stream') not in ('stdout', 'stderr'):
            raise ValueError('Unsupported process log identity.')
        return safe_read(store.path / 'logs' / run_id / (file['stream'] + '.log'))
    return safe_read(blob_path(store.path, file['blob']))


@unavailable_errors
@locked_store
def publish(store, run_id):
    run = store.run(run_id, False)
    if run['status'] == 'running':
        raise ValueError('Archive publication requires a finalized run.')
    candidates = [(prefix, get(store, 'pending:' + run_id, namespace=prefix)) for prefix in NAMESPACES]
    candidates = [(prefix, value) for prefix, value in candidates if value]
    if not candidates:
        return {'status': 'nothing pending'}
    if len(candidates) != 1:
        raise ValueError('Conflicting pending operations; inspect before retrying.')
    namespace, pending = candidates[0]
    saved = connection(store)
    if saved['identity'] != pending['repository']['identity']:
        raise ValueError('Reconnect the archive associated with this operation.')
    if pending.get('record'):
        from .preservation import budget as preservation_budget
        preservation_budget(store, run_id, pending['files'], pending['record'])
    else:
        budget(store, run_id, pending['files'])
    deadline = time.monotonic() + 120
    def within_budget():
        if time.monotonic() > deadline:
            raise ValueError('Archive operation exceeded two minutes; pending operation can be retried.')
    with repo_lock(store, saved) as root:
        ref = 'refs/simshelf/events/' + pending['id']
        refs = git(root, 'for-each-ref', '--format=%(refname) %(objectname)', ref, 'refs/heads/main').decode().splitlines()
        refs = dict(line.split(' ') for line in refs)
        commit = refs.get(ref)
        files = [{**f, 'path': f"simulations/{run['simulation_id']}/runs/{run_id}/{pending['id']}/{n:04d}/{clean_name(PurePosixPath(f['name']).name)}"} for n, f in enumerate(pending['files'])]
        manifest = {k: v for k, v in pending.items() if k not in ('review', 'repository', 'files')}
        manifest['files'] = files
        manifest_bytes = json_text(manifest).encode()
        if len(manifest_bytes) > 16 * 1024**2:
            raise ValueError('Archive manifest exceeds the 16 MiB metadata limit.')
        manifest_path = f"simulations/{run['simulation_id']}/runs/{run_id}/{pending['id']}/manifest.json"
        if not commit:
            needed = sum(f['size'] for f in files) * 2 + 16 * 1024**2
            if shutil.disk_usage(f'/proc/self/fd/{root}').free < needed:
                raise ValueError('Insufficient free space for archive operation.')
            with tempfile.TemporaryDirectory(prefix='simshelf-index-') as temporary:
                index = Path(temporary) / 'index'
                parent = refs.get('refs/heads/main')
                git(root, 'read-tree', parent if parent else '--empty', index=index)
                for f in [*files, {'path': manifest_path, 'data': manifest_bytes}]:
                    within_budget()
                    data = f.get('data')
                    if data is None:
                        data = candidate_bytes(store, run_id, f)
                        if len(data) != f['size'] or hash_bytes(data) != f['blob']:
                            raise ValueError('Managed archive candidate changed or is missing.')
                    oid = git(root, 'hash-object', '-w', '--stdin', data=data).decode().strip()
                    git(root, 'update-index', '--add', '--cacheinfo', '100644', oid, f['path'], index=index)
                tree = git(root, 'write-tree', index=index).decode().strip()
                args = ['commit-tree', tree, *(['-p', parent] if parent else [])]
                commit = git(root, *args, data=f"SimShelf {pending['kind']} {run_id} {pending['id']}\n".encode()).decode().strip()
                transaction = f"start\nupdate refs/heads/main {commit} {parent or '0'*40}\ncreate {ref} {commit}\nprepare\ncommit\n"
                git(root, 'update-ref', '--stdin', data=transaction.encode())
        # Recovery verifies the exact manifest and every byte before association.
        if git(root, 'show', f'{commit}:{manifest_path}', limit=16*1024**2) != manifest_bytes:
            raise ValueError('Published archive manifest does not match pending operation.')
        for f in files:
            within_budget()
            raw = git(root, 'cat-file', 'blob', f"{commit}:{f['path']}")
            if len(raw) != f['size'] or hash_bytes(raw) != f['blob']:
                raise ValueError('Published archive file failed verification.')
        event = {**pending, 'files': files, 'commit': commit}
        # Association and pending removal are atomic; events never updated.
        with store.connection() as conn:
            conn.execute('INSERT INTO metadata VALUES (?,?)', (namespace + 'event:' + run_id + ':' + pending['id'], json_text(event)))
            conn.execute('DELETE FROM metadata WHERE key IN (?,?)', (namespace + 'pending:' + run_id, namespace + 'error:' + run_id))
        return event


@unavailable_errors
@locked_store
def download(store, run_id, event_id, index):
    event = next((e for e in entries(store, run_id) if e['id'] == event_id), None)
    if not event or index < 0 or index >= len(event['files']):
        raise ValueError('Archived file not found for this run.')
    saved = connection(store)
    if saved['identity'] != event['repository']['identity']:
        raise ValueError('The original archive is not connected.')
    f = event['files'][index]
    with repo_lock(store, saved) as root:
        raw = git(root, 'cat-file', 'blob', f"{event['commit']}:{f['path']}")
    if len(raw) != f['size'] or hash_bytes(raw) != f['blob']:
        raise ValueError('Historical bytes failed integrity verification.')
    return f['name'], raw


def selected_output(name, plan):
    if plan.get('format') == 2:
        from .preservation import selected_output as selected
        return selected(name, plan)
    relative = plan['capture_config']['output_dir'].rstrip('/') + '/' + name
    return future_match(name, plan['future']) or any(matches(relative, r) for r in plan['rules'])


def fingerprint_outputs(simulation, plan):
    from .capture import output_inventory
    inventory_files, errors = output_inventory(simulation)
    if errors or len(inventory_files) > 20000:
        raise ValueError('Output inventory incomplete; automatic archival disabled for this run.')
    result, total = {}, 0
    for name in sorted(inventory_files):
        if not selected_output(name, plan):
            continue
        if len(result) >= COUNT_LIMIT:
            raise ValueError('Too many selected output candidates.')
        try:
            size = inventory_files[name]['size']
            total += size
            if size > FILE_LIMIT or total > RUN_LIMIT:
                result[name] = {'error': 'Output exceeds archive read budget'}
                continue
            data = safe_read(Path(simulation['root']) / simulation['config']['output_dir'] / name)
            result[name] = {'hash': hash_bytes(data), 'size': len(data)}
        except (OSError, ValueError) as exc:
            result[name] = {'error': str(exc)}
    return result


def prepare(recorder):
    """Called under start lock; optional failures must never prevent execution."""
    from .preservation import prepare as prepare_preservation, status
    try:
        effective = status(recorder.store, recorder.simulation['id'])
        if effective['state'] != 'enabled':
            put(recorder.store, 'initial:' + recorder.id,
                {'state': 'not_enabled' if effective['state'] == 'disabled' else 'unavailable'},
                namespace=PRESERVATION_PREFIX)
            if effective['state'] != 'disabled':
                put(recorder.store, 'error:' + recorder.id, effective['reason'], namespace=PRESERVATION_PREFIX)
            return
        if prepare_preservation(recorder):
            return
    except Exception as exc:
        try:
            put(recorder.store, 'initial:' + recorder.id, {'state': 'unavailable'}, namespace=PRESERVATION_PREFIX)
            put(recorder.store, 'error:' + recorder.id, str(exc), namespace=PRESERVATION_PREFIX)
        except Exception:
            pass
        return
    store = recorder.store
    try:
        plan = get(store, 'settings:' + recorder.simulation['id'])
        if not plan:
            return
        saved = connection(store)
        if (plan['workspace'] != workspace_identity(store) or plan['repository'] != saved
                or plan['capture_config'] != recorder.base_capture_config or plan['source'] != recorder.simulation['root']):
            raise ValueError('Archive settings no longer match source, capture settings or repository. Review consent again.')
        # Validate location-bound #44 rules, but do not require existing filenames
        # to remain identical; explicitly consented folder/type rules cover future files.
        inv = inventory(store, recorder.simulation['id'])
        if inv['rules'] != plan['rules'] or inv['binding'] != plan['binding']:
            raise ValueError('Inclusion preferences changed. Review archive consent again.')
        validate_repo(store, saved)
        before = fingerprint_outputs(recorder.simulation, plan)
        frozen = {**plan, 'before': before}
        put(store, 'initial:' + recorder.id, {'state': 'prepared', 'plan': frozen})
        recorder.archive_plan = frozen
    except Exception as exc:
        try:
            put(store, 'error:' + recorder.id, str(exc))
        except Exception:
            pass


@locked_store
def finalize(store, run_id):
    """Only immutable managed output copies are offered to Git after finalization."""
    state = get(store, 'initial:' + run_id)
    if not state or state['state'] != 'prepared':
        return
    run = store.run(run_id)
    if run['status'] == 'running':
        return
    plan = state['plan']
    files, skipped = [], []
    total = 0
    omitted_details = 0

    def skip(name, reason):
        nonlocal omitted_details
        if len(skipped) < 1000:
            skipped.append({'name': name, 'reason': reason})
        else:
            omitted_details += 1

    def add(name, blob, size, category, artifact_id=None):
        nonlocal total
        try:
            if len(files) >= COUNT_LIMIT or total + size > RUN_LIMIT:
                raise ValueError('Cumulative run archive budget exceeded')
            item = managed_entry(store, name, blob, size, category, artifact_id)
            files.append(item)
            total += size
        except (ValueError, OSError) as exc:
            skip(name, str(exc))

    for source in run['snapshot']['files']:
        if any(matches(source['path'], r) for r in plan['rules']):
            add(source['path'], source['blob'], source['size'], 'source')
    # Only the finishing recorder calls this path, not generic crash recovery.
    sim = store.simulation(run['simulation_id'])
    sim = {**sim, 'config': run['capture_config']}
    after = fingerprint_outputs(sim, plan)
    candidates = set(after) | set(plan['before']) | {r for r in plan['future'] if '*' not in r}
    for name in sorted(candidates):
        current = after.get(name)
        reason = None
        if not current:
            reason = 'Missing after execution'
        elif current.get('error'):
            reason = current['error']
        elif plan['before'].get(name, {}).get('error'):
            reason = 'Initial bytes could not be verified'
        elif current == plan['before'].get(name):
            reason = 'Unchanged pre-existing output; not attributed to this run'
        else:
            a = next((a for a in run['artifacts'] if a.get('automatic') and a['name'] == name and a.get('blob') == current['hash'] and a['policy'] == 'copy'), None)
            if a:
                add(name, a['blob'], a['size'], 'result', a['id'])
            else:
                reason = 'No verified matching run-specific managed copy; changed, skipped or reference-only output'
        if reason:
            skip(name, reason)
    for pattern in plan['future']:
        if '*' in pattern and not any(future_match(name, [pattern]) for name in candidates):
            skip(pattern, 'No matching outputs after execution')
    if omitted_details:
        skipped.append({'name': 'Additional omissions', 'reason': f'{omitted_details} more files skipped; detail list limited to 1,000.'})
    pending = {'id': uuid.uuid4().hex, 'created_at': now(), 'kind': 'initial', 'repository': plan['repository'],
               'simulation': run['simulation_id'], 'run': run_id, 'files': files, 'skipped': skipped}
    with store.connection() as conn:
        conn.execute('INSERT INTO metadata VALUES (?,?)', (PREFIX + 'pending:' + run_id, json_text(pending)))
        conn.execute('UPDATE metadata SET value=? WHERE key=?', (json_text({'state': 'captured'}), PREFIX + 'initial:' + run_id))
    publish(store, run_id)


def finish_safely(store, run_id):
    from . import preservation
    namespace = PRESERVATION_PREFIX if preservation.get(store, 'initial:' + run_id) else PREFIX
    try:
        if namespace == PRESERVATION_PREFIX:
            preservation.finalize(store, run_id)
        else:
            finalize(store, run_id)
    except Exception as exc:
        try:
            put(store, 'error:' + run_id, str(exc), namespace=namespace)
        except Exception:
            pass  # Optional preservation failure never replaces scientific outcome.


@unavailable_errors
@locked_store
def download_record(store, run_id, event_id):
    event = next((e for e in entries(store, run_id) if e['id'] == event_id), None)
    if not event:
        raise ValueError('No preservation manifest for this event.')
    saved = connection(store)
    if saved['identity'] != event['repository']['identity']:
        raise ValueError('Connect the original archive for this record.')
    path = f"simulations/{event['simulation']}/runs/{run_id}/{event_id}/manifest.json"
    expected = {k: v for k, v in event.items() if k not in ('review', 'repository', 'commit')}
    with repo_lock(store, saved) as root:
        raw = git(root, 'show', f"{event['commit']}:{path}", limit=16 * 1024**2)
    if raw != json_text(expected).encode():
        raise ValueError('Historical preservation record failed verification.')
    return raw
