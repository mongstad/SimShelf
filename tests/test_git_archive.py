import json
import os
import uuid
from pathlib import Path

import pytest
from simshelf import git_archive as archive
from simshelf.store import Store
from simshelf.recording import Run, record_command
from simshelf.capture import save_file
from simshelf.git_selection import inventory, selection_preview, save_selection
from simshelf.backup import create_backup, restore_backup


@pytest.fixture
def setup(tmp_path):
    store = Store(tmp_path / 'library')
    repo = tmp_path / 'archive'; repo.mkdir()
    archive.connect(store, str(repo), True, True)
    sims = []
    for name in ('alpha', 'beta'):
        root = tmp_path / name; root.mkdir()
        (root / 'sim.py').write_text('SIMSHELF_VERSION = "1"\n')
        (root / 'outputs').mkdir()
        sim = store.add_simulation(root, name=name, entrypoint='sim.py')
        inv = inventory(store, sim['id'])
        save_selection(store, sim['id'], selection_preview(store, sim['id'], inv['revision'], [{'kind':'file','value':'sim.py'}]))
        review = archive.settings_preview(store, sim['id'], ['result.csv','logs/*.csv'])
        archive.enable(store, sim['id'], review, True)
        sims.append(sim)
    return store, repo, sims


def run_output(store, sim, text='one', fail=False):
    r = Run(sim['id'], workspace=store.path, capture_console=False)
    r.__enter__()
    (Path(sim['root']) / 'outputs/result.csv').write_text(text)
    r.finish(1 if fail else 0)
    return r.id


def test_shared_history_original_source_failure_and_overwritten_outputs(setup):
    store, repo, (a,b) = setup
    first = run_output(store,a)
    middle = run_output(store,b,'beta')
    last = run_output(store,a,'second',True)
    commits=[]
    for ident, expected in ((first,b'one'),(middle,b'beta'),(last,b'second')):
        v=archive.view(store,ident)
        assert not v['error'], v
        e,=v['events']; commits.append(e['commit'])
        assert e['simulation']==store.run(ident)['simulation_id']
        i=next(i for i,f in enumerate(e['files']) if f['category']=='result')
        assert archive.download(store,ident,e['id'],i)[1]==expected
    assert len(set(commits))==3
    assert store.run(last)['status']=='failed'
    r=Run(a['id'],workspace=store.path,capture_console=False);r.__enter__()
    (Path(a['root'])/'sim.py').write_text('# modified live source\n')
    r.finish()
    e,=archive.entries(store,r.id)
    assert archive.download(store,r.id,e['id'],0)[1]==b'SIMSHELF_VERSION = "1"\n'
    assert any(s['reason'].startswith('Unchanged') for s in e['skipped'])


def test_additions_revisions_idempotency_and_scientific_records_unchanged(setup,tmp_path):
    store,repo,(a,b)=setup
    ident=run_output(store,a)
    before=store.run(ident,False)
    source=tmp_path/'analysis.csv';source.write_bytes(b'analysis one')
    attachment=save_file(store,ident,source)
    review=archive.additions_preview(store,ident,[attachment['id']])
    op=uuid.uuid4().hex
    with pytest.raises(ValueError):archive.additions(store,ident,review,op,False)
    event=archive.additions(store,ident,review,op,True)
    assert archive.additions(store,ident,review,op,True)==event
    source.write_bytes(b'analysis two')
    other=save_file(store,ident,source)
    second=archive.additions(store,ident,archive.additions_preview(store,ident,[other['id']]),uuid.uuid4().hex,True)
    assert archive.download(store,ident,event['id'],0)[1]==b'analysis one'
    assert archive.download(store,ident,second['id'],0)[1]==b'analysis two'
    assert store.run(ident,False)==before
    assert len(archive.entries(store,ident))==3
    other_run=run_output(store,b)
    with pytest.raises(ValueError):archive.download(store,other_run,event['id'],0)
    with pytest.raises(ValueError):archive.additions_preview(store,other_run,[other['id']])


def test_future_first_run_missing_outside_and_limits(setup,monkeypatch):
    store,repo,(a,b)=setup
    r=Run(a['id'],workspace=store.path,capture_console=False);r.__enter__()
    root=Path(a['root'])
    (root/'outside.csv').write_text('not eligible')
    (root/'outputs/logs').mkdir();(root/'outputs/logs/first.csv').write_text('eligible')
    r.finish()
    event,=archive.entries(store,r.id)
    assert {f['name'] for f in event['files']}=={'sim.py','logs/first.csv'}
    assert any(f['name']=='result.csv' and f['reason'].startswith('Missing') for f in event['skipped'])
    for bad in ('../result.csv','/tmp/x.csv','**/*.csv','logs/../x','*/x','x?',''):
        with pytest.raises(ValueError):archive.future_rules([bad])
    monkeypatch.setattr(archive,'RUN_LIMIT',1)
    with pytest.raises(ValueError):archive.budget(store,r.id,[])


def test_pending_crash_recovery_after_commit(setup,monkeypatch):
    store,repo,(a,b)=setup
    original=archive.git
    def crash(root,*args,**kw):
        if args[0]=='show':raise ValueError('injected crash after ref publication')
        return original(root,*args,**kw)
    monkeypatch.setattr(archive,'git',crash)
    ident=run_output(store,a)
    assert store.run(ident)['status']=='completed'
    assert archive.view(store,ident)['pending'] and not archive.entries(store,ident)
    head=original(repo,'rev-parse','refs/heads/main')
    monkeypatch.setattr(archive,'git',original)
    archive.publish(store,ident)
    assert archive.git(repo,'rev-parse','refs/heads/main')==head
    assert len(archive.entries(store,ident))==1
    archive.publish(store,ident)
    assert len(archive.entries(store,ident))==1


def test_restore_requires_remap_and_preserves_associations(setup,tmp_path):
    store,repo,(a,b)=setup
    ident=run_output(store,a)
    e,=archive.entries(store,ident)
    backup=create_backup(store,tmp_path/'backup.zip')
    restored=restore_backup(backup,tmp_path/'restored')
    assert archive.entries(restored,ident)==[e]
    with pytest.raises(ValueError):archive.download(restored,ident,e['id'],0)
    archive.disconnect(restored)
    archive.connect(restored,str(repo),False,True)
    assert archive.download(restored,ident,e['id'],0)[1]
    assert store.run(ident,False)==restored.run(ident,False)


def test_optout_unsafe_config_and_missing_git_do_not_fail_recording(setup,monkeypatch):
    store,repo,(a,b)=setup
    archive.put(store,'settings:'+a['id'],None)
    ident=run_output(store,a)
    assert not archive.entries(store,ident)
    (repo/'config').write_bytes(archive.CONFIG+b'[core]\n hooksPath = /tmp/evil\n')
    ident=run_output(store,b)
    assert store.run(ident)['status']=='completed'
    assert archive.view(store,ident)['error']
    (repo/'config').write_bytes(archive.CONFIG)
    monkeypatch.setenv('PATH','/nonexistent')
    ident=run_output(store,b,'third')
    assert store.run(ident)['status']=='completed'
    assert archive.view(store,ident)['pending']


def test_consent_stale_paths_and_links(setup,tmp_path):
    store,repo,(a,b)=setup
    with pytest.raises(ValueError):archive.connect(store,a['root'],False,True)
    with pytest.raises(ValueError):archive.connect(store,str(store.path),True,True)
    link=tmp_path/'link';link.symlink_to(repo,target_is_directory=True)
    with pytest.raises((ValueError,OSError)):archive.connect(store,str(link),False,True)
    preview=archive.settings_preview(store,a['id'],[])
    (Path(a['root'])/'new.py').write_text('x')
    with pytest.raises(ValueError):archive.enable(store,a['id'],preview,True)
    with pytest.raises(ValueError):archive.enable(store,b['id'],preview,True)


def test_api_token_confirmation_download_and_attachment_flow(setup):
    from fastapi.testclient import TestClient
    from simshelf.api import create_app
    store,repo,(a,b)=setup
    ident=run_output(store,a)
    client=TestClient(create_app(store.path))
    headers={'X-SimShelf-Token':client.get('/api/workspace').json()['token']}
    assert client.post('/api/workspace/archive/disconnect').status_code==403
    uploaded=client.post(f'/api/runs/{ident}/attachments',headers=headers,files={'file':('analysis.csv',b'new analysis')}).json()
    review=client.post(f'/api/runs/{ident}/archive/preview',headers=headers,json={'artifact_ids':[uploaded['id']]}).json()
    op=uuid.uuid4().hex
    body={'review':review,'operation':op}
    assert client.post(f'/api/runs/{ident}/archive/add',headers=headers,json=body).status_code==400
    result=client.post(f'/api/runs/{ident}/archive/add',headers=headers,json={**body,'confirmed':True})
    assert result.status_code==200,result.text
    e=result.json()
    response=client.get(f'/api/runs/{ident}/archive/{e["id"]}/0/file')
    assert response.content==b'new analysis'
    assert response.headers['content-disposition'].startswith('attachment;')
    assert client.get(f'/api/runs/{ident}/archive/{e["id"]}/99/file').status_code==400
    assert client.post(f'/api/runs/{ident}/archive/add',headers=headers,json={**body,'confirmed':True}).json()==e


def test_overlap_and_archive_lock_contention(setup):
    store,repo,(a,b)=setup
    r=Run(a['id'],workspace=store.path,capture_console=False);r.__enter__()
    with pytest.raises(ValueError):
        Run(a['id'],workspace=store.path,capture_console=False).__enter__()
    import fcntl
    with (repo/'simshelf.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        r.finish()
        assert store.run(r.id)['status']=='completed'
        assert archive.view(store,r.id)['pending']
    archive.publish(store,r.id)
    assert len(archive.entries(store,r.id))==1


def test_corrupt_missing_objects_and_modified_inputs_fail_closed(setup,tmp_path):
    store,repo,(a,b)=setup
    ident=run_output(store,a)
    e,=archive.entries(store,ident)
    oid=archive.git(repo,'rev-parse',f"{e['commit']}:{e['files'][0]['path']}").decode().strip()
    (repo/'objects'/oid[:2]/oid[2:]).unlink()
    with pytest.raises(ValueError):archive.download(store,ident,e['id'],0)
    output=Path(a['root'])/'outputs/result.csv'
    output.unlink();output.symlink_to(tmp_path/'external.csv')
    (tmp_path/'external.csv').write_text('external')
    r=Run(a['id'],workspace=store.path,capture_console=False);r.__enter__();r.finish()
    events=archive.entries(store,r.id)
    assert not any(f['category']=='result' for e in events for f in e['files'])
    assert (tmp_path/'external.csv').read_text()=='external'


def test_real_cli_failed_exit_logs_and_cancellation(setup):
    import sys
    store,repo,(a,b)=setup
    code="from pathlib import Path; import sys; Path('outputs/result.csv').write_text('partial'); print('scientific log'); sys.exit(7)"
    ident,rc=record_command(store,a['id'],[sys.executable,'-c',code],cwd=a['root'],quiet=True)
    assert rc==7 and store.run(ident)['status']=='failed'
    assert (store.path/'logs'/ident/'stdout.log').read_text()=='scientific log\n'
    assert len(archive.entries(store,ident))==1
    import threading
    cancel=threading.Event();cancel.set()
    ident,rc=record_command(store,b['id'],[sys.executable,'-c','import time;time.sleep(30)'],cwd=b['root'],quiet=True,cancel=cancel)
    assert store.run(ident)['status']=='interrupted'
    assert rc!=0


def test_cumulative_addition_limits_and_removed_run_retains_git(setup,tmp_path,monkeypatch):
    store,repo,(a,b)=setup
    ident=run_output(store,a)
    original=archive.entries(store,ident)
    used=sum(f['size'] for e in original for f in e['files'])
    file=tmp_path/'attachment';file.write_bytes(b'12345')
    attachment=save_file(store,ident,file)
    monkeypatch.setattr(archive,'RUN_LIMIT',used+4)
    with pytest.raises(ValueError):archive.additions_preview(store,ident,[attachment['id']])
    head=archive.git(repo,'rev-parse','refs/heads/main')
    store.remove_runs([ident],confirmed=True)
    assert archive.git(repo,'rev-parse','refs/heads/main')==head
    with pytest.raises((KeyError,ValueError)):archive.view(store,ident)


def test_future_patterns_do_not_capture_nested_or_outside_files(setup):
    store,repo,(a,b)=setup
    sim=store.simulation(a['id']); config=sim['config']; config['rules']=[{'pattern':'**/*','action':'reference'}]
    store.update_simulation(a['id'],config=config)
    archive.enable(store,a['id'],archive.settings_preview(store,a['id'],['logs/*.csv']),True)
    r=Run(a['id'],workspace=store.path,capture_console=False);r.__enter__()
    root=Path(a['root'])/'outputs';(root/'logs/nested').mkdir(parents=True)
    (root/'logs/yes.csv').write_text('yes');(root/'logs/nested/no.csv').write_text('no')
    r.finish()
    policies={f['name']:f['policy'] for f in store.run(r.id)['artifacts']}
    assert policies=={'logs/yes.csv':'copy','logs/nested/no.csv':'reference'}
    e,=archive.entries(store,r.id)
    assert {f['name'] for f in e['files']}=={'sim.py','logs/yes.csv'}


def test_boundary_dotdot_and_hardlinks(setup,tmp_path):
    store,repo,(a,b)=setup
    with pytest.raises(ValueError):archive.connect(store,str(repo/'..'/'alpha'),True,True)
    f=tmp_path/'a';f.write_bytes(b'secret');os.link(f,tmp_path/'b')
    with pytest.raises(ValueError):archive.safe_read(f)


def test_concurrent_simulations_get_distinct_commits(setup):
    from concurrent.futures import ThreadPoolExecutor
    store,repo,(a,b)=setup
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(run_output,store,s,s['name']) for s in (a,b)]
        ids=[f.result(timeout=30) for f in futures]
    assert len({archive.entries(store,i)[0]['commit'] for i in ids})==2
    for ident,sim in zip(ids,(a,b)):
        e,=archive.entries(store,ident)
        assert e['simulation']==sim['id']
        n=next(n for n,f in enumerate(e['files']) if f['category']=='result')
        assert archive.download(store,ident,e['id'],n)[1]==sim['name'].encode()


def test_changed_after_capture_not_archived(setup,monkeypatch):
    store,repo,(a,b)=setup
    original=archive.fingerprint_outputs
    count=0
    def changing(sim,plan):
        nonlocal count
        count+=1
        if count==2:(Path(sim['root'])/'outputs/result.csv').write_text('changed by another writer')
        return original(sim,plan)
    monkeypatch.setattr(archive,'fingerprint_outputs',changing)
    ident=run_output(store,a)
    e,=archive.entries(store,ident)
    assert not any(f['category']=='result' for f in e['files'])
    assert any('No verified matching' in f['reason'] for f in e['skipped'])
    assert store.run(ident)['status']=='completed'


def test_source_git_index_and_history_unchanged(setup):
    import subprocess
    store,repo,(a,b)=setup
    root=Path(a['root'])
    def git(*args):return subprocess.check_output(['git','-C',str(root),*args],stderr=subprocess.DEVNULL)
    git('init','--template=');git('add','sim.py')
    git('-c','user.name=Test','-c','user.email=test@localhost','-c','commit.gpgSign=false','commit','-m','source')
    # Source repo changed binding: explicitly save preferences and consent again.
    inv=inventory(store,a['id']);save_selection(store,a['id'],selection_preview(store,a['id'],inv['revision'],[{'kind':'file','value':'sim.py'}]))
    archive.enable(store,a['id'],archive.settings_preview(store,a['id'],['result.csv']),True)
    before_index=(root/'.git/index').read_bytes();before_head=git('rev-parse','HEAD')
    ident=run_output(store,a)
    assert archive.entries(store,ident)
    assert (root/'.git/index').read_bytes()==before_index
    assert git('rev-parse','HEAD')==before_head


def test_prepared_crash_does_not_recapture_live_files(setup):
    store,repo,(a,b)=setup
    r=Run(a['id'],workspace=store.path,capture_console=False);r.__enter__()
    store.emit(r.id,'finish',{'status':'interrupted','ended_at':'2026-10-17T00:00:00Z','capture_status':'incomplete'})
    (Path(a['root'])/'outputs/result.csv').write_text('later unrelated bytes')
    store.reconcile()
    assert archive.publish(store,r.id)=={'status':'nothing pending'}
    assert not archive.entries(store,r.id)
    assert archive.view(store,r.id)['initial']['state']=='prepared'


def test_unavailable_repository_and_invalid_payload_errors(setup):
    store,repo,(a,b)=setup
    ident=run_output(store,a);e,=archive.entries(store,ident)
    for ids in ([{}],['../bad'],[None]):
        with pytest.raises(ValueError):archive.additions_preview(store,ident,ids)
    (repo/'simshelf-archive-id').unlink()
    with pytest.raises(ValueError,match='unavailable or unsafe'):
        archive.download(store,ident,e['id'],0)


def test_corrupt_optional_archive_settings_do_not_block_recording(setup):
    store,repo,(a,b)=setup
    with store.connection() as conn:
        conn.execute('UPDATE metadata SET value=? WHERE key=?', ('invalid json',archive.PREFIX+'settings:'+a['id']))
    ident=run_output(store,a)
    assert store.run(ident)['status']=='completed'
    assert not archive.entries(store,ident)
    assert archive.view(store,ident)['error']


def test_read_only_status_and_downloads_independent_of_source_git(setup, monkeypatch):
    store, repo, (a, b) = setup
    ident = run_output(store, a)
    event, = archive.entries(store, ident)
    before_run = store.run(ident)
    with store.connection() as conn:
        before = [tuple(row) for row in conn.execute('SELECT * FROM metadata ORDER BY key')]
    files = {str(p.relative_to(repo)): p.read_bytes() for p in repo.rglob('*') if p.is_file()}
    assert archive.connection_status(store)['state'] == 'connected'
    assert archive.automatic_status(store, a['id'])['state'] == 'enabled'
    assert archive.view(store, ident)['connection_status']['identity'] == event['repository']['identity']
    with store.connection() as conn:
        assert before == [tuple(row) for row in conn.execute('SELECT * FROM metadata ORDER BY key')]
    assert files == {str(p.relative_to(repo)): p.read_bytes() for p in repo.rglob('*') if p.is_file()}
    assert before_run == store.run(ident)
    saved = archive.get(store, 'connection')
    archive.put(store, 'connection', None)
    assert archive.connection_status(store)['state'] == 'disconnected'
    assert archive.automatic_status(store, a['id'])['state'] == 'review_required'
    assert archive.view(store, ident)['events'] == [event]
    artifact = next(x for x in store.run(ident)['artifacts'] if x['policy'] == 'copy')
    assert store.artifact_file(artifact['id']).read_bytes() == b'one'
    with pytest.raises(ValueError): archive.download(store, ident, event['id'], 0)
    archive.put(store, 'connection', saved)
    assert archive.download(store, ident, event['id'], 0)
    monkeypatch.setattr(archive.shutil, 'which', lambda name: None)
    assert archive.connection_status(store)['state'] == 'unavailable'
    assert archive.automatic_status(store, a['id'])['state'] == 'review_required'
    assert store.artifact_file(artifact['id']).read_bytes() == b'one'


def test_consent_projection_disabled_stale_and_future_matches(setup):
    store, repo, (a, b) = setup
    # New matching filenames are allowed by existing consent, not a stale revision.
    (Path(a['root']) / 'outputs/new.csv').write_text('new')
    assert archive.automatic_status(store, a['id'])['state'] == 'enabled'
    inv = inventory(store, a['id'])
    save_selection(store, a['id'], selection_preview(store, a['id'], inv['revision'], []))
    assert archive.automatic_status(store, a['id'])['state'] == 'review_required'
    assert archive.automatic_status(store, b['id'])['state'] == 'enabled'
    archive.put(store, 'settings:' + a['id'], None)
    assert archive.automatic_status(store, a['id'])['state'] == 'disabled'
    saved = archive.get(store, 'connection')
    archive.put(store, 'connection', {**saved, 'workspace': 'different'})
    assert archive.connection_status(store)['state'] == 'unavailable'
    archive.put(store, 'connection', saved)
    (repo / 'simshelf-archive-id').write_text('wrong')
    assert archive.connection_status(store)['state'] == 'unavailable'
    assert archive.automatic_status(store, b['id'])['state'] == 'review_required'


def test_api_availability_disconnect_reload_and_workspace_copy(setup):
    from fastapi.testclient import TestClient
    from simshelf.api import create_app
    store, repo, (a, b) = setup
    ident = run_output(store, a)
    client = TestClient(create_app(store.path))
    assert client.get('/api/workspace/archive').json()['status']['state'] == 'connected'
    assert client.get(f'/api/simulations/{a["id"]}/archive').json()['automatic_status']['state'] == 'enabled'
    assert client.get('/api/workspace/git').json()['connection'] is None
    saved = archive.get(store, 'connection')
    archive.put(store, 'connection', None)
    response = client.get(f'/api/runs/{ident}/archive').json()
    assert response['connection_status']['state'] == 'disconnected'
    event, = response['events']
    item = next(x for x in store.run(ident)['artifacts'] if x['policy'] == 'copy')
    assert client.get(f'/api/artifacts/{item["id"]}/file?download=true').content == b'one'
    assert client.get(f'/api/runs/{ident}/archive/{event["id"]}/0/file').status_code == 400
    archive.connect(store, saved['path'], False, True)
    reloaded = TestClient(create_app(store.path))
    assert reloaded.get('/api/workspace/archive').json()['status']['state'] == 'connected'
    assert reloaded.get(f'/api/runs/{ident}/archive/{event["id"]}/0/file').status_code == 200


def test_toggle_disable_preserves_running_consent_other_simulations_and_history(setup):
    from fastapi.testclient import TestClient
    from simshelf.api import create_app
    store, repo, (a, b) = setup
    old = run_output(store, a)
    old_record = store.run(old, False)
    old_events = archive.entries(store, old)
    other_settings = archive.get(store, 'settings:' + b['id'])
    running = Run(a['id'], workspace=store.path, capture_console=False)
    running.__enter__()
    frozen = archive.get(store, 'initial:' + running.id)
    client = TestClient(create_app(store.path))
    headers = {'X-SimShelf-Token': client.get('/api/workspace').json()['token']}
    assert client.post(f'/api/simulations/{a["id"]}/archive/disable', headers=headers).status_code == 200
    assert archive.automatic_status(store, a['id'])['state'] == 'disabled'
    assert archive.get(store, 'settings:' + b['id']) == other_settings
    assert archive.get(store, 'initial:' + running.id) == frozen
    assert store.run(running.id)['status'] == 'running'
    # Requesting a preview (then canceling it) grants no consent.
    review = client.post(f'/api/simulations/{a["id"]}/archive/preview', headers=headers, json={'future':['later.csv']}).json()
    assert archive.automatic_status(store, a['id'])['state'] == 'disabled'
    assert client.post(f'/api/simulations/{a["id"]}/archive/enable', headers=headers, json={'review':review}).status_code == 400
    assert archive.automatic_status(store, a['id'])['state'] == 'disabled'
    # Explicitly change future-run settings while the original run is still active.
    assert client.post(f'/api/simulations/{a["id"]}/archive/enable', headers=headers, json={'review':review,'confirmed':True}).status_code == 200
    assert archive.get(store, 'initial:' + running.id) == frozen
    (Path(a['root'])/'outputs/result.csv').write_text('frozen result')
    (Path(a['root'])/'outputs/later.csv').write_text('future rule')
    running.finish()
    event, = archive.entries(store, running.id)
    assert any(f['name']=='result.csv' for f in event['files'])
    assert not any(f['name']=='later.csv' for f in event['files'])
    reloaded = Store(store.path)
    assert archive.automatic_status(reloaded, a['id'])['state'] == 'enabled'
    assert archive.get(reloaded, 'settings:' + a['id'])['future'] == ['later.csv']
    assert archive.get(reloaded, 'settings:' + b['id']) == other_settings
    assert reloaded.run(old, False) == old_record
    assert archive.entries(reloaded, old) == old_events
    assert archive.download(reloaded, old, old_events[0]['id'], 0)


def test_activation_rejects_stale_capture_and_selection_reviews(setup):
    store, repo, (a, b) = setup
    archive.put(store, 'settings:' + a['id'], None)
    review = archive.settings_preview(store, a['id'], ['result.csv'])
    store.update_simulation(a['id'], config={**a['config'], 'max_file_mb': 10})
    with pytest.raises(ValueError, match='Settings changed'):
        archive.enable(store, a['id'], review, True)
    assert archive.automatic_status(store, a['id'])['state'] == 'disabled'
    review = archive.settings_preview(store, a['id'], ['result.csv'])
    inv = inventory(store, a['id'])
    save_selection(store, a['id'], selection_preview(store, a['id'], inv['revision'], []))
    with pytest.raises(ValueError, match='Settings changed'):
        archive.enable(store, a['id'], review, True)
    assert archive.automatic_status(Store(store.path), a['id'])['state'] == 'disabled'
    assert archive.automatic_status(store, b['id'])['state'] == 'enabled'


def test_verified_reconnect_preserves_consent_history_and_running_plan(setup):
    from fastapi.testclient import TestClient
    from simshelf.api import create_app
    store, repo, (a, b) = setup
    ident = run_output(store, a)
    record = store.run(ident, False)
    events = archive.entries(store, ident)
    saved = archive.get(store, 'connection')
    consent = [archive.get(store, 'settings:' + s['id']) for s in (a, b)]
    running = Run(a['id'], workspace=store.path, capture_console=False)
    running.__enter__()
    plan = archive.get(store, 'initial:' + running.id)
    client = TestClient(create_app(store.path))
    headers = {'X-SimShelf-Token': client.get('/api/workspace').json()['token']}
    assert client.post('/api/workspace/archive/disconnect', headers=headers).status_code == 200
    assert archive.connection_status(Store(store.path))['state'] == 'disconnected'
    assert [archive.get(store, 'settings:' + s['id']) for s in (a, b)] == consent
    assert archive.get(store, 'initial:' + running.id) == plan
    assert archive.automatic_status(store, a['id'])['state'] == 'review_required'
    with pytest.raises(ValueError):
        archive.settings_preview(store, a['id'], [])
    file = next(f for f in store.run(ident)['artifacts'] if f['policy'] == 'copy')
    assert client.get(f'/api/artifacts/{file["id"]}/file?download=true').content == b'one'
    route = f'/api/runs/{ident}/archive/{events[0]["id"]}/0/file'
    assert client.get(route).status_code == 400
    body = {'path': saved['path'], 'expected_connection': saved, 'confirmed': True}
    assert client.post('/api/workspace/archive/connect', headers=headers, json=body).status_code == 200
    assert client.get(route).status_code == 200
    assert archive.connection_status(Store(store.path))['state'] == 'connected'
    assert [archive.get(store, 'settings:' + s['id']) for s in (a, b)] == consent
    assert archive.get(store, 'initial:' + running.id) == plan
    running.finish()
    assert store.run(ident, False) == record
    assert archive.entries(store, ident) == events


def test_quick_reconnect_rejects_replacement_missing_changed_binding_and_initialization(setup, monkeypatch):
    store, repo, (a, b) = setup
    saved = archive.get(store, 'connection')
    archive.put(store, 'connection', None)
    marker = repo / 'simshelf-archive-id'
    marker.write_text(uuid.uuid4().hex)
    with pytest.raises(ValueError, match='identity changed'):
        archive.connect(store, saved['path'], confirmed=True, expected_connection=saved)
    assert archive.get(store, 'connection') is None
    marker.write_text(saved['identity'])
    moved = repo.with_name('moved'); repo.rename(moved)
    with pytest.raises(ValueError):
        archive.connect(store, saved['path'], confirmed=True, expected_connection=saved)
    moved.rename(repo)
    for expected, initialize in [({**saved, 'workspace':'other'}, False), (saved, True), ({}, False)]:
        with pytest.raises(ValueError):
            archive.connect(store, saved['path'], initialize, True, expected)
        assert archive.get(store, 'connection') is None
    monkeypatch.setattr(archive.shutil, 'which', lambda _: None)
    with pytest.raises(ValueError, match='Git unavailable'):
        archive.connect(store, saved['path'], confirmed=True, expected_connection=saved)
    assert archive.get(store, 'connection') is None
    monkeypatch.undo()
    other = {**saved, 'identity':uuid.uuid4().hex}
    archive.put(store, 'connection', other)
    with pytest.raises(ValueError, match='Disconnect the current archive'):
        archive.connect(store, saved['path'], confirmed=True, expected_connection=saved)
    assert archive.get(store, 'connection') == other


def test_connection_write_failure_preserves_previous_state(setup, monkeypatch):
    from fastapi.testclient import TestClient
    from simshelf.api import create_app
    store, repo, sims = setup
    saved = archive.get(store, 'connection')
    client = TestClient(create_app(store.path))
    headers = {'X-SimShelf-Token': client.get('/api/workspace').json()['token']}
    original_put = archive.put
    def rejected(*args):
        raise ValueError('Connection change failed; refresh and retry.')
    monkeypatch.setattr(archive, 'save_connection', rejected)
    assert client.post('/api/workspace/archive/disconnect', headers=headers).status_code == 400
    assert archive.get(store, 'connection') == saved
    original_put(store, 'connection', None)
    response = client.post('/api/workspace/archive/connect', headers=headers,
                          json={'path':saved['path'],'confirmed':True,'expected_connection':saved})
    assert response.status_code == 400
    assert archive.get(store, 'connection') is None


def test_connected_location_cannot_be_replaced_or_initialized_via_api(setup, tmp_path):
    from fastapi.testclient import TestClient
    from simshelf.api import create_app
    store, repo, sims = setup
    saved = archive.get(store, 'connection')
    other = tmp_path / 'other'; other.mkdir()
    client = TestClient(create_app(store.path))
    headers = {'X-SimShelf-Token':client.get('/api/workspace').json()['token']}
    for path, initialize in [(str(other), True), (str(repo), False), (str(other), False)]:
        response = client.post('/api/workspace/archive/connect', headers=headers,
                               json={'path':path,'initialize':initialize,'confirmed':True})
        assert response.status_code == 400
        assert 'Disconnect' in response.json()['detail']
        assert archive.get(store, 'connection') == saved
        assert archive.get(store, 'last_connection') == saved
        assert list(other.iterdir()) == []
    assert client.post('/api/workspace/archive/disconnect', headers=headers).status_code == 200
    assert client.post('/api/workspace/archive/connect', headers=headers,
                       json={'path':str(other),'initialize':True,'confirmed':True}).status_code == 200
    assert archive.get(store, 'connection')['path'] == str(other)


def test_remembered_connection_restart_failure_and_old_library_compatibility(setup):
    from fastapi.testclient import TestClient
    from simshelf.api import create_app
    store, repo, sims = setup
    saved = archive.get(store, 'connection')
    consent = [archive.get(store, 'settings:'+s['id']) for s in sims]
    with store.connection() as db:
        schema = db.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()[0]
    # Simulate a library from before the preference existed.
    with store.connection() as db:
        db.execute('DELETE FROM metadata WHERE key=?', (archive.PREFIX+'last_connection',))
    archive.disconnect(store)
    reloaded = Store(store.path)
    client = TestClient(create_app(reloaded.path))
    response = client.get('/api/workspace/archive').json()
    assert response['connection'] is None
    assert response['remembered_connection'] == saved
    assert response['status']['state'] == 'disconnected'
    with reloaded.connection() as db:
        assert db.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()[0] == schema
    marker = repo/'simshelf-archive-id'; marker.write_text(uuid.uuid4().hex)
    for expected in (None, saved):
        with pytest.raises(ValueError, match='identity changed'):
            archive.connect(reloaded, saved['path'], confirmed=True, expected_connection=expected)
        assert archive.get(reloaded,'connection') is None
        assert archive.get(reloaded,'last_connection') == saved
    with pytest.raises(ValueError):
        archive.connect(reloaded, saved['path'], initialize=True, confirmed=True)
    marker.write_text(saved['identity'])
    archive.connect(reloaded, saved['path'], confirmed=True, expected_connection=saved)
    assert [archive.get(reloaded,'settings:'+s['id']) for s in sims] == consent


def test_connection_preference_write_is_atomic(setup):
    import sqlite3
    store, repo, sims = setup
    saved = archive.get(store, 'connection')
    with store.connection() as db:
        db.execute("CREATE TRIGGER reject_preference BEFORE INSERT ON metadata WHEN NEW.key = 'archive_v1:last_connection' BEGIN SELECT RAISE(ABORT, 'test failure'); END")
    with pytest.raises(sqlite3.IntegrityError, match='test failure'):
        archive.disconnect(store)
    assert archive.get(store, 'connection') == saved
    assert archive.get(store, 'last_connection') == saved
    archive.put(store, 'connection', None)
    with pytest.raises(sqlite3.IntegrityError, match='test failure'):
        archive.connect(store, saved['path'], confirmed=True, expected_connection=saved)
    assert archive.get(store, 'connection') is None
    assert archive.get(store, 'last_connection') == saved


def test_isolated_outputs_keep_base_consent_and_capture_relative_selection(setup):
    store, repo, (a, b) = setup
    ids = []
    for value in ('first isolated', 'second isolated'):
        with Run(a['id'], workspace=store.path, capture_console=False, output_policy='per_run') as run:
            (run.output_dir / 'result.csv').write_text(value)
            (run.output_dir / 'not-selected.csv').write_text('only managed')
        ids.append(run.id)
        view = archive.view(store, run.id)
        assert not view['error'], view
        event, = view['events']
        assert {f['name'] for f in event['files']} == {'sim.py', 'result.csv'}
        index = next(i for i, f in enumerate(event['files']) if f['name'] == 'result.csv')
        assert archive.download(store, run.id, event['id'], index)[1] == value.encode()
    assert store.run(ids[0])['snapshot_id'] == store.run(ids[1])['snapshot_id']
    assert Path(store.run(ids[0])['capture_root'], 'result.csv').read_text() == 'first isolated'
    # A genuinely changed base/budget still invalidates consent.
    with Run(a['id'], workspace=store.path, capture_console=False, output_dir='other', output_policy='per_run') as run:
        (run.output_dir / 'result.csv').write_text('not consented')
    assert not archive.entries(store, run.id)
    assert 'no longer match' in archive.view(store, run.id)['error']
