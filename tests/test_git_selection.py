import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from simshelf.api import create_app
from simshelf.git_selection import inventory, selection_preview, save_selection, ignore_preview, apply_ignore
from simshelf.recording import Run
from simshelf.backup import create_backup, restore_backup
from simshelf.store import Store
from test_git_provenance import project, command, link


def add_files(root):
    source = root / 'alpha'
    for name in ('config.json', 'checkpoint.npz', 'metrics.csv'):
        (source / name).write_text('scientific input or result\n')
    (source / 'output').mkdir(); (source / 'output/result.csv').write_text('original\n')
    return source


def bytes_tree(root):
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file() and not p.is_symlink()}


def test_read_only_selection_and_preferences_not_git_state(project):
    store, root, sims = project; source = add_files(root); before = bytes_tree(root)
    view = inventory(store, sims[0]['id']); assert view['rules'] == []
    assert {f['path']: f['state'] for f in view['files']}['sim.py'] == 'tracked'
    rules = [{'kind':'extension','value':'.csv'}, {'kind':'folder','value':'output'}, {'kind':'file','value':'config.json'}]
    review = selection_preview(store,sims[0]['id'],view['revision'],rules)
    assert set(review['selected']) == {'metrics.csv','output/result.csv','config.json'}
    assert review['matches'][0]['paths'] == ['metrics.csv','output/result.csv']
    assert bytes_tree(root) == before  # preview/cancel has no source/index/history writes
    save_selection(store,sims[0]['id'],review)
    view = inventory(store,sims[0]['id']); assert view['rules'] == rules
    assert bytes_tree(root) == before
    save_selection(store,sims[0]['id'],selection_preview(store,sims[0]['id'],view['revision'],[]))
    assert 'alpha/sim.py' in command(root,'ls-files')  # unchecked tracked path stays tracked
    assert bytes_tree(root) == before


def test_ignore_exact_paths_existing_bytes_and_no_git_writes(project):
    store, root, sims = project; source = add_files(root)
    (source / '.gitignore').write_bytes(b'# Authored\r\nkeep-this\r\n')
    (source / 'literal [*] #!.csv').write_text('input')
    before = bytes_tree(root)
    view = inventory(store,sims[0]['id'])
    review = ignore_preview(store,sims[0]['id'],view['revision'],['output/result.csv','literal [*] #!.csv'])
    assert review['addition'] == '/literal\\ \\[\\*\\]\\ \\#\\!.csv\r\n/output/result.csv\r\n'
    assert bytes_tree(root) == before
    apply_ignore(store,sims[0]['id'],review)
    after = bytes_tree(root); changed = {k for k in after if before.get(k) != after[k]}
    assert changed == {'alpha/.gitignore'}
    assert after['alpha/.gitignore'] == before['alpha/.gitignore'] + review['addition'].encode()
    states = {f['path']: f['state'] for f in inventory(store,sims[0]['id'])['files']}
    assert states['output/result.csv'] == states['literal [*] #!.csv'] == 'ignored'
    assert states['metrics.csv'] == 'untracked'
    with pytest.raises(ValueError): apply_ignore(store,sims[0]['id'],review)


def test_nested_rules_shared_repo_and_nested_repo(project):
    store, root, sims = project; source = add_files(root)
    (root / '.gitignore').write_text('*.npz\nalpha/sim.py\n')
    (source / 'output/.gitignore').write_text('*.csv\n!result.csv\n')
    nested = source / 'independent'; nested.mkdir(); command(nested,'init'); (nested/'secret.py').write_text('secret')
    view = inventory(store,sims[0]['id']); states = {f['path']: f for f in view['files']}
    assert states['sim.py']['state'] == 'tracked' and states['sim.py']['ignored_rule']
    assert states['checkpoint.npz']['state'] == 'ignored'
    assert states['output/result.csv']['state'] == 'untracked'
    assert 'independent/secret.py' not in states and not any('beta' in p for p in states)
    assert any(r['path'] == str(root / '.gitignore') for r in view['ignore_files'])
    for path in ['output/result.csv','../beta/sim.py','sim.py','checkpoint.npz']:
        with pytest.raises(ValueError): ignore_preview(store,sims[0]['id'],view['revision'],[path])


@pytest.mark.parametrize('change', ['source','ignore','index','preferences','symlink','root'])
def test_stale_reviews_rejected(project, change, tmp_path):
    store, root, sims = project; source = add_files(root)
    view = inventory(store,sims[0]['id'])
    review = ignore_preview(store,sims[0]['id'],view['revision'],['metrics.csv'])
    if change == 'source': (source / 'metrics.csv').write_text('changed scientific bytes')
    elif change == 'ignore': (source / '.gitignore').write_text('# concurrent edit')
    elif change == 'index': command(root,'add','alpha/metrics.csv')
    elif change == 'preferences': save_selection(store,sims[0]['id'],selection_preview(store,sims[0]['id'],view['revision'],[{'kind':'file','value':'sim.py'}]))
    elif change == 'symlink': (source / '.gitignore').symlink_to(root / '.gitignore')
    else:
        source.rename(root / 'moved'); source.symlink_to(root / 'moved',target_is_directory=True)
    before = bytes_tree(root)
    with pytest.raises(ValueError): apply_ignore(store,sims[0]['id'],review)
    assert bytes_tree(root) == before


def test_missing_git_no_repo_limits_and_unsafe_files(project, monkeypatch, tmp_path):
    store, root, sims = project; source = add_files(root)
    (source/'link').symlink_to(tmp_path/'outside')
    os.link(source/'config.json',source/'hardlink')
    os.mkfifo(source/'fifo')
    (source/'line\nbreak').write_text('not displayed')
    monkeypatch.setenv('PATH','')
    view = inventory(store,sims[0]['id']); assert not view['ignore_writable']
    assert len(view['blocked']) == 5
    assert all(f['state'] == 'unknown' for f in view['files'])
    review = selection_preview(store,sims[0]['id'],view['revision'],[{'kind':'extension','value':'.py'}])
    save_selection(store,sims[0]['id'],review)
    monkeypatch.setattr('simshelf.git_selection.MAX_ENTRIES',2)
    with pytest.raises(ValueError,match='1,000'): inventory(store,sims[0]['id'])
    monkeypatch.undo()
    # Isolate host ancestor markers: this machine has an unrelated /tmp/.git.
    original = os.path.lexists
    monkeypatch.setattr('simshelf.git_selection.os.path.lexists',lambda p: False if str(p).endswith('/.git') else original(p))
    assert inventory(store,sims[0]['id'])['repository'] is None


def test_permissions_and_large_ignore_decline_without_writes(project, monkeypatch):
    store, root, sims = project; source = add_files(root)
    (source/'.gitignore').write_bytes(b'x' * 65537)
    with pytest.raises(ValueError): inventory(store,sims[0]['id'])
    (source/'.gitignore').unlink()
    original = os.scandir
    def denied(path): raise PermissionError('denied')
    monkeypatch.setattr('simshelf.git_selection.os.scandir',denied)
    with pytest.raises(ValueError, match='permissions'): inventory(store,sims[0]['id'])


def test_api_consent_provenance_backup_and_no_migration(project, tmp_path):
    store, root, sims = project; source = add_files(root); link(project)
    with Run(sims[0]['id'],workspace=store.path,capture_console=False) as run: run.metric('energy',4)
    original = store.run(run.id)
    with store.connection() as conn: schema = conn.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()[0]
    with TestClient(create_app(store.path)) as client:
        base = '/api/simulations/' + sims[0]['id'] + '/git'
        view = client.get(base+'/files').json()
        request = {'revision':view['revision'],'rules':[{'kind':'file','value':'sim.py'}]}
        assert client.post(base+'/files/preview',json=request).status_code == 403
        client.headers['X-SimShelf-Token'] = client.get('/api/workspace').json()['token']
        preview = client.post(base+'/files/preview',json=request).json()
        assert client.post(base+'/files/save',json={'review':preview}).status_code == 400
        assert client.post(base+'/files/save',json={'review':preview,'confirmed':True}).status_code == 200
        view = client.get(base+'/files').json()
        preview = client.post(base+'/ignore/preview',json={'revision':view['revision'],'paths':['metrics.csv']}).json()
        assert client.post(base+'/ignore/apply',json={'review':preview}).status_code == 400
        assert client.post(base+'/ignore/apply',json={'review':preview,'confirmed':True}).status_code == 200
    assert store.run(run.id) == original
    with store.connection() as conn: assert conn.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()[0] == schema
    archive = tmp_path/'saved.zip'; create_backup(store,archive)
    restored = tmp_path/'restored'; restore_backup(archive,restored)
    other = Store(restored)
    assert other.run(run.id)['git'] == original['git']
    assert inventory(other,sims[0]['id'])['rules'] == []  # moved library needs new review


@pytest.mark.parametrize('rule',[{'kind':'file','value':'../escape'}, {'kind':'extension','value':'*'}, {'kind':'file','value':'.git/config'}, {'kind':'file','value':'/absolute'}, {'kind':'folder','value':'a//b'}])
def test_untrusted_rules_declined(project,rule):
    store, root, sims = project; v = inventory(store,sims[0]['id'])
    with pytest.raises(ValueError): selection_preview(store,sims[0]['id'],v['revision'],[rule])


def test_worktree_large_files_and_hooks_are_inert(project, tmp_path):
    store, root, sims = project
    worktree = tmp_path/'worktree'; command(root,'worktree','add','-b','other',str(worktree))
    sim = store.add_simulation(worktree/'alpha',entrypoint='sim.py',name='Linked worktree')
    large = worktree/'alpha/data.npz'
    with large.open('wb') as stream: stream.truncate(11 * 1024 * 1024)
    marker = tmp_path/'hook-ran'
    hook = root/'.git/hooks/post-index-change'; hook.write_text(f'#!/bin/sh\ntouch {marker}\n'); hook.chmod(0o755)
    command(root,'config','core.fsmonitor',f'touch {marker}')
    before = bytes_tree(root)
    v = inventory(store,sim['id'])
    assert v['repository']['root'] == str(worktree)
    assert next(f for f in v['files'] if f['path']=='data.npz')['risk'].startswith('Large file')
    review = ignore_preview(store,sim['id'],v['revision'],['data.npz'])
    apply_ignore(store,sim['id'],review)
    assert not marker.exists() and bytes_tree(root) == before
    assert command(worktree,'ls-files','alpha/data.npz') == ''


def test_target_replacement_race_refused(project, monkeypatch):
    store, root, sims = project; source = add_files(root)
    (source/'.gitignore').write_text('# original\n')
    v = inventory(store,sims[0]['id'])
    review = ignore_preview(store,sims[0]['id'],v['revision'],['metrics.csv'])
    original_open = os.open
    def replace(path, flags, *args, **kwargs):
        if path == '.gitignore' and flags & os.O_WRONLY:
            (source/'.gitignore').unlink()
            (source/'.gitignore').symlink_to(root/'.gitignore')
        return original_open(path,flags,*args,**kwargs)
    monkeypatch.setattr('simshelf.git_selection.os.open',replace)
    authored = (root/'.gitignore').read_bytes()
    with pytest.raises(ValueError): apply_ignore(store,sims[0]['id'],review)
    assert (root/'.gitignore').read_bytes() == authored
