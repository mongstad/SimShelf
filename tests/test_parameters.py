import json
import subprocess

from fastapi.testclient import TestClient
from simshelf.api import create_app
from simshelf.parameters import discover_parameters
from test_portal import headers, settings, finish


def test_static_discovery_never_executes_and_reports_fallbacks(project, monkeypatch):
    store, sim, root, source = project
    source.write_text('''import argparse
import missing_gpu_library
raise RuntimeError("must never execute")
p = argparse.ArgumentParser()
p.add_argument('--steps', '-n', type=int, default=10, help='Steps')
p.add_argument('--dt', type=float, default=-0.25)
p.add_argument('--name', default='with spaces', choices=['with spaces', 'other'])
p.add_argument('--quiet', action='store_true')
p.add_argument('--no-save', action='store_false', default=True)
p.add_argument('--tag', action='append')
p.add_argument('input', type=str)
p.add_argument('--dynamic', default=calculate())
p.add_argument('--custom', type=convert)
p.add_argument('--dynamic-action', action=choose())
p.add_argument('--required', required=True)
''')
    before = source.read_bytes()
    monkeypatch.setattr(subprocess, 'Popen', lambda *a, **k: (_ for _ in ()).throw(AssertionError('No execution')))
    result = discover_parameters(sim, source='static')
    rows = {r['name']: r for r in result['parameters']}
    assert rows['--steps']['default'] == 10
    assert rows['--dt']['default'] == -.25
    assert rows['--name']['choices'] == ['with spaces', 'other']
    assert rows['--quiet']['default'] is False
    assert rows['--no-save']['default'] is True
    assert rows['--required']['required']
    for name in ('--tag', 'input', '--dynamic', '--custom'):
        assert not rows[name]['supported']
    assert not rows['--dynamic']['default_known']
    assert not rows['--dynamic-action']['default_known']
    assert source.read_bytes() == before
    assert store.runs(sim['id']) == []


def test_parser_mutations_multiple_parsers_and_dynamic_names(project):
    _, sim, _, source = project
    source.write_text("from argparse import ArgumentParser as AP\np=AP()\np.add_argument('--x', default=1)\np.set_defaults(x=2)\n")
    row = discover_parameters(sim, source='static')['parameters'][0]
    assert not row['supported'] and not row['default_known']
    source.write_text("import argparse\na=argparse.ArgumentParser()\nb=argparse.ArgumentParser()\na.add_argument('--x')\n")
    assert not discover_parameters(sim, source='static')['parameters']
    source.write_text("import argparse\np=argparse.ArgumentParser()\np.add_argument(name)\n")
    assert any('dynamic' in w for w in discover_parameters(sim, source='static')['warnings'])
    source.write_text("import argparse\np=argparse.ArgumentParser()\np.add_argument('--x')\np.add_argument('--x')\n")
    assert all(not r['supported'] for r in discover_parameters(sim, source='static')['parameters'])


def test_discovery_api_preserves_saved_unknown_argv_and_source(project):
    store, sim, root, source = project
    source.write_text("import argparse\np=argparse.ArgumentParser()\np.add_argument('--dt', type=float, default=.1)\n")
    before = source.read_bytes()
    with TestClient(create_app(store.path)) as client:
        auth = headers(client)
        saved = settings(arguments=['--unknown', 'a b', '--tag=x', '--tag=y'])
        assert client.put(f"/api/simulations/{sim['id']}/execution", headers=auth, json=saved).status_code == 200
        response = client.get(f"/api/simulations/{sim['id']}/parameters?source=static")
        assert response.status_code == 200
        first = response.json()
        assert first['parameters'][0]['default'] == .1
        source.write_text(source.read_text().replace('default=.1', 'default=.2'))
        assert client.get(f"/api/simulations/{sim['id']}/parameters?source=static").json()['fingerprint'] != first['fingerprint']
        assert client.get(f"/api/simulations/{sim['id']}/parameters?source=static", headers={'Origin': 'https://bad.example'}).status_code == 403
        assert store.runs(sim['id']) == []
        assert store.simulation(sim['id'])['execution']['arguments'] == saved['arguments']
    assert source.read_bytes() == before.replace(b'default=.1', b'default=.2')


def test_discovered_values_launch_exactly_without_inserting_defaults(project):
    store, sim, root, source = project
    source.write_text("""import argparse, json
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--dt', type=float, default=.1)
p.add_argument('--steps', type=int, default=10)
p.add_argument('--name', default='original')
p.add_argument('--quiet', action='store_true')
p.add_argument('--tag', action='append')
p.add_argument('input')
args=p.parse_args()
Path('outputs').mkdir(exist_ok=True)
Path('outputs/result.json').write_text(json.dumps(vars(args)))
""")
    argv = ['--tag=x', '--tag=y', 'input file', '--dt=-0.25', '--name=a "b"', '--quiet']
    with TestClient(create_app(store.path)) as client:
        auth = headers(client)
        assert client.get(f"/api/simulations/{sim['id']}/parameters?source=static").status_code == 200
        response = client.post(f"/api/simulations/{sim['id']}/launch", headers=auth, json=settings(arguments=argv))
        assert response.status_code == 201, response.text
        run = finish(store, response.json()['run_id'])
        assert run['status'] == 'completed'
        assert run['command'][2:] == argv
    result = json.loads((root / 'outputs/result.json').read_text())
    assert result == {'dt': -.25, 'steps': 10, 'name': 'a "b"', 'quiet': True, 'tag': ['x', 'y'], 'input': 'input file'}
