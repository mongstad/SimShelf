"""Data-only SWSS 2 metadata. No source execution or alternate-file discovery."""
from __future__ import annotations

import hashlib
import math
import os
from pathlib import Path
import re
import stat
import tomllib

DOCUMENT_LIMIT = 262144
SOURCE_LIMIT = 16 * 1024 * 1024
IDENT = r'[a-z][a-z0-9_]{0,63}'
ALIAS = r'(?:--[A-Za-z][A-Za-z0-9_-]*|-[A-Za-z])'


def portable_path(name):
    if (not isinstance(name, str) or len(name.encode('utf-8')) > 1024
            or any(c in name for c in '\\:')
            or any(ord(c) < 32 or ord(c) == 127 for c in name)
            or any(p in ('', '.', '..') for p in name.split('/'))):
        raise ValueError('Unsafe SWSS relative path')
    return name.split('/')


def safe_read(root, name, limit=DOCUMENT_LIMIT, *, identity_only=False, hashing=False):
    """Walk held directory fds, then recheck every association after reading."""
    parts = portable_path(name)
    if not hasattr(os, 'O_NOFOLLOW') or os.open not in os.supports_dir_fd:
        raise ValueError('Safe SWSS file access unavailable on this platform')
    fds, links = [], []
    identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    try:
        fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        fds.append(fd)
        for part in parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            fds.append(child)
            links.append((fd, part, child))
            fd = child
        file = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        fds.append(file)
        before = os.fstat(file)
        if not stat.S_ISREG(before.st_mode) or (not identity_only and before.st_size > limit):
            raise ValueError('SWSS file is not regular or exceeds its byte limit')
        chunks, size, digest = [], 0, hashlib.sha256()
        if not identity_only:
            while chunk := os.read(file, min(65536, limit + 1 - size)):
                if hashing:
                    digest.update(chunk)
                else:
                    chunks.append(chunk)
                size += len(chunk)
                if size > limit:
                    raise ValueError('SWSS file exceeds its byte limit')
        after = os.fstat(file)
        current = os.stat(parts[-1], dir_fd=fd, follow_symlinks=False)
        if identity(before) != identity(after) or identity(after) != identity(current):
            raise ValueError('SWSS file changed while reading; review again')
        for parent, part, child in links:
            observed = os.stat(part, dir_fd=parent, follow_symlinks=False)
            held = os.fstat(child)
            if not stat.S_ISDIR(observed.st_mode) or (observed.st_dev, observed.st_ino) != (held.st_dev, held.st_ino):
                raise ValueError('SWSS directory association changed while reading')
        observed, held = os.stat(root, follow_symlinks=False), os.fstat(fds[0])
        if not stat.S_ISDIR(observed.st_mode) or (observed.st_dev, observed.st_ino) != (held.st_dev, held.st_ino):
            raise ValueError('SWSS root association changed while reading')
        return None if identity_only else (digest.hexdigest(), size) if hashing else b''.join(chunks)
    finally:
        for fd in reversed(fds):
            os.close(fd)


def parse(data):
    if len(data) > DOCUMENT_LIMIT:
        raise ValueError('SWSS document exceeds 262144 bytes')
    text = data.decode('utf-8')
    # Bound syntactic nesting before tomllib allocates recursive arrays/tables.
    # Strings/comments are skipped lexically; TOML itself validates their syntax.
    i, nesting = 0, 0
    syntax = []
    while i < len(text):
        c = text[i]
        if c == '#':
            end = text.find('\n', i)
            i = len(text) if end < 0 else end
            continue
        if c in "\"'":
            quote = c * (3 if text.startswith(c * 3, i) else 1)
            i += len(quote)
            while i < len(text) and not text.startswith(quote, i):
                if c == '"' and text[i] == '\\':
                    i += 1
                i += 1
            i += len(quote)
            continue
        syntax.append(c)
        if c in '[{':
            nesting += 1
            if nesting > 8:
                raise ValueError('SWSS nesting exceeds depth 8')
        elif c in ']}':
            nesting -= 1
        i += 1
    # Dotted table/key paths can allocate deep dictionaries without brackets.
    # Check the lexical key/header prefix before parsing (strings already removed).
    for line in ''.join(syntax).splitlines():
        prefix = line.split('=', 1)[0]
        if prefix.count('.') > 7:
            raise ValueError('SWSS dotted paths exceed depth 8')
    raw = tomllib.loads(text)
    count = 0

    def visit(value, depth=1, location=(), key=False):
        nonlocal count
        if isinstance(value, (dict, list)):
            if depth > 8:
                raise ValueError('SWSS nesting exceeds depth 8')
            count += len(value)
            if count > 4096:
                raise ValueError('SWSS document exceeds 4096 entries')
            for k, v in (value.items() if isinstance(value, dict) else enumerate(value)):
                if isinstance(k, str):
                    visit(k, depth, location, True)
                visit(v, depth + 1 if isinstance(v, (dict, list)) else depth, (*location, k))
        elif isinstance(value, str):
            multiline = not key and (location[:1] == ('extensions',) or location[-1:] == ('help',))
            if len(value.encode('utf-8')) > 4096 or any((ord(c) < 32 or ord(c) == 127) and not (multiline and c in '\n\t') for c in value):
                raise ValueError('SWSS string exceeds bounds or contains control characters')
        elif isinstance(value, float) and not math.isfinite(value):
            raise ValueError('SWSS numbers must be finite')
        elif type(value) not in (int, float, bool) and location[:1] != ('extensions',):
            raise ValueError('SWSS portable dates/times are unsupported')
    visit(raw)
    if set(raw) - {'swss', 'extensions'} or not isinstance(raw.get('swss'), dict):
        raise ValueError('Use only [swss] and optional [extensions.identifier] tables')
    extensions = raw.get('extensions', {})
    if not isinstance(extensions, dict) or any(not re.fullmatch(r'[a-z][a-z0-9_-]{0,63}', k) or not isinstance(v, dict) for k, v in extensions.items()):
        raise ValueError('Invalid SWSS extension tables')
    s = raw['swss']
    if set(s) - {'schema_version', 'entrypoint', 'simulation_version', 'parameters', 'source_files'} or type(s.get('schema_version')) is not int or s['schema_version'] != 2:
        raise ValueError('SWSS requires schema_version = 2 and supported portable fields')
    portable_path(s.get('entrypoint'))
    if not isinstance(s.get('simulation_version'), str) or not s['simulation_version'].strip():
        raise ValueError('SWSS requires simulation_version')
    return raw


def parameters(s):
    entries = s.get('parameters', [])
    if not isinstance(entries, list) or len(entries) > 128:
        raise ValueError('SWSS permits at most 128 parameter rows')
    ids, aliases, rows = set(), set(), []
    for p in entries:
        if not isinstance(p, dict) or not isinstance(p.get('id'), str) or not re.fullmatch(IDENT, p['id']) or p['id'] in ids:
            raise ValueError('Missing, invalid or duplicate SWSS parameter ID')
        ids.add(p['id'])
        flags = p.get('options', [])
        if p.get('kind') == 'option' or 'options' in p:
            if not isinstance(flags, list) or not 1 <= len(flags) <= 8 or any(not isinstance(f, str) or len(f.encode()) > 128 or not re.fullmatch(ALIAS, f) for f in flags) or len(set(flags)) != len(flags) or aliases.intersection(flags):
                raise ValueError('Invalid or duplicate SWSS option aliases')
            aliases.update(flags)
        choices = p.get('choices')
        if isinstance(choices, list) and len(choices) > 100:
            raise ValueError('SWSS permits at most 100 choices')
        reason = ''
        required = {'id', 'kind', 'required', 'type', 'action', 'help'}
        if not required <= p.keys() or p.keys() - (required | {'options', 'name', 'choices', 'default', 'repeatable'}):
            reason = 'Missing or unsupported row fields'
        kind, action = p.get('type'), p.get('action')
        if (p.get('kind') != 'option' or 'name' in p or type(p.get('required')) is not bool
                or not isinstance(p.get('help'), str) or type(p.get('repeatable', False)) is not bool or p.get('repeatable')
                or (kind == 'boolean' and action not in ('store_true', 'store_false'))
                or (kind in ('integer', 'float', 'string') and action != 'store')
                or kind not in ('integer', 'float', 'string', 'boolean')):
            reason = 'Positional, repeatable or unsupported type/action row'
        def valid(v):
            return ((kind == 'integer' and type(v) is int and -(2**63) <= v < 2**63)
                    or (kind == 'float' and type(v) is float and math.isfinite(v))
                    or (kind == 'string' and isinstance(v, str))
                    or (kind == 'boolean' and type(v) is bool))
        if 'default' in p and not valid(p['default']):
            reason = 'Default has wrong declared type/range'
        if 'choices' in p and (kind == 'boolean' or not isinstance(choices, list) or not choices or any(not valid(v) for v in choices)
                or any(v in choices[:i] for i, v in enumerate(choices)) or ('default' in p and p['default'] not in choices)):
            reason = 'Invalid choices or default outside choices'
        def transport(v):
            # JSON numbers cannot preserve all signed-64-bit integer hints in JS.
            return str(v) if type(v) is int and abs(v) > 2**53 - 1 else v
        rows.append({'id': p['id'], 'flags': flags, 'name': flags[0] if flags else p['id'],
                     'help': p.get('help', '') if isinstance(p.get('help', ''), str) else '',
                     'type': {'integer': 'int', 'float': 'float', 'string': 'str', 'boolean': 'bool'}.get(kind, 'unknown') if isinstance(kind, str) else 'unknown',
                     'action': action if isinstance(action, str) else 'unknown', 'required': p.get('required') is True,
                     'choices': [transport(v) for v in choices] if not reason and choices is not None else None, 'default_known': 'default' in p and not reason,
                     'default': transport(p.get('default')) if not reason else None, 'source': 'swss.toml',
                     'supported': not reason, 'reason': reason + '; use manual argv.' if reason else ''})
    return rows


def read(root, entrypoint=None, version_file=None):
    data = safe_read(root, 'swss.toml')
    raw = parse(data)
    s = raw['swss']
    rows = parameters(s)
    reasons, hashes = [], []
    if entrypoint is not None and s['entrypoint'] != entrypoint:
        reasons.append('SWSS entrypoint does not match the selected entrypoint')
    # Association itself is always checked, even with no source manifest.
    safe_read(root, s['entrypoint'], identity_only=True)
    sources = s.get('source_files')
    if sources is not None:
        if not isinstance(sources, list) or len(sources) > 32:
            raise ValueError('SWSS permits at most 32 bound sources')
        paths, total = set(), 0
        for source in sources:
            if not isinstance(source, dict) or set(source) != {'path', 'sha256'}:
                raise ValueError('Invalid SWSS source binding')
            name, expected = source['path'], source['sha256']
            portable_path(name)
            if name in paths or not isinstance(expected, str) or not re.fullmatch('[0-9a-f]{64}', expected):
                raise ValueError('Duplicate source path or invalid SHA-256')
            paths.add(name)
            actual, size = safe_read(root, name, min(SOURCE_LIMIT, 64 * 1024 * 1024 - total), hashing=True)
            total += size
            hashes.append({'path': name, 'sha256': actual, 'expected': expected})
            if actual != expected:
                reasons.append('Source binding changed: ' + name)
        if s['entrypoint'] not in paths:
            raise ValueError('SWSS source_files must include the entrypoint')
    # The SWSS declaration owns its version. An application-local Python tag
    # is not an independent SWSS version authority. Keep the optional argument
    # and provenance key for existing callers and historical record shape.
    comparable = None
    status = 'stale / manual-only' if reasons else 'listed bytes verified' if sources is not None else 'binding unverified'
    evidence = {'path': 'swss.toml', 'bytes_utf8': data.decode('utf-8'), 'sha256': hashlib.sha256(data).hexdigest(),
                'schema_version': 2, 'simulation_version': s['simulation_version'], 'entrypoint': entrypoint or s['entrypoint'],
                'discovery_source': 'swss.toml', 'binding_status': status, 'binding_reasons': reasons,
                'checked_sources': hashes, 'comparable_version': comparable}
    fingerprint = hashlib.sha256(repr(evidence).encode()).hexdigest()
    return {'raw': raw, 'parameters': [] if reasons else rows, 'warnings': reasons + [status + '; checks do not isolate later source edits or prove runtime semantics.'],
            'source': 'swss.toml', 'fingerprint': fingerprint, 'provenance': evidence}


def reject_legacy(root):
    for name in ('simshelf.toml', 'simshelf-arguments.json', 'swss-parameters.toml'):
        if os.path.lexists(Path(root) / name):
            raise ValueError(f'{name} is unsupported for new runs. Review and replace it explicitly with swss.toml schema 2; historical records remain intact.')


def output_policy_status(discovery, present):
    """Local allocation eligibility, never a claim of SWSS conformance."""
    provenance = discovery['provenance']
    if provenance and not provenance['binding_reasons']:
        return {'state': 'valid', 'launcher_allowed': False,
                'binding': provenance['binding_status'],
                'reason': 'Use Fixed output parent: the simulation creates its unique run directory and SimShelf watches the parent. Metadata does not establish a coordinated-root agreement.'}
    if present or provenance:
        return {'state': 'unavailable', 'launcher_allowed': False,
                'binding': provenance['binding_status'] if provenance else 'unverified',
                'reason': 'SWSS metadata is invalid, unsupported, stale or not associated. Output ownership is unknown. Review the capture parent and explicitly choose Fixed output parent for manual execution, or correct the metadata before reviewing again.'}
    return {'state': 'absent', 'launcher_allowed': True, 'binding': 'unverified',
            'reason': 'No SWSS metadata. Launcher-coordinated allocation requires explicit script support for SIMSHELF_OUTPUT_DIR or joined run.output_dir.'}


def review(simulation, decision=None):
    """Recheck before launch; client supplies only a digest and explicit mode."""
    from .parameters import discover_parameters
    reject_legacy(simulation['root'])
    current = discover_parameters(simulation)
    if decision is not None:
        if not isinstance(decision, dict) or set(decision) - {'mode', 'fingerprint'} or decision.get('mode') not in ('typed', 'manual'):
            raise ValueError('Invalid parameter review')
        if decision.get('fingerprint') is not None and (not isinstance(decision['fingerprint'], str) or not re.fullmatch('[0-9a-f]{64}', decision['fingerprint'])):
            raise ValueError('Invalid parameter review fingerprint')
        if decision.get('mode') == 'typed' and (not current['provenance'] or current['provenance']['binding_reasons'] or decision.get('fingerprint') != current['fingerprint']):
            raise ValueError('SWSS declarations/bindings changed or are unavailable. Rescan and review, or explicitly use manual argv.')
    return {**current, 'previous_provenance': simulation.get('parameter_provenance'), 'decision': decision or {'mode': 'manual', 'fingerprint': None}}
