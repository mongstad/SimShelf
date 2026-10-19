"""Read-only settings eligibility, independent of paged/filtered run lists."""
import json

import pytest
from fastapi.testclient import TestClient

from simshelf.api import create_app
from simshelf.common import json_text
from simshelf.recording import Run
from simshelf.simulation_activity import blocks_administration
from simshelf.simulation_removal import state


def record(store, sim, name='fixture'):
    run = Run(sim['id'], workspace=store.path, capture_console=False, name=name)
    run.__enter__()
    return run


def activity(store):
    return {s['id']: s['administration_active'] for s in store.simulations()}


def contents(store):
    with store.connection() as conn:
        return {table: [tuple(row) for row in conn.execute(f'SELECT * FROM {table} ORDER BY rowid')]
                for table in ('metadata', 'runs', 'simulations', 'artifacts', 'annotations', 'applied_events')}


@pytest.mark.parametrize('status,capture,blocked', [
    ('running', 'pending', True), ('running', 'complete', True),
    ('starting', 'complete', True), ('capturing', 'pending', True),
    ('completed', 'pending', True), ('failed', 'pending', True),
    ('interrupted', 'pending', True), ('completed', 'complete', False),
    ('failed', 'partial', False), ('interrupted', 'incomplete', False),
    ('completed', None, False),
])
def test_projection_matches_unchanged_removal_predicate(project, status, capture, blocked):
    store, sim, _, _ = project
    run = record(store, sim)
    run.finish()
    with store.connection() as conn:
        conn.execute("UPDATE metadata SET value='2' WHERE key='schema_version'")
        row = json.loads(conn.execute('SELECT data FROM runs WHERE id=?', (run.id,)).fetchone()[0])
        row['status'] = status
        if capture is None:
            row.pop('capture_status', None)
        else:
            row['capture_status'] = capture
        conn.execute('UPDATE runs SET status=?, data=? WHERE id=?', (status, json_text(row), run.id))
    before = contents(store)
    assert blocks_administration(row) is blocked
    assert activity(store)[sim['id']] is blocked
    with store.connection() as conn:
        assert state(conn, sim['id'])[0]['active'] is blocked
    assert contents(store) == before


def test_independent_concurrent_runs_and_capture_completion(project, tmp_path, monkeypatch):
    store, sim, _, _ = project
    other = tmp_path / 'other'; other.mkdir(); (other/'main.py').write_text('value=1')
    idle = store.add_simulation(other, name='Idle', entrypoint='main.py')
    first = Run(sim['id'], workspace=store.path, capture_console=False, output_dir='outputs/first')
    first.__enter__()
    # Source/capture isolation matches independent terminal/editor runs.
    second = Run(sim['id'], workspace=store.path, capture_console=False, output_dir='outputs/second')
    second.__enter__()
    assert activity(store) == {sim['id']: True, idle['id']: False}
    first.finish()
    assert activity(store)[sim['id']] is True
    from simshelf import recording
    capture = recording.capture_outputs
    def during_capture(*args, **kwargs):
        assert activity(store)[sim['id']] is True
        return capture(*args, **kwargs)
    monkeypatch.setattr(recording, 'capture_outputs', during_capture)
    second.finish()
    assert activity(store) == {sim['id']: False, idle['id']: False}
    with store.connection() as conn:
        assert conn.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()[0] == '1'


def test_activity_is_not_limited_to_visible_recent_runs(project):
    store, sim, _, _ = project
    active = record(store, sim, name='older active')
    # Disposable fixture rows: enough newer records to hide the active run from
    # the portal's default 200-item list and its 1,000-item maximum.
    with store.connection() as conn:
        original = json.loads(conn.execute('SELECT data FROM runs WHERE id=?', (active.id,)).fetchone()[0])
        for index in range(1001):
            data = {**original, 'id': f'recent-{index}', 'status': 'completed', 'capture_status': 'complete', 'started_at': '2099-01-01T00:00:00Z'}
            conn.execute('INSERT INTO runs VALUES (?,?,?,?,?,?)', (data['id'], sim['id'], data['status'], data['started_at'], data['version'], json_text(data)))
    assert all(r['id'] != active.id for r in store.runs(limit=1000))
    assert activity(store)[sim['id']] is True
    active.finish()
    assert activity(store)[sim['id']] is False


def test_api_includes_starting_and_finalizing_portal_jobs_without_mutation(project, tmp_path):
    store, sim, _, _ = project
    other = tmp_path/'other'; other.mkdir(); (other/'main.py').write_text('value=1')
    idle = store.add_simulation(other, name='Idle', entrypoint='main.py')
    app = create_app(store.path)
    jobs = app.state.jobs
    class Process:
        returncode = None
        def poll(self): return self.returncode
    process = Process()
    # A supervisor is already admitted but has no run ID/row during startup.
    jobs.jobs[process] = {'simulation_id': sim['id'], 'run_id': None, 'stopping': False}
    client = TestClient(app)  # No background reconciliation; inspect only GET.
    before = contents(store)
    def response():
        result = client.get('/api/simulations')
        assert result.status_code == 200
        return {s['id']: s['administration_active'] for s in result.json()}
    assert response() == {sim['id']: True, idle['id']: False}
    jobs.jobs[process].update(run_id='finalized', stopping=True)
    assert response()[sim['id']] is True  # finalizing supervisor is still alive
    process.returncode = 0
    assert response() == {sim['id']: False, idle['id']: False}
    assert contents(store) == before
    assert 'administration_active' not in store.simulation(sim['id'])


@pytest.mark.parametrize('starts_during_read', [True, False])
def test_supervisor_observations_cover_changes_during_read(project, monkeypatch, starts_during_read):
    store, sim, _, _ = project
    app = create_app(store.path)
    jobs = app.state.jobs
    class Process:
        returncode = None
        def poll(self): return self.returncode
    process = Process()
    job = {'simulation_id': sim['id'], 'run_id': None, 'stopping': False}
    if not starts_during_read:
        jobs.jobs[process] = job
    original = app.state.store.simulations
    def read():
        result = original()
        if starts_during_read:
            jobs.jobs[process] = job
        else:
            process.returncode = 0
        return result
    monkeypatch.setattr(app.state.store, 'simulations', read)
    client = TestClient(app)
    assert client.get('/api/simulations').json()[0]['administration_active'] is True
    # This was transient observation only; no run or stored preference was added.
    assert store.runs() == []
