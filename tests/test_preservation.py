import hashlib
import json
import shutil
import uuid
from pathlib import Path

import pytest

from simshelf import git_archive as archive, preservation as preservation
from simshelf.backup import create_backup, restore_backup
from simshelf.capture import save_file
from simshelf.recording import Run
from simshelf.source import blob_path
from simshelf.store import Store
from test_library_preservation_audit import library, launch, consent, SOURCE_RULES


def options(**changes):
    return {'enabled': True, 'all_sources': True, 'sources': [],
            'extensions': ['.json', '.csv', '.log'], 'process_logs': False, **changes}


def enable(store, sim, **changes):
    review = preservation.preview(store, sim['id'], sim['config'], options(**changes))
    preservation.save(store, sim['id'], review, True)
    return review


def verify(store, repo, run):
    events = archive.entries(store, run['id'])
    assert len(events) == 1, archive.view(store, run['id'])
    event = events[0]
    manifest = json.loads(archive.download_record(store, run['id'], event['id']))
    assert manifest['record'] == event['record']
    assert manifest['record']['execution']['command'] == run['command']
    for i, f in enumerate(event['files']):
        data = archive.download(store, run['id'], event['id'], i)[1]
        assert hashlib.sha256(data).hexdigest() == f['blob']
        assert len(data) == f['size']
        assert data == archive.candidate_bytes(store, run['id'], f)
    return event


def test_recursive_first_repeat_interleaved_restart(library):
    store, repo, (a, b) = library
    for sim in (a, b):
        enable(store, sim, process_logs=True)
    records = []
    for sim, label in ((a, 'A1'), (b, 'B'), (a, 'A2')):
        run = launch(store, sim, label, csv=True)
        event = verify(store, repo, run)
        assert len(event['files']) == 8  # two sources, four nested results, two streams
        assert event['record']['completeness'] == 'verified'
        assert event['record']['policy']['options']['extensions'] == ['.csv', '.json', '.log']
        assert archive.view(store, run['id'])['preservation']['output_files'] == 4
        records.append((run, event))
    reopened = Store(store.path)
    for run, event in records:
        assert verify(reopened, repo, run) == event
        assert reopened.run(run['id'], False)['command'] == run['command']
    assert len({e['commit'] for _, e in records}) == 3
    assert records[-1][0]['capture_counts']['unchanged'] == 4
    assert records[0][0]['snapshot_id'] == records[-1][0]['snapshot_id']


def test_consent_is_explicit_atomic_and_legacy_is_not_reinterpreted(library):
    store, repo, (a, _) = library
    consent(store, a, SOURCE_RULES, [])
    historical = launch(store, a, 'legacy')
    old = archive.entries(store, historical['id'])
    legacy_manifest = archive.download_record(store, historical['id'], old[0]['id'])
    assert 'record' not in json.loads(legacy_manifest)
    legacy = archive.get(store, 'settings:' + a['id'])
    review = preservation.preview(store, a['id'], a['config'], options())
    with pytest.raises(ValueError):
        preservation.save(store, a['id'], review, False)
    assert preservation.get(store, 'settings:' + a['id']) is None
    assert archive.get(store, 'settings:' + a['id']) == legacy
    changed = {**a['config'], 'max_file_mb': 10}
    store.update_simulation(a['id'], config=changed)
    with pytest.raises(ValueError, match='changed'):
        preservation.save(store, a['id'], review, True)
    assert preservation.get(store, 'settings:' + a['id']) is None
    review = preservation.preview(store, a['id'], changed, options())
    preservation.save(store, a['id'], review, True)
    assert archive.get(store, 'settings:' + a['id']) is None
    assert preservation.get(store, 'settings:' + a['id'])['legacy_settings'] == legacy
    assert archive.entries(store, historical['id']) == old
    assert archive.download_record(store, historical['id'], old[0]['id']) == legacy_manifest
    assert archive.view(store, historical['id'])['preservation']['output_files'] == 0
    assert archive.view(store, historical['id'])['preservation']['state'] == 'partial'
    with pytest.raises(ValueError, match='empty'):
        preservation.preview(store, a['id'], changed, options(all_sources=False, extensions=[]))


def test_reference_ignore_selection_and_size_omissions(library, monkeypatch):
    store, repo, (sim, _) = library
    config = {**sim['config'], 'rules': [{'pattern': '**/reference.json', 'action': 'reference'},
        {'pattern': '**/ignored.json', 'action': 'ignore'}, {'pattern': '**/*', 'action': 'copy'}]}
    preservation.save(store, sim['id'], preservation.preview(store, sim['id'], config,
        options(all_sources=False, sources=['sim.py'])), True)
    with Run(sim['id'], workspace=store.path, capture_console=False) as run:
        out = run.output_dir / 'unique'
        out.mkdir(parents=True)
        for name in ('reference.json', 'ignored.json', 'kept.json', 'unselected.txt'):
            (out / name).write_text(name)
        # Fail one file's Git admission, without changing ordinary copy policy.
        (out / 'large.json').write_bytes(b'x' * 30000)
        monkeypatch.setattr(archive, 'FILE_LIMIT', 20000)
    result = store.run(run.id)
    event = verify(store, repo, result)
    assert {f['name'] for f in event['files']} == {'sim.py', 'unique/kept.json'}
    ledger = {e['name']: e for e in event['record']['evidence']}
    assert 'reference' in ledger['unique/reference.json']['reason']
    assert ledger['unique/ignored.json']['disposition'] == 'not_retained'
    assert 'Not selected' in ledger['unique/unselected.txt']['reason']
    assert 'budget' in ledger['unique/large.json']['reason']
    assert event['record']['completeness'] == 'partial'
    assert result['capture_counts']['referenced'] == result['capture_counts']['ignored'] == 1
    assert result['capture_status'] == 'complete'


def test_disabled_disconnected_missing_identity_and_recording(library):
    store, repo, (sim, _) = library
    enable(store, sim, enabled=False)
    first = launch(store, sim, 'disabled')
    assert archive.view(store, first['id'])['preservation']['state'] == 'not_enabled'
    enable(store, sim)
    good = launch(store, sim, 'enabled')
    event = verify(store, repo, good)
    saved = archive.get(store, 'connection')
    archive.disconnect(store)
    disconnected = launch(store, sim, 'disconnected')
    assert disconnected['capture_counts']['copied'] == 3
    assert archive.view(store, disconnected['id'])['preservation']['state'] == 'unavailable'
    with pytest.raises(ValueError):
        archive.download_record(store, good['id'], event['id'])
    archive.connect(store, str(repo), confirmed=True, expected_connection=saved)
    assert verify(store, repo, good) == event
    identity = (repo / 'simshelf-archive-id').read_text()
    (repo / 'simshelf-archive-id').write_text(uuid.uuid4().hex)
    mismatch = launch(store, sim, 'mismatch')
    assert mismatch['capture_counts']['copied'] == 3
    assert not archive.entries(store, mismatch['id'])
    with pytest.raises(ValueError):
        archive.download_record(store, good['id'], event['id'])
    (repo / 'simshelf-archive-id').write_text(identity)
    moved = repo.with_name('temporarily-unavailable')
    repo.rename(moved)
    unavailable = launch(store, sim, 'missing')
    assert unavailable['capture_counts']['copied'] == 3 and not archive.entries(store, unavailable['id'])
    moved.rename(repo)
    assert verify(store, repo, good) == event


@pytest.mark.parametrize('crash_point', ['hash-object', 'show'])
def test_crash_restart_retry_never_recaptures(library, monkeypatch, crash_point):
    store, repo, (sim, _) = library
    enable(store, sim)
    original = archive.git
    def crash(root, *args, **kwargs):
        if args[0] == crash_point:
            raise ValueError('injected publication interruption')
        return original(root, *args, **kwargs)
    monkeypatch.setattr(archive, 'git', crash)
    run = launch(store, sim, 'interrupted-publication')
    pending = preservation.get(store, 'pending:' + run['id'])
    assert pending and archive.view(store, run['id'])['preservation']['state'] == 'pending'
    for a in run['artifacts']:
        Path(a['original_path']).write_text('changed live original')
    monkeypatch.setattr(archive, 'git', original)
    reopened = Store(store.path)
    first = archive.publish(reopened, run['id'])
    assert archive.publish(reopened, run['id']) == {'status': 'nothing pending'}
    assert verify(reopened, repo, run) == first
    assert first['record'] == pending['record']


def test_annotations_captions_append_only_and_backup(library, tmp_path):
    store, repo, (sim, _) = library
    enable(store, sim)
    run = launch(store, sim, 'notes')
    initial = verify(store, repo, run)
    raw_initial = archive.download_record(store, run['id'], initial['id'])
    original_record = store.run(run['id'], False)
    image = tmp_path / 'view.png'; image.write_bytes(b'fixture-image-bytes')
    artifact = save_file(store, run['id'], image)
    store.emit(run['id'], 'annotation', {'notes': 'first interpretation'})
    store.emit(run['id'], 'artifact_annotation', {'id': artifact['id'], 'caption': 'first caption'})
    review = preservation.additions_preview(store, run['id'], [artifact['id']], True)
    op = uuid.uuid4().hex
    first = preservation.additions(store, run['id'], review, op, True)
    assert preservation.additions(store, run['id'], review, op, True) == first
    assert len(first['record']['annotations']) == 3
    store.emit(run['id'], 'annotation', {'notes': 'revised interpretation'})
    with pytest.raises(ValueError, match='changed'):
        preservation.additions(store, run['id'], review, uuid.uuid4().hex, True)
    review = preservation.additions_preview(store, run['id'], [], True)
    second = preservation.additions(store, run['id'], review, uuid.uuid4().hex, True)
    assert not second['files'] and second['record']['annotations']
    assert archive.download_record(store, run['id'], initial['id']) == raw_initial
    for key in ('command', 'version', 'status', 'exit_code', 'snapshot_id'):
        assert store.run(run['id'], False)[key] == original_record[key]
    backup = create_backup(store, tmp_path / 'backup.zip')
    separate_repo = tmp_path / 'separately-preserved-archive'; shutil.copytree(repo, separate_repo)
    restored = restore_backup(backup, tmp_path / 'restored')
    assert archive.entries(restored, run['id']) == archive.entries(store, run['id'])
    with pytest.raises(ValueError):
        archive.download_record(restored, run['id'], first['id'])
    archive.disconnect(restored)
    archive.connect(restored, str(separate_repo), confirmed=True)
    assert archive.download_record(restored, run['id'], first['id']) == archive.download_record(store, run['id'], first['id'])


def test_record_and_annotation_bounds_fail_without_truncation(library, monkeypatch):
    store, repo, (sim, _) = library
    enable(store, sim)
    monkeypatch.setattr(preservation, 'RECORD_LIMIT', 100)
    run = launch(store, sim, 'too-big-record')
    assert not archive.entries(store, run['id'])
    assert '1 MiB' in archive.view(store, run['id'])['error']
    assert run['capture_counts']['copied'] == 3
    monkeypatch.setattr(preservation, 'RECORD_LIMIT', 1024**2)
    store.emit(run['id'], 'annotation', {'notes': 'é' * 40000})
    with pytest.raises(ValueError, match='64 KiB'):
        preservation.additions_preview(store, run['id'], [], True)


def test_preservation_api_confirmation_and_verified_source(library):
    from fastapi.testclient import TestClient
    from simshelf.api import create_app
    store, repo, (sim, _) = library
    with TestClient(create_app(store.path)) as client:
        endpoint = f'/api/simulations/{sim["id"]}/preservation'
        payload = {'config': sim['config'], 'options': options()}
        assert client.post(endpoint + '/preview', json=payload).status_code == 403
        client.headers['X-SimShelf-Token'] = client.get('/api/workspace').json()['token']
        review = client.post(endpoint + '/preview', json=payload).json()
        assert client.post(endpoint + '/save', json={'review': review}).status_code == 400
        assert client.post(endpoint + '/save', json={'review': review, 'confirmed': True}).status_code == 200
        run = launch(store, sim, 'api')
        event = verify(store, repo, run)
        assert client.get(f'/api/runs/{run["id"]}/archive/{event["id"]}/record').status_code == 200
        source = client.get(f'/api/runs/{run["id"]}/source-file', params={'path': 'sim.py'})
        assert source.content == (Path(sim['root']) / 'sim.py').read_bytes()
        file = run['snapshot']['files'][0]
        blob_path(store.path, file['blob']).write_bytes(b'corrupt')
        assert client.get(f'/api/runs/{run["id"]}/source-file', params={'path': file['path']}).status_code == 400


def test_failed_cancelled_and_prepared_interruption_are_separate(library):
    import sys
    import threading
    from simshelf.recording import record_command
    store, repo, (sim, _) = library
    enable(store, sim, process_logs=True)
    ident, code = record_command(store, sim['id'], [sys.executable, '-c', 'import sys;print("failure");sys.exit(7)'], cwd=sim['root'], quiet=True)
    run = store.run(ident)
    assert code == 7 and run['status'] == 'failed'
    assert verify(store, repo, run)['record']['execution']['exit_code'] == 7
    cancel = threading.Event(); cancel.set()
    ident, code = record_command(store, sim['id'], [sys.executable, '-c', 'raise AssertionError("must not execute")'], cwd=sim['root'], quiet=True, cancel=cancel)
    run = store.run(ident)
    assert run['status'] == 'interrupted'
    assert verify(store, repo, run)['record']['execution']['status'] == 'interrupted'
    recorder = Run(sim['id'], workspace=store.path, capture_console=False)
    recorder.__enter__()
    store.emit(recorder.id, 'finish', {'status': 'interrupted', 'ended_at': '2026-10-21T00:00:00Z', 'capture_status': 'incomplete'})
    reopened = Store(store.path)
    assert archive.view(reopened, recorder.id)['preservation']['state'] == 'partial'
    assert archive.publish(reopened, recorder.id) == {'status': 'nothing pending'}
    assert not archive.entries(reopened, recorder.id)


def test_replaced_source_links_corruption_and_git_absence_fail_closed(library, monkeypatch):
    store, repo, (sim, _) = library
    enable(store, sim)
    old = Path(sim['root']); moved = old.with_name('original-source'); old.rename(moved)
    shutil.copytree(moved, old)
    assert preservation.status(store, sim['id'])['state'] == 'unavailable'
    run = launch(store, sim, 'replacement')
    assert run['capture_counts']['copied'] == 3 and not archive.entries(store, run['id'])
    enable(store, store.simulation(sim['id']))
    monkeypatch.setattr(archive.shutil, 'which', lambda name: None)
    no_git = launch(store, sim, 'without-git')
    assert no_git['status'] == 'completed' and not archive.entries(store, no_git['id'])
    a = run['artifacts'][0]
    path = blob_path(store.path, a['blob'])
    path.write_bytes(b'bad')
    with pytest.raises(ValueError, match='integrity'):
        preservation.retained_artifact(store, a['id'])
    path.unlink(); path.symlink_to(Path(a['original_path']))
    with pytest.raises((OSError, ValueError)):
        preservation.retained_artifact(store, a['id'])


def test_cumulative_record_annotation_and_file_budgets(library, tmp_path, monkeypatch):
    store, repo, (sim, _) = library
    enable(store, sim)
    run = launch(store, sim, 'limits')
    original = archive.entries(store, run['id'])
    store.emit(run['id'], 'annotation', {'notes': 'first'})
    review = preservation.additions_preview(store, run['id'], [], True)
    preservation.additions(store, run['id'], review, uuid.uuid4().hex, True)
    monkeypatch.setattr(preservation, 'ANNOTATION_LIMIT', 1)
    with pytest.raises(ValueError, match='Cumulative'):
        preservation.additions_preview(store, run['id'], [], True)
    monkeypatch.setattr(preservation, 'ANNOTATION_LIMIT', 1000)
    monkeypatch.setattr(archive, 'RUN_LIMIT', 100)
    with pytest.raises(ValueError, match='Cumulative'):
        preservation.additions_preview(store, run['id'], [], True)
    assert archive.entries(store, run['id'])[0] == original[0]


def test_concurrent_simulations_and_exact_pending_identity(library, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    store, repo, (a, b) = library
    for sim in (a,b): enable(store, sim)
    with ThreadPoolExecutor(2) as pool:
        results=list(pool.map(lambda sim: launch(store, sim, sim['id']), (a,b)))
    events=[verify(store, repo, run) for run in results]
    assert len({e['commit'] for e in events}) == 2
    for run, event in zip(results,events):
        assert event['record']['execution']['simulation_id'] == run['simulation_id']
        assert event['simulation'] == run['simulation_id']


def test_pending_addition_survives_attachment_removal_backup_restart(library, tmp_path, monkeypatch):
    from simshelf.screenshots import delete_screenshot
    store, repo, (sim, _) = library
    enable(store, sim)
    run = launch(store, sim, 'pending-backup')
    image = tmp_path / 'pending.png'; image.write_bytes(b'pending screenshot fixture')
    attachment = save_file(store, run['id'], image)
    review = preservation.additions_preview(store, run['id'], [attachment['id']])
    op = uuid.uuid4().hex
    original = archive.git
    def crash(root, *args, **kwargs):
        if args[0] == 'hash-object': raise ValueError('injected publication failure')
        return original(root, *args, **kwargs)
    monkeypatch.setattr(archive, 'git', crash)
    with pytest.raises(ValueError): preservation.additions(store, run['id'], review, op, True)
    delete_screenshot(store, run['id'], attachment['id'], confirmed=True)
    assert blob_path(store.path, attachment['blob']).read_bytes() == image.read_bytes()
    backup = create_backup(store, tmp_path / 'pending.zip')
    restored = restore_backup(backup, tmp_path / 'restored-pending')
    monkeypatch.setattr(archive, 'git', original)
    archive.disconnect(restored)
    archive.connect(restored, str(repo), confirmed=True)
    event = archive.publish(restored, run['id'])
    assert event['id'] == op and event['record'] == review['record']
    assert archive.download(restored, run['id'], event['id'], 0)[1] == image.read_bytes()
    assert archive.publish(restored, run['id']) == {'status': 'nothing pending'}


def test_pinned_standalone_reference_new_policy_fixed_and_uncoordinated(tmp_path):
    import os
    import sys
    from simshelf.recording import record_command
    reference = os.environ.get('SIMSHELF_AUDIT_DECAY_REFERENCE')
    if not reference:
        pytest.skip('Pinned standalone decay reference path not supplied')
    hashes = {'simulate.py': '48a0b582d8bceb007a547dfc891333ad62d766114ffd17eb8284128e04780f41',
              'swss.toml': '44f9bc668492b4f0957fe77a958e7f9b952da7379867c3bbdf9c16b34f9c6a98'}
    root = tmp_path / 'decay'; root.mkdir()
    for name, digest in hashes.items():
        raw = (Path(reference) / name).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == digest
        (root / name).write_bytes(raw)
    store = Store(tmp_path / 'library'); repo = tmp_path / 'archive'; repo.mkdir()
    archive.connect(store, str(repo), initialize=True, confirmed=True)
    sim = store.add_simulation(root, entrypoint='simulate.py')
    enable(store, sim)
    original = []
    for policy in ('fixed', 'fixed', 'per_run'):
        argv = [sys.executable, str(root / 'simulate.py'), '--rate=0.005', '--steps=10']
        ident, code = record_command(store, sim['id'], argv, cwd=root, quiet=True, output_policy=policy)
        run = store.run(ident); event = verify(store, repo, run)
        assert code == 0 and run['version'] == '0.1.3' and run['command'] == argv
        assert len([f for f in event['files'] if f['category'] == 'result']) == (4 if policy == 'fixed' else 0)
        assert event['record']['completeness'] == ('verified' if policy == 'fixed' else 'partial')
        if policy == 'per_run': assert list(Path(run['capture_root']).iterdir()) == []
        original.append((run, event))
    for run, event in original: assert verify(store, repo, run) == event
    for name, digest in hashes.items(): assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest
