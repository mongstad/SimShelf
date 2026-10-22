"""SWSS schema-2 conformance and real local integration fixtures."""
import ast
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from simshelf.api import create_app
from simshelf.parameters import discover_parameters
from simshelf.swss import parse, read, review, parameters
from simshelf.store import Store
from test_portal import headers, settings, finish

HEADER = '[swss]\nschema_version = 2\nentrypoint = "sim.py"\nsimulation_version = "1.0.0"\n'
ROW = '''
[[swss.parameters]]
id = "number"
kind = "option"
options = ["--N", "-n"]
required = false
type = "integer"
action = "store"
help = "Grid"
default = 192
'''

@pytest.fixture
def companion(tmp_path):
    root = tmp_path / 'source'
    root.mkdir()
    (root / 'sim.py').write_text('SIMSHELF_VERSION = "1.0.0"\n')
    path = root / 'swss.toml'
    path.write_text(HEADER + ROW)
    sim = {'root': str(root), 'entrypoint': 'sim.py', 'version_file': 'sim.py'}
    return root, path, sim


def test_minimal_extensions_and_no_discovery_execution(companion, monkeypatch):
    root, path, sim = companion
    monkeypatch.setattr(subprocess, 'Popen', lambda *a, **k: pytest.fail('discovery executed'))
    monkeypatch.setattr(ast, 'parse', lambda *a, **k: pytest.fail('SWSS inspected AST'))
    for tail in ('', 'parameters = []\n', '\n[extensions.unknown]\nschema_version = 999\ntext = "$(false)"\n'):
        path.write_text(HEADER + tail)
        before = {p.name: p.read_bytes() for p in root.iterdir()}
        result = read(root, 'sim.py', 'sim.py')
        assert result['parameters'] == []
        assert result['provenance']['binding_status'] == 'binding unverified'
        assert before == {p.name: p.read_bytes() for p in root.iterdir()}


@pytest.mark.parametrize('change', [
    lambda s: s.replace('schema_version = 2', 'schema_version = 1'),
    lambda s: s.replace('schema_version = 2', 'schema_version = 3'),
    lambda s: s + '\n[apps.foo]\nx = 1\n',
    lambda s: s.replace('entrypoint = "sim.py"', 'entrypoint = "../sim.py"'),
    lambda s: s.replace('entrypoint = "sim.py"', 'entrypoint = "/sim.py"'),
    lambda s: s.replace('entrypoint = "sim.py"', 'entrypoint = "https:sim.py"'),
    lambda s: s + ROW,
    lambda s: s + ROW.replace('id = "number"', 'id = "other"'),
    lambda s: s.replace('id = "number"', 'id = "INVALID"'),
    lambda s: s.replace('["--N", "-n"]', '["--N", "--N"]'),
    lambda s: s.replace('default = 192', 'default = inf'),
    lambda s: s.replace('default = 192', 'default = 2026-01-01'),
    lambda s: s + '\n[extensions.foo]\nx = "' + 'x' * 4097 + '"',
    lambda s: s + '\n[extensions.foo]\nx = ' + '[' * 9 + '0' + ']' * 9,
    lambda s: s + '\n[extensions.foo]\nx = "\\u0000"',
    lambda s: s + '\n[extensions.foo]\nx = [' + ','.join('0' for _ in range(4097)) + ']',
])
def test_invalid_documents_manual_fallback(companion, change):
    root, path, sim = companion
    path.write_text(change(HEADER + ROW))
    result = discover_parameters(sim)
    assert not result['parameters'] and result['warnings']
    assert review(sim, {'mode': 'manual', 'fingerprint': None})['decision']['mode'] == 'manual'


@pytest.mark.parametrize('edit', [
    ('type = "integer"', 'type = "unknown"'),
    ('action = "store"', 'action = "append"'),
    ('default = 192', 'default = true'),
    ('default = 192', 'default = 9223372036854775808'),
    ('default = 192', 'choices = [1, 1]'),
    ('default = 192', 'choices = [1, 2]\ndefault = 3'),
    ('default = 192', 'repeatable = true'),
    ('default = 192', 'nargs = 2'),
])
def test_bad_rows_manual_only(companion, edit):
    root, path, sim = companion
    path.write_text((HEADER + ROW).replace(*edit))
    result = discover_parameters(sim)
    assert len(result['parameters']) == 1
    assert not result['parameters'][0]['supported']


def test_symlinks_bindings_stale_and_exact_evidence(companion):
    root, path, sim = companion
    original = read(root, 'sim.py', 'sim.py')
    digest = hashlib.sha256((root / 'sim.py').read_bytes()).hexdigest()
    path.write_text(HEADER + ROW + f'\n[[swss.source_files]]\npath = "sim.py"\nsha256 = "{digest}"\n')
    result = read(root, 'sim.py', 'sim.py')
    assert result['provenance']['binding_status'] == 'listed bytes verified'
    assert result['provenance']['bytes_utf8'].encode() == path.read_bytes()
    (root / 'sim.py').write_text('SIMSHELF_VERSION = "2.0.0"\n')
    stale = read(root, 'sim.py', 'sim.py')
    assert not stale['parameters'] and len(stale['provenance']['binding_reasons']) == 1
    with pytest.raises(ValueError, match='changed'):
        review(sim, {'mode': 'typed', 'fingerprint': result['fingerprint']})
    path.unlink()
    path.symlink_to(root / 'sim.py')
    assert not discover_parameters(sim)['parameters']
    path.unlink()
    path.write_text(HEADER + ROW)
    (root / 'sim.py').unlink()
    (root / 'sim.py').symlink_to(path)
    assert not discover_parameters(sim)['parameters']


def test_boundaries(companion):
    root, path, sim = companion
    base = (HEADER + ROW).encode()
    for size, valid in ((262144, True), (262145, False)):
        path.write_bytes(base + b'\n#' + b'x' * (size - len(base) - 2))
        assert bool(discover_parameters(sim)['parameters']) == valid
    path.write_bytes(b'\xff')
    assert not discover_parameters(sim)['parameters']
    path.write_text(HEADER + ROW.replace('help = "Grid"', 'help = "' + 'x' * 4096 + '"'))
    assert read(root)['parameters']
    path.write_text(HEADER + ''.join(ROW.replace('"number"', f'"n{i}"').replace('["--N", "-n"]', f'["--n{i}"]') for i in range(128)))
    assert len(read(root)['parameters']) == 128
    path.write_text(path.read_text() + ROW)
    assert not discover_parameters(sim)['parameters']


def test_large_source_exact_launch_and_history(companion, tmp_path, monkeypatch):
    root, path, sim = companion
    # This harmless conventional parser exceeds the old AST limit; never change that limit.
    (root / 'sim.py').write_text('''SIMSHELF_VERSION = "1.0.0"
import argparse, json, os, sys
from pathlib import Path
p = argparse.ArgumentParser()
p.add_argument('--N', '-n', type=int, default=192)
p.add_argument('--dt', type=float)
p.add_argument('--label')
p.add_argument('--export', action='store_true')
p.add_argument('--no-plots', action='store_false')
a, unknown = p.parse_known_args()
out = Path(os.environ['SIMSHELF_OUTPUT_DIR']) / __import__('uuid').uuid4().hex
out.mkdir(parents=True)
(out / 'run_20261019T000000Z_fixture.log').write_text(json.dumps({'argv': sys.argv[1:], 'resolved': vars(a)}))
''' + 'x = 0\n' * 5100)
    assert len(list(ast.walk(ast.parse((root / 'sim.py').read_bytes())))) > 20000
    path.write_text(HEADER + ROW + '\n[extensions.simshelf]\nschema_version = 1\n')
    store = Store(tmp_path / 'library')
    registered = store.add_simulation(root, entrypoint='sim.py')
    argv = ['--N', '00192', '--dt=1e-3', '--label', '', '--export', '--no-plots', '--unknown', '--', '--export']
    first_bytes = None
    with TestClient(create_app(store.path)) as client:
        auth = headers(client)
        for _ in range(2):
            d = client.get(f"/api/simulations/{registered['id']}/parameters").json()
            assert d['parameters'][0]['supported']
            config = settings(arguments=argv, output_policy='fixed')
            config['parameter_review'] = {'mode': 'typed', 'fingerprint': d['fingerprint']}
            response = client.put(f"/api/simulations/{registered['id']}/execution", headers=auth, json=config)
            assert response.status_code == 200, response.text
            response = client.post(f"/api/simulations/{registered['id']}/launch", headers=auth, json=config)
            assert response.status_code == 201, response.text
            run = finish(store, response.json()['run_id'])
            assert run['status'] == 'completed', run
            assert run['command'][2:] == argv
            assert run['parameter_metadata']['provenance']['bytes_utf8'].encode() == path.read_bytes()
            artifact = next(a for a in run['artifacts'] if a['name'].endswith('.log'))
            assert artifact['policy'] == 'copy'
            data = (root / run['capture_config']['output_dir'] / artifact['name']).read_bytes()
            assert json.loads(data)['argv'] == argv
            if first_bytes is None:
                first_bytes = data
                first_path = Path(run['capture_root']) / artifact['name']
                old = store.run(run['id'])
            else:
                assert Path(run['capture_root']) / artifact['name'] != first_path
                assert first_path.read_bytes() == first_bytes
                assert store.run(old['id']) == old

@pytest.mark.parametrize('mutation', [
    lambda s: s.replace('options = ["--N", "-n"]', 'options = [' + ','.join(f'"--a{i}"' for i in range(9)) + ']'),
    lambda s: s.replace('default = 192', 'choices = [' + ','.join(str(i) for i in range(101)) + ']'),
    lambda s: s + '\n[extensions.foo.a.b.c.d.e.f.g]\nx=1',
    lambda s: s.replace('entrypoint = "sim.py"', 'entrypoint = "' + 'a' * 1025 + '"'),
    lambda s: s.replace('options = ["--N", "-n"]', 'options = ["--' + 'a' * 127 + '"]'),
])
def test_more_limits(companion, mutation):
    _, path, sim = companion
    path.write_text(mutation(HEADER + ROW))
    assert not discover_parameters(sim)['parameters']


def test_choices_flags_and_bad_scalar_types(companion):
    root, path, sim = companion
    for typ, action, default in [('float', 'store', '1.0'), ('string', 'store', '""'), ('boolean', 'store_true', 'false'), ('boolean', 'store_false', 'true')]:
        path.write_text((HEADER + ROW).replace('type = "integer"', f'type = "{typ}"').replace('action = "store"', f'action = "{action}"').replace('default = 192', f'default = {default}'))
        assert read(root)['parameters'][0]['supported']
    path.write_text((HEADER + ROW).replace('type = "integer"', 'type = {}'))
    assert not discover_parameters(sim)['parameters'][0]['supported']


def test_source_hash_limits_and_missing_entry(companion):
    root, path, sim = companion
    with (root / 'large.dat').open('wb') as stream:
        stream.truncate(16 * 1024 * 1024 + 1)
    path.write_text(HEADER + ROW + '\n[[swss.source_files]]\npath="large.dat"\nsha256="' + '0' * 64 + '"\n')
    assert not discover_parameters(sim)['parameters']
    path.write_text(HEADER + ROW)
    (root / 'sim.py').unlink()
    assert not discover_parameters(sim)['parameters']


def test_companion_changes_reject_typed_and_keep_last_provenance(companion, tmp_path):
    root, path, sim = companion
    store = Store(tmp_path / 'workspace')
    sim = store.add_simulation(root, entrypoint='sim.py')
    original = discover_parameters(sim)
    decision = {'mode': 'typed', 'fingerprint': original['fingerprint']}
    store.update_simulation(sim['id'], execution={**settings(), 'parameter_review': decision})
    path.write_text(path.read_text() + '\n[extensions.annotation]\ntext="changed"\n')
    with pytest.raises(ValueError, match='changed'):
        review(store.simulation(sim['id']), decision)
    result = review(store.simulation(sim['id']), {'mode':'manual', 'fingerprint':None})
    assert result['previous_provenance'] == original['provenance']
    assert result['provenance']['sha256'] != original['provenance']['sha256']


def test_extensions_initialize_config_not_portable_identity(companion, tmp_path):
    root, path, sim = companion
    path.write_text(HEADER + '\n[extensions.simshelf]\nschema_version=1\nname="Fixture"\n[extensions.simshelf.capture]\nmax_file_mb=1\noutput_dir="results"\n')
    sim = Store(tmp_path / 'workspace').add_simulation(root, entrypoint='sim.py')
    assert sim['config']['max_file_mb'] == 1 and sim['config']['output_dir'] == 'results'
    path.write_text(path.read_text().replace('name="Fixture"', 'entrypoint="other.py"'))
    assert discover_parameters(sim)['provenance']  # portable reader ignores local semantics
    from simshelf.config import read_project
    with pytest.raises(ValueError, match='conflicting'):
        read_project(root)


@pytest.mark.parametrize('kind', ['missing', 'ignored', 'reference', 'oversized'])
def test_required_log_capture_incomplete(companion, tmp_path, kind):
    root, path, _ = companion
    from simshelf.recording import Run
    store = Store(tmp_path / 'workspace')
    sim = store.add_simulation(root, entrypoint='sim.py')
    config = {**sim['config'], 'max_file_mb': 0.00001 if kind == 'oversized' else 25}
    if kind in ('ignored', 'reference'):
        config['rules'] = [{'pattern':'**/*', 'action':'ignore' if kind == 'ignored' else 'reference'}]
    store.update_simulation(sim['id'], config=config)
    with Run(sim['id'], workspace=store.path, output_policy='fixed', capture_console=False) as run:
        if kind != 'missing':
            run.output_dir.mkdir(parents=True)
            (run.output_dir / 'run_20261019T000000Z_fixture.log').write_text('log data\n' * 10)
    result = store.run(run.id)
    assert result['status'] == 'completed'
    assert result['capture_status'] == 'partial'
    assert any('Required log' in e for e in result['capture_errors'])


def test_legacy_file_rejected_for_new_runs_without_modification(companion, tmp_path):
    root, path, _ = companion
    store = Store(tmp_path / 'workspace')
    sim = store.add_simulation(root, entrypoint='sim.py')
    legacy = root / 'simshelf.toml'
    legacy.write_text('[simulation]\nname="Old"\n')
    before = legacy.read_bytes()
    from simshelf.portal import execution_settings
    with pytest.raises(ValueError, match='unsupported for new runs'):
        execution_settings(sim, settings())
    assert legacy.read_bytes() == before


def test_open_time_substitution_refused(companion, monkeypatch):
    root, path, _ = companion
    from simshelf.swss import safe_read
    real_read = os.read
    replaced = False
    def swap(fd, count):
        nonlocal replaced
        data = real_read(fd, count)
        if not replaced:
            replaced = True
            replacement = root / 'replacement'
            replacement.write_text(HEADER)
            replacement.replace(path)
        return data
    monkeypatch.setattr(os, 'read', swap)
    with pytest.raises(ValueError, match='changed'):
        safe_read(root, 'swss.toml')


def test_exact_depth_alias_choice_source_boundaries(companion):
    root, path, sim = companion
    # root -> extensions -> foo -> five arrays = depth eight.
    path.write_text(HEADER + ROW + '\n[extensions.foo]\nx = [[[[[0]]]]]\n')
    assert read(root)['parameters']
    aliases = ','.join(f'"--a{i}"' for i in range(8))
    path.write_text((HEADER + ROW).replace('["--N", "-n"]', '[' + aliases + ']').replace('default = 192', 'choices = [' + ','.join(str(i) for i in range(100)) + ']'))
    assert read(root)['parameters'][0]['supported']
    source = root/'sim.py'
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    bindings = ''
    for i in range(32):
        name = 'sim.py' if i == 0 else f'part{i}.txt'
        (root/name).write_bytes(source.read_bytes())
        bindings += f'\n[[swss.source_files]]\npath="{name}"\nsha256="{digest}"\n'
    path.write_text(HEADER + ROW + bindings)
    assert len(read(root)['provenance']['checked_sources']) == 32
    path.write_text(path.read_text()+f'\n[[swss.source_files]]\npath="extra.txt"\nsha256="{digest}"\n')
    assert not discover_parameters(sim)['parameters']


def test_hash_boundary_and_unbound_large_source(companion):
    root, path, _ = companion
    source = root/'sim.py'
    with source.open('wb') as stream:
        stream.truncate(16 * 1024 * 1024)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    path.write_text(HEADER + ROW + f'\n[[swss.source_files]]\npath="sim.py"\nsha256="{digest}"\n')
    assert read(root)['provenance']['binding_status'] == 'listed bytes verified'
    with source.open('ab') as stream:
        stream.write(b'\n')
    path.write_text(HEADER + ROW)
    assert read(root)['parameters'][0]['supported']  # no AST or source-size requirement for an unbound entry


def test_shared_parent_swss_overlap_is_rejected(companion, tmp_path):
    root, path, _ = companion
    (root/'sim.py').write_text('''SIMSHELF_VERSION="1.0.0"
import os,time
from pathlib import Path
p=Path(os.environ['SIMSHELF_OUTPUT_DIR'])
p.mkdir(parents=True,exist_ok=True)
(p/'run_20261019T000000Z_fixture.log').write_text('started\\n')
time.sleep(0.7)
''')
    store=Store(tmp_path/'library');sim=store.add_simulation(root,entrypoint='sim.py')
    with TestClient(create_app(store.path)) as client:
        auth=headers(client)
        config=settings(output_policy='fixed')
        d=discover_parameters(sim)
        config['parameter_review']={'mode':'typed','fingerprint':d['fingerprint']}
        response=client.post(f"/api/simulations/{sim['id']}/launch",headers=auth,json=config)
        assert response.status_code==201,response.text
        ident=response.json()['run_id']
        response=client.post(f"/api/simulations/{sim['id']}/launch",headers=auth,json=config)
        assert response.status_code==400,response.text
        assert 'Another run is recording this output folder' in response.text
        run=finish(store,ident)
        assert run['status']=='completed' and run['capture_status']=='complete'



@pytest.mark.parametrize('cancel', [False, True])
def test_swss_failed_and_cancelled_capture(companion, tmp_path, cancel):
    root,path,_=companion
    (root/'sim.py').write_text('''SIMSHELF_VERSION="1.0.0"
import os,time,sys
from pathlib import Path
p=Path(os.environ['SIMSHELF_OUTPUT_DIR'])
p.mkdir(parents=True,exist_ok=True)
(p/'run_20261019T000000Z_fixture.log').write_text('partial evidence\\n')
print('partial',flush=True)
''' + ('time.sleep(30)\n' if cancel else 'sys.exit(3)\n'))
    store=Store(tmp_path/'library');sim=store.add_simulation(root,entrypoint='sim.py')
    with TestClient(create_app(store.path)) as client:
        auth=headers(client)
        response=client.post(f"/api/simulations/{sim['id']}/launch",headers=auth,json=settings(output_policy='fixed'))
        assert response.status_code==201,response.text
        ident=response.json()['run_id']
        if cancel:
            import time
            for _ in range(100):
                if list((root/'outputs').rglob('*.log')): break
                time.sleep(.02)
            assert client.post(f'/api/runs/{ident}/stop',headers=auth).status_code==202
        run=finish(store,ident)
        assert run['status']==('interrupted' if cancel else 'failed')
        assert run['exit_code']!=0
        assert any(a['name'].endswith('.log') and a['policy']=='copy' for a in run['artifacts'])


def test_invalid_companion_registration_keeps_manual_path(companion, tmp_path):
    root,path,_=companion
    path.write_text('not valid toml')
    before=path.read_bytes()
    store=Store(tmp_path/'workspace');sim=store.add_simulation(root,entrypoint='sim.py')
    assert not discover_parameters(sim)['parameters']
    from simshelf.portal import execution_settings
    plan=execution_settings(sim,{**settings(arguments=['--N','00192']), 'parameter_review':{'mode':'manual','fingerprint':None}})
    assert plan['command'][2:]==['--N','00192'] and path.read_bytes()==before


def test_int64_hints_transport_losslessly(companion):
    root,path,_=companion
    path.write_text((HEADER+ROW).replace('default = 192','default = 9223372036854775807\nchoices = [9223372036854775807]'))
    row=read(root)['parameters'][0]
    assert row['default']=='9223372036854775807' and row['choices']==['9223372036854775807']
