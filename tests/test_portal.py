import concurrent.futures
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time

from fastapi.testclient import TestClient
import httpx
import pytest

from simshelf.api import create_app
from simshelf.backup import create_backup, restore_backup
from simshelf.portal import execution_settings
from simshelf.recording import Run
from simshelf.store import Store

pytestmark = pytest.mark.skipif(not sys.platform.startswith("linux"), reason="Portal process ownership is Linux-only")


def settings(**changes):
    return {"interpreter": sys.executable, "cwd": ".", "arguments": [], "output_dir": "outputs", **changes}


def finish(store, run_id, timeout=12):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        run = store.run(run_id)
        if run["status"] != "running":
            return run
        time.sleep(.05)
    raise AssertionError(f"Run did not finish: {run_id}")


def headers(client):
    return {"X-SimShelf-Token": client.get("/api/workspace").json()["token"]}


def launch(client, sim, auth, **changes):
    response = client.post(f"/api/simulations/{sim['id']}/launch", headers=auth, json=settings(**changes))
    assert response.status_code == 201, response.text
    return response.json()["run_id"]


def test_registration_validation_and_authorization_do_not_execute_source(project):
    store, sim, root, source = project
    source.write_text("raise RuntimeError('must not run during validation')\n")
    with TestClient(create_app(store.path)) as client:
        auth = headers(client)
        for suffix, method in (("launch", "post"), ("execution/validate", "post"), ("execution", "put")):
            path = f"/api/simulations/{sim['id']}/{suffix}"
            assert getattr(client, method)(path, json=settings()).status_code == 403
            assert getattr(client, method)(path, headers={**auth, "Origin": "https://elsewhere.example"}, json=settings()).status_code == 403
        response = client.post(f"/api/simulations/{sim['id']}/execution/validate", headers=auth, json=settings())
        assert response.status_code == 200, response.text
        assert response.json()["command"] == [sys.executable, str(source)]
        assert response.json()["cwd"] == str(root)
        assert store.runs() == []
        assert not (root / "outputs").exists()
        assert client.post("/api/runs/unknown/stop").status_code == 403
        assert client.post(f"/api/simulations/{sim['id']}/launch", headers=auth, json={**settings(), "command": ["sh", "-c", "whoami"]}).status_code == 422


@pytest.mark.parametrize("change", [
    {"interpreter": "/nonexistent/python"}, {"interpreter": "/bin/sh"},
    {"interpreter": "python"}, {"cwd": "../outside"}, {"cwd": "missing"},
    {"arguments": "--seed 1"}, {"arguments": ["bad\x00arg"]},
    {"arguments": ["x"] * 257}, {"output_dir": "../outputs"},
])
def test_invalid_launch_creates_no_run(project, change):
    store, sim, root, source = project
    with TestClient(create_app(store.path)) as client:
        response = client.post(f"/api/simulations/{sim['id']}/launch", headers=headers(client), json=settings(**change))
        assert response.status_code in (400, 422), response.text
    assert store.runs() == []


def test_missing_or_escaping_entry_and_excluded_source_rejected(project, tmp_path):
    store, sim, root, source = project
    source.unlink()
    with TestClient(create_app(store.path)) as client:
        auth = headers(client)
        assert client.post(f"/api/simulations/{sim['id']}/launch", headers=auth, json=settings()).status_code == 400
        outside = tmp_path / "outside.py"
        outside.write_text("raise RuntimeError('must not execute')\n")
        source.symlink_to(outside)
        assert client.post(f"/api/simulations/{sim['id']}/launch", headers=auth, json=settings()).status_code == 400
        source.unlink()
        source.write_text("print('unused')\n")
        store.update_simulation(sim['id'], config={**sim['config'], 'source_exclude': ['field.py']})
        assert client.post(f"/api/simulations/{sim['id']}/launch", headers=auth, json=settings()).status_code == 400
    assert store.runs() == []


def test_real_argv_api_join_saved_settings_and_backup(project, tmp_path):
    store, sim, root, source = project
    source.write_text('''import json, os, sys
from pathlib import Path
import simshelf
SIMSHELF_VERSION = "1.0"
with simshelf.run("field", parameters={"argv": sys.argv[1:], "seed": 7}) as run:
    run.metric("energy", 2.5, step=1)
    run.note("portal evidence")
    run.output_dir.mkdir(parents=True)
    (run.output_dir / "result.json").write_text(json.dumps(sys.argv[1:]))
    (run.output_dir / "raw.bin").write_bytes(b"reference data")
    print("live stdout", flush=True)
    print("diagnostic stderr", file=sys.stderr, flush=True)
''')
    arguments = ["--label", "with spaces", "; touch SHOULD_NOT_EXIST", "$(touch OTHER)", "*", "", "--flag=2"]
    with TestClient(create_app(store.path)) as client:
        auth = headers(client)
        response = client.put(f"/api/simulations/{sim['id']}/execution", headers=auth, json=settings(arguments=arguments))
        assert response.status_code == 200, response.text
        run_id = launch(client, sim, auth, arguments=arguments)
        run = finish(store, run_id)
        assert run["status"] == "completed", run
        assert len(store.runs()) == 1
        assert run["command"] == [sys.executable, str(source), *arguments]
        assert run["parameters"]["argv"] == arguments
        assert run["environment"]["source"] == "python-api"
        assert run["metrics"][0]["value"] == 2.5
        assert run["notes"] == "portal evidence" and run["launch"]["kind"] == "portal"
        assert "live stdout" in client.get(f"/api/runs/{run_id}/logs").json()["text"]
        assert "diagnostic stderr" in client.get(f"/api/runs/{run_id}/logs?stream=stderr").json()["text"]
        assert not (root / "SHOULD_NOT_EXIST").exists() and not (root / "OTHER").exists()
        archive = create_backup(store, tmp_path / "portal.zip")
    restored = restore_backup(archive, tmp_path / "restored")
    assert restored.simulation(sim["id"])["execution"]["arguments"] == arguments
    assert restored.run(run_id)["snapshot"] == run["snapshot"]
    with TestClient(create_app(store.path)) as client:
        assert client.get("/api/simulations").json()[0]["execution"]["arguments"] == arguments


@pytest.mark.parametrize("code, expected, diagnostic", [
    ("raise SystemExit(9)", 9, ""),
    ("import nonexistent_simshelf_test_dependency", 1, "ModuleNotFoundError"),
    ("import argparse; argparse.ArgumentParser().parse_args()", 2, "unrecognized arguments"),
])
def test_child_failures_retained(project, code, expected, diagnostic):
    store, sim, root, source = project
    source.write_text(code + "\n")
    with TestClient(create_app(store.path)) as client:
        run_id = launch(client, sim, headers(client), arguments=["--invalid"])
        run = finish(store, run_id)
        assert run["status"] == "failed" and run["exit_code"] == expected
        assert run["snapshot"]["files"]
        assert diagnostic in client.get(f"/api/runs/{run_id}/logs?stream=stderr").json()["text"]


def wait_output(root, name="ready"):
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline:
        if (root / name).exists():
            return
        time.sleep(.025)
    raise AssertionError("Child did not start")


def long_script(source):
    source.write_text('''import os, signal, time
from pathlib import Path
signal.signal(signal.SIGTERM, signal.SIG_IGN)
Path("ready").write_text(str(os.getpid()))
print("still running", flush=True)
while True: time.sleep(.1)
''')


def test_explicit_stop_escalates_and_does_not_stop_cli_run(project):
    store, sim, root, source = project
    long_script(source)
    with TestClient(create_app(store.path)) as client:
        auth = headers(client)
        run_id = launch(client, sim, auth)
        wait_output(root)
        assert client.get(f"/api/runs/{run_id}").json()["can_stop"]
        assert "still running" in client.get(f"/api/runs/{run_id}/logs").json()["text"]
        assert client.post(f"/api/runs/{run_id}/stop", headers=auth).status_code == 202
        assert client.post(f"/api/runs/{run_id}/stop", headers=auth).status_code == 202
        run = finish(store, run_id)
        assert run["status"] == "interrupted" and run["exit_code"] == -signal.SIGKILL
        with Run(sim['id'], workspace=store.path, capture_console=False) as editor:
            assert client.post(f"/api/runs/{editor.id}/stop", headers=auth).status_code == 400


def test_simultaneous_starts_collide_but_distinct_capture_roots_work(project):
    store, sim, root, source = project
    long_script(source)
    with TestClient(create_app(store.path)) as client:
        auth = headers(client)
        def start():
            return client.post(f"/api/simulations/{sim['id']}/launch", headers=auth, json=settings())
        with concurrent.futures.ThreadPoolExecutor() as pool:
            results = list(pool.map(lambda _: start(), range(2)))
        assert sorted(r.status_code for r in results) == [201, 400]
        error = next(r.text for r in results if r.status_code == 400)
        assert "output folder" in error
        nested = client.post(f"/api/simulations/{sim['id']}/launch", headers=auth, json=settings(output_dir="outputs/nested"))
        assert nested.status_code == 400 and "output folder" in nested.text
        distinct = launch(client, sim, auth, output_dir="other-outputs")
        assert len(store.runs(status="running")) == 2
    # Lifespan shutdown stops all owned supervisors, including stubborn children.
    assert all(r["status"] == "interrupted" for r in store.runs())


def test_server_kill_cancels_supervisor_and_restart_reports_interrupted(project):
    store, sim, root, source = project
    long_script(source)
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    server = subprocess.Popen([sys.executable, "-B", "-m", "simshelf", "--workspace", str(store.path), "ui", "--no-open", "--port", str(port)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    run_id = None
    try:
        with httpx.Client(base_url=f"http://127.0.0.1:{port}", timeout=15) as client:
            deadline = time.monotonic() + 10
            while True:
                try:
                    auth = headers(client)
                    break
                except httpx.ConnectError:
                    if time.monotonic() > deadline: raise
                    time.sleep(.05)
            run_id = launch(client, sim, auth)
            wait_output(root)
            server.kill()
            server.wait(timeout=5)
        assert finish(store, run_id)["status"] == "interrupted"
        with TestClient(create_app(store.path)) as restarted:
            result = restarted.get(f"/api/runs/{run_id}").json()
            assert result["status"] == "interrupted" and not result["can_stop"]
            assert "still running" in restarted.get(f"/api/runs/{run_id}/logs").json()["text"]
    finally:
        if server.poll() is None:
            server.terminate()
            server.wait(timeout=10)


def test_update_registered_entry_does_not_run_or_change_history(project):
    store, sim, root, source = project
    with Run(sim['id'], workspace=store.path, capture_console=False) as run:
        pass
    before = store.run(run.id)
    (root / 'new.py').write_text("raise RuntimeError('not executed by registration')\n")
    with TestClient(create_app(store.path)) as client:
        auth = headers(client)
        path = f"/api/simulations/{sim['id']}"
        assert client.patch(path, headers=auth, json={'entrypoint': '../escape.py'}).status_code == 400
        response = client.patch(path, headers=auth, json={'entrypoint': 'new.py'})
        assert response.status_code == 200
        assert response.json()['version_file'] == sim['version_file']
    assert store.run(run.id) == before and len(store.runs()) == 1


def test_stop_before_child_start_preserves_interrupted_record(project):
    import threading
    from simshelf.recording import record_command
    store, sim, root, source = project
    source.write_text("from pathlib import Path; Path('should-not-run').touch()\n")
    cancel = threading.Event()
    cancel.set()
    run_id, code = record_command(store, sim['id'], [sys.executable, str(source)], cwd=root, cancel=cancel, quiet=True, launch={'kind': 'portal'})
    assert code == 130 and store.run(run_id)['status'] == 'interrupted'
    assert not (root / 'should-not-run').exists()


def test_remaining_descendants_are_stopped_and_not_reported_successful(project):
    store, sim, root, source = project
    source.write_text('''import subprocess, sys
subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
print("main finished")
''')
    with TestClient(create_app(store.path)) as client:
        run_id = launch(client, sim, headers(client))
        run = finish(store, run_id)
        assert run['status'] == 'interrupted' and run['exit_code'] == 0
        assert 'descendants' in run['error']


def test_failed_interpreter_probe_never_launches_source(project, tmp_path):
    store, sim, root, source = project
    interpreter = tmp_path / 'python'
    interpreter.write_text('#!/bin/sh\nexec /bin/sleep 10\n')
    interpreter.chmod(0o755)
    with TestClient(create_app(store.path)) as client:
        response = client.post(f"/api/simulations/{sim['id']}/execution/validate", headers=headers(client), json=settings(interpreter=str(interpreter)))
        assert response.status_code == 400 and 'validate Python' in response.text
    assert not store.runs()
