"""Output declarations never broaden capture or rewrite simulation arguments."""
import sys

import pytest
from fastapi.testclient import TestClient

from simshelf.api import create_app
from simshelf.backup import create_backup, restore_backup
from simshelf.output_paths import output_review
from test_portal import headers, settings, finish


def mapping(value, index=None, kind="file", form="token"):
    return {"argument_index": index, "value": value, "kind": kind, "format": form}


def test_review_literal_paths_mapping_and_no_source_execution(project):
    store, sim, root, source = project
    source.write_text("raise RuntimeError('never execute during path review')\n")
    (root / "working dir").mkdir()
    args = ["--custom=test file.wvz", "../outputs/data.csv", "$HOME/literal"]
    maps = [mapping(args[0], 0, form="equals"), mapping(args[1], 1), mapping("other logs", kind="directory")]
    result = output_review(sim, "working dir", args, "outputs", maps)
    assert result["output_path"] == str(root / "outputs")
    assert result["targets"][0]["suggested_argument"] == "--custom=../outputs/test file.wvz"
    assert result["targets"][0]["resolved_path"] == str(root / "working dir/test file.wvz")
    assert result["targets"][1]["covered"]
    assert not result["targets"][2]["covered"]
    assert result["requires_acknowledgement"]
    assert args == ["--custom=test file.wvz", "../outputs/data.csv", "$HOME/literal"]
    assert not (root / "outputs").exists()
    assert store.runs() == []
    result = output_review(sim, ".", [], "outputs", [mapping("~/file"), mapping("$HOME/file")])
    assert result["targets"][0]["resolved_path"] == str(root / "~/file")
    assert result["targets"][1]["resolved_path"] == str(root / "$HOME/file")


def test_declared_symlinks_and_outside_absolute_paths(project, tmp_path):
    store, sim, root, source = project
    (root / "outputs").mkdir()
    (root / "outputs/real").mkdir()
    (root / "outputs/link").symlink_to(root / "outputs/real", target_is_directory=True)
    result = output_review(sim, ".", [], "outputs", [mapping("outputs/link/new.csv"), mapping(str(tmp_path / "external.csv"))])
    assert all(not item["covered"] for item in result["targets"])
    assert "Symbolic link" in result["targets"][0]["reason"]
    outside = tmp_path / "outside"
    (outside / "child").mkdir(parents=True)
    (root / "outputs/escape").symlink_to(outside / "child", target_is_directory=True)
    escaped = output_review(sim, ".", [], "outputs", [mapping("outputs/escape/../file.csv")])
    assert escaped["targets"][0]["resolved_path"] == str(outside / "file.csv")
    assert not escaped["targets"][0]["covered"]
    (root / "loop").symlink_to(root / "loop")
    with pytest.raises(ValueError, match="Cannot inspect"):
        output_review(sim, ".", [], "outputs", [mapping("loop/file")])


@pytest.mark.parametrize("maps", [
    [mapping("old.csv", 0)], [mapping("new.csv", True)], [mapping("new.csv", 99)],
    [mapping("", None)], [mapping("x", kind="unknown")], [mapping("x", form="equals")],
    [mapping("x", None)] * 33, [{"unknown": "x"}],
])
def test_invalid_or_stale_mapping_rejected(project, maps):
    _, sim, _, _ = project
    with pytest.raises(ValueError):
        output_review(sim, ".", ["new.csv"], "outputs", maps)


def test_output_review_authorization_and_capture_root_constraints(project):
    store, sim, root, source = project
    with TestClient(create_app(store.path)) as client:
        url = f"/api/simulations/{sim['id']}/execution/outputs"
        body = {"cwd": ".", "arguments": [], "output_dir": "outputs", "output_mappings": []}
        assert client.post(url, json=body).status_code == 403
        auth = headers(client)
        assert client.post(url, headers={**auth, "Origin": "https://elsewhere.example"}, json=body).status_code == 403
        assert client.post(url, headers=auth, json=body).status_code == 200
        for output in [".", "../outside", str(root)]:
            assert client.post(url, headers=auth, json={**body, "output_dir": output}).status_code == 400
        assert not store.runs()


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="Portal execution is Linux-only")
def test_mismatch_aligned_capture_partial_failure_and_backup(project, tmp_path):
    store, sim, root, source = project
    source.write_text('''import sys
from pathlib import Path
SIMSHELF_VERSION = "1.0"
target = Path(sys.argv[1])
target.parent.mkdir(parents=True, exist_ok=True)
target.write_bytes(b"WVZ fixture")
for name in ["one.csv", "two.csv", "three.csv"]:
    (target.parent / name).write_text("value\\n1\\n")
(target.parent / "ignored.tmp").write_text("ignored")
(target.parent / "large.json").write_bytes(b"x" * 100)
if "--fail" in sys.argv: raise SystemExit(3)
''')
    # Capture limits/rules stay the authority, including for partial/failed runs.
    sim = store.update_simulation(sim['id'], config={**sim['config'], 'max_file_mb': .00005})
    with TestClient(create_app(store.path)) as client:
        auth = headers(client)
        base = f"/api/simulations/{sim['id']}"
        args = ["test-simshelf.wvz"]
        config = settings(arguments=args, output_mappings=[mapping(args[0], 0)])
        review = client.post(base + '/execution/validate', headers=auth, json=config).json()['output_review']
        assert review['requires_acknowledgement']
        denied = client.post(base + '/launch', headers=auth, json=config)
        assert denied.status_code == 400 and not store.runs()
        response = client.post(base + '/launch', headers=auth, json={**config, 'acknowledge_outputs': True})
        assert response.status_code == 201, response.text
        outside = finish(store, response.json()['run_id'])
        assert outside['status'] == 'completed' and outside['capture_status'] == 'complete'
        assert sum(outside['capture_counts'].values()) == 0
        assert outside['artifacts'] == []
        assert (root / 'test-simshelf.wvz').read_bytes() == b'WVZ fixture'
        assert not outside['launch']['output_review']['targets'][0]['covered']
        args = ['outputs with spaces/test-simshelf.wvz', '--fail']
        config = settings(arguments=args, output_dir='outputs with spaces', output_mappings=[mapping(args[0], 0), mapping('outputs with spaces', kind='directory')])
        assert client.put(base + '/execution', headers=auth, json=config).status_code == 200
        response = client.post(base + '/launch', headers=auth, json=config)
        assert response.status_code == 201, response.text
        aligned = finish(store, response.json()['run_id'])
        assert aligned['status'] == 'failed' and aligned['exit_code'] == 3
        assert aligned['capture_status'] == 'partial'
        assert aligned['capture_counts'] == {'copied': 3, 'referenced': 1, 'ignored': 1, 'skipped': 1, 'unchanged': 0}
        assert all(t['covered'] for t in aligned['launch']['output_review']['targets'])
        artifacts = client.get('/api/runs/' + aligned['id']).json()['artifacts']
        assert next(a for a in artifacts if a['name'].endswith('.wvz'))['availability'] == 'available'
        before = store.run(aligned['id'])
        assert client.put(base + '/execution', headers=auth, json=settings()).status_code == 200
        assert store.run(aligned['id']) == before
        # Restore the saved declarations for the backup round trip.
        assert client.put(base + '/execution', headers=auth, json=config).status_code == 200
        archive = create_backup(store, tmp_path / 'backup.zip')
    restored = restore_backup(archive, tmp_path / 'restored')
    assert restored.simulation(sim['id'])['execution']['output_mappings'] == config['output_mappings']
    assert restored.run(aligned['id'])['launch'] == before['launch']
    assert restored.run(aligned['id'])['snapshot'] == before['snapshot']
    assert not any(a.get('blob') for a in restored.run(aligned['id'])['artifacts'] if a['policy'] == 'reference')


@pytest.mark.parametrize('value,kind,exists', [
    ('outputs/new.csv', 'file', False),
    ('outputs/kept.csv', 'file', True),
    ('outputs/empty', 'directory', True),
    ('outputs/populated', 'directory', True),
    ('outputs/future', 'directory', False),
])
def test_declared_path_semantics_preview_and_execution_agree(project, value, kind, exists):
    store, sim, root, source = project
    (root / 'outputs/empty').mkdir(parents=True)
    (root / 'outputs/populated').mkdir()
    (root / 'outputs/populated/kept.csv').write_bytes(b'original')
    (root / 'outputs/kept.csv').write_bytes(b'original')
    before = {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}
    config = settings(output_mappings=[mapping(value, kind=kind)])
    with TestClient(create_app(store.path)) as client:
        auth = headers(client); base = f'/api/simulations/{sim["id"]}'
        preview = client.post(base + '/execution/outputs', headers=auth, json={k:v for k,v in config.items() if k != 'interpreter'})
        assert preview.status_code == 200, preview.text
        validated = client.post(base + '/execution/validate', headers=auth, json=config)
        assert validated.status_code == 200, validated.text
        assert validated.json()['output_review'] == preview.json()
        assert preview.json()['targets'][0]['kind'] == kind
        assert preview.json()['targets'][0]['covered']
        assert (root / value).exists() == exists
        assert client.put(base + '/execution', headers=auth, json=config).status_code == 200
    assert not store.runs()
    assert before == {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}


def test_empty_mapping_rejected_by_preview_save_validate_and_launch_then_removed(project):
    store, sim, root, source = project
    (root / 'outputs').mkdir()
    config = settings(output_mappings=[mapping('outputs/first.csv'), mapping('')])
    before = store.simulation(sim['id'])
    with TestClient(create_app(store.path)) as client:
        auth = headers(client); base = f'/api/simulations/{sim["id"]}'
        for method, route in [('post','/execution/outputs'), ('post','/execution/validate'),
                              ('put','/execution'), ('post','/launch')]:
            body = {k:v for k,v in config.items() if k != 'interpreter'} if route == '/execution/outputs' else config
            response = getattr(client, method)(base + route, headers=auth, json=body)
            assert response.status_code == 400, response.text
            assert response.json()['detail'] == 'Output 2: Declare a nonempty output path'
        # The independent capture review never drops the draft from saved settings.
        capture = client.post(base + '/execution/outputs', headers=auth,
                              json={**{k:v for k,v in config.items() if k != 'interpreter'}, 'output_mappings':[]})
        assert capture.status_code == 200
        assert capture.json()['output_path'] == str(root / 'outputs')
        assert capture.json()['targets'] == []
        removed = client.post(base + '/execution/outputs', headers=auth,
                              json={**{k:v for k,v in config.items() if k != 'interpreter'}, 'output_mappings':config['output_mappings'][:1]})
        assert removed.status_code == 200 and removed.json()['targets'][0]['covered']
    assert store.simulation(sim['id']) == before and not store.runs()
    assert list((root / 'outputs').iterdir()) == []
