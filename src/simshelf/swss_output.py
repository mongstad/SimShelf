"""Schema-3 destination resolution, separate from exact argv and solver execution.

All filesystem observations are local, read-only, and rechecked before use.
External capture requires an existing parent; this module never creates it.
"""
from pathlib import Path
import math
import os
import re
import stat

from .common import now
from .swss import parse, parameters


def resolve(provenance, arguments):
    if not provenance or provenance['schema_version'] != 3:
        return None
    if provenance['binding_reasons']:
        raise ValueError('SWSS output destination unavailable: stale/unassociated source binding; correct and rescan.')
    s = parse(provenance['bytes_utf8'].encode())['swss']
    rows = parameters(s)
    aliases = {alias: row for row in rows for alias in row['flags']}
    value = s.get('output_parent', 'outputs')
    origin = 'declaration' if 'output_parent' in s else 'schema-3 default'
    seen, span, i = set(), None, 0
    while i < len(arguments):
        start = i
        token = arguments[i]
        if token == '--' and i == len(arguments) - 1:
            break
        alias, eq, supplied = token.partition('=') if token.startswith('--') else (token, '', '')
        row = aliases.get(alias)
        if not row or not row['supported'] or row['id'] in seen:
            raise ValueError('Automatic SWSS destination unavailable: unknown, repeated or manual-only arguments. Correct argv or explicitly review a manual capture parent.')
        seen.add(row['id'])
        if row['action'] == 'store':
            grammar = r'[+-]?[0-9]+' if row['type'] == 'int' else r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?'
            if not eq:
                i += 1
                if i == len(arguments):
                    raise ValueError('Missing option value; review exact argv.')
                supplied = arguments[i]
                if supplied.startswith('-') and not (row['type'] in ('int', 'float') and re.fullmatch(grammar, supplied)):
                    raise ValueError('Ambiguous option-looking value; review exact argv.')
            parsed = supplied
            if row['type'] in ('int', 'float'):
                if not re.fullmatch(grammar, supplied):
                    raise ValueError('Invalid numeric argument; automatic output resolution unavailable.')
                parsed = int(supplied) if row['type'] == 'int' else float(supplied)
                if not (-(2**63) <= parsed < 2**63 if row['type'] == 'int' else math.isfinite(parsed)):
                    raise ValueError('Numeric argument outside supported bounds.')
            choices = row['choices']
            if choices is not None and parsed not in [int(c) if row['type'] == 'int' else c for c in choices]:
                raise ValueError('Argument outside declared choices; review argv.')
            if row['id'] == s.get('output_parent_parameter'):
                if not supplied:
                    raise ValueError('Empty output-parent override; review argv or an explicit manual mapping.')
                value, origin, span = supplied, 'bound CLI', [start, i + 1]
        elif eq:
            raise ValueError('A flag cannot take a value; review argv.')
        i += 1
    return {'value': value, 'origin': origin, 'binding_id': s.get('output_parent_parameter'),
            'token_span': span, 'declared_parent': s.get('output_parent', 'outputs'),
            'schema_version': 3, 'metadata_sha256': provenance['sha256'],
            'binding_status': provenance['binding_status'], 'argv': list(arguments)}


def literal_path(root, value):
    if not isinstance(value, str) or not value or len(value.encode()) > 8192 or any(ord(c) < 32 or ord(c) == 127 for c in value) or '..' in value.split('/') or any(c in value for c in '\\:'):
        raise ValueError('Output parent must be a nonempty literal path without traversal, controls, drive or URI syntax.')
    return Path(os.path.normpath(str(Path(root) / value)))


def identities(path):
    observed = {}
    for item in [*reversed(path.parents), path]:
        try:
            info = item.lstat()
        except FileNotFoundError:
            break
        if not stat.S_ISDIR(info.st_mode):
            raise ValueError('Output destination components must be directories without symbolic links.')
        observed[str(item)] = [info.st_dev, info.st_ino]
    return observed


def recheck(location):
    for name, expected in location['identities'].items():
        info = Path(name).lstat()
        if not stat.S_ISDIR(info.st_mode) or [info.st_dev, info.st_ino] != expected:
            raise ValueError('Output location changed or volume unavailable; review again. No fallback capture.')
    # Also reject a symlink inserted into a previously absent tail.
    current = identities(Path(location['parent']))
    if not current or not os.access(next(reversed(current)), os.R_OK | os.W_OK | os.X_OK):
        raise ValueError('Output destination is inaccessible or not writable; choose an available parent.')


def review(simulation, arguments, local, mode='manual', metadata=None):
    if mode not in ('auto', 'manual'):
        raise ValueError('Choose automatic or manually reviewed output capture.')
    if metadata is None:
        from .parameters import discover_parameters
        metadata = discover_parameters(simulation)
    provenance = metadata['provenance']
    if not provenance or provenance['schema_version'] != 3:
        if mode == 'auto':
            raise ValueError('Automatic output discovery requires valid associated SWSS schema 3 metadata.')
        return None
    try:
        result = resolve(provenance, arguments)
    except ValueError as exc:
        if mode != 'manual':
            raise
        result = {'value': local, 'origin': 'reviewed manual mapping', 'resolution_warning': str(exc),
                  'schema_version': 3, 'metadata_sha256': provenance['sha256'], 'argv': list(arguments)}
    root = Path(simulation['root'])
    parent = literal_path(root, result['value'])
    if mode == 'manual' and parent != literal_path(root, local):
        raise ValueError('Capture folder conflicts with SWSS metadata/argv. Correct it or select automatic discovery; arguments were not changed.')
    raw = parse(provenance['bytes_utf8'].encode())
    document = raw['swss']
    extension = raw.get('extensions', {}).get('simshelf', {})
    capture = extension.get('capture', {}) if isinstance(extension, dict) else {}
    if isinstance(capture, dict) and 'output_dir' in capture and capture['output_dir'] != document.get('output_parent', 'outputs'):
        raise ValueError('Local capture extension conflicts with the schema-3 output parent; correct the declaration explicitly.')
    result['declared_parent'] = document.get('output_parent', 'outputs')
    protected = {'swss.toml', simulation.get('entrypoint'), simulation.get('version_file')}
    protected.update(f['path'] for f in document.get('source_files', []))
    if root.is_relative_to(parent) or any((root / p).is_relative_to(parent) for p in protected if p):
        raise ValueError('Output parent overlaps the selected source root or declared source/input files. Correct the layout.')
    observed = identities(parent)
    observed.update(identities(root))
    external = not parent.is_relative_to(root)
    if external and str(parent) not in observed:
        raise ValueError('External output parent must already exist. Mount and explicitly prepare the intended destination before review; SimShelf will not create an external fallback directory.')
    result.update(parent=str(parent), mode=mode, external=external, identities=observed,
                  root=str(root), entrypoint=simulation.get('entrypoint'), checked_at=now(),
                  output_contract='SWSS v3.0 section 4.7',
                  allocation='simulation-owned standalone child')
    recheck(result)
    return result


def capture_path(simulation):
    location = simulation['config'].get('swss_output_location')
    if location:
        recheck(location)
        return Path(location['parent'])
    from .common import contained
    return contained(Path(simulation['root']), simulation['config']['output_dir'])
