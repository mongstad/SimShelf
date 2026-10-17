"""Opt-in, local-only Git observations. No Git/source writes or transport commands."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import selectors
import shutil
import signal
import socket
import stat
import subprocess
import time

from .common import json_text
from .workspace_lock import locked_store

KEY = 'git_connection_v1'
LIMIT = 4 * 1024 * 1024


class Unavailable(ValueError):
    pass


def git(root: Path, *args: str) -> bytes:
    executable = shutil.which('git')
    if not executable:
        raise Unavailable('Git is not installed; recording remains available.')
    # Ignore inherited repository, config, credential and transport overrides.
    env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
               GIT_TERMINAL_PROMPT='0', GIT_OPTIONAL_LOCKS='0',
               GIT_NO_LAZY_FETCH='1', GIT_NO_REPLACE_OBJECTS='1',
               GIT_PAGER='cat', LC_ALL='C')
    command = [executable, '--no-pager', '--no-optional-locks',
               '-c', 'core.fsmonitor=false', '-c', 'core.hooksPath=/dev/null',
               '-c', 'protocol.allow=never', '-C', str(root), *args]
    # Stream a bounded result; no shell, pager, diff driver, filter or status refresh.
    try:
        with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                              stdin=subprocess.DEVNULL, env=env, start_new_session=True) as process:
            chunks, size, deadline = [], 0, time.monotonic() + 3
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdout, selectors.EVENT_READ)
                try:
                    while selector.get_map():
                        remaining = deadline - time.monotonic()
                        if remaining <= 0:
                            raise Unavailable('Git inspection timed out; state is unknown.')
                        for key, _ in selector.select(min(remaining, .1)):
                            chunk = os.read(key.fileobj.fileno(), 65536)
                            if not chunk:
                                selector.unregister(key.fileobj)
                                continue
                            size += len(chunk)
                            if size > LIMIT:
                                raise Unavailable('Git inspection exceeds the bounded result limit.')
                            chunks.append(chunk)
                    process.wait(timeout=max(.01, deadline - time.monotonic()))
                    if process.returncode:
                        raise Unavailable('Git inspection unavailable; check repository access and integrity.')
                    return b''.join(chunks)
                finally:
                    if process.poll() is None:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait()
    except (OSError, subprocess.SubprocessError) as exc:
        raise Unavailable('Git inspection unavailable; recording remains available.') from exc


def text(root, *args):
    return git(root, *args).decode('utf-8', 'replace').strip()


def repository(path: str | Path) -> dict:
    try:
        root = Path(path).expanduser().resolve(strict=True)
    except (OSError, ValueError, TypeError) as exc:
        raise Unavailable('Repository folder is unavailable.') from exc
    if not root.is_dir():
        raise Unavailable('Choose an existing repository folder.')
    top = Path(text(root, 'rev-parse', '--show-toplevel')).resolve(strict=True)
    gitdir = Path(text(top, 'rev-parse', '--absolute-git-dir')).resolve(strict=True)
    # Identity prevents a different repository silently taking over an old path.
    st = gitdir.stat()
    identity = hashlib.sha256(f'{top}\0{gitdir}\0{st.st_dev}\0{st.st_ino}'.encode()).hexdigest()
    return {'root': str(top), 'identity': identity}


def connection(store):
    with store.connection() as conn:
        row = conn.execute('SELECT value FROM metadata WHERE key=?', (KEY,)).fetchone()
    return json.loads(row[0]) if row else None


def workspace_identity(store):
    st = store.path.stat()
    return hashlib.sha256(f'{socket.gethostname()}\0{store.path}\0{st.st_dev}\0{st.st_ino}'.encode()).hexdigest()


def preview(store, path: str, simulation_ids: list[str]) -> dict:
    if not path.strip() or len(path) > 4096 or len(simulation_ids) > 1000:
        raise ValueError('Choose a repository and at most 1,000 registered simulations.')
    repo = repository(path)
    root = Path(repo['root'])
    if root.is_relative_to(store.path) or store.path.is_relative_to(root):
        raise ValueError('Keep the source repository separate from the SimShelf library.')
    mappings = {}
    for ident in sorted(set(simulation_ids)):
        try:
            source = Path(store.simulation(ident)['root']).resolve(strict=True)
        except OSError as exc:
            raise ValueError('A selected simulation folder is unavailable.') from exc
        if not source.is_relative_to(root) or repository(source) != repo:
            raise ValueError('Every selected simulation must belong to this repository, not a nested repository.')
        mappings[ident] = source.relative_to(root).as_posix()
    return {**repo, 'mappings': mappings, 'workspace': str(store.path), 'workspace_identity': workspace_identity(store), 'format': 1}


def discover(store, ident: str):
    """Read-only suggestions; never persist a connection or change provenance."""
    simulation = store.simulation(ident)
    empty = {'status': 'unavailable', 'reason': None, 'preview': None,
             'eligible': [], 'partial': False}
    try:
        if not shutil.which('git'):
            raise Unavailable('Git is not installed. Recording remains available.')
        source = Path(simulation['root']).resolve(strict=True)
        if not source.is_dir():
            raise Unavailable('The registered source folder is unavailable.')
        if not any(os.path.lexists(parent / '.git') for parent in (source, *source.parents)):
            return {**empty, 'status': 'not_found'}
        proposed = preview(store, str(source), [ident])
        root = Path(proposed['root'])
        eligible = [{'id': ident, 'subdirectory': proposed['mappings'][ident]}]
        deadline = time.monotonic() + 10
        partial = False
        checked = 0
        for other in store.simulations():
            if other['id'] == ident:
                continue
            if checked >= 100 or time.monotonic() >= deadline:
                partial = True
                break
            checked += 1
            try:
                candidate = Path(other['root']).resolve(strict=True)
                if candidate.is_relative_to(root) and repository(candidate) == {k: proposed[k] for k in ('root', 'identity')}:
                    eligible.append({'id': other['id'], 'subdirectory': candidate.relative_to(root).as_posix()})
            except (OSError, ValueError):
                continue
        return {'status': 'found', 'reason': None, 'preview': proposed,
                'eligible': eligible, 'partial': partial}
    except (OSError, ValueError) as exc:
        return {**empty, 'reason': str(exc) if isinstance(exc, ValueError) else 'The registered source folder is unavailable.'}


@locked_store
def connect_repository(store, proposed: dict):
    if not isinstance(proposed, dict) or not isinstance(proposed.get('root'), str) or not isinstance(proposed.get('mappings'), dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in proposed['mappings'].items()):
        raise ValueError('Invalid connection preview; review the repository again.')
    checked = preview(store, proposed['root'], list(proposed['mappings']))
    if checked != proposed:
        raise ValueError('Repository or simulation mapping changed; review the connection again.')
    if connection(store):
        raise ValueError('Disconnect the current repository before connecting another.')
    if not checked['mappings']:
        raise ValueError('Select at least one registered simulation.')
    with store.connection() as conn:
        conn.execute('INSERT INTO metadata(key,value) VALUES (?,?)', (KEY, json_text(checked)))
    return checked


@locked_store
def disconnect_repository(store):
    with store.connection() as conn:
        conn.execute('DELETE FROM metadata WHERE key=?', (KEY,))
    return {'connected': False}


def tree(root, commit):
    entries = {}
    for row in git(root, 'ls-tree', '-r', '-z', commit).split(b'\0'):
        if not row:
            continue
        info, name = row.split(b'\t', 1)
        mode, kind, oid = info.decode('ascii').split()
        entries[os.fsdecode(name)] = (mode, kind, oid)
    return entries


def blob_id(data, algorithm):
    return hashlib.new(algorithm, b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def read_worktree_file(root, name):
    # Traverse through directory descriptors, refusing links at every component.
    parts = Path(name).parts
    if Path(name).is_absolute() or not parts or any(p in ('..', '.') for p in parts):
        raise Unavailable('Unsafe tracked path.')
    descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=descriptor)
        with os.fdopen(fd, 'rb') as stream:
            before = os.fstat(stream.fileno())
            if not stat.S_ISREG(before.st_mode) or before.st_size > 32 * 1024 * 1024:
                raise Unavailable('Unsupported or oversized tracked file.')
            data = stream.read(32 * 1024 * 1024 + 1)
            after = os.fstat(stream.fileno())
            if len(data) > 32 * 1024 * 1024 or (before.st_mtime_ns, before.st_size) != (after.st_mtime_ns, after.st_size):
                raise Unavailable('Source changed during inspection.')
            return data, after.st_mode
    finally:
        os.close(descriptor)


def worktree_state(root, entries, algorithm, subdir):
    """Conservative raw-byte status, intentionally avoiding user clean filters."""
    index = {}
    conflicts = False
    for row in git(root, 'ls-files', '--stage', '-z').split(b'\0'):
        if row:
            info, name = row.split(b'\t', 1)
            mode, oid, stage = info.decode('ascii').split()
            conflicts |= stage != '0'
            index[os.fsdecode(name)] = (mode, 'blob' if mode != '160000' else 'commit', oid)
    changed = set(entries) ^ set(index)
    changed.update(name for name in entries.keys() & index.keys() if entries[name] != index[name])
    unknown = False
    total_bytes = 0
    if len(index) > 10000:
        raise Unavailable('Repository exceeds the 10,000-file inspection limit.')
    for name, (mode, kind, oid) in index.items():
        path = root / name
        # Never follow symlinks or read outside the repository, including ancestor links.
        if kind != 'blob' or mode == '120000' or not path.resolve().is_relative_to(root):
            unknown = True
            continue
        try:
            data, mode_bits = read_worktree_file(root, name)
        except FileNotFoundError:
            changed.add(name)
            continue
        except (OSError, Unavailable):
            unknown = True
            continue
        total_bytes += len(data)
        if total_bytes > 100 * 1024 * 1024:
            raise Unavailable('Repository exceeds the 100 MB inspection limit.')
        if blob_id(data, algorithm) != oid or bool(mode_bits & 0o111) != (mode == '100755'):
            changed.add(name)
    untracked = {os.fsdecode(n) for n in git(root, 'ls-files', '--others', '--exclude-standard', '-z').split(b'\0') if n}
    changed |= untracked
    scope = lambda n: subdir == '.' or n.startswith(subdir + '/')
    return {'dirty': True if changed else None if unknown else False,
            'simulation_dirty': True if any(scope(n) for n in changed) else None if unknown else False,
            'conflicts': conflicts, 'changed_count': len(changed), 'untracked_count': len(untracked),
            'comparison': 'raw_bytes', 'incomplete': unknown}


def observe(store, simulation, snapshot=None, *, history=False):
    result = {'format': 1, 'availability': 'disabled', 'reason': None, 'repository': None,
              'subdirectory': None, 'commit': None, 'branch': None, 'dirty': None,
              'simulation_dirty': None, 'snapshot_id': snapshot['id'] if snapshot else None,
              'snapshot_relation': 'unknown', 'history': []}
    try:
        saved = connection(store)
        if saved is not None and (not isinstance(saved, dict) or saved.get('format') != 1 or not isinstance(saved.get('mappings'), dict)):
            raise ValueError('Invalid saved connection')
    except (ValueError, TypeError):
        result.update(availability='unavailable', reason='Invalid Git settings; disconnect and reconnect Git.')
        return result
    if not saved:
        return result
    result['availability'] = 'unmapped'
    subdir = saved.get('mappings', {}).get(simulation['id'])
    if subdir is None:
        return result
    result.update(availability='unavailable', subdirectory=subdir)
    try:
        if saved.get('workspace') != str(store.path) or saved.get('workspace_identity') != workspace_identity(store):
            raise Unavailable('Restored or moved library: disconnect and explicitly reconnect Git on this computer.')
        repo = repository(saved['root'])
        if repo['identity'] != saved['identity']:
            raise Unavailable('Repository identity changed; disconnect and review a new connection.')
        root = Path(repo['root'])
        source = Path(simulation['root']).resolve(strict=True)
        if source != (root / subdir).resolve() or not source.is_relative_to(root) or repository(source) != repo:
            raise Unavailable('Simulation mapping changed or is no longer inside the connected repository.')
        result['repository'] = repo
        # symbolic-ref returns empty for detached HEAD without executing hooks/config commands.
        try:
            result['branch'] = text(root, 'rev-parse', '--abbrev-ref', 'HEAD')
        except Unavailable:
            raise Unavailable('No readable HEAD commit. A new repository needs a first commit in your Git tools; recording remains available.')
        if result['branch'] == 'HEAD':
            result['branch'] = None
        commit = text(root, 'rev-parse', '--verify', 'HEAD^{commit}')
        if len(commit) not in (40, 64) or any(c not in '0123456789abcdef' for c in commit):
            raise Unavailable('No valid commit available.')
        algorithm = 'sha1' if len(commit) == 40 else 'sha256'
        entries = tree(root, commit)
        result.update(commit=commit, **worktree_state(root, entries, algorithm, subdir))
        if snapshot:
            from .source import blob_path
            same = True
            for file in snapshot['files']:
                name = file['path'] if subdir == '.' else subdir + '/' + file['path']
                entry = entries.get(name)
                expected_mode = '100755' if file['mode'] & 0o111 else '100644'
                if not entry or entry[:2] != (expected_mode, 'blob') or blob_id(blob_path(store.path, file['blob']).read_bytes(), algorithm) != entry[2]:
                    same = False
                    break
            result['snapshot_relation'] = 'captured_files_match_commit' if same else 'captured_files_differ'
        if history:
            raw = git(root, 'log', '-20', '--no-show-signature', '--format=%H%x00%ct%x00%s%x00', commit, '--', subdir)
            fields = raw.decode('utf-8', 'replace').split('\0')
            for i in range(0, len(fields) - 2, 3):
                result['history'].append({'commit': fields[i].strip(), 'timestamp': fields[i+1], 'subject': fields[i+2][:500]})
        if text(root, 'rev-parse', '--verify', 'HEAD^{commit}') != commit:
            raise Unavailable('Repository changed during inspection; refresh to try again.')
        result['availability'] = 'available'
    except (ValueError, OSError, KeyError, TypeError) as exc:
        result.update(availability='unavailable', reason=str(exc) if isinstance(exc, Unavailable) else 'Repository unavailable; check the saved connection.',
                      dirty=None, simulation_dirty=None, snapshot_relation='unknown', history=[])
    return result
