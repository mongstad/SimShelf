import json
import shutil
import sqlite3
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from simshelf.api import create_app
from simshelf.backup import create_backup, restore_backup
from simshelf.capture import save_file
from simshelf.common import json_text
from simshelf.recording import Run, record_command
from simshelf.relocation import preview, relocate, source_binding
from simshelf import git_archive as archive
from simshelf.git_selection import inventory, selection_preview, save_selection
from simshelf.store import Store


def destination(root):
    target = root.parent / 'new-source'
    shutil.copytree(root, target)
    return target


def historical_bytes(store):
    with store.connection() as c:
        tables = ('runs', 'artifacts', 'annotations', 'metrics', 'applied_events')
        rows = {t: [tuple(r) for r in c.execute(f'SELECT * FROM {t} ORDER BY rowid')] for t in tables}
    files = {str(p.relative_to(store.path)): p.read_bytes() for folder in ('blobs','snapshots','journal','logs')
             for p in (store.path / folder).rglob('*') if p.is_file()}
    return rows, files


def test_move_preserves_history_copies_references_and_restore(project, tmp_path):
    store, sim, root, source = project
    store.update_simulation(sim['id'], execution={'interpreter':sys.executable,'cwd':'.','arguments':['--seed','2'],'output_dir':'outputs'})
    with Run(sim['id'],workspace=store.path,capture_console=False) as run:
        run.log_parameters({'seed':2})
    attachment = root/'result.txt';attachment.write_text('kept result')
    copied=save_file(store,run.id,attachment)
    referenced=save_file(store,run.id,attachment,policy='reference')
    store.emit(run.id,'annotation',{'notes':'retain note'})
    before=historical_bytes(store);registered=store.simulation(sim['id'])
    target=root.with_name('moved');root.rename(target)
    result=relocate(store,sim['id'],preview(store,sim['id'],str(target)),True)
    assert result['id']==sim['id'] and result['root']==str(target)
    assert result['config']==registered['config'] and result['execution']==registered['execution']
    assert historical_bytes(store)==before
    assert store.artifact_file(copied['id']).read_text()=='kept result'
    assert store.artifact(referenced['id'])['availability']=='missing'
    assert store.artifact(referenced['id'])['original_path']==str(attachment)
    restored=restore_backup(create_backup(store,tmp_path/'backup.zip'),tmp_path/'restored')
    assert restored.simulation(sim['id'])==result
    assert restored.run(run.id)['snapshot_id']==store.run(run.id)['snapshot_id']
    assert restored.artifact_file(copied['id']).read_text()=='kept result'
    assert not root.exists() and (target/"field.py").is_file()


@pytest.mark.parametrize('kind',['missing','file','relative','traversal','workspace','workspace-parent','root-link','ancestor-link','entry-link','entry-missing','version-missing','output-link','collision','nested-collision','parent-collision'])
def test_reject_paths_without_changing_registration(project,tmp_path,kind):
    store,sim,root,source=project;target=destination(root)
    (root/'version.py').write_text('SIMSHELF_VERSION="v"')
    with store.connection() as c:
        original=store.simulation(sim['id']);original['version_file']='version.py'
        c.execute('UPDATE simulations SET data=? WHERE id=?',(json_text(original),sim['id']))
    (target/'version.py').write_text('SIMSHELF_VERSION="v"')
    path=str(target)
    if kind=='missing':path=str(tmp_path/'absent')
    if kind=='file':path=str(target/'field.py')
    if kind=='relative':path='relative'
    if kind=='traversal':path=str(target/'..'/'new-source')
    if kind=='workspace':path=str(store.path)
    if kind=='workspace-parent':path=str(tmp_path)
    if kind=='root-link':
        link=tmp_path/'link';link.symlink_to(target,target_is_directory=True);path=str(link)
    if kind=='ancestor-link':
        link=tmp_path/'link';link.symlink_to(tmp_path,target_is_directory=True);path=str(link/'new-source')
    if kind=='entry-link':
        (target/'field.py').unlink();(target/'field.py').symlink_to(source)
    if kind=='entry-missing':(target/'field.py').unlink()
    if kind=='version-missing':(target/'version.py').unlink()
    if kind=='output-link':(target/'outputs').symlink_to(tmp_path,target_is_directory=True)
    if kind=='collision':store.add_simulation(target,name='other')
    if kind=='nested-collision':
        other=tmp_path/'parent';other.mkdir();store.add_simulation(other,name='other');shutil.move(target,other);path=str(other/'new-source')
    if kind=='parent-collision':
        child=target/'child';child.mkdir();store.add_simulation(child,name='other')
    with pytest.raises(ValueError):preview(store,sim['id'],path)
    assert store.simulation(sim['id'])==original


def test_active_stale_and_cancelled_reviews(project):
    store,sim,root,_=project;target=destination(root)
    review=preview(store,sim['id'],str(target))
    assert store.simulation(sim['id'])==sim # Preview/cancel is passive.
    with pytest.raises(ValueError):relocate(store,sim['id'],review,False)
    with Run(sim['id'],workspace=store.path,capture_console=False):
        with pytest.raises(ValueError,match='active runs'):preview(store,sim['id'],str(target))
        with pytest.raises(ValueError,match='active runs'):relocate(store,sim['id'],review,True)
    store.update_simulation(sim['id'],description='edited elsewhere')
    with pytest.raises(ValueError,match='changed'):relocate(store,sim['id'],review,True)
    review=preview(store,sim['id'],str(target))
    target.rename(target.with_name('replaced'));shutil.copytree(root,target)
    with pytest.raises(ValueError,match='changed'):relocate(store,sim['id'],review,True)


def test_stale_recorder_and_portal_plan_cannot_start_after_relocation(project):
    store,sim,root,_=project;target=destination(root)
    recorder=Run(sim['id'],workspace=store.path,capture_console=False)
    binding=source_binding(sim)
    relocate(store,sim['id'],preview(store,sim['id'],str(target)),True)
    with pytest.raises(ValueError,match='location changed'):recorder.__enter__()
    with pytest.raises(ValueError,match='location changed'):
        record_command(store,sim['id'],[sys.executable,'-c','raise AssertionError'],launch={'kind':'portal','source_binding':binding},quiet=True)
    relocate(store,sim['id'],preview(store,sim['id'],str(root)),True)
    with pytest.raises(ValueError,match='location changed'):recorder.__enter__()
    assert store.runs()==[]


def test_missing_execution_preferences_retained_with_warning(project):
    store,sim,root,_=project;target=destination(root)
    settings={'interpreter':'/missing/python','cwd':'absent','arguments':[], 'output_dir':'outputs'}
    with store.connection() as c:
        sim['execution']=settings;c.execute('UPDATE simulations SET data=? WHERE id=?',(json_text(sim),sim['id']))
    review=preview(store,sim['id'],str(target));assert review['warnings']
    result=relocate(store,sim['id'],review,True);assert result['execution']==settings
    from simshelf.portal import execution_settings
    with pytest.raises(ValueError):execution_settings(result,settings,probe=True)


def test_transaction_rolls_back_registration_and_consent(project):
    store,sim,root,_=project;target=destination(root)
    archive.put(store,'settings:'+sim['id'],{'example':'consent'})
    review=preview(store,sim['id'],str(target))
    with store.connection() as c:
        c.execute("CREATE TRIGGER fail_relocation BEFORE DELETE ON metadata BEGIN SELECT RAISE(ABORT, 'injected'); END")
    with pytest.raises(sqlite3.IntegrityError):relocate(store,sim['id'],review,True)
    assert store.simulation(sim['id'])==sim
    assert archive.get(store,'settings:'+sim['id'])=={'example':'consent'}


def test_api_preview_confirmation_and_origin_protection(project):
    store,sim,root,_=project;target=destination(root)
    with TestClient(create_app(store.path)) as c:
        url=f'/api/simulations/{sim["id"]}/relocation'
        assert c.post(url+'/preview',json={'path':str(target)}).status_code==403
        headers={'X-SimShelf-Token':c.get('/api/workspace').json()['token']}
        assert c.post(url+'/preview',json={'path':str(target)},headers={**headers,'Origin':'https://elsewhere.invalid'}).status_code==403
        response=c.post(url+'/preview',json={'path':str(target)},headers=headers);assert response.status_code==200
        review=response.json()
        assert c.post(url,json={'review':review},headers=headers).status_code==400
        assert c.post(url,json={'review':review,'confirmed':True},headers=headers).status_code==200
        assert c.post(url,json={'review':review,'confirmed':True},headers=headers).status_code==400


def test_git_consent_invalidated_history_downloads_and_master_preserved(project,tmp_path):
    store,sim,root,_=project
    repo=tmp_path/'archive';repo.mkdir();archive.connect(store,str(repo),True,True)
    inv=inventory(store,sim['id']);save_selection(store,sim['id'],selection_preview(store,sim['id'],inv['revision'],[{'kind':'file','value':'field.py'}]))
    archive.enable(store,sim['id'],archive.settings_preview(store,sim['id'],[]),True)
    with store.connection() as c:
        c.execute('INSERT INTO metadata VALUES (?,?)',('git_connection_v1',json_text({'mappings':{sim['id']:'.','other':'other'},'root':str(root)})))
    with Run(sim['id'],workspace=store.path,capture_console=False) as run:pass
    event,=archive.entries(store,run.id)
    downloaded=archive.download(store,run.id,event['id'],0)
    connection=archive.get(store,'connection');history=historical_bytes(store)
    target=destination(root);relocate(store,sim['id'],preview(store,sim['id'],str(target)),True)
    assert archive.get(store,'connection')==connection
    assert archive.get(store,'settings:'+sim['id']) is None
    assert inventory(store,sim['id'])['rules']==[]
    assert archive.entries(store,run.id)==[event]
    assert archive.download(store,run.id,event['id'],0)==downloaded
    assert historical_bytes(store)==history
    with store.connection() as c:
        assert json.loads(c.execute("SELECT value FROM metadata WHERE key='git_connection_v1'").fetchone()[0])['mappings']=={'other':'other'}
    relocate(store,sim['id'],preview(store,sim['id'],str(root)),True)
    assert archive.get(store,'settings:'+sim['id']) is None
    assert inventory(store,sim['id'])['rules']==[]


def test_pending_portal_supervisor_rejects_changed_source(project, monkeypatch):
    from simshelf import portal
    store,sim,root,_=project;target=destination(root)
    original=portal.execution_settings
    def validated_then_relocated(simulation, settings, **kwargs):
        plan=original(simulation,settings,**kwargs)
        relocate(store,sim['id'],preview(store,sim['id'],str(target)),True)
        return plan
    monkeypatch.setattr(portal,'execution_settings',validated_then_relocated)
    jobs=portal.PortalJobs(store)
    try:
        with pytest.raises(ValueError,match='location changed'):
            jobs.start(sim['id'],{'interpreter':sys.executable,'cwd':'.','arguments':[],'output_dir':'outputs'},None)
        assert store.runs()==[]
    finally:jobs.close()


def test_fresh_launch_uses_new_source_without_touching_old(project):
    store,sim,root,source=project;target=destination(root)
    (target/'field.py').write_text('SIMSHELF_VERSION="2.0"\nprint("new location")\n')
    old=source.read_bytes()
    relocate(store,sim['id'],preview(store,sim['id'],str(target)),True)
    from simshelf.portal import PortalJobs
    import time
    jobs=PortalJobs(store)
    try:
        result=jobs.start(sim['id'],{'interpreter':sys.executable,'cwd':'.','arguments':[],'output_dir':'outputs'},None)
        ident=result['run_id']
        for _ in range(100):
            run=store.run(ident)
            if run['status']!='running':break
            time.sleep(.05)
        assert run['status']=='completed' and run['version']=='2.0'
        assert run['command'][1]==str(target/'field.py') and run['cwd']==str(target)
        assert run['capture_root']==str(target/'outputs')
        assert source.read_bytes()==old
    finally:jobs.close()


@pytest.mark.parametrize('value',['../field.py','/tmp/field.py','.'])
def test_unsafe_registered_relative_file_is_rejected(project,value):
    store,sim,root,_=project;target=destination(root)
    with store.connection() as c:
        sim['entrypoint']=value;c.execute('UPDATE simulations SET data=? WHERE id=?',(json_text(sim),sim['id']))
    with pytest.raises(ValueError):preview(store,sim['id'],str(target))
    assert store.simulation(sim['id'])==sim


def test_unrelated_active_run_does_not_block_and_review_is_invalidated_by_consent(project,tmp_path):
    store,sim,root,_=project;target=destination(root)
    other=tmp_path/'other';other.mkdir();(other/'sim.py').write_text('pass')
    another=store.add_simulation(other)
    with Run(another['id'],workspace=store.path,capture_console=False):
        review=preview(store,sim['id'],str(target))
        archive.put(store,'settings:'+sim['id'],{'changed':True})
        with pytest.raises(ValueError,match='changed'):relocate(store,sim['id'],review,True)
        relocate(store,sim['id'],preview(store,sim['id'],str(target)),True)
    assert store.simulation(another['id'])==another


def test_relocation_preserves_separation_from_master_archive(project):
    store,sim,root,_=project;target=destination(root)
    archive.put(store,'connection',{'path':str(target),'identity':'not consulted'})
    with pytest.raises(ValueError,match='master archive'):preview(store,sim['id'],str(target))
    assert store.simulation(sim['id'])==sim
