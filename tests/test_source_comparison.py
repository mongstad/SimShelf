"""Frozen baseline evidence and current-schema SWSS version transitions."""
import hashlib
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from simshelf.api import create_app
from simshelf.backup import create_backup, restore_backup
from simshelf.parameters import discover_parameters
from simshelf.recording import Run
from simshelf.source import blob_path
from simshelf.source_comparison import compare_sources
from simshelf.store import Store
from test_portal import finish, headers, settings


def record(store, sim):
    with Run(sim['id'], workspace=store.path, capture_console=False) as run:
        pass
    return store.run(run.id)


def managed_bytes(store):
    return {p.relative_to(store.path).as_posix(): p.read_bytes()
            for folder in ('snapshots', 'blobs', 'journal') for p in (store.path / folder).rglob('*') if p.is_file()}


def test_all_paths_classification_and_removed_preview_preserve_evidence(project):
    store, sim, root, source = project
    (root / 'helper.py').write_text('value=1\n')
    (root / 'settings.json').write_text('{"n":1}')
    (root / 'old.json').write_text('{"old":true}\n')
    (root / 'mode.py').write_text('pass\n')
    baseline = record(store, sim)
    source.write_text(source.read_text() + '# comment only\n')
    (root / 'helper.py').write_text('value=2\n')
    (root / 'settings.json').write_text('{"n":2}')
    (root / 'old.json').unlink()
    (root / 'new.json').write_text('{}')
    (root / 'mode.py').chmod(0o755)
    current = record(store, sim)
    original = managed_bytes(store)
    report = compare_sources(store, current['id'])
    changes = {row['path']: row for row in report['changes']}
    assert report['baseline']['id'] == baseline['id']
    assert report['counts'] == {'added': 1, 'removed': 1, 'changed': 4, 'unchanged': 0}
    assert changes['field.py']['classification'] == 'python-text'
    assert changes['helper.py']['classification'] == 'python-structure'
    assert changes['settings.json']['classification'] == 'non-python'
    assert changes['mode.py']['classification'] == 'permissions'
    assert changes['mode.py']['permissions_changed']
    with TestClient(create_app(store.path)) as client:
        result = client.get(f"/api/runs/{current['id']}/source-comparison")
        assert result.status_code == 200
        removed = client.get(f"/api/runs/{current['id']}/source", params={'path': 'old.json', 'compare': baseline['id']})
        assert removed.status_code == 200 and '-{"old":true}' in removed.json()['text']
        permissions = client.get(f"/api/runs/{current['id']}/source", params={'path': 'mode.py', 'compare': baseline['id']})
        assert 'Permissions changed' in permissions.json()['text']
        assert client.get(f"/api/runs/{current['id']}/source", params={'path': 'old.json'}).status_code == 400
    assert store.run(baseline['id']) == baseline and store.run(current['id']) == current
    assert managed_bytes(store) == original


def test_contaminated_baseline_and_selection_explanation_do_not_guess_ownership(project, tmp_path):
    store, sim, root, source = project
    # An undeclared old output tree was source in the baseline. Only the explicit
    # subsequent capture boundary establishes why these paths are now excluded.
    output = root / 'research_results' / 'earlier' / 'nested'
    output.mkdir(parents=True)
    (output / 'model.py').write_bytes(source.read_bytes())
    (output / 'summary.json').write_text('{"old":true}')
    (root / 'legitimate_run_named_input.json').write_text('{}')
    baseline = record(store, sim)
    sim = store.update_simulation(sim['id'], config={**sim['config'], 'output_dir': 'research_results'})
    current = record(store, sim)
    assert current['source_change'] == 'changed'
    report = compare_sources(store, current['id'])
    assert report['counts']['removed'] == 2
    assert all(row['output_boundary'] == 'research_results' for row in report['changes'])
    assert any(change['field'] == 'output_dirs' for change in report['selection_changes'])
    assert any('baseline includes 2 removed' in note for note in report['notes'])
    assert any(f['path'] == 'legitimate_run_named_input.json' for f in current['snapshot']['files'])
    original = managed_bytes(store)
    assert store.run(baseline['id']) == baseline
    store.remove_runs([baseline['id']], confirmed=True)
    report = compare_sources(store, current['id'])
    assert report['baseline']['id'] == baseline['id'] and report['baseline']['deleted']
    assert any('incomplete' in note for note in report['notes'])
    restored = restore_backup(create_backup(store, tmp_path / 'backup.zip'), tmp_path / 'restored')
    assert compare_sources(restored, current['id']) == report
    with TestClient(create_app(restored.path)) as client:
        path = 'research_results/earlier/nested/summary.json'
        result = client.get(f"/api/runs/{current['id']}/source", params={'path': path, 'compare': baseline['id']})
        assert result.status_code == 200 and '-{"old":true}' in result.json()['text']
    assert all((store.path / name).read_bytes() == data for name, data in original.items() if name.startswith(('blobs/', 'snapshots/')))


def test_history_without_selection_is_explicit_and_does_not_read_current_settings(project):
    store, sim, root, source = project
    baseline = record(store, sim)
    (root / 'settings.json').write_text('{}')
    current = record(store, sim)
    # Emulate pre-feature records; no production migration or rewrite is involved.
    with store.connection() as conn:
        for run in (baseline, current):
            data = json.loads(conn.execute('SELECT data FROM runs WHERE id=?', (run['id'],)).fetchone()[0])
            data.pop('source_selection')
            conn.execute('UPDATE runs SET data=? WHERE id=?', (json.dumps(data), run['id']))
    sim = store.update_simulation(sim['id'], config={**sim['config'], 'output_dir': 'settings.json'})
    report = compare_sources(store, current['id'])
    assert report['changes'][0]['path'] == 'settings.json'
    assert report['changes'][0]['output_boundary'] is None
    assert not report['selection_changes']
    assert any('Historical source-selection' in note for note in report['notes'])


def test_pattern_changes_are_separate_from_real_changes(project):
    store, sim, root, source = project
    (root / 'input.json').write_text('{"n":1}')
    baseline = record(store, sim)
    sim = store.update_simulation(sim['id'], config={**sim['config'], 'source_exclude': ['**/*.json', *sim['config']['source_exclude']]})
    source.write_text(source.read_text() + 'value = 3\n')
    current = record(store, sim)
    report = compare_sources(store, current['id'])
    assert {item['path']: item['classification'] for item in report['changes']} == {'field.py': 'python-structure', 'input.json': 'non-python'}
    assert report['selection_changes'][0]['field'] == 'source_exclude'
    assert report['recorded_change'] == 'changed' and current['baseline_run_id'] == baseline['id']


def test_historical_capture_setting_can_explain_consistency_without_claiming_cause(project):
    store, sim, root, source = project
    old = root / 'research_results' / 'old'; old.mkdir(parents=True)
    (old / 'summary.json').write_text('{}')
    baseline = record(store, sim)
    sim = store.update_simulation(sim['id'], config={**sim['config'], 'output_dir':'research_results'})
    current = record(store, sim)
    with store.connection() as conn:
        data = json.loads(conn.execute('SELECT data FROM runs WHERE id=?', (current['id'],)).fetchone()[0])
        data.pop('source_selection')
        conn.execute('UPDATE runs SET data=? WHERE id=?', (json.dumps(data), current['id']))
    store.update_simulation(sim['id'], config={**sim['config'], 'output_dir':'different_today'})
    report = compare_sources(store, current['id'])
    row = report['changes'][0]
    assert row['output_boundary'] == 'research_results' and not row['output_boundary_confirmed']
    assert any('consistent with corrected output exclusion' in note for note in report['notes'])
    assert report['baseline']['id'] == baseline['id']


def test_pagination_limits_and_missing_or_corrupt_bytes(project):
    store, sim, root, source = project
    (root / 'broken.py').write_text('pass\n')
    record(store, sim)
    for number in range(205):
        (root / f'added_{number:03}.json').write_text('{}')
    (root / 'broken.py').write_text('broken python (\n')
    current = record(store, sim)
    first = compare_sources(store, current['id'], limit=200)
    last = compare_sources(store, current['id'], offset=200, limit=200)
    assert first['total'] == 206 and len(first['changes']) == 200 and len(last['changes']) == 6
    assert last['changes'][-1]['classification'] == 'python-unverified'
    for offset, limit in [(-1, 1), (0, 0), (0, 201)]:
        with pytest.raises(ValueError): compare_sources(store, current['id'], offset, limit)
    with pytest.raises(ValueError, match='not found'): compare_sources(store, 'missing')
    entry = next(f for f in current['snapshot']['files'] if f['path'] == 'broken.py')
    blob_path(store.path, entry['blob']).write_bytes(b'corrupt fixture blob')
    report = compare_sources(store, current['id'], offset=205)
    assert report['changes'][0]['classification'] == 'python-unverified'
    assert 'integrity' in report['changes'][0]['detail']
    manifest = store.path / 'snapshots' / f"{current['snapshot_id']}.json"
    data = json.loads(manifest.read_text()); data['files'][0]['mode'] = 0
    manifest.write_text(json.dumps(data))
    with pytest.raises(ValueError, match='manifest failed integrity'): compare_sources(store, current['id'])


def test_large_python_not_parsed_and_large_baseline_never_shown_as_addition(project):
    store, sim, root, source = project
    (root / 'large.py').write_text('#' + 'x' * (1024 * 1024))
    baseline = record(store, sim)
    (root / 'large.py').write_text('pass\n')
    current = record(store, sim)
    report = compare_sources(store, current['id'])
    assert report['changes'][0]['classification'] == 'python-unverified'
    with TestClient(create_app(store.path)) as client:
        result = client.get(f"/api/runs/{current['id']}/source", params={'path': 'large.py', 'compare': baseline['id']})
        assert result.status_code == 400 and 'including the baseline' in result.json()['detail']


def test_ast_page_budget_limits_retained_byte_reads(project):
    store, sim, root, source = project
    for index in range(5):
        (root / f'helper_{index}.py').write_text('#' + 'a' * 900_000)
    record(store, sim)
    for index in range(5):
        (root / f'helper_{index}.py').write_text('#' + 'b' * 900_000)
    current = record(store, sim)
    report = compare_sources(store, current['id'])
    assert [row['classification'] for row in report['changes']] == ['python-text'] * 4 + ['python-unverified']
    assert '8 MB/page' in report['changes'][-1]['detail']


def test_empty_and_non_utf8_differences_are_not_reported_as_unchanged(project):
    store, sim, root, source = project
    (root / 'binary.txt').write_bytes(b'\xff')
    (root / 'removed.txt').write_bytes(b'')
    baseline = record(store, sim)
    (root / 'binary.txt').write_bytes(b'\xfe')
    (root / 'removed.txt').unlink()
    (root / 'added.txt').write_bytes(b'')
    current = record(store, sim)
    with TestClient(create_app(store.path)) as client:
        for path, expected in [('binary.txt', 'Recorded bytes differ'), ('removed.txt', 'File removed'), ('added.txt', 'File added')]:
            response = client.get(f"/api/runs/{current['id']}/source", params={'path':path,'compare':baseline['id']})
            assert response.status_code == 200 and expected in response.json()['text']


@pytest.mark.parametrize('edit_source', [False, True])
def test_portal_version_A_B_baselines_fixed_outputs_and_stale_bindings(tmp_path, edit_source):
    root = tmp_path / 'source'; root.mkdir()
    script = root / 'model.py'
    script.write_text('''from pathlib import Path
import uuid, sys, json
VERSION='0.3.1'
SIMSHELF_VERSION='legacy-does-not-own-swss'
out = Path(__file__).parent / 'results' / ('run_' + uuid.uuid4().hex)
out.mkdir(parents=True)
(out/'fixture.log').write_text('closed')
(out/'summary.json').write_text(json.dumps(sys.argv[1:]))
''')
    def declare(version, digest=None):
        sha = digest or hashlib.sha256(script.read_bytes()).hexdigest()
        (root / 'swss.toml').write_text(f'[swss]\nschema_version=2\nentrypoint="model.py"\nsimulation_version="{version}"\n[[swss.source_files]]\npath="model.py"\nsha256="{sha}"\n')
    declare('0.3.1')
    store = Store(tmp_path / 'library'); sim = store.add_simulation(root, entrypoint='model.py', config={'output_dir': 'results'})
    argv = ['--label', '', '--seed', '007', '--', '--literal']
    with TestClient(create_app(store.path)) as client:
        auth = headers(client); base = f"/api/simulations/{sim['id']}"
        def launch(typed=True):
            discovery = client.get(base + '/parameters').json()
            data = settings(arguments=argv, output_dir='results', parameter_review={'mode': 'typed' if typed else 'manual', 'fingerprint': discovery['fingerprint']})
            response = client.post(base + '/launch', headers=auth, json=data)
            assert response.status_code == 201, response.text
            return finish(store, response.json()['run_id'])
        a = launch(); repeat = launch()
        assert a['version'] == repeat['version'] == '0.3.1' and repeat['source_change'] == 'same'
        if edit_source: script.write_text(script.read_text().replace("VERSION='0.3.1'", "VERSION='0.3.2'"))
        declare('0.3.2')
        b = launch(); again = launch()
        assert b['version'] == '0.3.2' and b['baseline_run_id'] == b['id']
        assert again['source_change'] == 'same' and again['baseline_run_id'] == b['id']
        (root / 'helper.py').write_text('value=1\n')
        helper = launch()
        report = client.get(f"/api/runs/{helper['id']}/source-comparison").json()
        assert [row['path'] for row in report['changes']] == ['helper.py']
        unchanged = client.get(f"/api/runs/{helper['id']}/source", params={'path': 'model.py', 'compare': b['id']})
        assert unchanged.json()['text'] == 'No changes in this file.'
        assert helper['source_change'] == 'changed' and helper['version'] == '0.3.2'
        declare('0.3.2', '0' * 64)
        stale = launch(False)
        assert stale['version'] == 'unversioned'
        assert 'Source binding changed: model.py' in stale['parameter_metadata']['provenance']['binding_reasons']
        bad = client.post(base + '/launch', headers=auth, json=settings(output_dir='results', parameter_review={'mode': 'typed', 'fingerprint': discover_parameters(sim)['fingerprint']}))
        assert bad.status_code == 400 and 'Rescan' in bad.json()['detail']
        assert store.run(a['id']) == a
        assert {v['version'] for v in client.get(base + '/versions').json()} == {'0.3.1', '0.3.2', 'unversioned'}
    for run in (a, repeat, b, again, helper):
        assert run['command'][2:] == argv and run['capture_status'] == 'complete'
        assert not any(f['path'].startswith('results/') for f in run['snapshot']['files'])
        summary = next(f for f in run['artifacts'] if f['name'].endswith('summary.json'))
        assert json.loads(blob_path(store.path, summary['blob']).read_bytes()) == argv
