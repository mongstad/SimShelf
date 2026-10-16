"""Exercise launcher boundaries using disposable checkouts and real CLI processes."""
import importlib.util
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import sys

import pytest

from simshelf.recording import Run
from simshelf.store import Store

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("dev", ROOT / "scripts/dev.py")
dev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dev)


@pytest.fixture
def checkout(tmp_path, monkeypatch):
    for name in ("SIMSHELF_HOME", "SIMSHELF_DEV_ROOT", "SIMSHELF_DEV_ENV"):
        monkeypatch.delenv(name, raising=False)
    project = tmp_path / "development space" / "SimShelf"
    project.mkdir(parents=True)
    for name in ("scripts", "src/simshelf", "examples"):
        shutil.copytree(ROOT / name, project / name,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "outputs"))
    shutil.copy2(ROOT / "start.sh", project / "start.sh")
    monkeypatch.chdir(tmp_path)
    return project


def prepared(project):
    environment, _ = dev.layout(project)
    (environment / "bin").mkdir(parents=True)
    (environment / ".simshelf-development.json").write_text(json.dumps({"checkout": str(project)}))
    python = environment / "bin/python"
    python.write_text("#!/bin/sh\nexec " + shlex.quote(sys.executable) + ' "$@"\n')
    python.chmod(0o755)
    return environment


def launch(project, *args):
    return subprocess.run([str(project / "start.sh"), *map(str, args)],
                          text=True, capture_output=True)


def files(project):
    return {str(p.relative_to(project)): p.read_bytes()
            for p in project.rglob("*") if p.is_file() and ".git" not in p.parts}


def test_paths_precedence_and_legacy_guard(checkout, monkeypatch, tmp_path):
    environment, library = dev.layout(checkout)
    assert environment == checkout.parent / "environments/SimShelf"
    assert library == checkout.parent / "workspaces/SimShelf"
    (checkout / ".simshelf").mkdir()
    with pytest.raises(ValueError, match="Legacy workspace"):
        dev.layout(checkout)
    monkeypatch.setenv("SIMSHELF_HOME", "relative library")
    assert dev.layout(checkout)[1] == tmp_path / "relative library"
    assert dev.layout(checkout, str(checkout / ".simshelf"))[1] == checkout / ".simshelf"
    monkeypatch.setenv("SIMSHELF_DEV_ROOT", str(tmp_path / "custom root"))
    assert dev.layout(checkout)[0] == tmp_path / "custom root/environments/SimShelf"
    monkeypatch.setenv("SIMSHELF_DEV_ENV", str(tmp_path / "specific env"))
    assert dev.layout(checkout)[0] == tmp_path / "specific env"
    monkeypatch.setenv("SIMSHELF_DEV_ENV", str(checkout / ".venv"))
    with pytest.raises(ValueError, match="outside"):
        dev.layout(checkout)
    monkeypatch.setenv("SIMSHELF_DEV_ENV", "")
    with pytest.raises(ValueError, match="empty"):
        dev.layout(checkout)


def test_default_root_cannot_resolve_into_checkout(checkout, monkeypatch):
    monkeypatch.setenv("SIMSHELF_DEV_ROOT", str(checkout / "local"))
    with pytest.raises(ValueError, match="outside"):
        dev.layout(checkout)
    monkeypatch.setenv("SIMSHELF_DEV_ENV", str(checkout.parent / "external-env"))
    with pytest.raises(ValueError, match="outside"):
        dev.layout(checkout)


def test_missing_or_unowned_environment_never_installs(checkout):
    before = files(checkout)
    result = launch(checkout, "--cli", "init")
    assert result.returncode == 1 and "--setup" in result.stderr
    environment, library = dev.layout(checkout)
    assert not environment.exists() and not library.exists()
    environment.mkdir(parents=True)
    sentinel = environment / "keep.txt"
    sentinel.write_text("unrelated interpreter")
    result = launch(checkout, "--setup")
    assert result.returncode == 1 and "unowned" in result.stderr
    assert sentinel.read_text() == "unrelated interpreter"
    assert list(environment.iterdir()) == [sentinel]
    assert files(checkout) == before


def test_cli_default_custom_and_source_update_leave_checkout_clean(checkout, tmp_path):
    prepared(checkout)
    subprocess.run(["git", "init", "-q", str(checkout)], check=True)
    subprocess.run(["git", "-C", str(checkout), "add", "."], check=True)
    before = files(checkout)
    result = launch(checkout, "--cli", "init")
    assert result.returncode == 0, result.stderr
    default = checkout.parent / "workspaces/SimShelf"
    assert (default / "simshelf.sqlite3").exists()
    custom = tmp_path / "custom library"
    result = launch(checkout, "--workspace", custom, "--cli", "init")
    assert result.returncode == 0, result.stderr
    assert (custom / "simshelf.sqlite3").exists()
    assert launch(checkout, "--cli", "--help").returncode == 0
    assert files(checkout) == before  # Includes ignored bytecode/generated files.
    status = subprocess.run(["git", "-C", str(checkout), "diff", "--exit-code"], capture_output=True)
    assert status.returncode == 0
    assert not subprocess.check_output(["git", "-C", str(checkout), "ls-files", "--others", "--exclude-standard"])
    # A code edit uses the same external records on the next invocation.
    research = tmp_path / "persisted-source"
    research.mkdir()
    (research / "model.py").write_text("value = 1\n")
    sim = Store(default).add_simulation(research)
    source = checkout / "src/simshelf/__init__.py"
    source.write_text(source.read_text() + "\n# simulated code update\n")
    listing = launch(checkout, "--cli", "list")
    assert listing.returncode == 0 and sim["id"] in listing.stdout
    assert (default / "simshelf.sqlite3").exists()


def test_legacy_continuation_and_backup_restore_preserve_records(checkout, tmp_path):
    prepared(checkout)
    legacy = checkout / ".simshelf"
    store = Store(legacy)
    source = tmp_path / "research"
    source.mkdir()
    (source / "model.py").write_text('SIMSHELF_VERSION = "1"\n')
    sim = store.add_simulation(source)
    with Run(sim["id"], workspace=legacy, parameters={"seed": 42}) as run:
        print("migration log")
        run.note("keep this annotation")
        run.output_dir.mkdir()
        (run.output_dir / "kept.json").write_text('{"value": 3}')
        (run.output_dir / "external.bin").write_bytes(b"reference")
    assert "Legacy workspace" in launch(checkout, "--cli", "list").stderr
    archive = tmp_path / "migration.zip"
    result = launch(checkout, "--workspace", legacy, "--cli", "backup", archive)
    assert result.returncode == 0, result.stderr
    target = tmp_path / "restored"
    result = launch(checkout, "--workspace", legacy, "--cli", "restore", archive, "--to", target)
    assert result.returncode == 0, result.stderr
    restored = Store(target).run(run.id)
    original = store.run(run.id)
    for key in ("snapshot", "parameters", "notes", "status"):
        assert restored[key] == original[key]
    for artifact in restored["artifacts"]:
        if artifact["policy"] == "copy":
            assert Store(target).artifact_file(artifact["id"]).read_bytes() == b'{"value": 3}'
    assert (target / "logs" / run.id / "stdout.log").read_bytes() == (legacy / "logs" / run.id / "stdout.log").read_bytes()
    assert (source / "outputs/external.bin").read_bytes() == b"reference"
    assert launch(checkout, "--workspace", target, "--cli", "list", "--simulation", sim["id"]).returncode == 0
    result = launch(checkout, "--workspace", legacy, "--cli", "restore", archive, "--to", target)
    assert result.returncode != 0 and "empty" in result.stderr


def test_demo_keeps_sources_outputs_and_workspaces_external(checkout):
    prepared(checkout)
    before = files(checkout)
    result = launch(checkout, "--demo")
    assert result.returncode == 0, result.stderr
    store = Store(checkout.parent / "workspaces/SimShelf-demo")
    runs = store.runs()
    assert sorted(run["status"] for run in runs) == ["completed"] * 3 + ["failed"]
    assert all(not Path(sim["root"]).is_relative_to(checkout) for sim in store.simulations())
    assert files(checkout) == before
    result = launch(checkout, "--demo")
    assert result.returncode == 0, result.stderr
    assert len(store.runs()) == 8
    assert files(checkout) == before
