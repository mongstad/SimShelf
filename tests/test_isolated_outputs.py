"""Coordinated original-output isolation, not filesystem write redirection."""
import concurrent.futures
import json
import os
from pathlib import Path
import sys
import threading

from fastapi.testclient import TestClient
import pytest

from simshelf.api import create_app
from simshelf.backup import create_backup, restore_backup
from simshelf.output_paths import allocate_output, output_review
from simshelf.portal import execution_settings
from simshelf.recording import Run, record_command
from test_portal import settings, headers, launch, finish


def test_review_and_saved_policy_are_passive(project):
    store, sim, root, source = project
    mapping = {"argument_index": 1, "value": "outputs", "kind": "directory", "format": "token"}
    config = settings(output_policy="per_run", arguments=["--output-dir", "outputs"], output_mappings=[mapping])
    plan = execution_settings(sim, config)
    assert plan['command'] == [sys.executable, str(source), '--output-dir', 'outputs']
    assert plan['output_review']['requires_acknowledgement']
    assert plan['output_review']['targets'][0]['suggested_argument'] is None
    assert not (root / 'outputs').exists()
    with TestClient(create_app(store.path)) as client:
        auth = headers(client)
        base = f"/api/simulations/{sim['id']}"
        assert client.put(base + '/execution', headers=auth, json=config).status_code == 200
        assert store.simulation(sim['id'])['execution']['output_policy'] == 'per_run'
        assert not (root / 'outputs').exists()
        assert client.post(base + '/launch', headers=auth, json=config).status_code == 400
        assert not store.runs()
        assert client.post(base + '/execution/validate', headers=auth, json=settings(output_policy='unsafe')).status_code == 400
    assert execution_settings(sim, settings())['settings']['output_policy'] == 'fixed'


@pytest.mark.parametrize('bad', ['../escape', '/absolute', '.', '', 'outputs/../other'])
def test_reject_invalid_parent(project, bad):
    _, sim, root, _ = project
    with pytest.raises(ValueError):
        output_review(sim, '.', [], bad, [], 'per_run')


def test_symlinks_files_and_collision_preserve_originals(project):
    _, sim, root, _ = project
    (root / 'real').mkdir()
    (root / 'outputs').symlink_to(root / 'real', target_is_directory=True)
    with pytest.raises(ValueError, match='symbolic'):
        allocate_output(root, 'outputs', 'a' * 32)
    (root / 'outputs').unlink()
    (root / 'outputs').write_text('original')
    with pytest.raises(ValueError):
        allocate_output(root, 'outputs', 'a' * 32)
    assert (root / 'outputs').read_text() == 'original'
    relative, identity = allocate_output(root, 'nested/base', 'a' * 32)
    (root / relative / 'result.csv').write_text('old result')
    with pytest.raises(ValueError, match='Cannot allocate'):
        allocate_output(root, 'nested/base', 'a' * 32)
    assert (root / relative / 'result.csv').read_text() == 'old result'


@pytest.mark.parametrize('joined', [False, True])
def test_successive_and_concurrent_portal_runs(project, tmp_path, joined):
    store, sim, root, source = project
    # Nondefault base and no explicit exclusions: exclude the whole base from
    # snapshots, including previous sibling runs and old fixed-folder results.
    sim = store.update_simulation(sim['id'], config={**sim['config'], 'output_dir': 'results', 'source_exclude': []})
    (root / 'results').mkdir()
    (root / 'results' / 'old.json').write_text('old original')
    source.write_text('''import os, json, time
from pathlib import Path
SIMSHELF_VERSION = "1.0"
''' + ('''import simshelf
with simshelf.run("field") as run:
    output = run.output_dir
    assert str(output) == os.environ["SIMSHELF_OUTPUT_DIR"]
    run.metric("energy", 2.5)
''' if joined else '''output = Path(os.environ["SIMSHELF_OUTPUT_DIR"])
''') + '''output.mkdir(parents=True, exist_ok=True)
(output / "result.json").write_text(json.dumps({"run": os.environ["SIMSHELF_RUN_ID"], "path": str(output)}))
(output / "raw.bin").write_bytes(b"reference")
(output / "ignored.tmp").write_text("ignored")
time.sleep(1)
''')
    with TestClient(create_app(store.path)) as client:
        auth = headers(client)
        def start():
            return launch(client, sim, auth, output_dir='results', output_policy='per_run')
        first = finish(store, start())
        second = finish(store, start())
        with concurrent.futures.ThreadPoolExecutor() as pool:
            ids = list(pool.map(lambda _: start(), range(2)))
        assert all(store.run(ident)['status'] == 'running' for ident in ids)
        runs = [first, second, *(finish(store, ident) for ident in ids)]
        assert len({r['capture_root'] for r in runs}) == 4
        assert len({r['snapshot_id'] for r in runs}) == 1
        for run in runs:
            assert run['status'] == 'completed', run
            folder = Path(run['capture_root'])
            assert folder.parent == root / 'results'
            assert run['launch']['output_review']['output_path'] == str(folder)
            assert run['capture_config']['output_dir'] == folder.relative_to(root).as_posix()
            assert run['capture_counts'] == {'copied': 1, 'referenced': 1, 'ignored': 1, 'skipped': 0, 'unchanged': 0}
            assert {f['path'] for f in run['snapshot']['files']} == {'field.py'}
            artifact = next(a for a in run['artifacts'] if a['name'] == 'result.json')
            data = client.get('/api/artifacts/' + artifact['id'] + '/file').content
            assert json.loads(data) == {'run': run['id'], 'path': str(folder)}
            assert json.loads((folder / 'result.json').read_text())['run'] == run['id']
            if joined:
                assert run['metrics'][0]['value'] == 2.5
        assert (root / 'results' / 'old.json').read_text() == 'old original'
        before = store.run(first['id'])
        client.put(f"/api/simulations/{sim['id']}/execution", headers=auth, json=settings())
        assert store.run(first['id']) == before
        backup = create_backup(store, tmp_path / 'backup.zip')
    restored = restore_backup(backup, tmp_path / 'restored')
    assert restored.run(first['id'])['capture_root'] == first['capture_root']
    assert restored.run(first['id'])['snapshot'] == first['snapshot']


def test_fixed_output_omission_and_child_failure(project):
    store, sim, root, source = project
    source.write_text('''from pathlib import Path
Path("outputs/fixed.csv").write_text("outside agreed folder")
raise SystemExit(7)
''')
    with TestClient(create_app(store.path)) as client:
        mapping = {"argument_index": None, "value": "outputs/fixed.csv", "kind": "file", "format": "token"}
        ident = launch(client, sim, headers(client), output_policy='per_run', output_mappings=[mapping], acknowledge_outputs=True)
        run = finish(store, ident)
        assert run['status'] == 'failed' and run['exit_code'] == 7
        assert not run['artifacts']
        assert sum(run['capture_counts'].values()) == 0
        assert not run['launch']['output_review']['targets'][0]['covered']
        assert (root / 'outputs/fixed.csv').read_text() == 'outside agreed folder'


def test_overlap_budgets_and_replaced_directory(project):
    store, sim, root, source = project
    sim = store.update_simulation(sim['id'], config={**sim['config'], 'max_run_mb': .00001, 'max_file_mb': .00002})
    with Run(sim['id'], workspace=store.path, capture_console=False) as fixed:
        with pytest.raises(ValueError, match='output folder'):
            with Run(sim['id'], workspace=store.path, capture_console=False, output_policy='per_run'):
                pass
    with Run(sim['id'], workspace=store.path, capture_console=False, output_policy='per_run') as r:
        (r.output_dir / 'a.csv').write_bytes(b'x' * 8)
        (r.output_dir / 'b.csv').write_bytes(b'x' * 8)
        (r.output_dir / 'large.csv').write_bytes(b'x' * 32)
    run = store.run(r.id)
    assert run['capture_counts']['copied'] == 1
    assert run['capture_counts']['skipped'] == 2
    assert run['capture_status'] == 'partial'
    with Run(sim['id'], workspace=store.path, capture_console=False, output_policy='per_run') as r:
        original = r.output_dir
        moved = original.with_name('preserved')
        original.rename(moved)
        original.mkdir()
        (original / 'wrong.csv').write_text('not this run')
    run = store.run(r.id)
    assert run['capture_status'] == 'incomplete' and not run['artifacts']
    assert 'replaced' in run['capture_errors'][0]
    assert moved.exists() and (original / 'wrong.csv').exists()


def test_cancel_before_child_preserves_record_and_empty_folder(project):
    store, sim, root, source = project
    cancel = threading.Event(); cancel.set()
    ident, code = record_command(store, sim['id'], [sys.executable, str(source)], cwd=root,
                                output_policy='per_run', cancel=cancel, quiet=True)
    run = store.run(ident)
    assert code == 130 and run['status'] == 'interrupted'
    assert Path(run['capture_root']).is_dir()
    assert not run['artifacts']


def test_cli_opt_in_and_live_portal_cancellation(project):
    import subprocess
    import time
    store, sim, root, source = project
    source.write_text('''import os, time, sys
from pathlib import Path
output = Path(os.environ["SIMSHELF_OUTPUT_DIR"])
(output / "result.csv").write_text("retained on stop")
if "--wait" in sys.argv:
    while True: time.sleep(.05)
''')
    result = subprocess.run([sys.executable, '-B', '-m', 'simshelf', '--workspace', str(store.path),
                             'record', '-s', sim['id'], '--output-policy', 'per_run', '--cwd', str(root),
                             '--', sys.executable, str(source)], capture_output=True, timeout=10)
    assert result.returncode == 0, result.stderr
    cli, = store.runs()
    assert cli['output_policy'] == 'per_run'
    assert Path(cli['capture_root'], 'result.csv').read_text() == 'retained on stop'
    with TestClient(create_app(store.path)) as client:
        auth = headers(client)
        ident = launch(client, sim, auth, output_policy='per_run', arguments=['--wait'])
        folder = Path(store.run(ident)['capture_root'])
        deadline = time.monotonic() + 5
        while not (folder / 'result.csv').exists():
            assert time.monotonic() < deadline
            time.sleep(.025)
        assert client.post(f'/api/runs/{ident}/stop', headers=auth).status_code == 202
        run = finish(store, ident)
        assert run['status'] == 'interrupted'
        assert run['capture_counts']['copied'] == 1
        assert (folder / 'result.csv').read_text() == 'retained on stop'


@pytest.mark.parametrize('path', ['portal', 'cli', 'python'])
@pytest.mark.parametrize('policy', ['fixed', 'per_run'])
def test_explicit_child_policy_and_repeated_capture(project, monkeypatch, path, policy):
    import subprocess
    store, sim, root, source = project
    (root / 'work').mkdir()
    monkeypatch.setenv('SIMSHELF_OUTPUT_POLICY', 'stale-inherited-value')
    monkeypatch.setenv('SIMSHELF_OUTPUT_DIR', '/not-the-launch-destination')
    source.write_text('''import json, os, sys
from pathlib import Path
parent = Path(os.environ['SIMSHELF_OUTPUT_DIR'])
policy = os.environ['SIMSHELF_OUTPUT_POLICY']
existed = parent.exists()
if policy == 'fixed':
    output = parent / ('child_' + os.environ['SIMSHELF_RUN_ID'])
    output.mkdir(parents=True, exist_ok=False)
elif policy == 'per_run':
    assert parent.is_dir() and not list(parent.iterdir())
    output = parent
else:
    raise RuntimeError('Unknown output allocation policy')
(output / 'result.json').write_text(json.dumps(dict(
    policy=policy, parent=str(parent), existed=existed, argv=sys.argv[1:],
    run=os.environ['SIMSHELF_RUN_ID'], cwd=str(Path.cwd()))))
''')
    args = ['--alias=01.00', '', '--repeat', 'a', '--repeat', 'b', '--', '$literal']
    command = [sys.executable, str(source), *args]
    with TestClient(create_app(store.path)) as client:
        runs = []
        for _ in range(2):
            if path == 'portal':
                ident = launch(client, sim, headers(client), cwd='work', output_dir='results',
                               output_policy=policy, arguments=args)
            elif path == 'cli':
                result = subprocess.run([
                    sys.executable, '-B', '-m', 'simshelf', '--workspace', str(store.path),
                    'record', '-s', sim['id'], '--cwd', str(root / 'work'),
                    '--output-dir', 'results', '--output-policy', policy, '--', *command,
                ], capture_output=True, timeout=15)
                assert result.returncode == 0, result.stderr
                ident, = {r['id'] for r in store.runs()} - {r['id'] for r in runs}
            else:
                ident, code = record_command(store, sim['id'], command, cwd=root / 'work',
                                             output_dir='results', output_policy=policy, quiet=True)
                assert code == 0
            run = finish(store, ident)
            assert run['status'] == 'completed', run
            assert run['command'] == command
            artifact, = run['artifacts']
            data = client.get('/api/artifacts/' + artifact['id'] + '/file').json()
            parent = root / 'results'
            if policy == 'per_run':
                parent /= 'run_' + ident
            assert data == dict(policy=policy, parent=str(parent), existed=(policy == 'per_run' or bool(runs)),
                                argv=args, run=ident, cwd=str(root / 'work'))
            assert run['capture_root'] == str(parent)
            assert {f['path'] for f in run['snapshot']['files']} == {'field.py'}
            runs.append(run)
        assert runs[0]['snapshot_id'] == runs[1]['snapshot_id']
        assert store.run(runs[0]['id']) == runs[0]
    assert os.environ['SIMSHELF_OUTPUT_POLICY'] == 'stale-inherited-value'
