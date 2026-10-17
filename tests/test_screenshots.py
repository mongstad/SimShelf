import json
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient

from simshelf.api import create_app
from simshelf.backup import create_backup, restore_backup
from simshelf.capture import save_file
from simshelf.recording import Run
from simshelf.source import blob_path
from simshelf.store import Store
from simshelf.screenshots import delete_screenshot
from simshelf import screenshots, removal


def finished(store, sim):
    with Run(sim['id'], workspace=store.path, capture_console=False) as run:
        pass
    return run.id


def attach(store, ident, root, name='manual.png', content=b'manual screenshot', **kwargs):
    file = root / name
    file.write_bytes(content)
    return save_file(store, ident, file, **kwargs)


def raw_run(store, ident):
    with store.connection() as conn:
        return conn.execute('SELECT data FROM runs WHERE id=?', (ident,)).fetchone()[0]


def test_exact_deletion_history_replay_cover_and_backup(project, tmp_path):
    store, sim, root, source = project
    ident = finished(store, sim)
    first = attach(store, ident, root)
    second = attach(store, ident, root, 'kept.png', b'keep me')
    store.emit(ident, 'annotation', {'cover_id': first['id'], 'notes': 'scientific context'})
    store.emit(ident, 'artifact_annotation', {'id': first['id'], 'caption': 'original caption'})
    before = store.run(ident)
    raw = raw_run(store, ident)
    journals = {p: p.read_bytes() for p in (store.path / 'journal' / ident).glob('*.json')}
    old = create_backup(store, tmp_path / 'before.zip')
    result = delete_screenshot(store, ident, first['id'], confirmed=True)
    assert result == {'deleted_id': first['id'], 'already_deleted': False, 'cleanup_errors': []}
    assert raw_run(store, ident) == raw
    assert source.exists() and (root / 'manual.png').read_bytes() == b'manual screenshot'
    assert not blob_path(store.path, first['blob']).exists()
    assert store.artifact_file(second['id']).read_bytes() == b'keep me'
    assert all(p.read_bytes() == data for p, data in journals.items())
    after = store.run(ident)
    assert after['snapshot'] == before['snapshot'] and after['metrics'] == before['metrics']
    assert len(after['annotation_history']) == len(before['annotation_history']) + 1
    assert after['annotation_history'][0]['kind'] == 'screenshot_deleted'
    store.emit(ident, 'annotation', {'notes': 'later note'})
    assert store.run(ident)['annotation_history'][0]['notes'] == 'later note'
    with store.connection() as conn:
        assert conn.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()[0] == '3'
        conn.execute('DELETE FROM applied_events')
    assert store.reconcile()['errors'] == []
    assert [a['id'] for a in store.run(ident)['artifacts']] == [second['id']]
    assert delete_screenshot(store, ident, first['id'], confirmed=True)['already_deleted']
    with TestClient(create_app(store.path)) as client:
        listed = client.get('/api/runs').json()[0]
        assert listed['image_count'] == 1 and listed['cover_id'] == second['id']
    restored = restore_backup(create_backup(store, tmp_path / 'after.zip'), tmp_path / 'restored')
    assert restored.reconcile()['errors'] == []
    assert [a['id'] for a in restored.run(ident)['artifacts']] == [second['id']]
    assert delete_screenshot(restored, ident, first['id'], confirmed=True)['already_deleted']
    original = restore_backup(old, tmp_path / 'old')
    assert original.artifact_file(first['id']).read_bytes() == b'manual screenshot'
    # Subsequent whole-run removal must not downgrade the screenshot replay guard.
    restored.remove_runs([ident], confirmed=True)
    with restored.connection() as conn:
        assert conn.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()[0] == '3'


def test_shared_source_and_automatic_content_is_retained(project):
    store, sim, root, source = project
    ident, other = finished(store, sim), finished(store, sim)
    first = attach(store, ident, root)
    shared = attach(store, other, root, 'shared.png')
    source_image = attach(store, ident, root, 'source.png', source.read_bytes())
    captured = attach(store, ident, root, 'capture.png', b'captured result', automatic=True)
    duplicate_capture = attach(store, ident, root, 'manual-capture.png', b'captured result')
    for image in (first, source_image, duplicate_capture):
        assert not delete_screenshot(store, ident, image['id'], confirmed=True)['cleanup_errors']
        assert blob_path(store.path, image['blob']).exists()
    assert store.artifact_file(shared['id']).exists()
    assert store.artifact_file(captured['id']).read_bytes() == b'captured result'
    with pytest.raises(ValueError, match='Captured outputs'):
        delete_screenshot(store, ident, captured['id'], confirmed=True)


def test_ineligible_unknown_external_cross_run_and_workspace(project, tmp_path):
    store, sim, root, source = project
    ident, other = finished(store, sim), finished(store, sim)
    image = attach(store, ident, root)
    external = attach(store, ident, root, 'external.png', policy='reference')
    text = attach(store, ident, root, 'data.txt')
    unknown = attach(store, ident, root, 'old.png')
    with store.connection() as conn:
        data = dict(unknown); data.pop('automatic')
        conn.execute('UPDATE artifacts SET data=? WHERE id=?', (json.dumps(data), unknown['id']))
    for item, reason in ((external, 'External'), (text, 'Only PNG'), (unknown, 'unknown ownership')):
        with pytest.raises(ValueError, match=reason):
            delete_screenshot(store, ident, item['id'], confirmed=True)
    with pytest.raises(ValueError, match='Confirm'):
        delete_screenshot(store, ident, image['id'])
    for run_id, artifact_id in ((other, image['id']), (ident, '0' * 32), ('../outside', image['id']), (ident, '../../x')):
        with pytest.raises(ValueError):
            delete_screenshot(store, run_id, artifact_id, confirmed=True)
    with pytest.raises(ValueError, match='Run not found'):
        delete_screenshot(Store(tmp_path / 'different-workspace'), ident, image['id'], confirmed=True)
    assert (root / 'external.png').exists() and store.artifact(image['id'])
    with store.connection() as conn:
        assert conn.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()[0] == '1'


@pytest.mark.parametrize('status,capture,allowed', [('running', 'pending', False), ('completed', 'pending', False), ('completed', 'complete', True), ('failed', 'partial', True), ('interrupted', 'incomplete', True)])
def test_status_boundaries(project, status, capture, allowed):
    store, sim, root, source = project
    ident = finished(store, sim)
    image = attach(store, ident, root)
    with store.connection() as conn:
        data = json.loads(raw_run(store, ident)); data.update(status=status, capture_status=capture)
        conn.execute('UPDATE runs SET data=?,status=? WHERE id=?', (json.dumps(data), status, ident))
    if allowed:
        delete_screenshot(store, ident, image['id'], confirmed=True)
    else:
        with pytest.raises(ValueError, match='Wait until'):
            delete_screenshot(store, ident, image['id'], confirmed=True)
        assert store.artifact(image['id'])


def test_missing_file_and_concurrent_duplicates(project):
    store, sim, root, source = project
    ident = finished(store, sim)
    image = attach(store, ident, root)
    blob_path(store.path, image['blob']).unlink()
    with ThreadPoolExecutor(2) as pool:
        results = list(pool.map(lambda _: delete_screenshot(Store(store.path), ident, image['id'], confirmed=True), range(2)))
    assert sorted(r['already_deleted'] for r in results) == [False, True]
    assert all(not r['cleanup_errors'] for r in results)
    assert len([a for a in store.run(ident)['annotation_history'] if a.get('kind') == 'screenshot_deleted']) == 1


@pytest.mark.parametrize('parent', [False, True])
def test_symlink_cleanup_is_safe(project, tmp_path, parent):
    store, sim, root, source = project
    ident = finished(store, sim)
    image = attach(store, ident, root)
    path = blob_path(store.path, image['blob'])
    outside = tmp_path / 'outside'; outside.mkdir()
    target = outside / path.name; target.write_bytes(b'valuable external image')
    path.unlink()
    if parent:
        path.parent.rename(path.parent.with_name(path.parent.name + '-saved'))
        path.parent.symlink_to(outside, target_is_directory=True)
    else:
        path.symlink_to(target)
    result = delete_screenshot(store, ident, image['id'], confirmed=True)
    assert result['cleanup_errors']
    assert target.read_bytes() == b'valuable external image'
    assert store.run(ident)['artifacts'] == []


def test_read_only_database_rolls_back(project, monkeypatch):
    store, sim, root, source = project
    ident = finished(store, sim)
    image = attach(store, ident, root)
    original = store.connection
    @contextmanager
    def readonly():
        conn = sqlite3.connect(f'file:{store.db}?mode=ro', uri=True)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()
    monkeypatch.setattr(store, 'connection', readonly)
    with pytest.raises(sqlite3.OperationalError, match='readonly'):
        delete_screenshot(store, ident, image['id'], confirmed=True)
    monkeypatch.setattr(store, 'connection', original)
    assert store.artifact_file(image['id']).exists()
    assert not any(a.get('kind') == 'screenshot_deleted' for a in store.run(ident)['annotation_history'])


def test_cleanup_failure_and_crash_recovery(project, monkeypatch):
    store, sim, root, source = project
    ident = finished(store, sim)
    first = attach(store, ident, root)
    cleanup = screenshots.cleanup_removed
    monkeypatch.setattr(screenshots, 'cleanup_removed', lambda *_: (_ for _ in ()).throw(PermissionError('injected permission failure')))
    assert delete_screenshot(store, ident, first['id'], confirmed=True)['cleanup_errors']
    assert blob_path(store.path, first['blob']).exists()
    monkeypatch.setattr(screenshots, 'cleanup_removed', cleanup)
    assert store.reconcile()['errors'] == []
    assert not blob_path(store.path, first['blob']).exists()
    second = attach(store, ident, root, 'second.png', b'second')
    unlink = removal.unlink_managed
    def crash(*args):
        unlink(*args)
        raise SystemExit('crash after unlink before acknowledgement')
    monkeypatch.setattr(removal, 'unlink_managed', crash)
    with pytest.raises(SystemExit):
        delete_screenshot(store, ident, second['id'], confirmed=True)
    monkeypatch.setattr(removal, 'unlink_managed', unlink)
    assert Store(store.path).reconcile()['errors'] == []
    assert store.run(ident)['artifacts'] == []


def test_api_authorization_and_permission_feedback(project, monkeypatch):
    store, sim, root, source = project
    ident, other = finished(store, sim), finished(store, sim)
    image = attach(store, ident, root)
    with TestClient(create_app(store.path)) as client:
        headers = {'X-SimShelf-Token': client.get('/api/workspace').json()['token']}
        url = f'/api/runs/{ident}/screenshots/{image["id"]}/delete'
        assert client.post(url, json={'confirmed': True}).status_code == 403
        assert client.post(url, json={'confirmed': True}, headers={**headers, 'Origin': 'https://outside.example'}).status_code == 403
        assert client.post(url, json={'confirmed': False}, headers=headers).status_code == 400
        assert client.post(url, json={'confirmed': True, 'path': str(source)}, headers=headers).status_code == 422
        assert client.post(url.replace(ident, other), json={'confirmed': True}, headers=headers).status_code == 400
        import simshelf.api as api_module
        with monkeypatch.context() as patch:
            patch.setattr(api_module, 'delete_screenshot', lambda *args, **kwargs: (_ for _ in ()).throw(sqlite3.OperationalError('readonly')))
            response = client.post(url, json={'confirmed': True}, headers=headers)
            assert response.status_code == 409 and 'permissions' in response.json()['detail']
        assert client.post(url, json={'confirmed': True}, headers=headers).status_code == 200
        assert client.post(url, json={'confirmed': True}, headers=headers).json()['already_deleted']
        assert client.patch(f'/api/runs/{ident}', headers=headers, json={'cover_id': image['id']}).status_code == 400
        assert client.patch(f'/api/artifacts/{image["id"]}', headers=headers, json={'caption': 'late'}).status_code == 400
        assert client.get(f'/api/artifacts/{image["id"]}/file').status_code == 400


def test_attachment_and_backup_serialize_with_deletion(project, tmp_path, monkeypatch):
    store, sim, root, source = project
    ident, other = finished(store, sim), finished(store, sim)
    image = attach(store, ident, root)
    reached, release = threading.Event(), threading.Event()
    emit = store.emit
    def paused_emit(*args, **kwargs):
        reached.set(); assert release.wait(10)
        return emit(*args, **kwargs)
    monkeypatch.setattr(store, 'emit', paused_emit)
    with ThreadPoolExecutor(2) as pool:
        upload = pool.submit(save_file, store, other, root / 'manual.png')
        assert reached.wait(10)
        deletion = pool.submit(delete_screenshot, store, ident, image['id'], confirmed=True)
        assert not deletion.done()
        release.set()
        shared = upload.result(timeout=10)
        assert not deletion.result(timeout=10)['cleanup_errors']
    assert store.artifact_file(shared['id']).exists()
    monkeypatch.setattr(store, 'emit', emit)
    import simshelf.backup as backup_module
    digest = backup_module.file_digest
    reached.clear(); release.clear()
    def paused_digest(path):
        reached.set(); assert release.wait(10)
        return digest(path)
    monkeypatch.setattr(backup_module, 'file_digest', paused_digest)
    with ThreadPoolExecutor(2) as pool:
        backup = pool.submit(create_backup, store, tmp_path / 'concurrent.zip')
        assert reached.wait(10)
        deletion = pool.submit(delete_screenshot, store, other, shared['id'], confirmed=True)
        assert not deletion.done()
        release.set()
        archive = backup.result(timeout=10)
        assert not deletion.result(timeout=10)['cleanup_errors']
    restored = restore_backup(archive, tmp_path / 'restored')
    assert restored.artifact_file(shared['id']).exists()


def test_invalid_blob_and_pending_journal_fail_closed(project):
    store, sim, root, source = project
    ident = finished(store, sim)
    image = attach(store, ident, root)
    with store.connection() as conn:
        conn.execute('UPDATE artifacts SET data=? WHERE id=?', (json.dumps({**image, 'blob': '../../outside'}), image['id']))
    with pytest.raises(ValueError, match='valid managed'):
        delete_screenshot(store, ident, image['id'], confirmed=True)
    with store.connection() as conn:
        conn.execute('UPDATE artifacts SET data=? WHERE id=?', (json.dumps(image), image['id']))
        assert conn.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()[0] == '1'
    pending = store.path / 'journal' / ident / ('9' * 20 + '-' + 'a' * 32 + '.json')
    pending.write_text('{invalid journal')
    with pytest.raises(ValueError, match='Resolve journal'):
        delete_screenshot(store, ident, image['id'], confirmed=True)
    assert store.artifact_file(image['id']).exists() and source.exists()


def test_schema_two_opens_without_migration_and_upgrades_only_on_deletion(project, tmp_path):
    store, sim, root, source = project
    old = finished(store, sim)
    store.remove_runs([old], confirmed=True)
    store = Store(store.path)
    ident = finished(store, sim)
    image = attach(store, ident, root)
    backup = create_backup(store, tmp_path / 'schema-two.zip')
    restored = restore_backup(backup, tmp_path / 'schema-two-restored')
    with restored.connection() as conn:
        assert conn.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()[0] == '2'
    assert delete_screenshot(restored, ident, image['id'], confirmed=True)['cleanup_errors'] == []
    with restored.connection() as conn:
        assert conn.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()[0] == '3'


def test_workspace_reports_live_schema_for_confirmation(project):
    store, sim, root, source = project
    removed = finished(store, sim)
    ident = finished(store, sim)
    image = attach(store, ident, root)
    with TestClient(create_app(store.path)) as client:
        assert client.get('/api/workspace').json()['schema_version'] == 1
        store.remove_runs([removed], confirmed=True)
        assert client.get('/api/workspace').json()['schema_version'] == 2
        info = client.get('/api/workspace').json()
        assert info['schema_version'] == 2  # Reading never upgrades the library.
        response = client.post(f'/api/runs/{ident}/screenshots/{image["id"]}/delete',
            json={'confirmed': True}, headers={'X-SimShelf-Token': info['token']})
        assert response.status_code == 200
        assert client.get('/api/workspace').json()['schema_version'] == 3
