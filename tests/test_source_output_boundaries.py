"""Known output parents are boundaries, regardless of run names or contents."""
import json
from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient

from simshelf.api import create_app
from simshelf.backup import create_backup, restore_backup
from simshelf.recording import Run, record_command
from simshelf.source import blob_path, source_snapshot
from simshelf.store import Store
from test_portal import finish, headers, settings

SCRIPT = '''import json, os, shutil, uuid
from pathlib import Path
base = Path(os.environ["SIMSHELF_OUTPUT_DIR"])
out = base if os.environ["SIMSHELF_OUTPUT_POLICY"] == "per_run" else base / ("run_" + uuid.uuid4().hex)
out.mkdir(parents=True, exist_ok=True)
shutil.copyfile(__file__, out / "model.py")
(out / "summary.json").write_text(json.dumps({"run": out.name}))
(out / "timestamp-version.log").write_text("closed fixture log")
'''
HEADER = '[swss]\nschema_version=2\nentrypoint="model.py"\nsimulation_version="0.3.1"\n'


def fixture(tmp_path, swss, parent):
    root = tmp_path/'source'; root.mkdir()
    source = root/'model.py'
    source.write_text('SIMSHELF_VERSION="0.3.1"\n' + SCRIPT)
    (root/'helper.py').write_text('value = 7\n')
    (root/'input.json').write_text('{"real_input": 1}')
    if swss:
        (root/'swss.toml').write_text(HEADER + f'\n[extensions.simshelf]\nschema_version=1\n[extensions.simshelf.capture]\noutput_dir="{parent}"\n')
    store = Store(tmp_path/'library')
    sim = store.add_simulation(root, entrypoint='model.py', config=None if swss else {'output_dir': parent, 'source_exclude': []})
    old = root/parent/'arbitrary-old-folder'/'nested'
    old.mkdir(parents=True)
    (old/'model.py').write_bytes(source.read_bytes())
    (old/'summary.json').write_text('{"old_output": true}')
    # Too large for source capture if exclusion is applied after reading.
    with (old/'large.json').open('wb') as stream:
        stream.truncate(33 * 1024 * 1024)
    return root, source, store, sim


@pytest.mark.parametrize('swss,policy', [(False,'fixed'), (False,'per_run'), (True,'fixed')])
@pytest.mark.parametrize('parent', ['research_results', 'nested/generated/results'])
@pytest.mark.parametrize('override', [False, True])
def test_successive_recordings_prune_parent_before_reads_and_keep_output_capture(tmp_path, monkeypatch, swss, policy, parent, override):
    root, source, store, sim = fixture(tmp_path, swss, parent)
    original = source.read_bytes()
    import simshelf.source as module
    stable = module.stable_bytes
    reads = []
    def checked(path, *args):
        reads.append(path.relative_to(root).as_posix())
        assert not path.is_relative_to(root/parent), 'generated output reached source reader'
        return stable(path, *args)
    monkeypatch.setattr(module, 'stable_bytes', checked)
    records = []
    for _ in range(2):
        ident, code = record_command(store, sim['id'], [sys.executable, str(source), '--seed', '007', ''],
            cwd=root, quiet=True, output_policy=policy, output_dir=f'{parent}/current' if override else None)
        assert code == 0
        result = store.run(ident); records.append(result)
        assert result['capture_status'] == 'complete'
        assert {a['name'].split('/')[-1] for a in result['artifacts']} == {'model.py','summary.json','timestamp-version.log'}
        assert result['command'][2:] == ['--seed','007','']
        assert all(not f['path'].startswith(parent + '/') for f in result['snapshot']['files'])
        assert {f['path'] for f in result['snapshot']['files']} == {'model.py','helper.py','input.json', *({'swss.toml'} if swss else set())}
    assert records[0]['source_change'] == 'baseline' and records[1]['source_change'] == 'same'
    assert records[0]['snapshot_id'] == records[1]['snapshot_id']
    assert records[0]['structure_id'] == records[1]['structure_id']
    assert source.read_bytes() == original
    assert (root/parent/'arbitrary-old-folder/nested/summary.json').read_text() == '{"old_output": true}'
    assert store.run(records[0]['id']) == records[0]


def test_portal_override_repeated_swss_runs_and_source_file_downloads(tmp_path):
    root, source, store, sim = fixture(tmp_path, True, 'results')
    original_sim = store.simulation(sim['id'])
    with TestClient(create_app(store.path)) as client:
        auth = headers(client)
        data = settings(output_dir='results/current')
        results = []
        for _ in range(2):
            response = client.post(f"/api/simulations/{sim['id']}/launch", headers=auth, json=data)
            assert response.status_code == 201, response.text
            results.append(finish(store, response.json()['run_id']))
        assert results[1]['source_change'] == 'same'
        assert results[0]['snapshot_id'] == results[1]['snapshot_id']
        assert client.get(f"/api/runs/{results[1]['id']}/source", params={'path':'model.py','compare':results[0]['id']}).json()['text'] == 'No changes in this file.'
    assert store.simulation(sim['id']) == original_sim


def test_current_local_declaration_and_saved_output_root_apply_without_mutating_preferences(tmp_path):
    root, source, store, sim = fixture(tmp_path, False, 'registered_outputs')
    # Companion adoption after registration does not migrate deliberate settings.
    (root/'swss.toml').write_text(HEADER + '\n[extensions.simshelf]\nschema_version=1\n[extensions.simshelf.capture]\noutput_dir="declared_outputs"\n')
    store.update_simulation(sim['id'], execution=settings(output_dir='saved_outputs'))
    for folder in ('declared_outputs', 'saved_outputs', 'override_outputs'):
        (root/folder).mkdir()
        (root/folder/'generated.json').write_text('{"output":true}')
    before = store.simulation(sim['id'])
    with Run(sim['id'], workspace=store.path, output_dir='override_outputs', capture_console=False) as run:
        paths = {f['path'] for f in store.run(run.id)['snapshot']['files']}
    assert paths == {'model.py','helper.py','input.json','swss.toml'}
    assert store.simulation(sim['id']) == before
    for folder in ('declared_outputs', 'saved_outputs', 'override_outputs'):
        assert (root/folder/'generated.json').read_text() == '{"output":true}'


def test_legitimate_selected_source_changes_and_python_comments_remain_detectable(tmp_path):
    root, source, store, sim = fixture(tmp_path, True, 'results')
    # A folder called run_* outside declared output remains legitimate source.
    (root/'run_research').mkdir()
    helper = root/'run_research'/'helper.py'; helper.write_text('value=1\n')
    def record():
        with Run(sim['id'], workspace=store.path, capture_console=False) as run: pass
        return store.run(run.id)
    first = record()
    helper.write_text('value=1  # comment-only change\n')
    comment = record()
    assert comment['source_change'] == 'text-only'
    assert first['structure_id'] == comment['structure_id']
    helper.write_text('value=2\n')
    assert record()['source_change'] == 'changed'
    helper.write_text('value=1\n')
    (root/'input.json').write_text('{"real_input": 2}')
    data_change = record()
    assert data_change['source_change'] == 'changed'
    assert next(f['blob'] for f in data_change['snapshot']['files'] if f['path']=='model.py') == next(f['blob'] for f in first['snapshot']['files'] if f['path']=='model.py')


@pytest.mark.parametrize('target', ['root', 'outside'])
def test_unsafe_output_alias_refused_without_capturing_or_deleting_data(tmp_path, target):
    root, source, store, sim = fixture(tmp_path, False, 'results')
    outside = tmp_path/'outside'; outside.mkdir()
    (outside/'keep.json').write_text('untouched')
    (root/'alias').symlink_to(root if target=='root' else outside, target_is_directory=True)
    with pytest.raises(ValueError, match='simulation root|registered folder'):
        with Run(sim['id'], workspace=store.path, output_dir='alias', capture_console=False): pass
    assert not store.runs()
    assert (outside/'keep.json').read_text() == 'untouched'


def test_internal_canonical_output_alias_prunes_real_tree_not_other_source(tmp_path):
    root, source, store, sim = fixture(tmp_path, False, 'real_outputs')
    (root/'real_outputs_notes').mkdir()
    (root/'real_outputs_notes/input.json').write_text('{"legitimate":1}')
    (root/'alias').symlink_to(root/'real_outputs', target_is_directory=True)
    sim = {**sim, 'config': {**sim['config'], 'output_dir':'alias'}}
    snap = source_snapshot(store.path, sim)
    assert {f['path'] for f in snap['files']} == {'model.py','helper.py','input.json','real_outputs_notes/input.json'}


def test_historical_snapshot_rows_blobs_and_backups_are_not_rewritten(tmp_path):
    root = tmp_path/'source'; root.mkdir()
    (root/'model.py').write_text('SIMSHELF_VERSION="1.0"\n')
    (root/'research_results').mkdir()
    (root/'research_results/summary.json').write_text('{"old":1}')
    store = Store(tmp_path/'library'); sim = store.add_simulation(root, entrypoint='model.py')
    with Run(sim['id'], workspace=store.path, capture_console=False) as old: pass
    before = store.run(old.id)
    manifest = store.path/'snapshots'/f"{before['snapshot_id']}.json"
    original = manifest.read_bytes()
    blobs = {f['blob']:blob_path(store.path,f['blob']).read_bytes() for f in before['snapshot']['files']}
    archive = create_backup(store, tmp_path/'old.zip'); backup_bytes = archive.read_bytes()
    store.update_simulation(sim['id'], config={**sim['config'], 'output_dir':'research_results'})
    for _ in range(2):
        with Run(sim['id'], workspace=store.path, capture_console=False) as new: pass
    # Comparing a newly clean scope to a contaminated old baseline stays truthful.
    assert store.run(new.id)['source_change'] == 'changed'
    assert store.run(old.id) == before and manifest.read_bytes() == original
    assert all(blob_path(store.path,key).read_bytes()==value for key,value in blobs.items())
    assert archive.read_bytes() == backup_bytes
    restored = restore_backup(archive, tmp_path/'restored')
    assert restored.run(old.id)['snapshot'] == before['snapshot']


def test_repeated_swss_runs_preserve_source_and_output_bytes_in_git_separately(tmp_path):
    from simshelf import git_archive as archive, preservation
    root, source, store, sim = fixture(tmp_path, True, 'research_results')
    repo=tmp_path/'archive';repo.mkdir()
    archive.connect(store,str(repo),initialize=True,confirmed=True)
    archive.set_global_enabled(store,True)
    options={'enabled':True,'all_sources':True,'sources':[],
             'extensions':['.json','.log'],'process_logs':True}
    preservation.save(store,sim['id'],preservation.preview(store,sim['id'],sim['config'],options),True)
    saved=[]
    for _ in range(2):
        ident,code=record_command(store,sim['id'],[sys.executable,str(source)],cwd=root,quiet=True)
        assert code==0
        result=store.run(ident)
        event,=archive.entries(store,ident)
        sources={f['name'] for f in event['files'] if f['category']=='source'}
        assert sources=={'model.py','helper.py','input.json','swss.toml'}
        for index,file in enumerate(event['files']):
            assert archive.download(store,ident,event['id'],index)[1]==archive.candidate_bytes(store,ident,file)
        saved.append((result,event,archive.download_record(store,ident,event['id'])))
    assert saved[1][0]['source_change']=='same'
    assert saved[0][0]['snapshot_id']==saved[1][0]['snapshot_id']
    assert archive.entries(store,saved[0][0]['id'])==[saved[0][1]]
    assert archive.download_record(store,saved[0][0]['id'],saved[0][1]['id'])==saved[0][2]


def test_unknown_local_extension_does_not_block_manual_recording(tmp_path):
    root,source,store,sim=fixture(tmp_path,False,'results')
    (root/'swss.toml').write_text(HEADER+'\n[extensions.simshelf]\nschema_version=999\n')
    with Run(sim['id'],workspace=store.path,capture_console=False) as run: pass
    result=store.run(run.id)
    assert result['version']=='0.3.1'
    assert any('Local SWSS capture settings unavailable' in warning for warning in result['source_warnings'])


def test_unassociated_companion_cannot_exclude_another_entrypoints_source(tmp_path):
    root,source,store,sim=fixture(tmp_path,False,'results')
    (root/'other.py').write_text('pass\n')
    (root/'research_source').mkdir()
    (root/'research_source/module.py').write_text('value=42\n')
    (root/'swss.toml').write_text(HEADER.replace('model.py','other.py')+'\n[extensions.simshelf]\nschema_version=1\n[extensions.simshelf.capture]\noutput_dir="research_source"\n')
    with Run(sim['id'],workspace=store.path,capture_console=False) as run: pass
    result=store.run(run.id)
    assert result['version']=='unversioned'
    assert 'research_source/module.py' in {f['path'] for f in result['snapshot']['files']}
