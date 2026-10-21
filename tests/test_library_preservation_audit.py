"""Issue #118 Phase 1: characterize current storage, not the proposed workflow.

All stores, archives and independently executed fixtures live under pytest's
temporary root. No user's database, source, output or archive is opened.
"""
import hashlib
import json
import os
import sys
from pathlib import Path

import pytest

from simshelf import git_archive as archive
from simshelf.git_selection import inventory, save_selection, selection_preview
from simshelf.recording import record_command
from simshelf.source import blob_path
from simshelf.store import Store


SCRIPT = '''import json, sys, uuid
from datetime import datetime, timezone
from pathlib import Path

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
root = Path("outputs") / ("run_" + stamp + "_" + uuid.uuid4().hex)
root.mkdir(parents=True)
payloads = {
    "provenance.json": json.dumps({"argv": sys.argv[1:], "root": str(root)}),
    "summary.json": json.dumps({"label": sys.argv[1], "status": "completed"}),
    "run_" + stamp + ".log": "closed scientific log: " + sys.argv[1] + "\\n",
}
if "--csv" in sys.argv:
    payloads["series.csv"] = "step,value\\n0,1\\n"
for name, value in payloads.items():
    with (root / name).open("x", encoding="utf-8") as stream:
        stream.write(value)
print("run_directory=" + str(root))
'''
SOURCE_RULES = [{'kind': 'file', 'value': name} for name in ('sim.py', 'swss.toml')]
TEXT_RULES = [{'kind': 'extension', 'value': ext} for ext in ('.json', '.log', '.csv')]
SHALLOW_RULES = ['*.csv', '*.json', '*.log', 'outputs/*.csv', 'outputs/*.json', 'outputs/*.log']


@pytest.fixture
def library(tmp_path):
    store = Store(tmp_path / 'library')
    repo = tmp_path / 'archive'
    repo.mkdir()
    archive.connect(store, str(repo), initialize=True, confirmed=True)
    simulations = []
    for name in ('alpha', 'beta'):
        root = tmp_path / name
        root.mkdir()
        (root / 'sim.py').write_text(SCRIPT)
        (root / 'swss.toml').write_text(
            '[swss]\nschema_version = 2\nentrypoint = "sim.py"\nsimulation_version = "1.0.0"\n'
        )
        simulations.append(store.add_simulation(root, name=name, entrypoint='sim.py'))
    return store, repo, simulations


def consent(store, simulation, rules, future):
    inv = inventory(store, simulation['id'])
    save_selection(store, simulation['id'], selection_preview(store, simulation['id'], inv['revision'], rules))
    archive.enable(store, simulation['id'], archive.settings_preview(store, simulation['id'], future), True)


def launch(store, simulation, label, *, policy='fixed', csv=False):
    command = [sys.executable, str(Path(simulation['root']) / 'sim.py'), label, '--rate=001e-3', '']
    if csv:
        command.append('--csv')
    ident, code = record_command(store, simulation['id'], command, quiet=True,
                                 cwd=simulation['root'], output_policy=policy)
    run = store.run(ident)
    assert code == run['exit_code'] == 0
    assert run['status'] == 'completed'
    assert run['command'] == command
    assert run['version'] == '1.0.0'
    return run


def verify_event(store, repo, run):
    event, = archive.entries(store, run['id'])
    prefix = f"simulations/{run['simulation_id']}/runs/{run['id']}/{event['id']}/"
    paths = archive.git(repo, 'ls-tree', '-r', '--name-only', event['commit']).decode().splitlines()
    own_paths = {p for p in paths if p.startswith(prefix)}
    assert own_paths == {prefix + 'manifest.json', *(f['path'] for f in event['files'])}
    raw = archive.git(repo, 'show', event['commit'] + ':' + prefix + 'manifest.json')
    manifest = json.loads(raw)
    assert manifest == {k: v for k, v in event.items() if k not in ('repository', 'commit')}
    for index, item in enumerate(event['files']):
        data = archive.git(repo, 'cat-file', 'blob', event['commit'] + ':' + item['path'])
        assert len(data) == item['size']
        assert hashlib.sha256(data).hexdigest() == item['blob']
        assert data == blob_path(store.path, item['blob']).read_bytes()
        assert data == archive.download(store, run['id'], event['id'], index)[1]
    return event, manifest


@pytest.mark.parametrize('rules,future,source_count,result_count,skip_count', [
    ([], [], 0, 0, 0),
    (SOURCE_RULES, [], 2, 0, 0),
    (SOURCE_RULES, SHALLOW_RULES, 2, 0, 6),
    (SOURCE_RULES + TEXT_RULES, [], 2, 3, 0),
])
def test_audit_three_copies_do_not_imply_three_git_files(
    library, rules, future, source_count, result_count, skip_count
):
    store, repo, (sim, _) = library
    consent(store, sim, rules, future)
    run = launch(store, sim, 'three-files')
    assert run['capture_status'] == 'complete'
    assert run['capture_counts']['copied'] == len(run['artifacts']) == 3
    assert {f['path'] for f in run['snapshot']['files']} == {'sim.py', 'swss.toml'}
    for artifact in run['artifacts']:
        assert artifact['automatic'] and artifact['policy'] == 'copy'
        assert len(Path(artifact['name']).parts) == 2
        assert blob_path(store.path, artifact['blob']).read_bytes() == Path(artifact['original_path']).read_bytes()
    event, manifest = verify_event(store, repo, run)
    assert len([f for f in event['files'] if f['category'] == 'source']) == source_count
    assert len([f for f in event['files'] if f['category'] == 'result']) == result_count
    assert len(event['skipped']) == skip_count
    assert not archive.view(store, run['id'])['error']
    # Existing manifests have file inventory, not a portable execution record.
    assert set(manifest) == {'id', 'created_at', 'kind', 'simulation', 'run', 'files', 'skipped'}
    assert run['archive_capture_rules'] == future


def test_audit_nested_future_rules_are_not_supported():
    for pattern in ('run_*/*.json', '**/*.json', 'outputs/**'):
        with pytest.raises(ValueError):
            archive.future_rules([pattern])
    assert not archive.future_match('run_new/summary.json', SHALLOW_RULES)


def test_audit_multisimulation_history_and_restart(library):
    store, repo, (alpha, beta) = library
    for sim in (alpha, beta):
        consent(store, sim, SOURCE_RULES + TEXT_RULES, [])
    runs, events, originals = [], [], {}
    for sim, label in ((alpha, 'A-first'), (beta, 'B-middle'), (alpha, 'A-last')):
        run = launch(store, sim, label, csv=True)
        assert run['capture_counts']['copied'] == 4
        assert run['capture_status'] == 'complete'
        event, _ = verify_event(store, repo, run)
        assert len(event['files']) == 6
        payload = next(a for a in run['artifacts'] if a['name'].endswith('/provenance.json'))
        assert json.loads(blob_path(store.path, payload['blob']).read_bytes())['argv'] == run['command'][2:]
        for artifact in run['artifacts']:
            originals[artifact['original_path']] = blob_path(store.path, artifact['blob']).read_bytes()
        runs.append(run)
        events.append(event)
    assert len({e['commit'] for e in events}) == 3
    assert runs[0]['snapshot_id'] == runs[2]['snapshot_id']
    assert runs[2]['capture_counts']['unchanged'] == 4
    head_paths = set(archive.git(repo, 'ls-tree', '-r', '--name-only', events[-1]['commit']).decode().splitlines())
    for event in events:
        assert all(f['path'] in head_paths for f in event['files'])
    before = [store.run(r['id'], False) for r in runs]
    reopened = Store(store.path)
    for run, event, record in zip(runs, events, before):
        assert reopened.run(run['id'], False) == record
        assert verify_event(reopened, repo, run)[0] == event
    assert all(Path(path).read_bytes() == data for path, data in originals.items())


def test_audit_disconnect_keeps_capture_but_blocks_git(library):
    store, repo, (sim, _) = library
    consent(store, sim, SOURCE_RULES + TEXT_RULES, [])
    first = launch(store, sim, 'connected')
    event, _ = verify_event(store, repo, first)
    connection = archive.get(store, 'connection')
    archive.disconnect(store)
    second = launch(store, sim, 'disconnected')
    assert second['capture_status'] == 'complete' and second['capture_counts']['copied'] == 3
    assert archive.entries(store, second['id']) == []
    assert archive.view(store, second['id'])['error']
    with pytest.raises(ValueError):
        archive.download(store, first['id'], event['id'], 0)
    for artifact in first['artifacts'] + second['artifacts']:
        assert blob_path(store.path, artifact['blob']).read_bytes() == Path(artifact['original_path']).read_bytes()
    archive.connect(store, str(repo), confirmed=True, expected_connection=connection)
    assert verify_event(store, repo, first)[0] == event
    # Reconnection does not retroactively create a frozen plan for the second run.
    assert archive.publish(store, second['id']) == {'status': 'nothing pending'}
    assert archive.entries(store, second['id']) == []


def test_audit_uncoordinated_per_run_root_misses_simulation_owned_outputs(library):
    store, _, (sim, _) = library
    # Independent fixture deliberately knows nothing about SimShelf's environment.
    run = launch(store, sim, 'independent', policy='per_run')
    capture = Path(run['capture_root'])
    assert capture.is_dir() and list(capture.iterdir()) == []
    siblings = [p for p in capture.parent.iterdir() if p != capture]
    assert len(siblings) == 1 and len(list(siblings[0].iterdir())) == 3
    assert run['capture_counts']['copied'] == 0
    assert run['capture_status'] == 'partial'
    assert any('Required log capture incomplete' in e for e in run['capture_errors'])
    assert not run['artifacts']


@pytest.mark.parametrize('policy,copied', [('fixed', 3), ('per_run', 0)])
def test_audit_pinned_decay_reference(tmp_path, policy, copied):
    reference = os.environ.get('SIMSHELF_AUDIT_DECAY_REFERENCE')
    if not reference:
        pytest.skip('Set SIMSHELF_AUDIT_DECAY_REFERENCE to the pinned standalone 0.1.3 package')
    expected = {
        'simulate.py': '48a0b582d8bceb007a547dfc891333ad62d766114ffd17eb8284128e04780f41',
        'swss.toml': '44f9bc668492b4f0957fe77a958e7f9b952da7379867c3bbdf9c16b34f9c6a98',
    }
    # Inspect/copy only these pinned public fixture bytes; never execute in the source checkout.
    root = tmp_path / 'decay'
    root.mkdir()
    for name, digest in expected.items():
        data = (Path(reference) / name).read_bytes()
        assert hashlib.sha256(data).hexdigest() == digest, 'Reference revision changed; review explicitly'
        (root / name).write_bytes(data)
    store = Store(tmp_path / 'library')
    repo = tmp_path / 'archive'
    repo.mkdir()
    archive.connect(store, str(repo), initialize=True, confirmed=True)
    sim = store.add_simulation(root, entrypoint='simulate.py')
    rules = [{'kind': 'file', 'value': name} for name in expected] + TEXT_RULES
    consent(store, sim, rules, [])
    command = [sys.executable, str(root / 'simulate.py'), '--rate=0.005', '--steps=10', '--no-series']
    ident, code = record_command(store, sim['id'], command, cwd=root, quiet=True, output_policy=policy)
    run = store.run(ident)
    assert code == 0 and run['status'] == 'completed' and run['version'] == '0.1.3'
    assert run['command'] == command and run['capture_counts']['copied'] == copied
    assert run['capture_status'] == ('complete' if copied else 'partial')
    event, _ = verify_event(store, repo, run)
    assert len([f for f in event['files'] if f['category'] == 'result']) == copied
    assert len([f for f in event['files'] if f['category'] == 'source']) == 2
    generated = list((root / 'outputs').glob('run_*/provenance.json'))
    assert len(generated) == 1
    if policy == 'per_run':
        capture = Path(run['capture_root'])
        assert not list(capture.iterdir()) and generated[0].parent != capture
        assert any('Required log capture incomplete' in e for e in run['capture_errors'])
    else:
        for artifact in run['artifacts']:
            assert blob_path(store.path, artifact['blob']).read_bytes() == Path(artifact['original_path']).read_bytes()
    for name, digest in expected.items():
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest
