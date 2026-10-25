"""Annotation writes are independent of recorder ownership and execution events."""
import concurrent.futures
import sys
import time

from fastapi.testclient import TestClient
import pytest

from simshelf.api import create_app
from simshelf.progress import enable_progress
from simshelf.store import Store

pytestmark = pytest.mark.skipif(not sys.platform.startswith('linux'), reason='Portal recording requires Linux')


def token(client):
    return {'X-SimShelf-Token': client.get('/api/workspace').json()['token']}


def test_active_annotations_owned_nonowned_and_completed(project):
    store, sim, root, source = project
    enable_progress(store, confirmed=True)
    source.write_text('''import time
from pathlib import Path
SIMSHELF_VERSION = "1.0"
for i in range(600):
    print(f"{i / 6:.1f}%", flush=True)
    if Path("finish").exists(): break
    time.sleep(.05)
Path("outputs").mkdir(exist_ok=True)
Path("outputs/result.txt").write_text("preserved output")
''')
    original = source.read_bytes()
    owner_app = create_app(store.path)
    with TestClient(owner_app) as owner, TestClient(create_app(store.path)) as observer:
        auth, other = token(owner), token(observer)
        response = owner.post(f"/api/simulations/{sim['id']}/launch", headers=auth, json={
            'interpreter': sys.executable, 'cwd': '.', 'arguments': [],
            'output_dir': 'outputs', 'progress_mode': 'percent'})
        assert response.status_code == 201, response.text
        ident = response.json()['run_id']
        path = f'/api/runs/{ident}'
        assert owner.get(path).json()['can_stop']
        assert not observer.get(path).json()['can_stop']
        previous_name = store.run(ident)['name']
        for client, headers, owned in ((owner, auth, True), (observer, other, False)):
            for tags in (['control', 'favorite'], ['control'], ['control', 'favorite']):
                name = f"{'Owner' if owned else 'Observer'} edit {len(store.run(ident)['annotation_history'])}"
                saved = client.patch(path, headers=headers, json={'name': name, 'tags': tags, 'notes': 'Keep these notes'})
                assert saved.status_code == 200, saved.text
                data = saved.json()
                assert data['status'] == 'running'
                assert data['tags'] == tags
                assert data.get('can_stop') is owned
                assert data.get('stop_requested') is False
                store.reconcile()
                fresh = Store(store.path).run(ident)
                assert fresh['tags'] == tags
                assert fresh['notes'] == 'Keep these notes'
                assert fresh['name'] == name
                assert fresh['annotation_history'][0]['tags'] == tags
                assert fresh['annotation_history'][0]['previous_name'] == previous_name
                previous_name = name
        before = store.run(ident)
        # A token from another server instance models an old browser after restart.
        rejected = observer.patch(path, headers=auth, json={'name': 'Rejected stale name', 'tags': []})
        assert rejected.status_code == 403
        assert rejected.json()['detail'] == 'Refresh SimShelf before saving.'
        assert observer.patch(path, headers={**other, 'Origin': 'https://elsewhere.example'}, json={'tags': []}).status_code == 403
        assert observer.patch(path, headers=other, json={'tags': ['']}).status_code == 400
        assert store.run(ident)['annotation_history'] == before['annotation_history']
        assert store.run(ident)['tags'] == before['tags']
        assert store.run(ident)['name'] == before['name']
        # Refresh obtains the new instance token; finalization/recovery overlap edits.
        with concurrent.futures.ThreadPoolExecutor() as pool:
            pending = pool.submit(observer.patch, path, headers=token(observer), json={'name': 'Finalization edit', 'tags': ['control', 'favorite']})
            (root / 'finish').touch()
            assert pending.result(timeout=10).status_code == 200
        deadline = time.monotonic() + 15
        while store.run(ident)['status'] == 'running' and time.monotonic() < deadline:
            time.sleep(.05)
        store.reconcile()
        final = observer.get(path).json()
        assert final['status'] == 'completed', final
        assert final['tags'] == ['control', 'favorite']
        assert final['notes'] == 'Keep these notes'
        assert final['name'] == 'Finalization edit'
        assert final['progress'] is not None
        assert owner.get(path + '/logs').json()['text']
        assert (root / 'outputs/result.txt').read_text() == 'preserved output'
        assert source.read_bytes() == original
        for tags in (['control'], ['control', 'favorite']):
            assert observer.patch(path, headers=other, json={'tags': tags}).status_code == 200
            assert observer.get(path).json()['tags'] == tags


def test_interrupted_recovery_preserves_confirmed_annotations(project, monkeypatch):
    from simshelf.recording import Run
    store, sim, root, source = project
    with Run(sim['id'], workspace=store.path, capture_console=False) as recorder:
        store.emit(recorder.id, 'annotation', {'name': 'Recovery name', 'tags': ['favorite', 'control'], 'notes': 'keep'})
        before = store.run(recorder.id)
        monkeypatch.setattr('simshelf.store.process_alive', lambda *_: False)
        assert not store.reconcile()['errors']
        recovered = store.run(recorder.id)
        assert recovered['status'] == 'interrupted'
        assert recovered['tags'] == before['tags']
        assert recovered['notes'] == before['notes']
        assert recovered['name'] == before['name'] == 'Recovery name'
        assert recovered['annotation_history'] == before['annotation_history']
        assert recovered['snapshot_id'] == before['snapshot_id']
    assert store.run(recorder.id)['tags'] == ['favorite', 'control']
