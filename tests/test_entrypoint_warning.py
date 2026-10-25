"""Named warning uses primary bytes/declarations, never whole-snapshot changes."""
import json

import pytest
from fastapi.testclient import TestClient

from simshelf.api import create_app
from simshelf.backup import create_backup, restore_backup
from simshelf.entrypoint_warning import EntrypointWarnings
from simshelf.source import blob_path
from test_source_comparison import managed_bytes
from test_swss_versions import fixture, record, HEADER


def check(store, run):
    return EntrypointWarnings(store).check(run)


@pytest.mark.parametrize('change', ['helper', 'json', 'outputs', 'permissions', 'toml', 'capture', 'arguments'])
def test_non_primary_changes_never_warn(tmp_path, change):
    root, store, sim = fixture(tmp_path, 'VERSION="A"\nvalue=1\n')
    baseline = record(store, sim)
    if change == 'helper':
        (root/'helper.py').write_text('value=2\n')
    elif change == 'json':
        (root/'settings.json').write_text('{"value":2}')
    elif change == 'outputs':
        (root/'old_runs').mkdir()
        (root/'old_runs'/'copy.py').write_text('value=999\n')
        (root/'old_runs'/'data.json').write_text('{}')
    elif change == 'permissions':
        (root/'sim.py').chmod(0o755)
    elif change == 'toml':
        (root/'swss.toml').write_text(HEADER+'# metadata edit\n')
    elif change == 'capture':
        sim = store.update_simulation(sim['id'], config={**sim['config'], 'output_dir':'other'})
    elif change == 'arguments':
        from simshelf.recording import Run
        with Run(sim['id'], workspace=store.path, parameters={'N':2}, command=['python','sim.py','--N','2'], capture_console=False) as run:
            pass
        current = store.run(run.id)
    if change != 'arguments':
        current = record(store, sim)
    assert check(store, current)['status'] == 'same'
    assert store.versions(sim['id'])[0]['changed'] == 0
    assert store.run(baseline['id']) == baseline


@pytest.mark.parametrize('edit', ['# comment\n', 'value=2\n'])
@pytest.mark.parametrize('tag', ['', 'VERSION="A"\n', 'SIMSHELF_VERSION="A"\n', '__version__: str="A"\n'])
def test_primary_byte_edit_warns_even_comments(tmp_path, edit, tag):
    root, store, sim = fixture(tmp_path, tag+'value=1\n')
    record(store, sim)
    (root/'sim.py').write_text(tag+'value=1\n'+edit)
    current = record(store, sim)
    assert check(store, current)['warn']
    assert store.versions(sim['id'])[0]['changed'] == 1


@pytest.mark.parametrize('bump', ['python', 'toml', 'both'])
def test_version_changes_suppress_warning_without_relabelling(tmp_path, bump):
    root, store, sim = fixture(tmp_path, 'VERSION="A"\nvalue=1\n')
    baseline = record(store, sim)
    (root/'sim.py').write_text(('VERSION="B"\n' if bump != 'toml' else 'VERSION="A"\n')+'value=2\n')
    if bump != 'python':
        (root/'swss.toml').write_text(HEADER.replace('0.1.3', '0.1.4'))
    current = record(store, sim)
    assert not check(store, current)['warn']
    assert store.run(baseline['id']) == baseline
    assert all(group['changed'] == 0 for group in store.versions(sim['id']))


def test_historical_contamination_apis_counts_and_provenance(tmp_path):
    root, store, sim = fixture(tmp_path, 'VERSION="A"\npass\n')
    (root/'old_runs').mkdir()
    (root/'old_runs'/'copy.py').write_text('value=999\n')
    baseline = record(store, sim)
    sim = store.update_simulation(sim['id'], config={**sim['config'], 'output_dir':'old_runs'})
    unchanged = record(store, sim)
    (root/'sim.py').write_text('VERSION="A"\npass\n# comment\n')
    changed = record(store, sim)
    # Simulate records from accepted main: no newly added entrypoint identity.
    with store.connection() as conn:
        for run in (baseline, unchanged, changed):
            run.pop('source_entrypoint')
            conn.execute('UPDATE runs SET data=? WHERE id=?', (json.dumps({k:v for k,v in run.items() if k not in {'snapshot','artifacts','metrics','metric_count','annotation_history','baseline_deleted'}}), run['id']))
    original = managed_bytes(store)
    with store.connection() as conn:
        rows = [r[0] for r in conn.execute('SELECT data FROM runs')]
    with TestClient(create_app(store.path)) as client:
        history = {r['id']:r for r in client.get('/api/runs').json()}
        assert unchanged['source_change'] == 'changed'
        assert not history[unchanged['id']]['entrypoint_warning']['warn']
        assert history[changed['id']]['entrypoint_warning']['warn']
        for ident, run in history.items():
            detail = client.get(f'/api/runs/{ident}').json()
            assert detail['entrypoint_warning'] == run['entrypoint_warning']
        assert client.get(f"/api/simulations/{sim['id']}/versions").json()[0]['changed'] == 1
        assert client.get(f"/api/runs/{unchanged['id']}/source-comparison").json()['counts']['removed'] == 1
        assert managed_bytes(store) == original
        with store.connection() as conn:
            assert [r[0] for r in conn.execute('SELECT data FROM runs')] == rows
        from test_portal import headers
        saved = client.patch(f"/api/runs/{changed['id']}", headers=headers(client), json={'name':changed['name']}).json()
        assert saved['entrypoint_warning']['warn']
    # Annotation above is deliberately separate; inspect read-only checks anew.
    original = managed_bytes(store)
    with store.connection() as conn:
        rows = [r[0] for r in conn.execute('SELECT data FROM runs')]
    store.versions(sim['id'])
    for run in store.runs():
        check(store, run)
    assert managed_bytes(store) == original
    with store.connection() as conn:
        assert [r[0] for r in conn.execute('SELECT data FROM runs')] == rows
    store.remove_runs([baseline['id']], confirmed=True)
    assert check(store, changed)['warn']
    assert not check(store, unchanged)['warn']
    restored = restore_backup(create_backup(store, tmp_path/'backup.zip'), tmp_path/'restored')
    assert check(restored, changed) == check(store, changed)


@pytest.mark.parametrize('fault', ['missing', 'corrupt', 'oversized', 'dynamic', 'stale', 'association'])
def test_unavailable_evidence_does_not_guess(tmp_path, fault):
    root, store, sim = fixture(tmp_path, 'VERSION="A"\npass\n')
    baseline = record(store, sim)
    (root/'sim.py').write_text('VERSION="A"\npass\n# edit\n')
    if fault == 'dynamic':
        (root/'sim.py').write_text('VERSION=read_version()\n')
    elif fault == 'oversized':
        (root/'sim.py').write_text('#'+('x'*(1024*1024))+'\n')
    elif fault == 'stale':
        (root/'swss.toml').write_text(HEADER+'[[swss.source_files]]\npath="sim.py"\nsha256="'+'0'*64+'"\n')
    current = record(store, sim)
    if fault in {'missing', 'corrupt'}:
        entry = next(f for f in baseline['snapshot']['files'] if f['path']=='sim.py')
        path = blob_path(store.path, entry['blob'])
        path.unlink() if fault == 'missing' else path.write_bytes(b'corrupt')
    elif fault == 'association':
        current['source_entrypoint'] = 'different.py'
    result = check(store, current)
    assert result['status'] == 'unavailable' and result['detail'] and not result['warn']


def test_legacy_registered_primary_and_old_unknown_identity(project):
    store, sim, root, source = project
    baseline = record(store, sim)
    source.write_text(source.read_text()+'# comment\n')
    changed = record(store, sim)
    assert check(store, changed)['warn']
    changed.pop('source_entrypoint')
    assert check(store, changed)['status'] == 'unavailable'


def test_bound_edit_revert_and_live_registration_do_not_rewrite_warning(tmp_path):
    import hashlib
    root, store, sim = fixture(tmp_path, 'VERSION="A"\npass\n')
    def bind():
        sha = hashlib.sha256((root/'sim.py').read_bytes()).hexdigest()
        (root/'swss.toml').write_text(HEADER+f'[[swss.source_files]]\npath="sim.py"\nsha256="{sha}"\n')
    bind()
    record(store, sim)
    (root/'sim.py').write_text('VERSION="A"\npass\n# comment\n')
    bind()
    changed = record(store, sim)
    assert check(store, changed)['warn']
    (root/'sim.py').write_text('VERSION="A"\npass\n')
    bind()
    assert check(store, record(store, sim))['status'] == 'same'
    (root/'other.py').write_text('VERSION="B"\n')
    store.update_simulation(sim['id'], entrypoint='other.py')
    assert check(store, changed)['warn']
