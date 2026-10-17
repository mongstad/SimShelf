import math

import pytest

from simshelf.progress import MAX_LINE, TextProgressParser, progress_report


def test_known_unknown_and_phase_reset():
    assert progress_report() == {"current": None, "total": None, "stage": None}
    assert progress_report(42)["total"] is None
    assert progress_report(10, 10, stage="Solve")["current"] == 10
    assert progress_report(0, 20, stage="Render")["current"] == 0


@pytest.mark.parametrize("current,total", [(1, 0), (-1, 5), (6, 5), (None, 5),
    (True, 10), ("1", 10), (math.nan, 10), (1, math.inf), (1e16, None), (10**1000, None)])
def test_invalid_reports(current, total):
    with pytest.raises(ValueError):
        progress_report(current, total)


@pytest.mark.parametrize("stage", [1, "x" * 161, "hello\nworld", "\0"])
def test_invalid_stages(stage):
    with pytest.raises(ValueError):
        progress_report(stage=stage)


def test_step_stream_chunking_crlf_and_final_line():
    parser = TextProgressParser("step")
    assert list(parser.feed(b"st")) == []
    reports = list(parser.feed(b"ep 1/10\rstep 2/10\r\nSTEP 3/10\nstep 4/10"))
    assert [r["current"] for r in reports] == [1, 2, 3]
    assert parser.finish()["current"] == 4


def test_opt_in_and_conservative_recognition():
    data = b"energy 25%\nstep 1/0\nstep 11/10\n50%\nstep 2/10\n"
    assert list(TextProgressParser("off").feed(data)) == []
    assert [r["current"] for r in TextProgressParser("percent").feed(data)] == [50]
    assert [r["current"] for r in TextProgressParser("step").feed(data)] == [2]
    assert list(TextProgressParser("percent").feed(b"NaN%\n101%\n-1%\n")) == []


def test_overlong_lines_cannot_parse_suffix_and_memory_is_bounded():
    parser = TextProgressParser("percent")
    for _ in range(100):
        assert list(parser.feed(b"x" * 8192)) == []
        assert len(parser.pending) <= MAX_LINE
    assert list(parser.feed(b"50%\r")) == []
    assert list(parser.feed(b"25.5%\r"))[0]["current"] == 25.5

import concurrent.futures
import json
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

from fastapi.testclient import TestClient
from simshelf.api import create_app
from simshelf.backup import create_backup, restore_backup
from simshelf.common import now
from simshelf.progress import enable_progress, write_progress, recover_progress, ProgressWriter
from simshelf.recording import Run, record_command
from simshelf.store import Store


def schema(store):
    with store.connection() as conn:
        return conn.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()[0]


def test_enable_explicit_transactional_and_preserves_records(project, monkeypatch):
    store, sim, root, source = project
    assert schema(Store(store.path)) == '1'
    with pytest.raises(ValueError, match='Explicitly'):
        enable_progress(store)
    with Run(sim['id'], workspace=store.path, capture_console=False) as run:
        with pytest.raises(ValueError, match='finalize'):
            enable_progress(store, confirmed=True)
        with pytest.raises(ValueError, match='enable'):
            run.progress(1, 10)
    before = store.run(run.id)
    with store.connection() as conn:
        conn.execute("CREATE TRIGGER refuse_upgrade BEFORE UPDATE ON metadata WHEN NEW.key='schema_version' BEGIN SELECT RAISE(ABORT, 'injected'); END")
    with pytest.raises(sqlite3.Error, match='injected'):
        enable_progress(store, confirmed=True)
    assert schema(store) == '1'
    with store.connection() as conn:
        assert not conn.execute("SELECT 1 FROM sqlite_master WHERE name='progress'").fetchone()
        conn.execute('DROP TRIGGER refuse_upgrade')
    enable_progress(store, confirmed=True)
    assert enable_progress(store, confirmed=True) == {'schema_version': 4}
    assert schema(store) == '4'
    after = store.run(run.id)
    assert after.pop('progress') is None
    assert before == after


def test_enable_api_authorization_and_no_implicit_upgrade(project):
    store, sim, root, source = project
    with TestClient(create_app(store.path)) as client:
        info = client.get('/api/workspace').json()
        url = '/api/workspace/progress/enable'
        assert client.post(url, json={'confirmed': True}).status_code == 403
        headers = {'X-SimShelf-Token': info['token']}
        assert client.post(url, headers=headers, json={}).status_code == 400
        assert client.post(url, headers={**headers, 'Origin': 'https://example.org'}, json={'confirmed': True}).status_code == 403
        assert schema(store) == '1'
        assert client.post(url, headers=headers, json={'confirmed': True}).json()['schema_version'] == 4


def test_coalescing_final_flush_recovery_and_immutable_completion(project):
    store, sim, root, source = project
    enable_progress(store, confirmed=True)
    with Run(sim['id'], workspace=store.path, capture_console=False) as run:
        for i in range(10000):
            run.progress(i, 9999, stage='Solve')
        with store.connection() as conn:
            row = conn.execute('SELECT sequence FROM progress WHERE run_id=?', (run.id,)).fetchone()
            assert row[0] <= 2  # No one-event-per-step journal growth.
        assert len(list((store.path/'journal'/run.id).glob('progress.json'))) == 1
        run.metric('energy', 12)
    record = store.run(run.id)
    assert record['progress']['current'] == 9999
    assert record['status'] == 'completed'
    assert len(record['metrics']) == 1
    assert record['annotation_history'] == []
    with store.connection() as conn:
        frozen = conn.execute('SELECT data FROM runs WHERE id=?', (run.id,)).fetchone()[0]
    with pytest.raises(ValueError, match='active run'):
        write_progress(store, run.id, {**progress_report(1, 10), 'reported_at': now()}, 'structured', force=True)
    store.reconcile()
    with store.connection() as conn:
        assert frozen == conn.execute('SELECT data FROM runs WHERE id=?', (run.id,)).fetchone()[0]


def test_timer_flushes_last_infrequent_update(project):
    store, sim, root, source = project
    enable_progress(store, confirmed=True)
    with Run(sim['id'], workspace=store.path, capture_console=False) as run:
        run.progress(0, 10)
        run.progress(7, 10)
        deadline = time.monotonic() + 3
        while store.run(run.id)['progress']['current'] != 7 and time.monotonic() < deadline:
            time.sleep(.05)
        assert store.run(run.id)['progress']['current'] == 7


def test_crash_checkpoint_replay_stale_sequence_and_failure_finish(project, monkeypatch):
    store, sim, root, source = project
    enable_progress(store, confirmed=True)
    run = Run(sim['id'], workspace=store.path, capture_console=False).__enter__()
    import simshelf.progress as progress
    original = progress.recover_progress
    calls = 0
    def fail_after_publication(*args):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise sqlite3.OperationalError('injected crash after checkpoint')
        return original(*args)
    monkeypatch.setattr(progress, 'recover_progress', fail_after_publication)
    with pytest.warns(RuntimeWarning, match='could not be saved'):
        run.progress(5, 10)
    monkeypatch.setattr(progress, 'recover_progress', original)
    assert not store.reconcile()['errors']
    assert store.run(run.id)['progress']['current'] == 5
    checkpoint = store.path/'journal'/run.id/'progress.json'
    old = checkpoint.read_bytes()
    write_progress(store, run.id, {**progress_report(0, 20, stage='Reset'), 'reported_at': now()}, 'structured', force=True)
    checkpoint.write_bytes(old)
    recover_progress(store, run.id)
    assert store.run(run.id)['progress']['total'] == 20
    # Invalid telemetry must not prevent scientific finalization.
    run.progress_writer.pending = None
    checkpoint.write_text('{broken')
    run.finish(7)
    assert store.run(run.id)['status'] == 'failed'
    assert 'recovery failed' in store.run(run.id)['progress_error']


def test_backup_restore_deletion_and_schema_preserved(project, tmp_path):
    store, sim, root, source = project
    before = create_backup(store, tmp_path/'before.zip')
    enable_progress(store, confirmed=True)
    with Run(sim['id'], workspace=store.path, capture_console=False) as run:
        run.progress(3, 10)
        archive = create_backup(store, tmp_path/'active.zip')
    restored = restore_backup(archive, tmp_path/'restored')
    assert restored.run(run.id)['status'] == 'interrupted'
    assert restored.run(run.id)['progress']['current'] == 3
    assert schema(restored) == '4'
    assert schema(restore_backup(before, tmp_path/'old')) == '1'
    store.remove_runs([run.id], confirmed=True)
    assert schema(store) == '4'
    assert not (store.path/'journal'/run.id/'progress.json').exists()
    with store.connection() as conn:
        assert conn.execute('SELECT count(*) FROM progress').fetchone()[0] == 0
    assert source.exists()


def test_text_adapter_logs_and_structured_join(project):
    store, sim, root, source = project
    source.write_text("import sys\nsys.stdout.buffer.write(b'step 1/10\\rstep 4/10\\r\\n')\nsys.stderr.buffer.write(b'step 6/10\\r')\n")
    with pytest.raises(ValueError, match='Enable'):
        record_command(store, sim['id'], [sys.executable, str(source)], progress_mode='step', quiet=True)
    assert store.runs() == []
    enable_progress(store, confirmed=True)
    ident, code = record_command(store, sim['id'], [sys.executable, str(source)], progress_mode='step', quiet=True)
    assert code == 0
    assert store.run(ident)['progress']['current'] in (4, 6)  # Two streams have no global ordering.
    assert (store.path/'logs'/ident/'stdout.log').read_bytes() == b'step 1/10\rstep 4/10\r\n'
    assert (store.path/'logs'/ident/'stderr.log').read_bytes() == b'step 6/10\r'
    source.write_text(f"import simshelf\nwith simshelf.run({sim['id']!r}) as run:\n run.progress(2, 5, stage='Structured')\n print('step 5/5', flush=True)\n")
    ident, code = record_command(store, sim['id'], [sys.executable, str(source)], progress_mode='step', quiet=True)
    assert code == 0
    report = store.run(ident)['progress']
    assert (report['source'], report['current'], report['total']) == ('structured', 2, 5)


def test_concurrent_writers_and_long_job_constant_storage(project):
    store, sim, root, source = project
    enable_progress(store, confirmed=True)
    with Run(sim['id'], workspace=store.path, capture_console=False) as run:
        def report(i):
            write_progress(Store(store.path), run.id, {**progress_report(i, 200), 'reported_at': now()}, 'structured', force=True)
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(report, range(200)))
        with store.connection() as conn:
            assert conn.execute('SELECT count(*) FROM progress').fetchone()[0] == 1
            sequence = conn.execute('SELECT sequence FROM progress').fetchone()[0]
            assert 1 <= sequence <= 200  # Delayed older reports can be suppressed.
        for i in range(200):
            report(i)
        with store.connection() as conn:
            assert conn.execute('SELECT sequence FROM progress').fetchone()[0] == sequence + 200
        files = list((store.path/'journal'/run.id).glob('*.json'))
        assert len(files) == 2  # Immutable start + bounded latest checkpoint.
        assert (store.path/'journal'/run.id/'progress.json').stat().st_size < 4096

@pytest.mark.parametrize('initial_schema', ['1', '2', '3'])
def test_supported_upgrade_and_screenshot_does_not_downgrade(project, initial_schema):
    store, sim, root, source = project
    with store.connection() as conn:
        conn.execute("UPDATE metadata SET value=? WHERE key='schema_version'", (initial_schema,))
    enable_progress(store, confirmed=True)
    with Run(sim['id'], workspace=store.path, capture_console=False) as run:
        run.progress(1, 10)
    from simshelf.capture import save_file
    from simshelf.screenshots import delete_screenshot
    image = root/'manual.png'
    image.write_bytes(b'fixture')
    artifact = save_file(store, run.id, image)
    delete_screenshot(store, run.id, artifact['id'], confirmed=True)
    assert schema(store) == '4'
    assert store.run(run.id)['progress']['current'] == 1


def test_delayed_report_and_dead_owner_recovery(project):
    store, sim, root, source = project
    enable_progress(store, confirmed=True)
    run = Run(sim['id'], workspace=store.path, capture_console=False).__enter__()
    recent = {**progress_report(5, 10), 'reported_at': now()}
    write_progress(store, run.id, recent, 'structured', force=True)
    write_progress(store, run.id, {**progress_report(2, 10), 'reported_at': '2000-01-01T00:00:00+00:00'}, 'structured', force=True)
    assert store.run(run.id)['progress']['current'] == 5
    # Simulate an owner whose process vanished; recovery keeps the last progress.
    with store.connection() as conn:
        raw = json.loads(conn.execute('SELECT data FROM runs WHERE id=?', (run.id,)).fetchone()[0])
        raw['owner']['pid'] = 99999999
        conn.execute('UPDATE runs SET data=? WHERE id=?', (json.dumps(raw), run.id))
    assert not store.reconcile()['errors']
    assert store.run(run.id)['status'] == 'interrupted'
    assert store.run(run.id)['progress']['current'] == 5
    run.progress_writer.close()


def test_portal_live_reconnect_unknown_failure_and_stop(project):
    store, sim, root, source = project
    with TestClient(create_app(store.path)) as client:
        auth = headers(client)
        source.write_text("print('step 1/10')\n")
        rejected = client.post(f"/api/simulations/{sim['id']}/launch", headers=auth, json=settings(progress_mode='step'))
        assert rejected.status_code == 400 and store.runs() == []
        enable_progress(store, confirmed=True)
        source.write_text("import time\nprint('step 2/10', flush=True)\ntime.sleep(10)\n")
        ident = launch(client, sim, auth, progress_mode='step')
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            report = client.get(f'/api/runs/{ident}').json().get('progress')
            if report: break
            time.sleep(.05)
        assert report['current'] == 2
        assert Store(store.path).run(ident)['progress'] == report
        assert client.post(f'/api/runs/{ident}/stop', headers=auth).status_code == 202
        result = finish(store, ident)
        assert result['status'] == 'interrupted' and result['progress']['current'] == 2
        source.write_text("import sys\nprint('100%', flush=True)\nsys.exit(3)\n")
        ident = launch(client, sim, auth, progress_mode='percent')
        result = finish(store, ident)
        assert result['status'] == 'failed' and result['progress']['current'] == 100
        source.write_text("print('step 5/10')\n")
        ident = launch(client, sim, auth)
        assert finish(store, ident)['progress'] is None


def test_portal_structured_progress_preserves_scientific_values(project):
    store, sim, root, source = project
    enable_progress(store, confirmed=True)
    source.write_text(f"import simshelf\nwith simshelf.run({sim['id']!r}, parameters={{'seed':7}}) as run:\n run.progress(3, 4, stage='Solve')\n run.metric('energy', 9)\n")
    with TestClient(create_app(store.path)) as client:
        ident = launch(client, sim, headers(client))
        result = finish(store, ident)
    assert result['status'] == 'completed'
    assert result['progress']['current'] == 3  # Finalization never forces 100%.
    assert result['parameters']['seed'] == 7
    assert result['metrics'][0]['value'] == 9


def settings(**changes):
    return {"interpreter": sys.executable, "cwd": ".", "arguments": [], "output_dir": "outputs", **changes}


def headers(client):
    return {"X-SimShelf-Token": client.get("/api/workspace").json()["token"]}


def launch(client, sim, auth, **changes):
    result = client.post(f"/api/simulations/{sim['id']}/launch", headers=auth, json=settings(**changes))
    assert result.status_code == 201, result.text
    return result.json()['run_id']


def finish(store, ident):
    deadline = time.monotonic() + 12
    while time.monotonic() < deadline:
        result = store.run(ident)
        if result['status'] != 'running': return result
        time.sleep(.05)
    raise AssertionError('Run did not finish')


def test_cross_process_sequences_and_run_deletion_serialization(project):
    store, sim, root, source = project
    enable_progress(store, confirmed=True)
    with Run(sim['id'], workspace=store.path, capture_console=False) as run:
        code = "from simshelf.store import Store; from simshelf.progress import write_progress,progress_report; from simshelf.common import now; import sys; write_progress(Store(sys.argv[1]),sys.argv[2],{**progress_report(int(sys.argv[3]),10),'reported_at':now()},'structured',force=True)"
        children = [subprocess.Popen([sys.executable, '-B', '-c', code, str(store.path), run.id, str(i)]) for i in range(6)]
        assert all(child.wait(timeout=10) == 0 for child in children)
        with store.connection() as conn:
            # Timestamp ordering may suppress an older report acquired later.
            count = conn.execute('SELECT sequence FROM progress').fetchone()[0]
            assert 1 <= count <= 6
        assert not store.reconcile()['errors']
    store.remove_runs([run.id], confirmed=True)
    assert not store.reconcile()['errors']
    with pytest.raises(ValueError, match='active run'):
        write_progress(store, run.id, {**progress_report(1, 2), 'reported_at': now()}, 'structured')


def test_cli_explicit_enable_and_terminal_mode(project):
    store, sim, root, source = project
    prefix = [sys.executable, '-B', '-m', 'simshelf', '--workspace', str(store.path)]
    denied = subprocess.run([*prefix, 'enable-progress'], capture_output=True, text=True)
    assert denied.returncode == 1 and 'older SimShelf' in denied.stderr
    assert schema(store) == '1'
    subprocess.run([*prefix, 'enable-progress', '--confirm'], check=True, capture_output=True)
    source.write_text("print('25%')\n")
    subprocess.run([*prefix, 'record', '-s', sim['id'], '--progress', 'percent', '--', sys.executable, str(source)], check=True, capture_output=True)
    ident = store.runs()[0]['id']
    assert store.run(ident)['progress']['current'] == 25
    assert store.run(ident)['progress_mode'] == 'percent'


def test_progress_io_failure_does_not_change_exit_or_logs(project, monkeypatch):
    store, sim, root, source = project
    enable_progress(store, confirmed=True)
    import simshelf.progress as progress
    def fail(*args):
        raise OSError('injected disk failure')
    monkeypatch.setattr(progress, 'atomic_write', fail)
    source.write_text("import sys\nsys.stdout.buffer.write(b'step 1/10\\rstep 2/10\\n')\nsys.exit(7)\n")
    with pytest.warns(RuntimeWarning, match='injected disk failure'):
        ident, code = record_command(store, sim['id'], [sys.executable, str(source)], progress_mode='step', quiet=True)
    assert code == 7
    assert store.run(ident)['exit_code'] == 7
    assert 'injected disk failure' in store.run(ident)['progress_error']
    assert (store.path/'logs'/ident/'stdout.log').read_bytes() == b'step 1/10\rstep 2/10\n'


def test_restore_rejects_invalid_progress_before_install(project, tmp_path):
    import zipfile, hashlib
    store, sim, root, source = project
    enable_progress(store, confirmed=True)
    with Run(sim['id'], workspace=store.path, capture_console=False) as run:
        run.progress(1, 2)
    original = create_backup(store, tmp_path/'valid.zip')
    with zipfile.ZipFile(original) as z:
        files = {name:z.read(name) for name in z.namelist()}
    db = tmp_path/'edited.sqlite3'
    db.write_bytes(files['simshelf.sqlite3'])
    with sqlite3.connect(db) as conn:
        conn.execute('PRAGMA journal_mode=DELETE')  # Include edits in the archived DB, not a sidecar WAL.
        conn.execute("UPDATE progress SET data=?", (json.dumps({'current':1,'total':0}),))
    files['simshelf.sqlite3'] = db.read_bytes()
    manifest = json.loads(files['manifest.json'])
    manifest['files']['simshelf.sqlite3'] = hashlib.sha256(files['simshelf.sqlite3']).hexdigest()
    files['manifest.json'] = json.dumps(manifest).encode()
    archive = tmp_path/'invalid-progress.zip'
    with zipfile.ZipFile(archive,'w') as z:
        for name,data in files.items(): z.writestr(name,data)
    destination = tmp_path/'must-not-exist'
    with pytest.raises(ValueError, match='positive total'):
        restore_backup(archive, destination)
    assert not destination.exists()
