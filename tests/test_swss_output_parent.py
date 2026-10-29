"""Schema-3 consumer tests use only disposable, deliberately harmless sources."""
import hashlib
import json
import sys
from pathlib import Path

import pytest

from simshelf.store import Store
from simshelf.recording import record_command
from simshelf.portal import execution_settings
from simshelf.swss import read, parse
from simshelf.swss_output import resolve, review, recheck
from simshelf.output_paths import output_review

HEADER = '[swss]\nschema_version=3\nentrypoint="solver/sim.py"\nsimulation_version="1.0.0"\n'
ROW = '''
[[swss.parameters]]
id="destination"
kind="option"
options=["--destination", "-o"]
required=false
type="string"
action="store"
help="Parent for generated children"
'''


@pytest.fixture
def project3(tmp_path):
    root = tmp_path / 'source'
    (root / 'solver').mkdir(parents=True)
    source = root / 'solver/sim.py'
    source.write_text('''import argparse, pathlib, tomllib, uuid
p=argparse.ArgumentParser()
p.add_argument('--destination', '-o')
a=p.parse_args()
root=pathlib.Path(__file__).resolve().parents[1]
config=tomllib.loads((root/'swss.toml').read_text())['swss']
parent=root/(a.destination or config.get('output_parent', 'outputs'))
child=parent/('run_20261029T000000Z_'+uuid.uuid4().hex)
child.mkdir(parents=True, exist_ok=False)
(child/'run.log').write_text('completed\\n')
(child/'summary.json').write_text('{"value": 42}')
''')
    (root / 'swss.toml').write_text(HEADER + 'output_parent_parameter="destination"\n' + ROW)
    (root / 'input.json').write_text('{"input": true}')
    (root / 'outputs-lookalike').mkdir()
    (root / 'outputs-lookalike/input.json').write_text('{}')
    store = Store(tmp_path / 'workspace')
    sim = store.add_simulation(root, entrypoint='solver/sim.py')
    return root, store, sim


@pytest.mark.parametrize('argv', [[], ['--destination=results/custom'], ['-o', 'results/custom'], ['--destination', 'results/custom']])
def test_repeated_runs_capture_exact_argv_source_and_history(project3, argv):
    root, store, sim = project3
    old = root / 'outputs/older'
    old.mkdir(parents=True)
    (old / 'copied.py').write_text('old output, not source')
    expected = root / ('results/custom' if argv else 'outputs')
    records = []
    original = (root/'swss.toml').read_bytes()
    for _ in range(2):
        ident, code = record_command(store, sim['id'], [sys.executable, str(root/'solver/sim.py'), *argv], cwd=root/'solver', quiet=True)
        assert code == 0
        run = store.run(ident)
        assert run['capture_root'] == str(expected)
        assert run['capture_status'] == 'complete'
        assert run['command'][2:] == argv
        assert run['swss_output_location']['allocation'] == 'simulation-owned standalone child'
        assert {f['path'] for f in run['snapshot']['files']} == {'solver/sim.py', 'swss.toml', 'input.json', 'outputs-lookalike/input.json'}
        assert {Path(a['name']).name for a in run['artifacts']} == {'run.log', 'summary.json'}
        records.append(run)
    assert records[0]['snapshot_id'] == records[1]['snapshot_id']
    assert store.run(records[0]['id']) == records[0]
    assert (old/'copied.py').read_text() == 'old output, not source'
    assert (root/'swss.toml').read_bytes() == original
    assert len(list(expected.glob('run_*'))) == 2


def test_custom_default_external_and_changed_preview(project3, tmp_path):
    root, store, sim = project3
    path = root/'swss.toml'
    path.write_text(HEADER + 'output_parent="generated/runs"\noutput_parent_parameter="destination"\n' + ROW)
    empty = review(sim, [], 'outputs', 'auto')
    assert empty['parent'] == str(root/'generated/runs')
    external = tmp_path/'external'
    external.mkdir()
    argv = ['--destination', str(external)]
    preview = output_review(sim, '.', argv, 'outputs', [], output_mode='auto')
    settings = {'interpreter': sys.executable, 'arguments': argv, 'cwd': '.', 'output_dir': 'outputs', 'output_mode': 'auto', 'output_revision': preview['output_revision']}
    plan = execution_settings(sim, settings)
    ident, code = record_command(store, sim['id'], plan['command'], cwd=root, quiet=True, output_dir='outputs',
                                launch={'kind': 'portal', 'output_mode': 'auto', 'output_review': plan['output_review']})
    assert code == 0 and store.run(ident)['capture_status'] == 'complete'
    assert store.run(ident)['capture_root'] == str(external)
    external.rename(tmp_path/'original-external')
    external.mkdir()
    with pytest.raises(ValueError, match='changed'):
        execution_settings(sim, settings)
    with pytest.raises(ValueError, match='changed'):
        recheck(preview['swss_output_location'])
    with pytest.raises(ValueError, match='already exist'):
        review(sim, ['-o', str(tmp_path/'missing-volume/output')], 'outputs', 'auto')
    assert not (tmp_path/'missing-volume').exists()


@pytest.mark.parametrize('argv', [['--destination'], ['--destination='], ['-o', ''], ['-o', 'a', '--destination=b'], ['-oa'], ['--unknown'], ['--', '-o', 'a'], ['--destination', '--other'], ['positional']])
def test_ambiguous_args_require_manual_review_without_mutation(project3, argv):
    root, store, sim = project3
    original = list(argv)
    with pytest.raises(ValueError):
        review(sim, argv, 'outputs', 'auto')
    manual = review(sim, argv, 'reviewed-parent', 'manual')
    assert manual['origin'] == 'reviewed manual mapping'
    assert manual['resolution_warning']
    assert argv == original and store.runs() == []
    assert not (root/'reviewed-parent').exists()


@pytest.mark.parametrize('value', ['../escape', '/', '.', 'solver', 'swss.toml', 'bad\x00path'])
def test_unsafe_parent_rejected(project3, value):
    root, store, sim = project3
    with pytest.raises(ValueError):
        review(sim, ['--destination='+value], 'outputs', 'auto')
    assert store.runs() == []


def test_symlinks_stale_binding_conflict_and_partial_capture(project3):
    root, store, sim = project3
    (root/'alias').symlink_to(root/'solver', target_is_directory=True)
    with pytest.raises(ValueError, match='symbolic'):
        review(sim, ['-o', 'alias'], 'outputs', 'auto')
    with pytest.raises(ValueError, match='conflicts'):
        review(sim, [], 'elsewhere', 'manual')
    path = root/'swss.toml'
    path.write_text(path.read_text() + '\n[[swss.source_files]]\npath="solver/sim.py"\nsha256="'+'0'*64+'"\n')
    with pytest.raises(ValueError, match='stale'):
        review(sim, [], 'outputs', 'auto')
    path.write_text(HEADER)
    (root/'solver/sim.py').write_text('raise SystemExit(3)\n')
    ident, code = record_command(store, sim['id'], [sys.executable, str(root/'solver/sim.py')], quiet=True)
    run = store.run(ident)
    assert code == 3 and run['status'] == 'failed'
    assert run['capture_status'] == 'partial'


@pytest.mark.parametrize('edit', [
    'output_parent="../bad"', 'output_parent="/bad"', 'output_parent="a/"',
    'output_parent="a//b"', 'output_parent="~user"', 'output_parent=3',
    'output_parent_parameter="missing"', 'output_parent_parameter=[]',
])
def test_invalid_schema3_parent_documents(edit):
    with pytest.raises(ValueError):
        parse((HEADER + edit + '\n').encode())


def test_schema2_no_new_semantics_and_invalid_binding(project3):
    root, _, sim = project3
    path = root/'swss.toml'
    path.write_text(HEADER.replace('schema_version=3', 'schema_version=2'))
    assert resolve(read(root)['provenance'], []) is None
    for tail in ('required=true', 'choices=["outputs"]', 'default="elsewhere"', 'repeatable=true'):
        doc = HEADER + 'output_parent_parameter="destination"\n' + ROW
        doc = doc.replace('required=false', tail) if tail.startswith('required') else doc + tail + '\n'
        with pytest.raises(ValueError):
            parse(doc.encode())


def test_prior_custom_parent_remains_excluded_and_source_edit_visible(project3):
    root, store, sim = project3
    original = None
    for parent in ('first-results', 'second-results'):
        ident, code = record_command(store, sim['id'], [sys.executable, str(root/'solver/sim.py'), '-o', parent], quiet=True)
        run = store.run(ident)
        assert code == 0
        assert not any(f['path'].startswith(('first-results/', 'second-results/')) for f in run['snapshot']['files'])
        if original:
            assert run['snapshot_id'] == original['snapshot_id']
        original = run
    (root/'input.json').write_text('{"input": "changed"}')
    ident, _ = record_command(store, sim['id'], [sys.executable, str(root/'solver/sim.py')], quiet=True)
    assert store.run(ident)['snapshot_id'] != original['snapshot_id']
    assert store.run(original['id']) == original


def test_schema3_portal_round_trip_and_revision_refusal(project3):
    from fastapi.testclient import TestClient
    from simshelf.api import create_app
    from test_portal import headers, finish
    root, store, sim = project3
    body = {'interpreter': sys.executable, 'cwd': 'solver', 'arguments': [], 'output_dir': 'outputs', 'output_mode': 'auto'}
    with TestClient(create_app(store.path)) as client:
        auth = headers(client)
        base = f"/api/simulations/{sim['id']}"
        validation = client.post(base+'/execution/validate', headers=auth, json=body)
        assert validation.status_code == 200, validation.text
        body['output_revision'] = validation.json()['output_review']['output_revision']
        launched = client.post(base+'/launch', headers=auth, json=body)
        assert launched.status_code == 201, launched.text
        run = finish(store, launched.json()['run_id'])
        assert run['capture_status'] == 'complete' and run['exit_code'] == 0
        # The newly created parent changes the review identity, so stale launch
        # requests must be revalidated instead of quietly reusing a preview.
        stale = client.post(base+'/launch', headers=auth, json=body)
        assert stale.status_code == 400 and 'changed' in stale.text


def test_pinned_schema3_reference(tmp_path):
    import os
    reference = os.environ.get('SIMSHELF_SCHEMA3_REFERENCE')
    if not reference:
        pytest.skip('Pinned schema-3 reference path not supplied')
    root = tmp_path/'reference'
    root.mkdir()
    hashes = {'simulate.py': '4a0095b3985e9ee225c901a59c101084c9125f9029d6e50baf35bb9181312585',
              'output_contract.py': '945137bee432e6dfb0516ad4c9601ab888dbdc7f32f321b9edca3a91372ecd93'}
    for name in ('simulate.py', 'output_contract.py', 'swss.toml'):
        data = (Path(reference)/name).read_bytes()
        if name in hashes:
            assert hashlib.sha256(data).hexdigest() == hashes[name]
        (root/name).write_bytes(data)
    store = Store(tmp_path/'library')
    sim = store.add_simulation(root, entrypoint='simulate.py')
    external = tmp_path/'external'
    external.mkdir()
    records = []
    for parent in (None, None, 'custom', str(external)):
        args = ['-k', '1e-1', '-n', '0010', '--dt=0.25', '--label', '']
        if parent:
            args += ['--output-parent', parent]
        ident, code = record_command(store, sim['id'], [sys.executable, str(root/'simulate.py'), *args], cwd=tmp_path, quiet=True)
        run = store.run(ident)
        assert code == 0 and run['capture_status'] == 'complete'
        assert run['version'] == '0.1.4' and run['command'][2:] == args
        assert run['capture_counts']['copied'] == 4
        assert {f['path'] for f in run['snapshot']['files']} == {'simulate.py', 'output_contract.py', 'swss.toml'}
        records.append(run)
    assert len({r['snapshot_id'] for r in records}) == 1
    for r in records:
        assert store.run(r['id']) == r


def test_schema3_archive_consent_and_backup_preserve_bytes(project3, tmp_path):
    from simshelf import git_archive as archive
    from simshelf.backup import create_backup, restore_backup
    from test_preservation import enable, verify
    root, store, sim = project3
    repo = tmp_path/'archive'
    repo.mkdir()
    archive.connect(store, str(repo), initialize=True, confirmed=True)
    archive.set_global_enabled(store, True)
    enable(store, sim)
    ident, code = record_command(store, sim['id'], [sys.executable, str(root/'solver/sim.py')], quiet=True)
    run = store.run(ident)
    assert code == 0
    event = verify(store, repo, run)
    assert event['record']['completeness'] == 'verified'
    backup = create_backup(store, tmp_path/'backup.zip')
    restored = restore_backup(backup, tmp_path/'restored')
    assert restored.run(ident)['snapshot'] == run['snapshot']
    assert restored.run(ident)['swss_output_location'] == run['swss_output_location']
    for artifact in run['artifacts']:
        assert restored.artifact_file(artifact['id']).read_bytes() == store.artifact_file(artifact['id']).read_bytes()
    with store.connection() as original, restored.connection() as other:
        assert list(original.execute("SELECT * FROM metadata WHERE key LIKE 'swss_output_boundaries:%'")) == list(other.execute("SELECT * FROM metadata WHERE key LIKE 'swss_output_boundaries:%'"))
    external = tmp_path/'external'
    external.mkdir()
    ident, code = record_command(store, sim['id'], [sys.executable, str(root/'solver/sim.py'), '-o', str(external)], quiet=True)
    assert code == 0 and store.run(ident)['capture_status'] == 'complete'
    assert archive.entries(store, ident) == []  # Never silently widen consent.


def test_boundary_write_failure_rolls_back_start_and_replays_atomically(project3):
    import sqlite3
    root, store, sim = project3
    with store.connection() as conn:
        conn.execute("CREATE TRIGGER reject_boundary BEFORE INSERT ON metadata WHEN NEW.key LIKE 'swss_output_boundaries:%' BEGIN SELECT RAISE(ABORT, 'injected boundary failure'); END")
    with pytest.raises(sqlite3.IntegrityError, match='injected'):
        record_command(store, sim['id'], [sys.executable, str(root/'solver/sim.py'), '-o', 'generated'], quiet=True)
    assert store.runs() == [] and not (root/'generated').exists()
    events = list((store.path/'journal').glob('*/*.json'))
    start = next(json.loads(p.read_text()) for p in events if json.loads(p.read_text())['kind'] == 'start')
    with store.connection() as conn:
        conn.execute('DROP TRIGGER reject_boundary')
    store.apply(start)
    store.apply(start)
    with store.connection() as conn:
        saved = conn.execute("SELECT value FROM metadata WHERE key LIKE 'swss_output_boundaries:%'").fetchone()
    assert 'generated' in json.loads(saved[0])
    assert len(store.runs()) == 1
    store.emit(start['run_id'], 'finish', {'status': 'interrupted', 'capture_status': 'incomplete'})


def test_inaccessible_parent_refused_before_recording(project3, monkeypatch):
    import simshelf.swss_output as module
    root, store, sim = project3
    monkeypatch.setattr(module.os, 'access', lambda *args: False)
    with pytest.raises(ValueError, match='inaccessible'):
        record_command(store, sim['id'], [sys.executable, str(root/'solver/sim.py')], quiet=True)
    assert store.runs() == [] and not (root/'outputs').exists()
