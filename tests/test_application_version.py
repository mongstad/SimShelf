import importlib.util
from pathlib import Path
import subprocess
import sys
import tomllib

import pytest
from fastapi.testclient import TestClient
from packaging.version import Version

from simshelf import __version__
from simshelf.api import create_app

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('application_version', ROOT / 'scripts/application_version.py')
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)


def test_application_surfaces_agree_without_creating_cli_workspace(tmp_path):
    assert Version(__version__) > Version('0.1.0')
    config = tomllib.loads((ROOT / 'pyproject.toml').read_text())
    assert 'version' not in config['project']
    assert config['tool']['setuptools']['dynamic']['version']['attr'] == 'simshelf._version.__version__'
    assert policy.read_version((ROOT / policy.VERSION_FILE).read_text()) == __version__
    unused = tmp_path / 'unused'
    result = subprocess.run([sys.executable, '-B', '-m', 'simshelf', '--workspace', str(unused), '--version'], text=True, capture_output=True, check=True)
    assert result.stdout.strip() == f'SimShelf {__version__}'
    assert not unused.exists()
    app = create_app(tmp_path / 'workspace')
    with TestClient(app) as client:
        assert client.get('/api/workspace').json()['version'] == __version__ == app.version


@pytest.mark.parametrize('base,change,expected', [
    ('0.1.0', 'build', '0.1.0.1'), ('0.1.0.1', 'build', '0.1.0.2'),
    ('0.1.0.9', 'patch', '0.1.1.1'), ('0.1.2.9', 'minor', '0.2.0.1'),
    ('0.9.2.9', 'major', '1.0.0.1'),
])
def test_increment_policy(base, change, expected):
    assert policy.next_version(base, change) == expected
    assert Version(base) < Version(expected)


@pytest.mark.parametrize('base', ['0.1', '0.1.0.0', '0.1.0.dev1', '01.1.0', '0.1.0.1.2'])
def test_invalid_baselines_are_rejected(base):
    with pytest.raises(ValueError):
        policy.next_version(base)


def test_explicit_increment_is_repeatable_and_rejects_duplicates(tmp_path):
    def git(*args):
        return subprocess.run(['git', *args], cwd=tmp_path, check=True, capture_output=True)
    git('init')
    git('config', 'user.name', 'Fixture')
    git('config', 'user.email', 'fixture@example.invalid')
    (tmp_path / 'pyproject.toml').write_text('[project]\nversion = "0.1.0"\n')
    git('add', '.')
    git('commit', '-m', 'Historical baseline')
    path = tmp_path / policy.VERSION_FILE
    path.parent.mkdir(parents=True)
    path.write_text('__version__ = "0.1.0"\n')
    args = ['--base-ref', 'HEAD']
    assert policy.main(args, tmp_path) == 1
    assert policy.main(args + ['--write'], tmp_path) == 0
    first = path.read_bytes()
    assert policy.main(args + ['--write'], tmp_path) == 0
    assert path.read_bytes() == first
    assert policy.main(args, tmp_path) == 0
    git('add', '.')
    git('commit', '-m', 'Accepted first numbered build')
    assert policy.main(args, tmp_path) == 1  # Reusing the accepted number fails.
    assert policy.main(args + ['--write'], tmp_path) == 0
    assert policy.read_version(path.read_text()) == '0.1.0.2'
    path.write_text('__version__ = "0.1.0.99"\n')
    assert policy.main(args + ['--write'], tmp_path) == 1
    assert '0.1.0.99' in path.read_text()
