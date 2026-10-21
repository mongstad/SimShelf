"""Issue 114 audit probes; no production inspector or scientific source changes."""
import hashlib
import json

import pytest
from fastapi.testclient import TestClient
from simshelf.api import create_app
from simshelf.parameters import discover_parameters, static_parameters
from simshelf.store import Store
from simshelf.swss import review
from test_portal import finish, headers, settings
from test_swss import HEADER, ROW


@pytest.mark.parametrize('metadata', [None, 'not valid toml', HEADER.replace('= 2', '= 3') + ROW,
                                     HEADER + ROW, HEADER + ROW + '\n[[swss.source_files]]\npath="sim.py"\nsha256="' + '0'*64 + '"\n'])
def test_audit_manual_launch_matrix(tmp_path, metadata):
    root = tmp_path/'source'; root.mkdir()
    source = root/'sim.py'
    source.write_text('import json, sys\nprint(json.dumps(sys.argv[1:]))\n')
    if metadata is not None:
        (root/'swss.toml').write_text(metadata)
    before = {p.name: p.read_bytes() for p in root.iterdir()}
    store = Store(tmp_path/'library'); sim = store.add_simulation(root, entrypoint='sim.py')
    argv = ['--N', '00192', '--label', '', '--unknown=x', '--', '--N']
    with TestClient(create_app(store.path)) as client:
        auth = headers(client)
        discovered = client.get(f"/api/simulations/{sim['id']}/parameters").json()
        if metadata == HEADER + ROW:
            assert discovered['parameters'][0]['supported']
            assert discovered['provenance']['binding_status'] == 'binding unverified'
        else:
            assert not discovered['parameters'] and discovered['warnings']
        config = settings(arguments=argv, parameter_review={'mode':'manual','fingerprint':None})
        assert client.put(f"/api/simulations/{sim['id']}/execution", headers=auth, json=config).status_code == 200
        response = client.post(f"/api/simulations/{sim['id']}/launch", headers=auth, json=config)
        assert response.status_code == 201, response.text
        run = finish(store, response.json()['run_id'])
        assert run['status'] == 'completed' and run['command'][2:] == argv
        assert run['parameter_metadata']['argv'] == argv
        assert json.loads((store.path/'logs'/run['id']/'stdout.log').read_text()) == argv
        assert store.simulation(sim['id'])['execution']['arguments'] == argv
    assert before == {name: (root/name).read_bytes() for name in before}


def test_audit_verified_bytes_do_not_prove_parser_compatibility(tmp_path):
    root = tmp_path/'source'; root.mkdir()
    source = root/'sim.py'
    source.write_text('import argparse\np=argparse.ArgumentParser()\np.add_argument("--actual", type=int)\np.parse_args()\n')
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    (root/'swss.toml').write_text(HEADER + ROW + f'\n[[swss.source_files]]\npath="sim.py"\nsha256="{digest}"\n')
    store = Store(tmp_path/'library'); sim = store.add_simulation(root, entrypoint='sim.py')
    d = discover_parameters(sim)
    assert d['provenance']['binding_status'] == 'listed bytes verified'
    assert d['parameters'][0]['supported']
    argv = ['--N', '00192']
    with TestClient(create_app(store.path)) as client:
        config = settings(arguments=argv, parameter_review={'mode':'typed','fingerprint':d['fingerprint']})
        response = client.post(f"/api/simulations/{sim['id']}/launch", headers=headers(client), json=config)
        assert response.status_code == 201, response.text
        run = finish(store, response.json()['run_id'])
        assert run['status'] == 'failed' and run['exit_code'] == 2
        assert run['command'][2:] == argv and run['parameter_metadata']['argv'] == argv
        assert 'unrecognized arguments: --N 00192' in (store.path/'logs'/run['id']/'stderr.log').read_text()


def test_audit_row_fallback_and_unbound_edit(tmp_path):
    root = tmp_path/'source'; root.mkdir(); source = root/'sim.py'
    source.write_text('print("first")\n'); metadata = root/'swss.toml'
    other = ROW.replace('"number"', '"other"').replace('["--N", "-n"]', '["--other"]')
    metadata.write_text(HEADER + ROW.replace('default = 192', 'nargs = 2') + other.replace('default = 192', ''))
    store = Store(tmp_path/'library'); sim = store.add_simulation(root, entrypoint='sim.py')
    d = discover_parameters(sim)
    assert [r['supported'] for r in d['parameters']] == [False, True]
    assert not d['parameters'][1]['default_known'] and not d['parameters'][1]['required']
    argv = ['--other', '00192', '--label', '']
    decision = {'mode':'typed', 'fingerprint':d['fingerprint']}
    store.update_simulation(sim['id'], execution=settings(arguments=argv, parameter_review=decision))
    source.write_text('print("second")\n')
    # No source manifest/comparable version: no promise of source-change detection.
    assert discover_parameters(sim)['fingerprint'] == d['fingerprint']
    assert review(store.simulation(sim['id']), decision)['provenance']['binding_status'] == 'binding unverified'
    metadata.write_text(metadata.read_text() + '\n# reviewed metadata changed\n')
    with pytest.raises(ValueError, match='changed'):
        review(store.simulation(sim['id']), decision)
    assert store.simulation(sim['id'])['execution']['arguments'] == argv
    assert review(store.simulation(sim['id']), {'mode':'manual','fingerprint':None})['previous_provenance'] == d['provenance']


@pytest.mark.xfail(strict=True, reason='Issue 114: nested portable row value should invalidate whole document under SWSS 4.5')
def test_audit_nested_portable_value_is_document_failure(tmp_path):
    root = tmp_path/'source'; root.mkdir(); (root/'sim.py').write_text('pass\n')
    other = ROW.replace('"number"', '"other"').replace('["--N", "-n"]', '["--other"]')
    (root/'swss.toml').write_text(HEADER + ROW.replace('default = 192', 'default = { unexpected = 1 }') + other)
    d = discover_parameters({'root': str(root), 'entrypoint':'sim.py'})
    assert d['provenance'] is None and d['parameters'] == []


@pytest.mark.parametrize('declaration', [
    "if False:\n    p.add_argument('--x', type=int)\n",
    "def unrelated(p):\n    p.add_argument('--x', type=int)\n",
    "int = str\np.add_argument('--x', type=int)\n",
])
def test_audit_static_suggestions_are_not_verification(declaration):
    # Parse only: these examples must never be executed or treated as proven CLI contracts.
    source = 'import argparse\np=argparse.ArgumentParser()\n' + declaration
    rows, warnings = static_parameters(source.encode(), 'fixture.py')
    assert rows[0]['supported'] and rows[0]['type'] == 'int'
    assert any('not proof' in w for w in warnings)


def test_audit_reference_literal_evidence(monkeypatch):
    """Optional pinned external reference, read only; never imported or executed."""
    import os
    import socket
    import subprocess
    import tomllib
    from pathlib import Path
    location = os.environ.get('SWSS_AUDIT_REFERENCE')
    if not location:
        pytest.skip('Set SWSS_AUDIT_REFERENCE to the pinned scalar-decay reference directory')
    root = Path(location)
    with (root/'simulate.py').open('rb') as stream:
        source = stream.read(262145)
    with (root/'swss.toml').open('rb') as stream:
        metadata = stream.read(262145)
    assert len(source) <= 262144 and len(metadata) <= 262144
    assert hashlib.sha256(source).hexdigest() == '48a0b582d8bceb007a547dfc891333ad62d766114ffd17eb8284128e04780f41'
    def forbidden(*args, **kwargs):
        raise AssertionError('Inspection attempted execution or network')
    monkeypatch.setattr(subprocess, 'Popen', forbidden)
    monkeypatch.setattr(socket, 'socket', forbidden)
    rows, _ = static_parameters(source, 'simulate.py')
    declared = tomllib.loads(metadata.decode())['swss']['parameters']
    assert len(rows) == len(declared) == 12
    for observed, expected in zip(rows, declared):
        assert observed['supported']
        for actual, field in [('flags','options'), ('action','action'), ('required','required')]:
            assert observed[actual] == expected[field]
        typ = 'boolean' if observed['action'] in ('store_true','store_false') else {'int':'integer','float':'float','str':'string'}[observed['type']]
        assert typ == expected['type']
        assert observed['choices'] == expected.get('choices')
        if 'default' in expected:
            assert type(observed['default']) is type(expected['default'])
            assert observed['default'] == expected['default']
    # Deliberate literal-source disagreements with unchanged metadata, parse only.
    row = rows[2]  # --steps/-n, integer, store, optional, choices 10/20/40, default 20.
    mutations = [
        (b"'--steps', '-n'", b"'--renamed', '-n'", 'flags'),
        (b"'--steps', '-n'", b"'--steps'", 'flags'),
        (b"'--steps', '-n', type=int", b"'--steps', '-n', type=float", 'type'),
        (b"'--steps', '-n', type=int", b"'--steps', '-n', action='append', type=int", 'action'),
        (b"'--steps', '-n', type=int", b"'--steps', '-n', required=True, type=int", 'required'),
        (b"choices=[10, 20, 40]", b"choices=[10, 30, 40]", 'choices'),
        (b"default=20, help='Number", b"default=10, help='Number", 'default'),
    ]
    for old, new, field in mutations:
        altered = source.replace(old, new)
        assert altered != source
        changed, _ = static_parameters(altered, 'simulate.py')
        assert changed[2][field] != row[field]
    # Arity cannot be promoted from the existing suggestions API to a verified field.
    altered = source.replace(b"'--steps', '-n', type=int", b"'--steps', '-n', nargs=2, type=int")
    assert altered != source
    changed, _ = static_parameters(altered, 'simulate.py')
    assert not changed[2]['supported']
