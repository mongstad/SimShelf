import json
import os
from pathlib import Path
import subprocess

import pytest

from simshelf.store import Store
from simshelf.recording import Run
from simshelf.source import source_snapshot
from simshelf.git_provenance import (preview, connect_repository, disconnect_repository,
                                    observe, connection, git, Unavailable)
from simshelf.backup import create_backup, restore_backup


def command(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.DEVNULL).decode().strip()


@pytest.fixture
def project(tmp_path):
    root = tmp_path / 'repo'; root.mkdir()
    command(root, 'init', '-b', 'main')
    command(root, 'config', 'user.name', 'Test'); command(root, 'config', 'user.email', 'test@example.invalid')
    for folder in ['alpha', 'beta']:
        (root / folder).mkdir(); (root / folder / 'sim.py').write_text('SIMSHELF_VERSION = "science-1"\nx = 1\n')
    (root / '.gitignore').write_text('ignored\n')
    command(root, 'add', '.'); command(root, 'commit', '-m', 'Initial sources')
    store = Store(tmp_path / 'library')
    sims = [store.add_simulation(root / folder, entrypoint='sim.py') for folder in ['alpha','beta']]
    return store, root, sims


def link(project):
    store, root, sims = project
    proposed = preview(store, str(root), [s['id'] for s in sims])
    connect_repository(store, proposed)
    return proposed


def test_disabled_missing_git_and_unmapped(project, monkeypatch):
    store, root, sims = project
    monkeypatch.setenv('PATH', '')
    assert observe(store, sims[0])['availability'] == 'disabled'
    with Run(sims[0]['id'], workspace=store.path, capture_console=False) as r: pass
    assert store.run(r.id)['git']['availability'] == 'disabled'
    monkeypatch.undo(); link(project); monkeypatch.setenv('PATH', '')
    view = observe(store, sims[0]); assert view['availability'] == 'unavailable' and view['dirty'] is None
    with Run(sims[0]['id'], workspace=store.path, capture_console=False) as r: pass
    assert store.run(r.id)['status'] == 'completed'
    monkeypatch.undo()
    outsider = root.parent/'outside'; outsider.mkdir(); (outsider/'sim.py').write_text('x=1')
    sim = store.add_simulation(outsider, entrypoint='sim.py')
    assert observe(store, sim)['availability'] == 'unmapped'


def test_mapping_history_and_snapshot_truth(project):
    store, root, sims = project; link(project)
    snap = source_snapshot(store.path, sims[0]); v = observe(store, sims[0], snap, history=True)
    assert v['availability'] == 'available' and v['dirty'] is False
    assert v['subdirectory'] == 'alpha' and v['branch'] == 'main'
    assert v['snapshot_relation'] == 'captured_files_match_commit'
    assert len(v['history']) == 1
    (root/'beta/sim.py').write_text('x=2')
    v = observe(store, sims[0], snap)
    assert v['dirty'] is True and v['simulation_dirty'] is False
    assert v['snapshot_relation'] == 'captured_files_match_commit'
    (root/'alpha/sim.py').write_text('x=3')
    snap = source_snapshot(store.path, sims[0]); v = observe(store, sims[0], snap)
    assert v['simulation_dirty'] is True and v['snapshot_relation'] == 'captured_files_differ'
    (root/'ignored').write_text('ignored')
    (root/'alpha/new.py').write_text('x=4')
    assert observe(store,sims[0])['untracked_count'] == 1
    command(root,'add','.'); command(root,'commit','-m','Changed sources')
    command(root,'checkout','--detach')
    assert observe(store,sims[0])['branch'] is None


def test_no_hooks_filters_fsmonitor_transport_or_inherited_git(project, tmp_path, monkeypatch):
    store, root, sims = project; link(project)
    marker = tmp_path/'EXECUTED'
    hook = root/'.git/hooks/post-index-change'; hook.write_text(f'#!/bin/sh\ntouch {marker}\n'); hook.chmod(0o755)
    command(root,'config','core.fsmonitor',f'touch {marker}')
    command(root,'config','filter.evil.clean',f'touch {marker}')
    (root/'.gitattributes').write_text('*.py filter=evil\n')
    monkeypatch.setenv('GIT_CONFIG_COUNT','1'); monkeypatch.setenv('GIT_CONFIG_KEY_0','core.fsmonitor'); monkeypatch.setenv('GIT_CONFIG_VALUE_0',f'touch {marker}')
    monkeypatch.setenv('GIT_DIR',str(tmp_path/'wrong'))
    (root/'alpha/sim.py').write_text('changed')
    assert observe(store,sims[0],history=True)['availability'] == 'available'
    assert not marker.exists()
    assert not (root/'.git/index.lock').exists()


def test_paths_stale_previews_disconnect_restore_and_immutable_runs(project, tmp_path):
    store, root, sims = project
    with pytest.raises(ValueError): preview(store, str(tmp_path), [sims[0]['id']])
    proposed = preview(store,str(root),[sims[0]['id']])
    proposed['mappings'][sims[0]['id']] = '../elsewhere'
    with pytest.raises(ValueError): connect_repository(store,proposed)
    link(project)
    with Run(sims[0]['id'],workspace=store.path,capture_console=False) as r:
        r.metric('energy', 2)
    before = store.run(r.id)
    backup = create_backup(store,tmp_path/'backup.zip')
    restored = restore_backup(backup,tmp_path/'restored')
    assert observe(restored,restored.simulation(sims[0]['id']))['availability'] == 'unavailable'
    assert restored.run(r.id)['git'] == before['git']
    disconnect_repository(store)
    assert connection(store) is None and store.run(r.id) == before
    with store.connection() as conn:
        assert conn.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()[0] == '1'
    assert (root/'alpha/sim.py').exists()


@pytest.mark.parametrize('remote_style', ['path','file'])
def test_remote_configuration_is_irrelevant_and_offline(project, tmp_path, remote_style):
    store, root, sims = project
    remote = tmp_path/'remote.git'; subprocess.run(['git','init','--bare',str(remote)],check=True,capture_output=True)
    command(root,'remote','add','origin',str(remote) if remote_style=='path' else remote.as_uri())
    link(project)
    assert observe(store,sims[0],history=True)['availability'] == 'available'
    command(root,'remote','set-url','origin','https://invalid.example/private/repo.git')
    assert observe(store,sims[0],history=True)['availability'] == 'available'
    assert not (root/'.git/FETCH_HEAD').exists()


def test_nested_repository_symlink_and_unborn(project, tmp_path):
    store, root, sims = project
    command(root/'alpha','init')
    with pytest.raises(ValueError): preview(store,str(root),[sims[0]['id']])
    proposed = preview(store,str(root),[sims[1]['id']]); connect_repository(store,proposed)
    (root/'beta/link').symlink_to(tmp_path/'outside')
    assert observe(store,sims[1])['dirty'] is True
    disconnect_repository(store)
    empty = tmp_path/'empty'; empty.mkdir(); command(empty,'init')
    (empty/'sim.py').write_text('x=1'); sim=store.add_simulation(empty,entrypoint='sim.py')
    connect_repository(store,preview(store,str(empty),[sim['id']]))
    assert observe(store,sim)['availability'] == 'unavailable'
    with Run(sim['id'],workspace=store.path,capture_console=False) as r: pass
    assert store.run(r.id)['status'] == 'completed'


def test_api_confirmation_and_same_origin(project):
    from simshelf.api import create_app
    from fastapi.testclient import TestClient
    store, root, sims = project
    with TestClient(create_app(store.path)) as client:
        token=client.get('/api/workspace').json()['token']
        assert client.post('/api/workspace/git/preview',json={'path':str(root),'simulation_ids':[sims[0]['id']]}).status_code == 403
        headers={'x-simshelf-token':token}
        proposed=client.post('/api/workspace/git/preview',headers=headers,json={'path':str(root),'simulation_ids':[sims[0]['id']]}).json()
        assert client.post('/api/workspace/git/connect',headers=headers,json={'preview':proposed}).status_code == 400
        assert client.post('/api/workspace/git/connect',headers=headers,json={'preview':proposed,'confirmed':True}).status_code == 200
        assert client.get(f"/api/simulations/{sims[0]['id']}/git").json()['availability']=='available'
        assert client.post('/api/workspace/git/disconnect',headers={**headers,'origin':'https://evil.invalid'}).status_code==403
        assert client.post('/api/workspace/git/disconnect',headers=headers).status_code==200


def test_failures_never_become_clean_or_block_recording(project, monkeypatch):
    import simshelf.git_provenance as provenance
    store, root, sims = project; link(project)
    real = provenance.git
    def failing(root,*args):
        if args[0]=='ls-files': raise Unavailable('Injected inspection failure')
        return real(root,*args)
    monkeypatch.setattr(provenance,'git',failing)
    v=observe(store,sims[0]);assert v['availability']=='unavailable' and v['dirty'] is None
    with Run(sims[0]['id'],workspace=store.path,capture_console=False) as r: pass
    assert store.run(r.id)['status']=='completed'
    with store.connection() as conn:conn.execute('UPDATE metadata SET value=? WHERE key=?',('bad json',provenance.KEY))
    assert observe(store,sims[0])['availability']=='unavailable'


def test_bounded_output_and_safe_symlink_read(project, tmp_path, monkeypatch):
    import simshelf.git_provenance as provenance
    store,root,sims=project;link(project)
    outside=tmp_path/'external';outside.mkdir();(outside/'secret').write_text('private')
    (root/'link').symlink_to(outside,target_is_directory=True)
    with pytest.raises(OSError):provenance.read_worktree_file(root,'link/secret')
    with pytest.raises(Unavailable):provenance.read_worktree_file(root,'../external/secret')
    monkeypatch.setattr(provenance,'LIMIT',8)
    with pytest.raises(Unavailable):git(root,'rev-parse','HEAD')


def test_conflict_worktree_and_repository_identity_change(project,tmp_path):
    store,root,sims=project;link(project)
    command(root,'checkout','-b','other');(root/'alpha/sim.py').write_text('other')
    command(root,'commit','-am','other')
    command(root,'checkout','main');(root/'alpha/sim.py').write_text('main')
    command(root,'commit','-am','main')
    subprocess.run(['git','-C',str(root),'merge','other'],capture_output=True)
    v=observe(store,sims[0]);assert v['conflicts'] and v['dirty']
    command(root,'merge','--abort')  # Disposable fixture cleanup, never product behavior.
    worktree=tmp_path/'worktree';command(root,'worktree','add',str(worktree),'-b','linked')
    other_store=Store(tmp_path/'other-library');sim=other_store.add_simulation(worktree/'alpha',entrypoint='sim.py')
    connect_repository(other_store,preview(other_store,str(worktree),[sim['id']]))
    assert observe(other_store,sim)['branch']=='linked'
    (root/'.git').rename(root/'.old-git');command(root,'init')
    assert observe(store,sims[0])['availability']=='unavailable'


def test_timeout_is_bounded_and_unknown(project,tmp_path,monkeypatch):
    import time
    import simshelf.git_provenance as provenance
    fake=tmp_path/'git';fake.write_text('#!/bin/sh\nsleep 30\n');fake.chmod(0o755)
    monkeypatch.setattr(provenance.shutil,'which',lambda _:str(fake))
    start=time.monotonic()
    with pytest.raises(Unavailable,match='timed out'):git(project[1],'rev-parse','HEAD')
    assert time.monotonic()-start < 6


def test_ignored_capture_and_filter_bytes_never_claim_commit_equivalence(project):
    store,root,sims=project;link(project)
    (root/'alpha/local.py').write_text('scientific_input = 42\n')
    (root/'.git/info/exclude').write_text('alpha/local.py\n')
    snap=source_snapshot(store.path,sims[0]);v=observe(store,sims[0],snap)
    assert v['dirty'] is False and v['snapshot_relation']=='captured_files_differ'
    (root/'alpha/sim.py').write_bytes(b'SIMSHELF_VERSION = "science-1"\r\nx = 1\r\n')
    assert observe(store,sims[0])['simulation_dirty'] is True


def test_mapping_confirmation_revalidates_registration(project,tmp_path):
    store,root,sims=project
    proposed=preview(store,str(root),[sims[0]['id']])
    with store.connection() as conn:
        changed=dict(sims[0],root=str(root/'beta'))
        conn.execute('UPDATE simulations SET data=? WHERE id=?',(json.dumps(changed),sims[0]['id']))
    with pytest.raises(ValueError,match='changed'):connect_repository(store,proposed)
    assert connection(store) is None
    for bad in [{},{'root':4,'mappings':[]},{'root':str(root),'mappings':{'alpha':None}}]:
        with pytest.raises(ValueError):connect_repository(store,bad)


def test_sha256_repository_snapshot_relation(tmp_path):
    root=tmp_path/'sha256';root.mkdir()
    command(root,'init','--object-format=sha256','-b','main')
    command(root,'config','user.name','Test');command(root,'config','user.email','test@example.invalid')
    (root/'sim.py').write_text('x=1\n');command(root,'add','.');command(root,'commit','-m','Source')
    store=Store(tmp_path/'library');sim=store.add_simulation(root,entrypoint='sim.py')
    connect_repository(store,preview(store,str(root),[sim['id']]))
    result=observe(store,sim,source_snapshot(store.path,sim))
    assert len(result['commit'])==64 and result['snapshot_relation']=='captured_files_match_commit'
