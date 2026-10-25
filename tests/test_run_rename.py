"""Display-name annotations preserve execution identity and an auditable history."""
import json
import sqlite3

import pytest
from fastapi.testclient import TestClient

from simshelf.api import create_app
from simshelf.backup import create_backup, restore_backup
from simshelf.recording import Run
from simshelf.store import Store
from test_library_preservation_audit import library, launch


@pytest.mark.parametrize('state', ['running', 'completed', 'failed', 'interrupted'])
def test_rename_history_restart_backup_and_unchanged_execution(project, tmp_path, state):
    store, sim, root, source = project
    recorder = Run(sim['id'], workspace=store.path, name='Original name', parameters={'seed': 7}, capture_console=False).__enter__()
    recorder.metric('energy', 1.25)
    recorder.output_dir.mkdir()
    output = recorder.output_dir/'result.json'
    output.write_bytes(b'{"answer":42}')
    if state != 'running':
        recorder.finish(7 if state == 'failed' else 0, status=state)
    before = store.run(recorder.id)
    start = next(p for p in (store.path/'journal'/recorder.id).glob('*.json') if json.loads(p.read_text())['kind'] == 'start')
    start_bytes = start.read_bytes()
    source_bytes, output_bytes = source.read_bytes(), output.read_bytes()
    with store.connection() as conn:
        schema = conn.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()[0]
        metadata = conn.execute('SELECT * FROM metadata ORDER BY key').fetchall()
    with TestClient(create_app(store.path)) as client:
        headers = {'X-SimShelf-Token': client.get('/api/workspace').json()['token']}
        path = f'/api/runs/{recorder.id}'
        for name, previous in [('First rename', 'Original name'), ('Final rename', 'First rename')]:
            result = client.patch(path, headers=headers, json={'name': f'  {name}  '})
            assert result.status_code == 200, result.text
            saved = result.json()
            assert saved['name'] == name and saved['status'] == state
            assert saved['annotation_history'][0]['name'] == name
            assert saved['annotation_history'][0]['previous_name'] == previous
            assert client.get('/api/runs', params={'q': name}).json()[0]['id'] == recorder.id
        after = store.run(recorder.id)
        assert {k: v for k, v in after.items() if k not in ('name', 'annotation_history')} == {
            k: v for k, v in before.items() if k not in ('name', 'annotation_history')}
    reopened = Store(store.path)
    assert not reopened.reconcile()['errors']
    assert reopened.run(recorder.id)['name'] == 'Final rename'
    assert start.read_bytes() == start_bytes
    assert source.read_bytes() == source_bytes and output.read_bytes() == output_bytes
    with reopened.connection() as conn:
        assert conn.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()[0] == schema
        assert [tuple(r) for r in conn.execute('SELECT * FROM metadata ORDER BY key')] == [tuple(r) for r in metadata]
    restored = restore_backup(create_backup(reopened, tmp_path/'renamed.zip'), tmp_path/'restored')
    record = restored.run(recorder.id)
    assert record['name'] == 'Final rename'
    assert record['annotation_history'] == after['annotation_history']
    assert record['annotation_history'][-1]['previous_name'] == 'Original name'
    assert record['snapshot_id'] == before['snapshot_id'] and record['command'] == before['command']
    recorder.finish(0)
    assert store.run(recorder.id)['name'] == 'Final rename'


@pytest.mark.parametrize('name', ['', ' \t\n', 'x' * 161, None])
def test_rename_validation_does_not_write_history(project, name):
    store, sim, root, source = project
    with Run(sim['id'], workspace=store.path, name='Confirmed name', capture_console=False) as run:
        pass
    before = store.run(run.id)
    journals = {p.name: p.read_bytes() for p in (store.path/'journal'/run.id).glob('*.json')}
    with TestClient(create_app(store.path)) as client:
        auth = {'X-SimShelf-Token': client.get('/api/workspace').json()['token']}
        result = client.patch(f'/api/runs/{run.id}', headers=auth, json={'name': name})
        assert result.status_code in (400, 422)
        if name is None or name == ' \t\n':
            assert 'Run name must contain' in result.json()['detail']
    assert store.run(run.id) == before
    assert {p.name: p.read_bytes() for p in (store.path/'journal'/run.id).glob('*.json')} == journals


def test_rename_token_origin_and_permission_failure(project, monkeypatch):
    store, sim, root, source = project
    with Run(sim['id'], workspace=store.path, name='Confirmed name', capture_console=False) as run:
        pass
    before = store.run(run.id)
    app = create_app(store.path)
    with TestClient(app) as client:
        auth = {'X-SimShelf-Token': client.get('/api/workspace').json()['token']}
        path = f'/api/runs/{run.id}'
        for headers in ({}, {'X-SimShelf-Token': 'old-token'}, {**auth, 'Origin': 'https://elsewhere.example'}):
            assert client.patch(path, headers=headers, json={'name': 'Rejected name'}).status_code == 403
        def denied(*args):
            raise PermissionError('read-only fixture')
        monkeypatch.setattr(app.state.store, 'emit', denied)
        result = client.patch(path, headers=auth, json={'name': 'Rejected name'})
        assert result.status_code == 409
        assert 'permissions' in result.json()['detail'] and 'refresh' in result.json()['detail']
    assert store.run(run.id) == before


def test_rename_durable_recovery_is_idempotent_and_keeps_previous_name(project, monkeypatch):
    store, sim, root, source = project
    with Run(sim['id'], workspace=store.path, name='Original', capture_console=False) as run:
        pass
    apply = store.apply
    def fail(*args):
        raise sqlite3.OperationalError('injected database lock')
    monkeypatch.setattr(store, 'apply', fail)
    with pytest.raises(sqlite3.OperationalError):
        store.emit(run.id, 'annotation', {'name': 'Recovered name'})
    assert store.run(run.id)['name'] == 'Original'
    monkeypatch.setattr(store, 'apply', apply)
    assert store.reconcile()['recovered'] == 1
    assert store.reconcile()['recovered'] == 0
    result = store.run(run.id)
    assert result['name'] == 'Recovered name'
    assert len(result['annotation_history']) == 1
    assert result['annotation_history'][0]['previous_name'] == 'Original'


def test_rename_leaves_published_git_history_and_download_bytes_unchanged(library):
    from simshelf import git_archive as archive, preservation
    store, repo, (sim, _) = library
    options = {'enabled': True, 'all_sources': True, 'sources': [],
               'extensions': ['.json', '.csv', '.log'], 'process_logs': True}
    preservation.save(store, sim['id'], preservation.preview(store, sim['id'], sim['config'], options), True)
    before = launch(store, sim, 'retained-argv', csv=True)
    head = archive.git(repo, 'rev-parse', 'HEAD')
    events = archive.entries(store, before['id'])
    record_bytes = archive.download_record(store, before['id'], events[0]['id'])
    files = [archive.download(store, before['id'], events[0]['id'], i)[1] for i in range(len(events[0]['files']))]
    with TestClient(create_app(store.path)) as client:
        auth = {'X-SimShelf-Token': client.get('/api/workspace').json()['token']}
        result = client.patch(f"/api/runs/{before['id']}", headers=auth, json={'name': 'Friendly annotation'})
        assert result.status_code == 200
    assert archive.git(repo, 'rev-parse', 'HEAD') == head
    assert archive.entries(store, before['id']) == events
    assert archive.download_record(store, before['id'], events[0]['id']) == record_bytes
    assert [archive.download(store, before['id'], events[0]['id'], i)[1] for i in range(len(files))] == files
    after = store.run(before['id'])
    assert after['command'] == before['command']
    assert after['snapshot'] == before['snapshot'] and after['git'] == before['git']
    review = preservation.additions_preview(store, before['id'], [], include_notes=True)
    assert review['record']['annotations'][-1]['data']['previous_name'] == before['name']
    assert archive.git(repo, 'rev-parse', 'HEAD') == head  # Review is not publication.
