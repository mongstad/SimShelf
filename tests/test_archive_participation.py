"""Two-level automatic Git consent; all data and Git repositories are disposable."""
import copy
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from simshelf import git_archive as archive, preservation
from simshelf.api import create_app
from simshelf.backup import create_backup, restore_backup
from simshelf.recording import Run
from simshelf.store import Store
from test_library_preservation_audit import library, launch, consent, SOURCE_RULES, verify_event
from test_preservation import enable, options, verify


@pytest.mark.parametrize('global_on,participating', [(False,False),(False,True),(True,False),(True,True)])
def test_effective_matrix_and_real_nested_bytes(library, global_on, participating):
    store, repo, (a, b) = library
    enable(store, a)
    preservation.set_participation(store, a['id'], participating)
    policy = preservation.get(store, 'settings:'+a['id'])
    archive.set_global_enabled(store, global_on)
    assert preservation.get(store, 'settings:'+a['id']) == policy
    state = preservation.status(store,a['id'])
    assert state['participating'] is participating
    assert state['state'] == ('enabled' if global_on and participating else 'disabled')
    assert not preservation.status(store,b['id'])['participating']
    run = launch(store,a,f'matrix-{global_on}-{participating}',csv=True)
    assert run['capture_status'] == 'complete'
    assert run['capture_counts']['copied'] == 4
    if global_on and participating:
        event = verify(store,repo,run)
        verify_event(store,repo,run)  # Independent git tree/cat-file inspection.
        assert {Path(f['name']).suffix for f in event['files'] if f['category']=='result'} == {'.json','.csv','.log'}
        assert archive.view(store,run['id'])['preservation']['output_files'] == 4
    else:
        assert not archive.entries(store,run['id'])
    assert preservation.get(Store(store.path),'settings:'+a['id']) == policy


def test_global_off_retains_connection_consent_history_and_new_sim_defaults(library):
    store, repo, (a,b) = library
    enable(store,a,all_sources=False,sources=['sim.py'],extensions=['.csv'])
    run=launch(store,a,'before',csv=True);event=verify(store,repo,run)
    record=archive.download_record(store,run['id'],event['id'])
    saved=copy.deepcopy(preservation.get(store,'settings:'+a['id']))
    connection=archive.get(store,'connection');head=archive.git(repo,'rev-parse','HEAD')
    archive.set_global_enabled(store,False)
    assert archive.get(store,'connection')==connection
    assert preservation.status(store,a['id'])['participating']
    off=launch(store,a,'off',csv=True);assert not archive.entries(store,off['id'])
    assert archive.git(repo,'rev-parse','HEAD')==head
    archive.set_global_enabled(store,True)
    assert preservation.get(store,'settings:'+a['id'])==saved
    assert not preservation.status(store,b['id'])['participating']
    for flag in (False,True):
        preservation.set_participation(store,a['id'],flag)
    assert preservation.get(store,'settings:'+a['id'])==saved
    assert archive.download_record(store,run['id'],event['id'])==record
    assert archive.git(repo,'rev-parse','HEAD')==head
    assert preservation.status(Store(store.path),a['id'])['state']=='enabled'


def test_unavailable_disconnected_and_replaced_identity_capture_locally(library):
    store,repo,(a,b)=library;enable(store,a)
    saved=archive.get(store,'connection')
    for disconnect in (True,False):
        if disconnect: archive.disconnect(store)
        else:
            archive.connect(store,str(repo),confirmed=True,expected_connection=saved)
            (repo/'simshelf-archive-id').write_text('0'*32)
        assert archive.global_enabled(store)
        assert preservation.status(store,a['id'])['state']=='unavailable'
        run=launch(store,a,'unavailable-'+str(disconnect),csv=True)
        assert run['capture_status']=='complete' and run['capture_counts']['copied']==4
        assert not archive.entries(store,run['id'])
        assert archive.view(store,run['id'])['preservation']['state']=='unavailable'
        with pytest.raises(ValueError): archive.set_global_enabled(store,True)


@pytest.mark.parametrize('legacy',[False,True])
def test_frozen_active_plan_survives_global_and_individual_off(library,legacy):
    store,repo,(a,b)=library
    if legacy: consent(store,a,SOURCE_RULES,[])
    else: enable(store,a)
    run=Run(a['id'],workspace=store.path,capture_console=False);run.__enter__()
    namespace=archive.PREFIX if legacy else preservation.PREFIX
    plan=archive.get(store,'initial:'+run.id,namespace=namespace)
    archive.set_global_enabled(store,False)
    preservation.set_participation(store,a['id'],False)
    (Path(a['root'])/'outputs').mkdir(exist_ok=True)
    (Path(a['root'])/'outputs/frozen.json').write_text('{"retained":true}')
    assert archive.get(store,'initial:'+run.id,namespace=namespace)==plan
    run.finish()
    assert archive.entries(store,run.id)
    later=launch(store,a,'later',csv=True);assert not archive.entries(store,later['id'])


def test_legacy_off_on_and_global_off_never_expand_scope(library):
    store,repo,(a,b)=library;consent(store,a,SOURCE_RULES,[])
    old=archive.get(store,'settings:'+a['id'])
    preservation.set_participation(store,a['id'],False)
    assert archive.get(store,'settings:'+a['id']) is None
    assert archive.get(store,'paused_settings:'+a['id'])==old
    archive.set_global_enabled(store,False);archive.set_global_enabled(store,True)
    assert not preservation.status(store,a['id'])['participating']
    preservation.set_participation(store,a['id'],True)
    assert archive.get(store,'settings:'+a['id'])==old
    assert preservation.get(store,'settings:'+a['id']) is None
    run=launch(store,a,'legacy-no-expansion',csv=True)
    event,=archive.entries(store,run['id'])
    assert {f['category'] for f in event['files']}=={'source'}
    preservation.set_participation(store,a['id'],False)
    store.update_simulation(a['id'],config={**a['config'],'max_file_mb':1})
    with pytest.raises(ValueError): preservation.set_participation(store,a['id'],True)
    assert not preservation.status(store,a['id'])['participating']


def test_api_requires_explicit_global_and_review_then_resumes_exact_policy(library):
    store,repo,(a,b)=library;archive.put(store,'automatic_enabled',None)
    client=TestClient(create_app(store.path));headers={'X-SimShelf-Token':client.get('/api/workspace').json()['token']}
    base=f'/api/simulations/{a["id"]}/preservation'
    assert not client.get('/api/workspace/archive').json()['enabled']
    assert client.post('/api/workspace/archive/automatic',json={'enabled':True}).status_code==403
    assert client.post('/api/workspace/archive/automatic',headers=headers,json={'enabled':'true'}).status_code==422
    assert client.post('/api/workspace/archive/automatic',headers=headers,json={'enabled':True}).status_code==200
    assert client.post(base+'/participation',headers=headers,json={'enabled':True}).status_code==400
    review=client.post(base+'/preview',headers=headers,json={'config':a['config'],'options':options()}).json()
    assert not preservation.status(store,a['id'])['participating'] # Cancel is read-only.
    assert client.post(base+'/save',headers=headers,json={'review':review,'confirmed':False}).status_code==400
    assert client.post(base+'/save',headers=headers,json={'review':review,'confirmed':True}).status_code==200
    old=preservation.get(store,'settings:'+a['id'])
    for flag in (False,True):
        assert client.post(base+'/participation',headers=headers,json={'enabled':flag}).status_code==200
    assert preservation.get(store,'settings:'+a['id'])==old
    assert client.get(base).json()['status']['state']=='enabled'
    # Global OFF prevents execution, not explicit approval of a future preference.
    review=preservation.preview(store,b['id'],b['config'],options())
    archive.set_global_enabled(store,False)
    preservation.save(store,b['id'],review,True)
    assert preservation.status(store,b['id'])['participating']
    assert preservation.status(store,b['id'])['state'] == 'disabled'


@pytest.mark.parametrize('legacy', [False, True])
def test_preference_editable_while_master_off_survives_restart_without_history_changes(library, legacy):
    store, repo, (sim, _) = library
    if legacy: consent(store, sim, SOURCE_RULES, [])
    else: enable(store, sim)
    old = launch(store, sim, 'before-preference', csv=True)
    events = archive.entries(store, old['id'])
    head = archive.git(repo, 'rev-parse', 'HEAD')
    source = (Path(sim['root']) / 'sim.py').read_bytes()
    archive.set_global_enabled(store, False)
    for preference in (False, True, False):
        preservation.set_participation(store, sim['id'], preference)
        reopened = Store(store.path)
        state = preservation.status(reopened, sim['id'])
        assert state['participating'] is preference and state['state'] == 'disabled'
        result = launch(reopened, sim, f'off-{preference}', csv=True)
        assert result['capture_status'] == 'complete'
        assert not archive.entries(reopened, result['id'])
        assert archive.git(repo, 'rev-parse', 'HEAD') == head
    archive.set_global_enabled(store, True)
    assert not preservation.status(store, sim['id'])['participating']
    archive.set_global_enabled(store, False)
    preservation.set_participation(store, sim['id'], True)
    archive.set_global_enabled(store, True)
    assert preservation.status(Store(store.path), sim['id'])['state'] == 'enabled'
    assert archive.git(repo, 'rev-parse', 'HEAD') == head
    assert store.run(old['id']) == old
    assert archive.entries(store, old['id']) == events
    assert (Path(sim['root']) / 'sim.py').read_bytes() == source


def test_master_off_missing_git_can_turn_off_but_cannot_bypass_scope_validation(library, monkeypatch):
    store, repo, (sim, _) = library
    enable(store, sim)
    archive.set_global_enabled(store, False)
    head = archive.git(repo, 'for-each-ref', '--format=%(refname) %(objectname)')
    with monkeypatch.context() as missing:
        missing.setenv('PATH', '/nonexistent')
        assert preservation.status(store, sim['id'])['connection'] == 'unavailable'
        preservation.set_participation(store, sim['id'], False)
        with pytest.raises(ValueError):
            preservation.set_participation(store, sim['id'], True)
        assert not preservation.status(store, sim['id'])['participating']
    preservation.set_participation(store, sim['id'], True)
    assert preservation.status(store, sim['id'])['state'] == 'disabled'
    assert archive.git(repo, 'for-each-ref', '--format=%(refname) %(objectname)') == head


def test_backup_retains_both_preferences_but_relocation_cannot_activate(library,tmp_path):
    store,repo,(a,b)=library;enable(store,a);consent(store,b,SOURCE_RULES,[])
    preservation.set_participation(store,b['id'],False)
    archive.set_global_enabled(store,False)
    old=preservation.get(store,'settings:'+a['id']);paused=archive.get(store,'paused_settings:'+b['id'])
    backup=create_backup(store,tmp_path/'library.zip');restored=restore_backup(backup,tmp_path/'restored')
    assert not archive.global_enabled(restored)
    assert preservation.get(restored,'settings:'+a['id'])==old
    assert archive.get(restored,'paused_settings:'+b['id'])==paused
    assert preservation.status(restored,a['id'])['participating']
    assert not preservation.status(restored,b['id'])['participating']
    with pytest.raises(ValueError):archive.set_global_enabled(restored,True)
    run=launch(restored,a,'restore-local',csv=True)
    assert run['capture_status']=='complete' and not archive.entries(restored,run['id'])


def test_paused_legacy_is_invalidated_by_explicit_relocation_and_removal(library,tmp_path):
    import shutil
    from simshelf import relocation, simulation_removal
    store,repo,(a,b)=library
    for sim in (a,b):
        consent(store,sim,SOURCE_RULES,[])
        preservation.set_participation(store,sim['id'],False)
    target=tmp_path/'moved';shutil.copytree(a['root'],target)
    relocation.relocate(store,a['id'],relocation.preview(store,a['id'],str(target)),True)
    assert archive.get(store,'paused_settings:'+a['id']) is None
    before=archive.get(store,'connection')
    # Explicitly prepared disposable removal-compatible fixture; no product migration.
    with store.connection() as db:
        db.execute("UPDATE metadata SET value='2' WHERE key='schema_version'")
    review=simulation_removal.preview(store,b['id'])
    simulation_removal.remove(store,b['id'],typed_name=b['name'],revision=review['revision'],confirmed=True)
    assert archive.get(store,'paused_settings:'+b['id']) is None
    assert archive.get(store,'connection')==before


def test_reviewed_scope_edit_while_global_off_retains_participation(library):
    store,repo,(a,b)=library;enable(store,a)
    archive.set_global_enabled(store,False)
    changed={**a['config'],'max_file_mb':10}
    review=preservation.preview(store,a['id'],changed,options(extensions=['.csv']))
    preservation.save(store,a['id'],review,True)
    assert not archive.global_enabled(store)
    assert preservation.status(store,a['id'])['participating']
    assert preservation.status(store,a['id'])['state']=='disabled'
    archive.set_global_enabled(store,True)
    preservation.set_participation(store,a['id'],False)
    store.update_simulation(a['id'],config={**changed,'max_file_mb':5})
    with pytest.raises(ValueError):preservation.set_participation(store,a['id'],True)
    assert not preservation.status(store,a['id'])['participating']
