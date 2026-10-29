"""Allocation restrictions are independent of typed/manual argv and binding claims."""
import hashlib
import json
import sys

import pytest
from fastapi.testclient import TestClient

from simshelf.api import create_app
from simshelf.parameters import discover_parameters
from simshelf.portal import execution_settings
from simshelf.recording import Run, record_command
from simshelf.store import Store
from test_portal import headers, settings

HEADER = '[swss]\nschema_version=2\nentrypoint="field.py"\nsimulation_version="1.0.0"\n'


@pytest.mark.parametrize('kind', ['unbound', 'bound', 'stale', 'malformed', 'unsupported', 'unassociated', 'symlink'])
def test_settings_launch_and_direct_recorder_refuse_before_allocation(project, kind):
    store, sim, root, source = project
    path = root / 'swss.toml'
    text = HEADER
    if kind in ('bound', 'stale'):
        digest = hashlib.sha256(source.read_bytes()).hexdigest() if kind == 'bound' else '0' * 64
        text += f'[[swss.source_files]]\npath="field.py"\nsha256="{digest}"\n'
    if kind == 'malformed': text = '[invalid'
    if kind == 'unsupported': text = HEADER.replace('schema_version=2', 'schema_version=4')
    if kind == 'unassociated':
        (root / 'other.py').write_text('pass\n')
        text = HEADER.replace('field.py', 'other.py')
    if kind == 'symlink': path.symlink_to(source)
    else: path.write_text(text)
    before = path.read_bytes()
    discovery = discover_parameters(sim)
    status = discovery['output_policy']
    assert status['state'] == ('valid' if kind in ('unbound', 'bound') else 'unavailable')
    assert status['launcher_allowed'] is False
    if kind == 'bound': assert status['binding'] == 'listed bytes verified'
    if kind == 'unbound': assert status['binding'] == 'binding unverified'
    config = settings(output_policy='per_run', parameter_review={'mode': 'manual', 'fingerprint': None}, arguments=['--label', '', '--N', '0010', '--', '--literal'])
    with TestClient(create_app(store.path)) as client:
        auth = headers(client)
        for suffix, method in [('execution', 'put'), ('execution/validate', 'post'), ('launch', 'post')]:
            result = getattr(client, method)(f"/api/simulations/{sim['id']}/{suffix}", headers=auth, json=config)
            assert result.status_code == 400, result.text
            assert 'Launcher-coordinated output is unavailable' in result.text
        result = client.post(f"/api/simulations/{sim['id']}/execution/outputs", headers=auth,
                             json={'cwd': '.', 'arguments': [], 'output_dir': 'outputs', 'output_policy': 'per_run'})
        assert result.status_code == 400
        # Explicit manual fixed-parent review remains available, with exact argv.
        result = client.put(f"/api/simulations/{sim['id']}/execution", headers=auth, json={**config, 'output_policy': 'fixed'})
        assert result.status_code == 200, result.text
    assert store.simulation(sim['id'])['execution']['arguments'] == config['arguments']
    with pytest.raises(ValueError, match='Launcher-coordinated'):
        record_command(store, sim['id'], [sys.executable, str(source)], output_policy='per_run', quiet=True)
    with pytest.raises(ValueError, match='Launcher-coordinated'):
        with Run(sim['id'], workspace=store.path, output_policy='per_run', capture_console=False): pass
    assert not (root / 'outputs').exists()
    assert not store.runs()
    assert path.read_bytes() == before


def test_saved_policy_adoption_restart_and_history_require_explicit_correction(project):
    store, sim, root, source = project
    config = settings(output_policy='per_run')
    store.update_simulation(sim['id'], execution=config)
    with Run(sim['id'], workspace=store.path, output_policy='per_run', capture_console=False) as run:
        (run.output_dir / 'old.json').write_text('{"historic": true}')
    old = store.run(run.id)
    original = (run.output_dir / 'old.json').read_bytes()
    (root / 'swss.toml').write_text(HEADER)
    reopened = Store(store.path)
    saved = reopened.simulation(sim['id'])['execution']
    assert saved['output_policy'] == 'per_run'
    with pytest.raises(ValueError, match='Saved settings were not changed'):
        execution_settings(reopened.simulation(sim['id']), saved)
    assert reopened.simulation(sim['id'])['execution'] == saved
    reopened.update_simulation(sim['id'], execution={**saved, 'output_policy': 'fixed'})
    assert reopened.simulation(sim['id'])['execution']['output_policy'] == 'fixed'
    assert reopened.run(run.id) == old
    assert (run.output_dir / 'old.json').read_bytes() == original


def test_adoption_during_snapshot_cannot_allocate(project, monkeypatch):
    store, sim, root, _ = project
    import simshelf.recording as recording
    original = recording.source_snapshot
    def adopt(*args, **kwargs):
        (root / 'swss.toml').write_text(HEADER)
        return original(*args, **kwargs)
    monkeypatch.setattr(recording, 'source_snapshot', adopt)
    with pytest.raises(ValueError, match='Launcher-coordinated'):
        with Run(sim['id'], workspace=store.path, output_policy='per_run', capture_console=False): pass
    assert not (root / 'outputs').exists()
    assert not store.runs()


def test_fixed_parent_captures_only_new_logs_and_missing_log_is_partial(project):
    store, sim, root, source = project
    (root / 'swss.toml').write_text(HEADER)
    records = []
    for index in range(3):
        with Run(sim['id'], workspace=store.path, capture_console=False) as run:
            output = run.output_dir / f'owned-{index}'
            output.mkdir(parents=True)
            (output / 'summary.json').write_text(json.dumps({'run': index}))
            if index < 2: (output / 'timestamp-version.log').write_text(f'run {index}')
        result = store.run(run.id)
        assert result['capture_status'] == ('complete' if index < 2 else 'partial')
        assert len(result['artifacts']) == (2 if index < 2 else 1)
        assert all(a['name'].startswith(f'owned-{index}/') for a in result['artifacts'])
        records.append(result)
    assert any('Required log' in error for error in records[-1]['capture_errors'])
    assert store.run(records[0]['id']) == records[0]
    assert (root / 'outputs/owned-0/timestamp-version.log').read_text() == 'run 0'
