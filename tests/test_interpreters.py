import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from simshelf.api import create_app
from simshelf.interpreters import discovery, probe_interpreter, declarations, check_dependencies
from test_portal import headers, settings


def fake_python(folder, content):
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / 'python'
    path.write_text(content)
    path.chmod(0o755)
    return path


def test_discovery_is_passive_bounded_and_preserves_venv_identity(project, tmp_path, monkeypatch):
    store, sim, root, _ = project
    sentinel = tmp_path / 'must-not-run'
    python = fake_python(root / '.venv/bin', f'#!/bin/sh\ntouch "{sentinel}"\n')
    (root / '.venv/pyvenv.cfg').write_text('home = /not/probed\n')
    # Two venvs pointing at the same base executable must remain separate choices.
    (root / 'venv/bin').mkdir(parents=True)
    (root / 'venv/bin/python').symlink_to(python)
    (root / 'venv/pyvenv.cfg').write_text('home = /not/probed\n')
    alias = tmp_path / 'alias'
    alias.symlink_to(root / '.venv/bin', target_is_directory=True)
    monkeypatch.setenv('PATH', f'{root}/.venv/bin:{alias}::relative/path')
    monkeypatch.delenv('VIRTUAL_ENV', raising=False)
    monkeypatch.delenv('CONDA_PREFIX', raising=False)
    monkeypatch.setattr(Path, 'home', classmethod(lambda cls: tmp_path))
    monkeypatch.setattr(subprocess, 'Popen', lambda *a, **k: pytest.fail('Passive discovery must not execute Git, Conda or Python'))
    result = discovery({**sim, 'execution': {'interpreter': str(python)}})
    assert not sentinel.exists()
    assert sum(c['path'] == str(python) for c in result['candidates']) == 1
    assert not any(c['path'] == str(alias / 'python') for c in result['candidates'])
    assert any(c['path'] == str(root / 'venv/bin/python') for c in result['candidates'])
    assert any(c['simshelf_runtime'] for c in result['candidates'])
    assert all(c['version'] is None for c in result['candidates'])
    missing = str(tmp_path / 'moved env/bin/python')
    result = discovery({**sim, 'execution': {'interpreter': missing}})
    assert result['candidates'][0]['path'] == missing
    assert not result['candidates'][0]['available']
    assert len(result['candidates']) <= 64


def test_discovery_conda_registry_and_broken_symlink(project, tmp_path, monkeypatch):
    _, sim, root, _ = project
    env = tmp_path / 'Conda env'
    (env / 'conda-meta').mkdir(parents=True)
    python = fake_python(env / 'bin', '#!/bin/sh\nexit 9\n')
    home = tmp_path / 'home'
    (home / '.conda').mkdir(parents=True)
    (home / '.conda/environments.txt').write_text(str(env) + '\nrelative/ignored\n')
    monkeypatch.setattr(Path, 'home', classmethod(lambda cls: home))
    monkeypatch.setenv('PATH', '')
    (root / '.venv/bin').mkdir(parents=True)
    (root / '.venv/bin/python').symlink_to(tmp_path / 'missing')
    found = discovery(sim)['candidates']
    assert any(c['path'] == str(python) and c['kind'] == 'Conda environment' for c in found)
    assert any(c['path'] == str(root / '.venv/bin/python') and not c['available'] for c in found)


@pytest.mark.parametrize('body, message', [
    ('#!/bin/sh\necho nonsense\n', 'valid version'),
    ('#!/bin/sh\nexit 4\n', 'check failed'),
    ('#!/bin/sh\nexec /bin/sleep 20\n', 'timed out'),
    ('#!/bin/sh\nexec /usr/bin/yes noise\n', 'output limit'),
    ('not an executable format', 'Could not start'),
])
def test_broken_probes_are_bounded(tmp_path, body, message):
    python = fake_python(tmp_path / 'space env', body)
    with pytest.raises(ValueError, match=message):
        probe_interpreter(str(python), timeout=.4)


def test_real_metadata_check_skips_hooks_project_and_imports(project, tmp_path):
    store, sim, root, source = project
    env = tmp_path / 'science env'
    subprocess.run([sys.executable, '-m', 'venv', '--without-pip', str(env)], check=True)
    python = env / 'bin/python'
    site = next((env / 'lib').glob('python*/site-packages'))
    sentinel = tmp_path / 'should-not-exist'
    (site / 'unsafe.pth').write_text(f"import pathlib; pathlib.Path({str(sentinel)!r}).touch()\n")
    (site / 'sitecustomize.py').write_text(f"raise RuntimeError('do not import')\n")
    (site / 'numpy.py').write_text("raise RuntimeError('do not import package')\n")
    source.write_text("raise RuntimeError('do not execute simulation')\n")
    meta = site / 'numpy-2.0.dist-info'
    meta.mkdir()
    (meta / 'METADATA').write_text('Name: numpy\nVersion: 2.0\n\n')
    (root / 'requirements.txt').write_text('numpy>=1.0\nnumpy<1\nmissing-science-package>=3\n-r external.txt\nnumpy[extra]\nelsewhere; python_version < "1"\n')
    (root / 'pyproject.toml').write_text('[project]\nrequires-python=">=99"\ndependencies=["numpy==2.0"]\n')
    before = sorted(str(p.relative_to(root)) for p in root.rglob('*'))
    environment_before = {str(p.relative_to(env)): (p.stat().st_size, p.stat().st_mtime_ns) for p in env.rglob("*") if p.is_file()}
    result = check_dependencies(sim, str(python))
    assert {str(p.relative_to(env)): (p.stat().st_size, p.stat().st_mtime_ns) for p in env.rglob("*") if p.is_file()} == environment_before
    assert result['python']['prefix'] == str(env)
    assert [r['status'] for r in result['requirements']] == ['incompatible','satisfied','incompatible','unknown','unknown','unknown','not-applicable','satisfied']
    assert result['warnings'] and not sentinel.exists()
    assert sorted(str(p.relative_to(root)) for p in root.rglob('*')) == before
    assert not store.runs()
    # Without path hooks, an absent distribution can be reported as missing.
    (site / 'unsafe.pth').unlink()
    assert check_dependencies(sim, str(python))['requirements'][3]['status'] == 'missing'


def test_declarations_unknown_and_symlink_boundaries(project, tmp_path):
    _, sim, root, _ = project
    assert declarations(root) == ([], None, [], [])
    (root / 'environment.yml').write_text('dependencies:\n - numpy\n')
    (root / 'requirements.txt').symlink_to(tmp_path / 'outside.txt')
    (tmp_path / 'outside.txt').write_text('numpy')
    (root / 'pyproject.toml').write_text('[project]\nrequires-python=3\n')
    req, spec, files, warnings = declarations(root)
    assert not req and spec is None and len(warnings) == 3
    (root / 'requirements.txt').unlink()
    (root / 'requirements.txt').write_text('x' * 262145)
    assert any('256 KB' in w for w in declarations(root)[3])


def test_check_endpoints_require_confirmation_and_do_not_change_saved_settings(project, tmp_path):
    store, sim, root, _ = project
    with TestClient(create_app(store.path)) as client:
        auth = headers(client)
        base = f"/api/simulations/{sim['id']}"
        assert client.put(base+'/execution',headers=auth,json=settings()).status_code == 200
        before = store.simulation(sim['id'])['execution']
        assert client.get(base+'/interpreters').status_code == 200
        for suffix in ('interpreter/check', 'dependencies/check'):
            body = {'interpreter':sys.executable,'confirmed':True}
            assert client.post(base+'/'+suffix,json=body).status_code == 403
            assert client.post(base+'/'+suffix,headers={**auth,'Origin':'https://elsewhere.example'},json=body).status_code == 403
            assert client.post(base+'/'+suffix,headers=auth,json={'interpreter':sys.executable}).status_code == 400
            response = client.post(base+'/'+suffix,headers=auth,json=body)
            assert response.status_code == 200,response.text
        assert store.simulation(sim['id'])['execution'] == before
        assert not store.runs()
        assert client.post(base+'/interpreter/check',headers=auth,json={'interpreter':str(tmp_path/'gone/python'),'confirmed':True}).status_code == 400


def test_unavailable_metadata_never_falls_back_to_server_environment(project, monkeypatch):
    from simshelf import interpreters
    _, sim, root, _ = project
    (root / 'requirements.txt').write_text('numpy; python_version >= "3"\n')
    monkeypatch.setattr(interpreters, 'probe_interpreter', lambda *a, **k: {'version': '3.14', 'prefix': '/unknown'})
    with pytest.raises(ValueError, match='metadata is unavailable'):
        check_dependencies(sim, '/unknown/python')
    monkeypatch.setattr(interpreters, 'probe_interpreter', lambda *a, **k: {'version': '3.14', 'prefix': '/unknown', 'distributions': [], 'marker_environment': {}})
    with pytest.raises(ValueError, match='marker metadata is incomplete'):
        check_dependencies(sim, '/unknown/python')
