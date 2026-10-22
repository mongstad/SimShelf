"""Bounded static CLI declarations; never imports or executes project code."""
import ast
import hashlib
import math
import os
from pathlib import Path
import re

SCHEMA = 'swss.toml'
LIMIT = 262144


def read_file(root, name):
    path = root / name
    if not path.resolve().is_relative_to(root.resolve()) or any(p.is_symlink() for p in [path, *path.parents] if p != root.parent):
        raise ValueError('Discovery does not follow symbolic links or paths outside the project')
    if not path.is_file():
        raise ValueError('Declaration file is missing or not a regular file')
    with path.open('rb') as stream:
        data = stream.read(LIMIT + 1)
    if len(data) > LIMIT:
        raise ValueError('Declaration file exceeds 256 KB')
    return data


def scalar(value):
    return value is None or type(value) in (str, bool, int) or (type(value) is float and math.isfinite(value))


def normalize(flags, values, source, unknown=()):
    if not isinstance(flags, list) or not flags or len(flags) > 8 or any(not isinstance(f, str) or not f or len(f) > 128 for f in flags):
        raise ValueError('Argument names must be a nonempty list of at most eight short strings')
    action = values.get('action', 'store')
    reason = ''
    if unknown or set(values) - {'help', 'default', 'type', 'choices', 'required', 'action', 'nargs', 'dest', 'metavar'}:
        reason = 'Dynamic or unsupported declaration; use the manual editor.'
    if action not in ('store', 'store_true', 'store_false') or 'nargs' in values:
        reason = 'Repeatable, custom or multi-value action; use the manual editor.'
    if any(not re.fullmatch(r'--?[A-Za-z][\w-]*', f) for f in flags):
        reason = 'Positional or unusual option syntax; use the manual editor.'
    kind = values.get('type', 'str')
    if kind not in ('str', 'int', 'float'):
        reason = 'Custom type conversion; use the manual editor.'
    choices = values.get('choices')
    if choices is not None and (not isinstance(choices, list) or len(choices) > 100 or any(not scalar(v) or v is None for v in choices)):
        reason = 'Unsupported choices; use the manual editor.'
        choices = None
    if not isinstance(values.get('help', ''), str) or not isinstance(values.get('required', False), bool):
        reason = 'Unsupported help or required metadata; use the manual editor.'
    known = None not in unknown and 'default' not in unknown and scalar(values.get('default')) and ('default' in values or (source != SCHEMA and 'action' not in unknown and action in ('store', 'store_true', 'store_false')))
    default = values.get('default', True if action == 'store_false' else False if action == 'store_true' else None)
    return {'flags': flags, 'name': next((f for f in flags if f.startswith('--')), flags[0]),
            'help': values.get('help', '') if isinstance(values.get('help', ''), str) else '',
            'type': kind if isinstance(kind, str) else 'unknown', 'action': action if isinstance(action, str) else 'unknown',
            'choices': choices, 'default_known': known, 'default': default if known else None,
            'required': values.get('required') is True or not flags[0].startswith('-'),
            'source': source, 'supported': not reason, 'reason': reason}


def static_parameters(data, name):
    tree = ast.parse(data, filename=name)
    nodes = list(ast.walk(tree))
    if len(nodes) > 20000:
        raise ValueError('Source exceeds the 20,000 syntax-node discovery limit')
    modules = {a.asname or a.name for n in nodes if isinstance(n, ast.Import) for a in n.names if a.name == 'argparse'}
    constructors = {a.asname or a.name for n in nodes if isinstance(n, ast.ImportFrom) and n.module == 'argparse' for a in n.names if a.name == 'ArgumentParser'}
    def constructor(n):
        return isinstance(n, ast.Call) and ((isinstance(n.func, ast.Name) and n.func.id in constructors) or (isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name) and n.func.value.id in modules and n.func.attr == 'ArgumentParser'))
    parsers = [(n.targets[0].id, n.value) for n in nodes if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name) and constructor(n.value)]
    if len(parsers) != 1:
        return [], ['No single static argparse parser found. Multiple parsers, factories and custom CLIs require a schema or manual arguments.']
    parser, creation = parsers[0]
    warnings = ['Static declarations are suggestions, not proof of runtime defaults or parser execution.']
    unsafe_parser = bool(creation.args) or any(k.arg not in ('description', 'epilog', 'prog', 'add_help', 'formatter_class', 'allow_abbrev') for k in creation.keywords)
    mutations = any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name) and n.func.value.id == parser and n.func.attr not in ('add_argument', 'parse_args', 'parse_known_args') for n in nodes)
    if unsafe_parser or mutations:
        warnings.append('Unsupported parser configuration, groups or mutations: use manual arguments or an explicit schema.')
    rows = []
    for n in nodes:
        if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name) and n.func.value.id == parser and n.func.attr == 'add_argument'):
            continue
        if len(rows) >= 128:
            raise ValueError('At most 128 parameters can be discovered')
        try:
            flags = [ast.literal_eval(v) for v in n.args]
            values, unknown = {}, []
            for k in n.keywords:
                try:
                    values[k.arg] = k.value.id if k.arg == 'type' and isinstance(k.value, ast.Name) and k.value.id in ('str', 'int', 'float') else ast.literal_eval(k.value)
                    if k.arg == 'choices' and isinstance(values[k.arg], tuple):
                        values[k.arg] = list(values[k.arg])
                except (ValueError, TypeError):
                    unknown.append(k.arg)
            row = normalize(flags, values, f'{name}:{n.lineno}', unknown)
            if unsafe_parser or mutations:
                row.update(supported=False, reason='Parser configuration/groups/default mutations require manual review.', default_known=False, default=None)
            rows.append(row)
        except (ValueError, TypeError):
            warnings.append(f'{name}:{n.lineno}: dynamic or unsupported argument names; use manual arguments.')
    return rows, warnings


def discover_parameters(simulation, source='swss'):
    root = Path(simulation['root'])
    result = {'parameters': [], 'warnings': [], 'source': 'swss.toml', 'fingerprint': None, 'provenance': None}
    try:
        from .swss import read, reject_legacy
        reject_legacy(root)
        if source == 'static':
            name = simulation.get('entrypoint')
            data = read_file(root, name)
            rows, warnings = static_parameters(data, name)
            counts = {}
            for row in rows:
                for flag in row['flags']:
                    counts[flag] = counts.get(flag, 0) + 1
            for row in rows:
                if any(counts[f] > 1 for f in row['flags']):
                    row.update(supported=False, reason='Conflicting option definitions; use manual arguments.')
            result.update(parameters=rows, warnings=warnings, source='Explicit static: ' + name,
                          fingerprint=hashlib.sha256(data).hexdigest())
            return result
        document = read(root, simulation.get('entrypoint'), simulation.get('version_file'))
        result.update({k: v for k, v in document.items() if k != 'raw'})
    except (ValueError, SyntaxError, OSError, TypeError, UnicodeError, RecursionError, RuntimeError) as exc:
        result['warnings'] = [f'Discovery unavailable: {exc}. Use explicit manual argv; existing arguments are unchanged.']
    from .swss import output_policy_status
    result['output_policy'] = output_policy_status(result, os.path.lexists(root / 'swss.toml'))
    return result
