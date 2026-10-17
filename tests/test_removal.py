import json
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from simshelf.api import create_app
from simshelf.backup import create_backup, restore_backup
from simshelf.capture import save_file
from simshelf.recording import Run
from simshelf.source import blob_path
from simshelf.store import Store
from simshelf import removal


def finished(store, sim, **kwargs):
    with Run(sim['id'], workspace=store.path, capture_console=False, **kwargs) as run:
        pass
    return run.id


def test_remove_batch_preserves_sources_references_and_shared_blobs(project, tmp_path):
    store, sim, root, source = project
    first = finished(store, sim)
    second = finished(store, sim)
    other = finished(store, sim)
    file = root / 'shared.txt'
    file.write_text('shared data')
    shared = save_file(store, first, file)
    kept = save_file(store, other, file)
    external = save_file(store, first, file, policy='reference')
    unique = root / 'unique.txt'
    unique.write_text('unique removed data')
    owned = save_file(store, second, unique)
    original = store.run(other)
    start_events = [json.loads(p.read_text()) for p in (store.path / 'journal' / first).glob('*.json')]
    result = store.remove_runs([first, second], confirmed=True)
    assert not result['cleanup_errors']
    assert store.simulations()[0]['run_count'] == 1
    assert store.versions(sim['id'])[0]['run_count'] == 1
    assert store.run(other)['baseline_deleted'] is True
    assert {k: v for k, v in store.run(other).items() if k != 'baseline_deleted'} == {k: v for k, v in original.items() if k != 'baseline_deleted'}
    assert store.artifact_file(kept['id']).read_text() == 'shared data'
    assert not blob_path(store.path, owned['blob']).exists()
    assert file.read_text() == 'shared data' and unique.exists() and source.exists()
    assert external['original_path'] == str(file)
    for event in start_events:
        store.apply(event)
    assert store.reconcile()['errors'] == []
    with pytest.raises(ValueError, match='not found'):
        store.run(first)
    with pytest.raises(ValueError, match='removed'):
        store.emit(first, 'annotation', {'notes': 'must not return'})
    assert store.remove_runs([first, second], confirmed=True)['removed_ids'] == [first, second]
    store.remove_runs([other], confirmed=True)
    assert not blob_path(store.path, shared['blob']).exists()
    assert not list((store.path / 'snapshots').glob('*.json'))
    assert store.versions(sim['id']) == []
    new = finished(store, sim)
    assert store.run(new)['source_change'] == 'baseline'


def test_active_unknown_unconfirmed_batch_is_atomic(project):
    store, sim, root, source = project
    done = finished(store, sim)
    with Run(sim['id'], workspace=store.path, capture_console=False) as active:
        with pytest.raises(ValueError, match='Running'):
            store.remove_runs([done, active.id], confirmed=True)
        assert store.run(done)
    with pytest.raises(ValueError, match='Confirm'):
        store.remove_runs([done])
    for identifiers in ([done, '0' * 32], ['../outside'], [], [12]):
        with pytest.raises(ValueError):
            store.remove_runs(identifiers, confirmed=True)
        assert store.run(done)
    with store.connection() as conn:
        assert conn.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()[0] == '1'


def test_baseline_diff_backup_and_old_backup(project, tmp_path):
    store, sim, root, source = project
    first = finished(store, sim)
    source.write_text(source.read_text() + '# second source\n')
    second = finished(store, sim)
    old_backup = create_backup(store, tmp_path / 'before.zip')
    store.remove_runs([first], confirmed=True)
    backup = create_backup(store, tmp_path / 'after.zip')
    restored = restore_backup(backup, tmp_path / 'restored')
    assert restored.reconcile()['errors'] == []
    assert len(restored.runs()) == 1
    assert restored.run(second)['baseline_run_id'] == first
    with TestClient(create_app(restored.path)) as client:
        result = client.get(f'/api/runs/{second}/source', params={'path': 'field.py', 'compare': first})
        assert result.status_code == 200
        assert '+# second source' in result.json()['text']
        assert client.get(f'/api/runs/{first}').status_code == 400
    old = restore_backup(old_backup, tmp_path / 'old')
    assert len(old.runs()) == 2
    new = finished(store, sim)
    assert store.run(new)['baseline_run_id'] == second
    restored.remove_runs([second], confirmed=True)
    assert not list((restored.path / 'snapshots').glob('*.json'))


def test_cleanup_failure_and_crash_retry(project, monkeypatch):
    store, sim, root, source = project
    ident = finished(store, sim)
    unlink = removal.unlink_managed
    monkeypatch.setattr(removal, 'unlink_managed', lambda *args: (_ for _ in ()).throw(PermissionError('injected')))
    result = store.remove_runs([ident], confirmed=True)
    assert result['cleanup_errors'] and store.runs() == []
    assert store.reconcile()['errors']
    monkeypatch.setattr(removal, 'unlink_managed', unlink)
    assert Store(store.path).reconcile()['errors'] == []
    assert not list((store.path / 'snapshots').glob('*.json'))
    ident = finished(store, sim)
    cleanup = removal.cleanup_removed
    monkeypatch.setattr(removal, 'cleanup_removed', lambda *_: (_ for _ in ()).throw(SystemExit('crash after commit')))
    with pytest.raises(SystemExit):
        store.remove_runs([ident], confirmed=True)
    monkeypatch.setattr(removal, 'cleanup_removed', cleanup)
    assert Store(store.path).reconcile()['errors'] == []
    assert store.runs() == []


def test_transaction_failure_rolls_back_all_records(project, monkeypatch):
    store, sim, root, source = project
    ids = [finished(store, sim), finished(store, sim)]
    original = removal.json_text
    calls = 0
    def fail_second(value):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise sqlite3.OperationalError('injected transaction failure')
        return original(value)
    monkeypatch.setattr(removal, 'json_text', fail_second)
    with pytest.raises(sqlite3.OperationalError):
        store.remove_runs(ids, confirmed=True)
    assert {r['id'] for r in store.runs()} == set(ids)
    assert all(store.run(i)['snapshot'] for i in ids)


def test_symlink_cleanup_does_not_touch_original(project, tmp_path):
    store, sim, root, source = project
    ident = finished(store, sim)
    logs = store.path / 'logs'
    logs.symlink_to(root, target_is_directory=True)
    outside = root / ident
    outside.mkdir()
    (outside / 'stdout.log').write_text('original scientific output')
    result = store.remove_runs([ident], confirmed=True)
    assert result['cleanup_errors']
    assert (outside / 'stdout.log').read_text() == 'original scientific output'
    logs.unlink()
    assert store.reconcile()['errors'] == []


def test_authorization_duplicate_requests_failed_run_and_late_upload(project):
    store, sim, root, source = project
    with pytest.raises(RuntimeError):
        with Run(sim['id'], workspace=store.path, capture_console=False) as run:
            raise RuntimeError('scientific failure')
    with TestClient(create_app(store.path)) as client:
        headers = {'X-SimShelf-Token': client.get('/api/workspace').json()['token']}
        body = {'run_ids': [run.id], 'confirmed': True}
        assert client.post('/api/runs/remove', json=body).status_code == 403
        assert client.post('/api/runs/remove', json=body, headers={**headers, 'Origin': 'https://other.example'}).status_code == 403
        assert client.post('/api/runs/remove', json={**body, 'confirmed': False}, headers=headers).status_code == 400
        assert client.post('/api/runs/remove', json={**body, 'path': str(source)}, headers=headers).status_code == 422
        assert client.post('/api/runs/remove', json=body, headers=headers).status_code == 200
        assert client.post('/api/runs/remove', json=body, headers=headers).status_code == 200
        assert client.post(f'/api/runs/{run.id}/attachments', headers=headers, files={'file': ('x.txt', b'x')}).status_code == 400
        assert client.patch(f'/api/runs/{run.id}', headers=headers, json={'notes': 'late'}).status_code == 400
        assert client.get('/api/runs').json() == []


def test_delete_waits_for_attachment_and_backup(project, tmp_path, monkeypatch):
    store, sim, root, source = project
    ident = finished(store, sim)
    other = finished(store, sim)
    file = root / 'shared.txt'
    file.write_text('shared')
    first = save_file(store, ident, file)
    reached, release = threading.Event(), threading.Event()
    emit = store.emit
    def blocked_emit(*args, **kwargs):
        reached.set()
        assert release.wait(10)
        return emit(*args, **kwargs)
    monkeypatch.setattr(store, 'emit', blocked_emit)
    with ThreadPoolExecutor(2) as pool:
        attachment = pool.submit(save_file, store, other, file)
        assert reached.wait(10)
        deletion = pool.submit(store.remove_runs, [ident], confirmed=True)
        assert not deletion.done()
        release.set()
        saved = attachment.result(timeout=10)
        assert not deletion.result(timeout=10)['cleanup_errors']
    assert store.artifact_file(saved['id']).read_text() == 'shared'
    assert blob_path(store.path, first['blob']).exists()
    monkeypatch.setattr(store, 'emit', emit)
    import simshelf.backup as backup_module
    original_digest = backup_module.file_digest
    reached.clear(); release.clear()
    def blocked_digest(path):
        reached.set()
        assert release.wait(10)
        return original_digest(path)
    monkeypatch.setattr(backup_module, 'file_digest', blocked_digest)
    with ThreadPoolExecutor(2) as pool:
        backup = pool.submit(create_backup, store, tmp_path / 'concurrent.zip')
        assert reached.wait(10)
        deletion = pool.submit(store.remove_runs, [other], confirmed=True)
        assert not deletion.done()
        release.set()
        archive = backup.result(timeout=10)
        deletion.result(timeout=10)
    restored = restore_backup(archive, tmp_path / 'concurrent-restored')
    assert restored.artifact_file(saved['id']).read_text() == 'shared'


def test_snapshot_start_is_protected_from_deletion(project, monkeypatch):
    store, sim, root, source = project
    first = finished(store, sim)
    import simshelf.recording as recording
    snapshot = recording.source_snapshot
    reached, release = threading.Event(), threading.Event()
    def blocked_snapshot(*args):
        result = snapshot(*args)
        reached.set()
        assert release.wait(10)
        return result
    monkeypatch.setattr(recording, 'source_snapshot', blocked_snapshot)
    with ThreadPoolExecutor(2) as pool:
        start = pool.submit(finished, store, sim)
        assert reached.wait(10)
        deletion = pool.submit(store.remove_runs, [first], confirmed=True)
        assert not deletion.done()
        release.set()
        second = start.result(timeout=10)
        assert not deletion.result(timeout=10)['cleanup_errors']
    assert store.run(second)['snapshot']['files']
    assert store.reconcile()['errors'] == []


def test_cross_process_lock_and_pending_event_failure(project, tmp_path):
    import os
    import subprocess
    import sys
    from simshelf.workspace_lock import workspace_lock
    store, sim, root, source = project
    ident = finished(store, sim)
    code = 'from simshelf.store import Store; import sys; print("ready", flush=True); Store(sys.argv[1]).remove_runs([sys.argv[2]], confirmed=True); print("done", flush=True)'
    with workspace_lock(store.path):
        process = subprocess.Popen([sys.executable, '-B', '-c', code, str(store.path), ident], stdout=subprocess.PIPE, text=True, env=os.environ.copy())
        try:
            assert process.stdout.readline().strip() == 'ready'
            assert process.poll() is None
            assert store.run(ident)
        finally:
            pass
    stdout, _ = process.communicate(timeout=10)
    assert process.returncode == 0 and stdout.strip() == 'done'
    ident = finished(store, sim)
    pending = store.path / 'journal' / ident / ('9' * 20 + '-' + 'a' * 32 + '.json')
    pending.write_text('{bad json')
    with pytest.raises(ValueError, match='Resolve journal'):
        store.remove_runs([ident], confirmed=True)
    assert store.run(ident)


def test_download_open_before_removal_preserves_ranges_and_bytes(project):
    from simshelf.api import OpenFileResponse
    from starlette.applications import Starlette
    from starlette.routing import Route
    store, sim, root, source = project
    ident = finished(store, sim)
    file = root / 'data.bin'
    file.write_bytes(b'0123456789')
    saved = save_file(store, ident, file)
    stream = store.artifact_file(saved['id']).open('rb')
    response = OpenFileResponse(stream, filename='data.bin', media_type='application/octet-stream')
    store.remove_runs([ident], confirmed=True)
    async def endpoint(request):
        return response
    with TestClient(Starlette(routes=[Route('/', endpoint)])) as client:
        result = client.get('/', headers={'Range': 'bytes=2-5'})
        assert result.status_code == 206
        assert result.content == b'2345'
    assert stream.closed


def test_duplicate_concurrent_removals_and_crash_after_unlink(project, monkeypatch):
    store, sim, root, source = project
    ident = finished(store, sim)
    unlink = removal.unlink_managed
    crashed = False
    def unlink_then_crash(*args):
        nonlocal crashed
        unlink(*args)
        if not crashed:
            crashed = True
            raise SystemExit('crash after unlink before acknowledgement')
    monkeypatch.setattr(removal, 'unlink_managed', unlink_then_crash)
    with pytest.raises(SystemExit):
        store.remove_runs([ident], confirmed=True)
    monkeypatch.setattr(removal, 'unlink_managed', unlink)
    with ThreadPoolExecutor(2) as pool:
        futures = [pool.submit(Store(store.path).remove_runs, [ident], confirmed=True) for _ in range(2)]
        assert all(not f.result(timeout=10)['cleanup_errors'] for f in futures)
    assert Store(store.path).reconcile()['errors'] == []
    with store.connection() as conn:
        assert conn.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()[0] == '2'
        assert conn.execute("SELECT count(*) FROM metadata WHERE key LIKE 'deleted_run:%'").fetchone()[0] == 1


def test_annotation_wait_does_not_block_event_loop(project):
    import asyncio
    import httpx
    from simshelf.workspace_lock import workspace_lock
    store, sim, root, source = project
    ident = finished(store, sim)
    reached, release = threading.Event(), threading.Event()
    def hold():
        with workspace_lock(store.path):
            reached.set()
            assert release.wait(10)
    async def scenario():
        app = create_app(store.path)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://testserver') as client:
            token = (await client.get('/api/workspace')).json()['token']
            thread = threading.Thread(target=hold)
            thread.start()
            assert reached.wait(10)
            patch = asyncio.create_task(client.patch(f'/api/runs/{ident}', headers={'X-SimShelf-Token': token}, json={'notes': 'waited safely'}))
            try:
                await asyncio.sleep(.05)
                response = await asyncio.wait_for(client.get('/api/workspace'), timeout=2)
                assert response.status_code == 200
                assert not patch.done()
            finally:
                release.set()
                thread.join(10)
            assert (await patch).status_code == 200
    asyncio.run(scenario())
