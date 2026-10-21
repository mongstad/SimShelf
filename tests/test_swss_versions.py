"""SWSS version authority, legacy fallback and immutable recording evidence."""
import hashlib
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from simshelf.api import create_app
from simshelf.parameters import discover_parameters
from simshelf.recording import Run
from simshelf.source import blob_path
from simshelf.store import Store
from simshelf.swss import review
from test_portal import finish, headers, settings

HEADER = '[swss]\nschema_version=2\nentrypoint="sim.py"\nsimulation_version="0.1.3"\n'


def fixture(tmp_path, source='raise RuntimeError("discovery must not execute")\n', companion=HEADER):
    root = tmp_path/'source'; root.mkdir()
    (root/'sim.py').write_text(source)
    if companion is not None:
        (root/'swss.toml').write_text(companion)
    store = Store(tmp_path/'library')
    sim = store.add_simulation(root, entrypoint='sim.py')
    return root, store, sim


def record(store, sim):
    with Run(sim['id'], workspace=store.path, capture_console=False) as run:
        pass
    return store.run(run.id)


@pytest.mark.parametrize('tag', ['', 'SIMSHELF_VERSION="different"\n', 'SIMSHELF_VERSION=unknown_call()\n'])
def test_swss_version_does_not_read_or_execute_legacy_tag(tmp_path, tag):
    root, store, sim = fixture(tmp_path, tag + 'raise RuntimeError("not executed")\n')
    d = discover_parameters(sim)
    assert d['provenance']['binding_status'] == 'binding unverified'
    assert d['provenance']['comparable_version'] is None
    assert not d['provenance']['binding_reasons']
    assert review(sim, {'mode':'typed','fingerprint':d['fingerprint']})
    result = record(store, sim)
    assert result['version'] == '0.1.3'
    assert result['parameter_metadata']['provenance']['simulation_version'] == '0.1.3'
    assert store.versions(sim['id'])[0]['version'] == '0.1.3'
    assert result['parameter_metadata']['provenance']['bytes_utf8'] == HEADER


@pytest.mark.parametrize('source,expected', [('SIMSHELF_VERSION="legacy"\n', 'legacy'), ('pass\n', 'unversioned')])
def test_no_companion_preserves_legacy_version(tmp_path, source, expected):
    _, store, sim = fixture(tmp_path, source, None)
    assert record(store, sim)['version'] == expected


@pytest.mark.parametrize('companion', ['not toml', HEADER.replace('schema_version=2','schema_version=3'),
                                     HEADER + '[[swss.source_files]]\npath="sim.py"\nsha256="'+'0'*64+'"\n'])
def test_disputed_companion_never_uses_legacy_tag(tmp_path, companion):
    root, store, sim = fixture(tmp_path, 'SIMSHELF_VERSION="legacy"\n', companion)
    d = discover_parameters(sim)
    assert d['warnings'] and not d['parameters']
    assert review(sim, {'mode':'manual','fingerprint':None})
    result = record(store, sim)
    assert result['version'] == 'unversioned'
    assert result['parameter_metadata']['warnings']
    snapshot = json.loads((store.path/'snapshots'/f"{result['snapshot_id']}.json").read_text())
    saved = next(f for f in snapshot['files'] if f['path']=='swss.toml')
    assert blob_path(store.path, saved['blob']).read_text() == companion


def test_companion_changes_preserve_historical_versions_and_review(tmp_path):
    root, store, sim = fixture(tmp_path)
    before = record(store, sim)
    first = discover_parameters(sim)
    (root/'swss.toml').write_text(HEADER.replace('0.1.3','0.1.4'))
    with pytest.raises(ValueError, match='changed'):
        review(sim, {'mode':'typed','fingerprint':first['fingerprint']})
    after = record(store, sim)
    assert after['version']=='0.1.4' and after['snapshot_id']!=before['snapshot_id']
    assert store.run(before['id'])==before
    assert before['parameter_metadata']['provenance']['simulation_version']=='0.1.3'


@pytest.mark.parametrize('changed', ['swss.toml', 'sim.py'])
def test_mutation_during_snapshot_cannot_record_old_reviewed_version(tmp_path, monkeypatch, changed):
    root, store, sim = fixture(tmp_path, 'pass\n')
    digest = hashlib.sha256((root/'sim.py').read_bytes()).hexdigest()
    (root/'swss.toml').write_text(HEADER + f'[[swss.source_files]]\npath="sim.py"\nsha256="{digest}"\n')
    import simshelf.recording as recording
    original = recording.source_snapshot
    def mutate(*args, **kwargs):
        target = root/changed
        target.write_text(target.read_text() + '\n# changed during capture\n')
        return original(*args, **kwargs)
    monkeypatch.setattr(recording, 'source_snapshot', mutate)
    with pytest.raises(ValueError, match='changed'):
        record(store, sim)
    assert store.runs(sim['id']) == []


def test_portal_displays_and_records_swss_version_with_exact_argv(tmp_path):
    root, store, sim = fixture(tmp_path, 'import sys\nprint(repr(sys.argv[1:]))\n')
    argv=['--label', '', '--N', '00192']
    with TestClient(create_app(store.path)) as client:
        d=client.get(f"/api/simulations/{sim['id']}/parameters").json()
        config=settings(arguments=argv, parameter_review={'mode':'typed','fingerprint':d['fingerprint']})
        auth=headers(client)
        response=client.post(f"/api/simulations/{sim['id']}/launch",headers=auth,json=config)
        assert response.status_code==201,response.text
        result=finish(store,response.json()['run_id'])
        assert result['version']=='0.1.3' and result['command'][2:]==argv
        assert result['parameter_metadata']['argv']==argv
        versions=client.get(f"/api/simulations/{sim['id']}/versions").json()
        assert versions[0]['version']=='0.1.3'


def test_invalid_companion_removed_during_capture_does_not_fall_back(tmp_path, monkeypatch):
    root, store, sim = fixture(tmp_path, 'SIMSHELF_VERSION="legacy"\n', 'not toml')
    import simshelf.recording as recording
    original = recording.source_snapshot
    def remove(*args, **kwargs):
        (root/'swss.toml').unlink()
        return original(*args, **kwargs)
    monkeypatch.setattr(recording, 'source_snapshot', remove)
    result = record(store, sim)
    assert result['version'] == 'unversioned'
    assert result['parameter_metadata']['warnings']


def test_existing_legacy_run_is_not_relabelled_after_swss_adoption(tmp_path):
    root, store, sim = fixture(tmp_path, 'SIMSHELF_VERSION="legacy"\n', None)
    old = record(store, sim)
    digest = hashlib.sha256((root/'sim.py').read_bytes()).hexdigest()
    (root/'swss.toml').write_text(HEADER + f'[[swss.source_files]]\npath="sim.py"\nsha256="{digest}"\n')
    d = discover_parameters(sim)
    assert d['provenance']['binding_status'] == 'listed bytes verified'
    new = record(store, sim)
    assert new['version'] == '0.1.3'
    assert store.run(old['id']) == old and old['version'] == 'legacy'
    assert {v['version'] for v in store.versions(sim['id'])} == {'legacy', '0.1.3'}
