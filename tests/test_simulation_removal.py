import json
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from simshelf.api import create_app
from simshelf.backup import create_backup, restore_backup
from simshelf.capture import save_file
from simshelf.common import json_text
from simshelf.recording import Run
from simshelf.store import Store
from simshelf import removal, simulation_removal as sr
from simshelf import git_archive


def ready(store, version='2'):
    # Disposable fixture setup only; the feature never upgrades a library.
    with store.connection() as conn:
        conn.execute("UPDATE metadata SET value=? WHERE key='schema_version'", (version,))


def finished(store, sim, fail=False):
    run = Run(sim['id'], workspace=store.path, capture_console=False)
    run.__enter__()
    run.finish(status='failed' if fail else 'completed', exit_code=1 if fail else 0)
    return run.id


def confirm(store, sim, review=None, **overrides):
    review = review or sr.preview(store, sim['id'])
    body = dict(typed_name=review['name'], revision=review['revision'], confirmed=True)
    body.update(overrides)
    return sr.remove(store, sim['id'], **body)


def logical(store):
    with store.connection() as conn:
        return {t: [tuple(r) for r in conn.execute(f'SELECT * FROM {t} ORDER BY rowid')]
                for t in ('metadata', 'simulations', 'runs', 'artifacts', 'metrics', 'annotations', 'applied_events')}


@pytest.mark.parametrize('runs', [0, 1])
def test_schema_one_refused_without_changes(project, runs):
    store, sim, root, source = project
    if runs:
        finished(store, sim)
    before = logical(store)
    with pytest.raises(ValueError, match='schema-1'):
        sr.preview(store, sim['id'])
    with pytest.raises(ValueError, match='schema-1'):
        confirm(store, sim, {'name': sim['name'], 'revision': '0'*64})
    assert logical(store) == before


@pytest.mark.parametrize('name', ['', 'field', 'FIELD', ' Field', 'Field ', 'different'])
def test_exact_name_and_confirmation(project, name):
    store, sim, *_ = project
    ready(store)
    review = sr.preview(store, sim['id'])
    before = logical(store)
    with pytest.raises(ValueError):
        confirm(store, sim, review, typed_name=name)
    with pytest.raises(ValueError):
        confirm(store, sim, review, confirmed=False)
    assert logical(store) == before


def test_zero_runs_retry_and_new_registration_identity(project):
    store, sim, root, source = project
    ready(store)
    review = sr.preview(store, sim['id'])
    pending = Run(sim['id'], workspace=store.path, capture_console=False)
    assert confirm(store, sim, review)['cleanup_errors'] == []
    assert confirm(store, sim, review)['already_removed']
    with pytest.raises(ValueError):
        confirm(store, sim, review, typed_name='different')
    new = store.add_simulation(root, name=sim['name'], entrypoint='field.py')
    assert new['id'] != sim['id']
    with pytest.raises(ValueError):
        pending.__enter__()
    assert store.simulation(new['id'])
    assert confirm(store, sim, review)['already_removed']
    assert store.simulation(new['id'])


def test_shared_data_archive_sources_and_backups(project, tmp_path):
    store, sim, root, source = project
    ready(store)
    other_root = tmp_path/'other'; other_root.mkdir()
    (other_root/'field.py').write_bytes(source.read_bytes())
    other = store.add_simulation(other_root, name='Other', entrypoint='field.py')
    a, b, keep = finished(store, sim), finished(store, sim, True), finished(store, other)
    external = root/'results.csv'; external.write_text('x,y\n1,2\n')
    (root/'data.npz').write_bytes(b'original npz')
    (root/'data.wvz').write_bytes(b'original wvz')
    (root/'.git').mkdir(); (root/'.git'/'evidence').write_text('source Git retained')
    original_files = {p.relative_to(root):p.read_bytes() for p in root.rglob('*') if p.is_file()}
    copied = save_file(store, a, external)
    kept = save_file(store, keep, external)
    save_file(store, b, external, policy='reference')
    store.emit(a, 'annotation', {'notes':'remove note'})
    git_archive.put(store, 'event:'+a+':fixture', {'commit':'historical', 'files':[]})
    git_archive.put(store, 'pending:'+a, {'fixture':True})
    git_archive.put(store, 'settings:'+sim['id'], {'fixture':True})
    git_archive.put(store, 'connection', {'path':str(tmp_path/'inaccessible-archive')})
    with store.connection() as conn:
        conn.execute('INSERT INTO metadata VALUES (?,?)', ('git_connection_v1', json_text({'mappings':{sim['id']:{'a':1},other['id']:{'b':2}}})))
        conn.execute('INSERT INTO metadata VALUES (?,?)', ('git_selection_v1:'+sim['id'], '{}'))
    keep_before = store.run(keep)
    old = create_backup(store, tmp_path/'before.zip')
    events = [json.loads(p.read_text()) for p in (store.path/'journal'/a).glob('*.json')]
    review = sr.preview(store, sim['id'])
    assert review['counts']['runs']==2 and review['counts']['references']==1
    assert review['counts']['archive_events']==1 and review['counts']['archive_pending']==1
    result = confirm(store, sim, review)
    assert result['cleanup_errors']==[]
    assert store.run(keep)==keep_before
    assert store.artifact_file(kept['id']).read_bytes()==external.read_bytes()
    assert {p.relative_to(root):p.read_bytes() for p in root.rglob('*') if p.is_file()}==original_files
    assert [s['id'] for s in store.simulations()]==[other['id']]
    for event in events:
        store.apply(event)
    git_archive.put(store, 'error:'+a, 'late optional finalizer')
    with store.connection() as conn:
        assert not conn.execute("SELECT 1 FROM metadata WHERE key LIKE ?", ('archive_v1:%'+a+'%',)).fetchone()
        assert json.loads(conn.execute("SELECT value FROM metadata WHERE key='git_connection_v1'").fetchone()[0])['mappings']=={other['id']:{'b':2}}
        assert conn.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()[0]=='2'
    new = restore_backup(create_backup(store, tmp_path/'after.zip'), tmp_path/'restored')
    assert [s['id'] for s in new.simulations()]==[other['id']]
    assert new.artifact_file(kept['id']).read_bytes()==external.read_bytes()
    assert len(restore_backup(old, tmp_path/'restored-old').simulations())==2


def test_stale_name_new_run_and_annotation_rejected(project):
    store, sim, *_ = project
    ready(store)
    review = sr.preview(store, sim['id'])
    store.update_simulation(sim['id'], name='Field renamed')
    with pytest.raises(ValueError, match='changed'):
        confirm(store, sim, review)
    review = sr.preview(store, sim['id'])
    ident = finished(store, sim)
    with pytest.raises(ValueError, match='changed'):
        confirm(store, sim, review)
    review = sr.preview(store, sim['id'])
    store.emit(ident, 'annotation', {'notes':'new note'})
    with pytest.raises(ValueError, match='changed'):
        confirm(store, sim, review)


def test_active_and_pending_start_race(project, monkeypatch):
    store, sim, *_ = project
    ready(store)
    review = sr.preview(store, sim['id'])
    import simshelf.recording as recording
    original = recording.source_snapshot
    entered, release = threading.Event(), threading.Event()
    def blocked(*args):
        value = original(*args); entered.set(); assert release.wait(10); return value
    monkeypatch.setattr(recording, 'source_snapshot', blocked)
    active = Run(sim['id'], workspace=store.path, capture_console=False)
    with ThreadPoolExecutor(2) as pool:
        start = pool.submit(active.__enter__)
        assert entered.wait(10)
        delete = pool.submit(confirm, store, sim, review)
        assert not delete.done()
        release.set(); start.result(timeout=10)
        with pytest.raises(ValueError): delete.result(timeout=10)
    assert sr.preview(store, sim['id'])['active']
    with pytest.raises(ValueError, match='Running'):
        confirm(store, sim)
    active.finish()
    # Completion can precede automatic capture finalization.
    with store.connection() as conn:
        run = json.loads(conn.execute('SELECT data FROM runs WHERE id=?', (active.id,)).fetchone()[0])
        run['capture_status'] = 'pending'
        conn.execute('UPDATE runs SET data=? WHERE id=?', (json_text(run), active.id))
    assert sr.preview(store, sim['id'])['active']
    with pytest.raises(ValueError, match='finalizing'):
        confirm(store, sim)
    assert store.simulation(sim['id'])


def test_rollback_and_cleanup_retry(project, monkeypatch):
    store, sim, *_ = project
    ready(store)
    finished(store, sim)
    review = sr.preview(store, sim['id'])
    records = removal.remove_records
    def failed(*args):
        records(*args)
        raise sqlite3.OperationalError('injected')
    monkeypatch.setattr(removal, 'remove_records', failed)
    before = logical(store)
    with pytest.raises(sqlite3.OperationalError): confirm(store, sim, review)
    assert logical(store)==before
    monkeypatch.setattr(removal, 'remove_records', records)
    unlink = removal.unlink_managed
    monkeypatch.setattr(removal, 'unlink_managed', lambda *_: (_ for _ in ()).throw(PermissionError('injected')))
    assert confirm(store, sim, review)['cleanup_errors']
    assert confirm(store, sim, review)['cleanup_errors']
    monkeypatch.setattr(removal, 'unlink_managed', unlink)
    assert confirm(store, sim, review)['cleanup_errors']==[]
    assert Store(store.path).reconcile()['errors']==[]


def test_api_authorization_validation_and_stale_target(project):
    store, sim, *_ = project
    ready(store)
    with TestClient(create_app(store.path)) as client:
        headers={'X-SimShelf-Token':client.get('/api/workspace').json()['token']}
        review=client.get(f"/api/simulations/{sim['id']}/removal-preview").json()
        url=f"/api/simulations/{sim['id']}/remove"
        body={'typed_name':sim['name'], 'revision':review['revision'], 'confirmed':True}
        assert client.post(url,json=body).status_code==403
        assert client.post(url,json=body,headers={**headers,'Origin':'https://outside.example'}).status_code==403
        for invalid in ({**body,'confirmed':'true'}, {**body,'extra':1}, {**body,'typed_name':42}):
            assert client.post(url,json=invalid,headers=headers).status_code==422
        assert client.post(url,json={**body,'typed_name':' Field'},headers=headers).status_code==400
        assert client.post(url,json=body,headers=headers).status_code==200
        assert client.post(url,json=body,headers=headers).json()['already_removed']
        assert client.get('/api/simulations').json()==[]


@pytest.mark.parametrize('version', ['2','3','4'])
def test_existing_schema_retained_and_progress_removed(project, version):
    store, sim, *_ = project
    ready(store, version)
    if version=='4':
        with store.connection() as conn:
            conn.execute('CREATE TABLE progress (run_id TEXT PRIMARY KEY, sequence INTEGER NOT NULL, data TEXT NOT NULL)')
    ident = finished(store, sim)
    if version=='4':
        with store.connection() as conn:
            conn.execute('INSERT INTO progress VALUES (?,?,?)', (ident, 1, json_text({'step':1})))
    confirm(store, sim)
    with store.connection() as conn:
        assert conn.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()[0]==version
        if version=='4': assert conn.execute('SELECT count(*) FROM progress').fetchone()[0]==0


def test_actual_shared_git_archive_is_untouched(project, tmp_path):
    from simshelf.git_selection import inventory, selection_preview, save_selection
    store, sim, root, source = project
    ready(store)
    repo=tmp_path/'archive';repo.mkdir()
    git_archive.connect(store,str(repo),True,True)
    git_archive.set_global_enabled(store, True)
    inv=inventory(store,sim['id'])
    save_selection(store,sim['id'],selection_preview(store,sim['id'],inv['revision'],[{'kind':'file','value':'field.py'}]))
    git_archive.enable(store,sim['id'],git_archive.settings_preview(store,sim['id'],[]),True)
    ident=finished(store,sim)
    assert git_archive.entries(store,ident)
    before={p.relative_to(repo):p.read_bytes() for p in repo.rglob('*') if p.is_file()}
    confirm(store,sim)
    assert {p.relative_to(repo):p.read_bytes() for p in repo.rglob('*') if p.is_file()}==before
    assert source.exists()


def test_large_simulation_is_one_transaction(project):
    import uuid
    store, sim, *_ = project
    ready(store)
    original=store.run(finished(store,sim),False)
    with store.connection() as conn:
        for _ in range(1000):
            run={**original,'id':uuid.uuid4().hex}
            conn.execute('INSERT INTO runs VALUES (?,?,?,?,?,?)',(run['id'],sim['id'],run['status'],run['started_at'],run['version'],json_text(run)))
    review=sr.preview(store,sim['id'])
    assert review['counts']['runs']==1001
    assert confirm(store,sim,review)['cleanup_errors']==[]
    assert store.runs()==[]


def test_new_unregistered_start_is_refused(project):
    store, sim, *_ = project
    ready(store)
    ident=finished(store,sim)
    event=json.loads(next(p for p in (store.path/'journal'/ident).glob('*.json') if json.loads(p.read_text())['kind']=='start').read_text())
    confirm(store,sim)
    event['id']='new-event';event['run_id']='a'*32;event['data']['id']='a'*32
    with pytest.raises(ValueError,match='removed'):
        store.apply(event)
    assert store.runs()==[]


def test_removed_baseline_is_in_preview_and_atomic_crash_recovery(project, monkeypatch):
    store, sim, root, source = project
    ready(store)
    first=finished(store,sim)
    source.write_text(source.read_text()+'value = 3\n')
    finished(store,sim)
    store.remove_runs([first],confirmed=True)
    review=sr.preview(store,sim['id'])
    assert review['counts']['snapshots']==2
    cleanup=removal.cleanup_removed
    # First reconcile cleanup runs before the transaction; crash only after commit.
    def crash(s):
        with s.connection() as conn:
            if conn.execute('SELECT 1 FROM metadata WHERE key=?',(sr.AUDIT+sim['id'],)).fetchone():
                raise SystemExit('crash after commit')
        return cleanup(s)
    monkeypatch.setattr(removal,'cleanup_removed',crash)
    with pytest.raises(SystemExit):confirm(store,sim,review)
    monkeypatch.setattr(removal,'cleanup_removed',cleanup)
    assert Store(store.path).reconcile()['errors']==[]
    assert store.simulations()==[] and store.runs()==[]
    assert not list((store.path/'snapshots').glob('*.json'))
    assert confirm(store,sim,review)['already_removed']
