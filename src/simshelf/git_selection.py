"""Explicit inclusion preferences and append-only, reviewed local ignore additions.

Independent of the recorder/provenance contract. No staging or Git mutations.
"""
from __future__ import annotations

from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import time

from .common import json_text
from .git_provenance import git, repository, workspace_identity
from .workspace_lock import locked_store

MAX_ENTRIES = 1000
MAX_RULES = 100
KEY = 'git_selection_v1:'


def digest(value):
    return hashlib.sha256(json_text(value).encode()).hexdigest()


@contextmanager
def directory(path):
    """Pin each component without following links, including the source root."""
    path = Path(path)
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path.parts[1:]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        yield fd
    finally:
        os.close(fd)


def stamp(st):
    return [st.st_dev, st.st_ino, st.st_mode, st.st_size, st.st_mtime_ns, st.st_ctime_ns]


def ignore_bytes(fd):
    try:
        child = os.open('.gitignore', os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
    except FileNotFoundError:
        return b'', None
    with os.fdopen(child, 'rb') as stream:
        st = os.fstat(stream.fileno())
        if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1 or st.st_size > 65536:
            raise ValueError('Ignore file is linked, unsupported or larger than 64 KiB.')
        data = stream.read(65537)
        if len(data) > 65536 or stamp(st) != stamp(os.fstat(stream.fileno())):
            raise ValueError('Ignore file changed during inspection.')
        data.decode('utf-8')
        return data, stamp(st)


def saved_settings(store, ident, binding):
    with store.connection() as conn:
        row = conn.execute('SELECT value FROM metadata WHERE key=?', (KEY + ident,)).fetchone()
    saved = json.loads(row[0]) if row else None
    return saved if saved and saved.get('binding') == binding else None


def inventory(store, ident):
    """Metadata only, except bounded .gitignore text; never read scientific files."""
    source = Path(store.simulation(ident)['root'])
    try:
        if source.is_relative_to(store.path) or store.path.is_relative_to(source):
            raise ValueError('Keep source folders separate from the SimShelf library.')
        repo, reason = None, None
        try:
            if any(os.path.lexists(p / '.git') for p in (source, *source.parents)):
                repo = repository(source)
        except (OSError, ValueError):
            reason = 'Git inspection unavailable. Preferences remain local; ignore writes are disabled.'
        files, ignores, blocked = [], [], []
        signatures = []
        deadline = time.monotonic() + 5
        count = 0
        with directory(source) as rootfd:
            rootstat = os.fstat(rootfd)
            binding = {'source': str(source), 'inode': [rootstat.st_dev, rootstat.st_ino],
                       'workspace': workspace_identity(store), 'repository': repo}
            def scan(fd, prefix='', depth=0):
                nonlocal count
                if depth > 20 or time.monotonic() > deadline:
                    raise ValueError('Source inventory exceeds the depth/time limit. Use a smaller registered project folder.')
                with os.scandir(fd) as entries:
                    names = []
                    for entry in entries:
                        count += 1
                        if count > MAX_ENTRIES:
                            raise ValueError('Source inventory exceeds 1,000 entries. Use a smaller registered project folder.')
                        names.append(entry.name)
                for name in sorted(names):
                    if name == '.git':
                        continue
                    path = prefix + name
                    st = os.stat(name, dir_fd=fd, follow_symlinks=False)
                    signatures.append([path, stamp(st)])
                    if any(ord(c) < 32 or ord(c) == 127 or 0xD800 <= ord(c) <= 0xDFFF for c in path) or len(path) > 512:
                        blocked.append('Unsupported filename (not displayed)'); continue
                    if stat.S_ISDIR(st.st_mode):
                        child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                        try:
                            try:
                                os.stat('.git', dir_fd=child, follow_symlinks=False)
                                blocked.append(path + '/ (independent repository)')
                            except FileNotFoundError:
                                scan(child, path + '/', depth + 1)
                        finally:
                            os.close(child)
                    elif stat.S_ISREG(st.st_mode) and st.st_nlink == 1:
                        files.append({'path': path, 'size': st.st_size, 'state': 'unknown',
                                      'risk': 'Large file; review scientific inputs/results' if st.st_size > 10 * 1024 * 1024 else
                                      'May contain credentials' if name.startswith('.env') or name.lower() in ('id_rsa', 'id_ed25519', 'credentials') else
                                      'May be scientific input or results' if Path(name).suffix.lower() in ('.json', '.csv', '.npz', '.npy', '.wvz', '.png', '.jpg', '.h5', '.hdf5', '.ckpt') else ''})
                        if name == '.gitignore':
                            data, sig = ignore_bytes(fd)
                            ignores.append({'path': path, 'text': data.decode('utf-8')})
                            signatures.append([path, sig, hashlib.sha256(data).hexdigest()])
                    else:
                        blocked.append(path + ' (link or special file)')
            scan(rootfd)
            target, target_stamp = ignore_bytes(rootfd)
        subdir = None
        if repo:
            root = Path(repo['root'])
            if root.is_relative_to(store.path) or store.path.is_relative_to(root):
                raise ValueError('Keep the Git repository separate from the SimShelf library.')
            subdir = source.relative_to(root).as_posix()
            def paths(*args):
                return {os.fsdecode(p) for p in git(root, 'ls-files', *args, '-z', '--', subdir).split(b'\0') if p}
            try:
                tracked = paths('--cached')
                signatures.append(['index', hashlib.sha256(git(root, 'ls-files', '--stage', '-z', '--', subdir)).hexdigest()])
                ignored = paths('--others', '--ignored', '--exclude-standard') | paths('--cached', '--ignored', '--exclude-standard')
                for item in files:
                    rel = item['path'] if subdir == '.' else subdir + '/' + item['path']
                    item['state'] = 'tracked' if rel in tracked else 'ignored' if rel in ignored else 'untracked'
                    item['ignored_rule'] = rel in ignored
                # Expose authored parent rules, but never read arbitrary configured exclude paths.
                parent = source.parent
                while source != root and parent.is_relative_to(root):
                    with directory(parent) as fd:
                        data, sig = ignore_bytes(fd)
                    signatures.append([str(parent / '.gitignore'), sig, hashlib.sha256(data).hexdigest()])
                    if sig:
                        ignores.append({'path': str(parent / '.gitignore'), 'text': data.decode('utf-8')})
                    if parent == root:
                        break
                    parent = parent.parent
            except (OSError, ValueError):
                reason = 'Git inspection unavailable. Preferences remain local; ignore writes are disabled.'
                for item in files:
                    item['state'] = 'unknown'; item.pop('ignored_rule', None)
        else:
            reason = reason or 'No Git repository found. Preferences do not initialize or connect Git.'
        saved = saved_settings(store, ident, binding)
        result = {'source': str(source), 'repository': repo, 'subdirectory': subdir,
                  'reason': reason, 'files': files, 'ignore_files': ignores, 'blocked': blocked,
                  'rules': saved['rules'] if saved else [], 'binding': binding,
                  'ignore_writable': bool(repo and not reason),
                  'target_text': target.decode('utf-8'), 'target_stamp': target_stamp}
        result['revision'] = digest([result, signatures])
        return result
    except (OSError, UnicodeError) as exc:
        raise ValueError('Source or ignore rules unavailable; check permissions and unsupported links. Nothing was changed.') from exc


def rules_checked(rules):
    if not isinstance(rules, list) or len(rules) > MAX_RULES:
        raise ValueError('Choose at most 100 inclusion rules.')
    result = []
    for rule in rules:
        if not isinstance(rule, dict) or set(rule) != {'kind', 'value'}:
            raise ValueError('Invalid inclusion rule.')
        kind, value = rule['kind'], rule['value']
        if kind not in ('file', 'folder', 'extension') or not isinstance(value, str) or not value or len(value) > 512:
            raise ValueError('Invalid inclusion rule.')
        if any(ord(c) < 32 or ord(c) == 127 or 0xD800 <= ord(c) <= 0xDFFF for c in value) or value.startswith('/') or any(p in ('', '.', '..', '.git') for p in value.split('/')):
            raise ValueError('Unsafe inclusion path.')
        if kind == 'extension' and (not value.startswith('.') or '/' in value or any(c in value for c in '*?[]\\')):
            raise ValueError('Choose an exact extension, such as .py; arbitrary globs are not supported.')
        if rule not in result:
            result.append(rule)
    return result


def matches(path, rule):
    return path == rule['value'] if rule['kind'] == 'file' else path.startswith(rule['value'] + '/') if rule['kind'] == 'folder' else Path(path).suffix == rule['value']


def selection_preview(store, ident, revision, rules):
    current = inventory(store, ident)
    if current['revision'] != revision:
        raise ValueError('Files, rules or preferences changed. Refresh and review again.')
    rules = rules_checked(rules)
    return {'revision': revision, 'rules': rules,
            'matches': [{'rule': rule, 'paths': [f['path'] for f in current['files'] if matches(f['path'], rule)]} for rule in rules],
            'selected': [f['path'] for f in current['files'] if any(matches(f['path'], r) for r in rules)]}


@locked_store
def save_selection(store, ident, review):
    checked = selection_preview(store, ident, review.get('revision'), review.get('rules'))
    if checked != review:
        raise ValueError('Review the exact selected paths again.')
    current = inventory(store, ident)
    if current['revision'] != review['revision']:
        raise ValueError('Files changed. Refresh and review again.')
    with store.connection() as conn:
        conn.execute('INSERT OR REPLACE INTO metadata(key,value) VALUES (?,?)',
                     (KEY + ident, json_text({'format': 1, 'binding': current['binding'], 'rules': checked['rules']})))
    return {'saved': True}


def ignore_preview(store, ident, revision, paths):
    current = inventory(store, ident)
    if current['revision'] != revision or not current['ignore_writable']:
        raise ValueError('Git state changed or is unavailable. Refresh and review again.')
    if not isinstance(paths, list) or not paths or len(paths) > 100 or not all(isinstance(p, str) for p in paths):
        raise ValueError('Select 1–100 untracked files to ignore.')
    nested_rules = [r['path'].rsplit('/', 1)[0] + '/' for r in current['ignore_files'] if not r['path'].startswith('/') and '/' in r['path']]
    if any(p.startswith(folder) for p in paths for folder in nested_rules):
        raise ValueError('Nested ignore rules affect these files. Review those rules in your Git tools instead.')
    candidates = {f['path'] for f in current['files'] if f['state'] == 'untracked' and f['path'] != '.gitignore' and not f['path'].endswith('/.gitignore')}
    if not set(paths) <= candidates:
        raise ValueError('Only existing untracked, non-ignored files can receive ignore rules.')
    # Literal, anchored paths only. No broad globs or future extension exclusions.
    def literal(path):
        return '/' + ''.join('\\' + c if c in '\\*?[]#! ' else c for c in path)
    lines = [literal(p) for p in sorted(set(paths))]
    existing = current['target_text']
    if any(line in existing.splitlines() for line in lines):
        raise ValueError('An authored rule already exists or conflicts. Review it in your Git tools.')
    newline = '\r\n' if '\r\n' in existing else '\n'
    addition = (newline if existing and not existing.endswith('\n') else '') + newline.join(lines) + newline
    return {'revision': revision, 'paths': sorted(set(paths)), 'target': str(Path(current['source']) / '.gitignore'),
            'before': existing, 'addition': addition}


@locked_store
def apply_ignore(store, ident, review):
    checked = ignore_preview(store, ident, review.get('revision'), review.get('paths'))
    if checked != review:
        raise ValueError('Review the exact ignore additions again.')
    current = inventory(store, ident)
    if current['revision'] != review['revision']:
        raise ValueError('Files changed. Refresh and review again.')
    source = Path(current['source'])
    try:
        with directory(source) as parent:
            rootst = os.fstat(parent)
            if [rootst.st_dev, rootst.st_ino] != current['binding']['inode']:
                raise ValueError('Source folder replaced. Review again; nothing appended.')
            if rootst.st_uid != os.getuid():
                raise ValueError('Only source folders owned by this user can be edited.')
            flags = os.O_WRONLY | os.O_APPEND | os.O_NOFOLLOW | os.O_NONBLOCK
            if current['target_stamp'] is None:
                flags |= os.O_CREAT | os.O_EXCL
            fd = os.open('.gitignore', flags, 0o644, dir_fd=parent)
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                st = os.fstat(fd)
                if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1 or st.st_uid != os.getuid():
                    raise ValueError('Unsafe ignore target; nothing appended.')
                if current['target_stamp'] is not None and stamp(st) != current['target_stamp']:
                    raise ValueError('Ignore file changed. Review again; nothing appended.')
                with directory(source) as again:
                    if os.fstat(again).st_ino != os.fstat(parent).st_ino or os.stat('.gitignore', dir_fd=again, follow_symlinks=False).st_ino != st.st_ino:
                        raise ValueError('Ignore path changed. Review again; nothing appended.')
                data = review['addition'].encode('utf-8')
                # One append avoids replacing/truncating independently authored bytes.
                if os.write(fd, data) != len(data):
                    raise ValueError('Ignore append was incomplete. Inspect .gitignore before retrying; existing bytes were not replaced.')
                os.fsync(fd)
                if os.stat('.gitignore', dir_fd=parent, follow_symlinks=False).st_ino != st.st_ino:
                    raise ValueError('Ignore path changed during append. Inspect .gitignore before retrying.')
            finally:
                os.close(fd)
    except OSError as exc:
        raise ValueError('Ignore update could not finish. Inspect .gitignore before retrying; no staging or commit was performed.') from exc
    return {'applied': True}
