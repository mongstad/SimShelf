import json
import os
import signal
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import pytest

from simshelf.common import process_identity
from simshelf.recording import Run, record_command
from simshelf.source import blob_path, read_version


def recorded(store, sim, **kwargs):
    with Run(sim["id"], workspace=store.path, capture_console=False, **kwargs) as run:
        pass
    return store.run(run.id)


def test_comments_and_formatting_are_snapshots_not_versions(project):
    store, sim, root, source = project
    first = recorded(store, sim)
    original = source.read_bytes()
    source.write_text('# clearer explanation\nSIMSHELF_VERSION="1.0"\n\nvalue=2 # a comment\n')
    second = recorded(store, sim)
    assert second["version"] == first["version"] == "1.0"
    assert second["snapshot_id"] != first["snapshot_id"]
    assert second["structure_id"] == first["structure_id"]
    assert second["source_change"] == "text-only"
    assert len(store.versions(sim["id"])) == 1
    assert blob_path(store.path, first["snapshot"]["files"][0]["blob"]).read_bytes() == original


def test_instrumentation_stays_in_named_version_but_is_visible(project):
    store, sim, root, source = project
    first = recorded(store, sim)
    source.write_text(source.read_text() + 'print("progress")\n')
    second = recorded(store, sim)
    assert second["version"] == first["version"]
    assert second["source_change"] == "changed"
    store.emit(second["id"], "annotation", {"version_note": "Progress display only"})
    assert store.run(second["id"])["version_note"] == "Progress display only"
    source.write_text(source.read_text().replace('"1.0"', '"1.1"'))
    third = recorded(store, sim)
    assert third["source_change"] == "baseline"
    assert len(store.versions(sim["id"])) == 2


def test_version_marker_never_executes_code(project):
    store, sim, root, source = project
    marker = root / "must-not-exist"
    source.write_text(f'SIMSHELF_VERSION = __import__("pathlib").Path({str(marker)!r}).write_text("bad")\n')
    with pytest.raises(ValueError, match="literal"):
        read_version(root, "field.py")
    assert not marker.exists()


def test_unversioned_source_still_gets_snapshots(project):
    store, sim, root, source = project
    source.write_text("value=1\n")
    first = recorded(store, sim)
    source.write_text("value=2\n")
    second = recorded(store, sim)
    assert first["version"] == second["version"] == "unversioned"
    assert second["source_change"] == "changed"


def test_failed_editor_run_keeps_parameters_outputs_and_logs(project):
    store, sim, root, source = project
    with pytest.raises(RuntimeError, match="numerical failure"):
        with Run(sim["id"], workspace=store.path, parameters={"dt": .01, "seed": 42}) as run:
            run.output_dir.mkdir()
            (run.output_dir / "summary.json").write_text('{"partial":true}')
            run.metric("energy", 3.2, step=1, sim_time=.01)
            print("working before failure")
            raise RuntimeError("numerical failure")
    data = store.run(run.id)
    assert data["status"] == "failed"
    assert data["parameters"]["dt"] == .01
    assert data["metrics"][0]["value"] == 3.2
    assert data["artifacts"][0]["policy"] == "copy"
    assert "working before failure" in (store.path / "logs" / run.id / "stdout.log").read_text()
    # Finalized execution metadata is immutable; annotations remain editable.
    store.emit(run.id, "parameters", {"values": {"dt": 5}})
    store.emit(run.id, "annotation", {"notes": "Investigate the timestep"})
    assert store.run(run.id)["parameters"]["dt"] == .01


def test_wrapper_and_sdk_join_one_run_with_resolved_defaults(project):
    store, sim, root, source = project
    source.write_text('''SIMSHELF_VERSION = "1.0"
import simshelf
with simshelf.run("field", parameters={"default_dt": 0.05, "seed": 42}) as run:
    run.output_dir.mkdir(parents=True, exist_ok=True)
    (run.output_dir / "result.json").write_text('{"ok":true}')
    print("hello from simulation")
''')
    ident, code = record_command(store, sim["id"], [sys.executable, "field.py", "--seed", "42"], cwd=root, output_dir="outputs/unique")
    assert code == 0
    assert len(store.runs()) == 1
    data = store.run(ident)
    assert data["parameters"] == {"default_dt": .05, "seed": 42}
    assert data["parameter_sources"]["seed"] == "python"
    assert data["environment"]["source"] == "python-api"
    assert data["command"][-2:] == ["--seed", "42"]
    assert data["capture_counts"]["copied"] == 1
    assert "hello from simulation" in (store.path / "logs" / ident / "stdout.log").read_text()


def test_wrapper_preserves_exit_status_and_stderr(project):
    store, sim, root, source = project
    source.write_text('SIMSHELF_VERSION="1.0"\nimport sys\nprint("oops",file=sys.stderr)\nsys.exit(7)\n')
    ident, code = record_command(store, sim["id"], [sys.executable, "field.py"], cwd=root)
    assert code == 7
    assert store.run(ident)["exit_code"] == 7
    assert store.run(ident)["status"] == "failed"
    assert (store.path / "logs" / ident / "stderr.log").read_text() == "oops\n"


def test_concurrent_runs_use_distinct_output_folders(project):
    store, sim, root, source = project
    def one(i):
        with Run(sim["id"], workspace=store.path, output_dir=f"outputs/{i}", capture_console=False) as run:
            run.output_dir.mkdir(parents=True)
            (run.output_dir / "result.json").write_text(json.dumps({"i": i}))
            run.log_parameters({"i": i})
            return run.id
    with ThreadPoolExecutor(max_workers=5) as pool:
        ids = list(pool.map(one, range(5)))
    assert len(store.runs()) == 5
    for i, ident in enumerate(ids):
        data = store.run(ident)
        assert data["status"] == "completed"
        assert data["parameters"]["i"] == i
        assert len(data["artifacts"]) == 1


def test_shared_output_folder_is_rejected_without_a_ghost_run(project):
    store, sim, root, source = project
    with Run(sim["id"], workspace=store.path, capture_console=False):
        with pytest.raises(ValueError, match="output folder"):
            with Run(sim["id"], workspace=store.path, capture_console=False):
                pass
    assert store.reconcile()["errors"] == []
    assert len(store.runs()) == 1


def test_nested_output_folders_are_also_rejected(project):
    store, sim, root, source = project
    with Run(sim["id"], workspace=store.path, capture_console=False):
        with pytest.raises(ValueError, match="output folder"):
            with Run(sim["id"], workspace=store.path, output_dir="outputs/nested", capture_console=False):
                pass
    assert len(store.runs()) == 1


def test_dead_recorder_recovered_and_pending_events_idempotent(project):
    store, sim, root, source = project
    run = Run(sim["id"], workspace=store.path, capture_console=False)
    run.__enter__()
    with store.connection() as conn:
        data = store.run(run.id, False)
        data["owner"]["identity"] = "not-this-process-start"
        conn.execute("UPDATE runs SET data=? WHERE id=?", (json.dumps(data),run.id))
    assert store.reconcile()["errors"] == []
    assert store.run(run.id)["status"] == "interrupted"
    store.reconcile()
    assert len(store.runs()) == 1


@pytest.mark.skipif(os.name != "posix", reason="POSIX signal forwarding")
def test_sigterm_is_forwarded_and_finalizes_the_run(project):
    store, sim, root, source = project
    source.write_text('SIMSHELF_VERSION="1.0"\nimport time\nprint("ready",flush=True)\ntime.sleep(30)\n')
    process = subprocess.Popen([sys.executable, "-m", "simshelf", "--workspace", str(store.path), "record", "-s", sim["id"], "--cwd", str(root), "--", sys.executable, "field.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        assert process.stdout.readline() == b"ready\n"
        process.send_signal(signal.SIGTERM)
        process.communicate(timeout=8)
        data = store.runs()[0]
        assert data["status"] == "interrupted"
        assert data["exit_code"] == -signal.SIGTERM
    finally:
        if process.poll() is None:
            process.kill()
            process.communicate()
