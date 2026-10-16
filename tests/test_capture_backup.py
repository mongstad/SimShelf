import json
import sqlite3
import zipfile
from pathlib import Path

import pytest

from simshelf.backup import create_backup, restore_backup
from simshelf.capture import preview
from simshelf.recording import Run
from simshelf.source import blob_path


def test_copy_reference_ignore_and_unchanged_files(project):
    store, sim, root, source = project
    output = root / "outputs"
    output.mkdir()
    (output / "previous.json").write_text('{"old":true}')
    with Run(sim["id"], workspace=store.path, capture_console=False) as run:
        (output / "result.json").write_text('{"value":42}')
        (output / "field.bin").write_bytes(b"field data")
        (output / "scratch.tmp").write_bytes(b"ignore")
        (output / "symlink.json").symlink_to(source)
    data = store.run(run.id)
    assert {a["name"]: a["policy"] for a in data["artifacts"]} == {"result.json": "copy", "field.bin": "reference"}
    assert data["capture_counts"]["unchanged"] == 1
    assert data["capture_counts"]["ignored"] == 1
    saved = next(a for a in data["artifacts"] if a["name"] == "result.json")
    (output / "result.json").write_text("changed original")
    assert store.artifact_file(saved["id"]).read_text() == '{"value":42}'
    reference = next(a for a in data["artifacts"] if a["policy"] == "reference")
    (output / "field.bin").write_bytes(b"different field")
    assert store.artifact(reference["id"])["availability"] == "changed"
    (output / "field.bin").unlink()
    assert store.artifact(reference["id"])["availability"] == "missing"
    assert (output / "scratch.tmp").exists()


def test_capture_budget_is_visible_not_silent(project):
    store, sim, root, source = project
    sim = store.update_simulation(sim["id"], config={**sim["config"], "max_file_mb": .001})
    with Run(sim["id"], workspace=store.path, capture_console=False) as run:
        run.output_dir.mkdir()
        (run.output_dir / "large.json").write_text("x" * 2048)
    data = store.run(run.id)
    assert data["status"] == "completed"
    assert data["capture_status"] == "partial"
    assert data["artifacts"][0]["policy"] == "skipped"
    assert "copy limit" in data["capture_errors"][0]
    assert preview(sim)["files"][0]["reason"]


def test_journal_can_replay_after_database_write_failure(project, monkeypatch):
    store, sim, root, source = project
    with Run(sim["id"], workspace=store.path, capture_console=False) as run:
        pass
    apply = store.apply
    monkeypatch.setattr(store, "apply", lambda _event: (_ for _ in ()).throw(sqlite3.OperationalError("locked")))
    with pytest.raises(sqlite3.OperationalError):
        store.emit(run.id, "annotation", {"notes": "Durable pending note"})
    monkeypatch.setattr(store, "apply", apply)
    assert store.reconcile()["recovered"] == 1
    assert store.run(run.id)["notes"] == "Durable pending note"
    assert store.reconcile()["recovered"] == 0


def test_backup_restores_snapshots_logs_annotations_and_copies(project, tmp_path):
    store, sim, root, source = project
    with Run(sim["id"], workspace=store.path, parameters={"seed": 7}) as run:
        print("backup evidence")
        run.output_dir.mkdir()
        (run.output_dir / "result.json").write_text('{"answer":42}')
        (run.output_dir / "raw.bin").write_bytes(b"not in backup")
        run.note("Useful run")
    archive = create_backup(store, tmp_path / "backup.zip")
    with zipfile.ZipFile(archive) as z:
        manifest = json.loads(z.read("manifest.json"))
        assert manifest["references_included"] is False
    restored = restore_backup(archive, tmp_path / "restored")
    data = restored.run(run.id)
    assert data["notes"] == "Useful run"
    assert data["parameters"] == {"seed": 7}
    assert data["status"] == "completed"
    copied = next(a for a in data["artifacts"] if a["policy"] == "copy")
    assert restored.artifact_file(copied["id"]).read_text() == '{"answer":42}'
    assert "backup evidence" in (restored.path / "logs" / run.id / "stdout.log").read_text()
    assert restored.run(run.id)["snapshot"] == store.run(run.id)["snapshot"]
    with pytest.raises(ValueError, match="exists"):
        create_backup(store, archive)
    with pytest.raises(ValueError, match="empty"):
        restore_backup(archive, restored.path)


def test_active_backup_restores_as_interrupted(project, tmp_path):
    store, sim, root, source = project
    with Run(sim["id"], workspace=store.path, capture_console=False) as run:
        archive = create_backup(store, tmp_path / "active.zip")
        restored = restore_backup(archive, tmp_path / "restored-active")
        assert restored.run(run.id)["status"] == "interrupted"
        assert store.run(run.id)["status"] == "running"


def test_backup_detects_tampering_without_partial_restore(project, tmp_path):
    store, sim, root, source = project
    with Run(sim["id"], workspace=store.path, capture_console=False):
        pass
    original = create_backup(store, tmp_path / "original.zip")
    tampered = tmp_path / "tampered.zip"
    with zipfile.ZipFile(original) as src, zipfile.ZipFile(tampered, "w") as dst:
        for entry in src.infolist():
            data = src.read(entry.filename)
            if entry.filename.startswith("blobs/"):
                data += b"tampered"
            dst.writestr(entry.filename, data)
    with pytest.raises(ValueError, match="checksum"):
        restore_backup(tampered, tmp_path / "bad-restore")
    assert not (tmp_path / "bad-restore").exists()


def test_capture_folder_cannot_escape_source(project):
    store, sim, root, source = project
    with pytest.raises(ValueError, match="relative"):
        store.update_simulation(sim["id"], config={**sim["config"], "output_dir": "../elsewhere"})
