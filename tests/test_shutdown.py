"""Explicit shutdown: consent, process ownership and actual listener release."""
import io
import os
import signal
import socket
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest
from fastapi.testclient import TestClient

from simshelf.api import create_app
from simshelf.portal import PortalJobs
from test_portal import settings, headers, launch, finish


def test_quit_protection_and_idempotence(project):
    store, sim, root, source = project
    calls = []
    app = create_app(store.path, request_shutdown=lambda: calls.append(True))
    with TestClient(app, client=("127.0.0.1", 1234)) as client:
        auth = headers(client)
        body = {"confirmed": True, "generation": 0}
        assert client.post("/api/server/quit", json=body).status_code == 403
        assert client.post("/api/server/quit", headers={**auth, "Origin": "https://bad.example"}, json=body).status_code == 403
        assert client.post("/api/server/quit", headers=auth, json={**body, "confirmed": False}).status_code == 400
        assert not app.state.jobs.closing
        with ThreadPoolExecutor(2) as pool:
            responses = list(pool.map(lambda _: client.post("/api/server/quit", headers=auth, json=body), range(2)))
        assert all(r.status_code == 200 for r in responses)
        assert calls == [True]
        assert client.post(f"/api/simulations/{sim['id']}/launch", headers=auth, json=settings()).status_code == 400
        assert store.runs() == []
    with TestClient(create_app(store.path), client=("127.0.0.1", 1234)) as client:
        assert not client.get("/api/server").json()["can_quit"]
        assert client.post("/api/server/quit", headers=headers(client), json=body).status_code == 409
    with TestClient(create_app(store.path, request_shutdown=lambda: None), client=("192.0.2.1", 1234)) as client:
        assert client.get("/api/server").status_code == 403
        assert client.post("/api/server/quit", headers=headers(client), json=body).status_code == 403


def test_active_and_pending_consent_and_bounded_capture(project):
    store, *_ = project
    jobs = PortalJobs(store)
    class Pending:
        stdin = io.BytesIO()
        waits = []
        def poll(self): return None
        def wait(self, timeout):
            self.waits.append(timeout)
            raise subprocess.TimeoutExpired("supervisor", timeout)
    process = Pending()
    jobs.jobs[process] = {"run_id": None, "stopping": False}
    jobs.generation = 1
    assert jobs.shutdown_status()["active_runs"] == 1
    with pytest.raises(ValueError, match="changed"):
        jobs.request_shutdown(0, True)
    with pytest.raises(ValueError, match="explicit"):
        jobs.request_shutdown(1, False)
    assert not process.stdin.closed
    assert jobs.request_shutdown(1, True)
    assert process.stdin.closed
    assert not jobs.request_shutdown(1, True)
    jobs.close()
    assert 0 <= process.waits[0] <= 15
    # No kill/finalize API on fake: pending capture remains owned by supervisor.


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="Linux process groups")
@pytest.mark.parametrize("active", [False, True])
def test_real_quit_releases_port_and_preserves_independent_recorder(project, active):
    store, sim, root, source = project
    source.write_text("import os, signal, time\nfrom pathlib import Path\nif Path(os.environ['SIMSHELF_OUTPUT_DIR']).name == 'outputs': signal.signal(signal.SIGTERM, signal.SIG_IGN)\np=Path(os.environ['SIMSHELF_OUTPUT_DIR']); p.mkdir(parents=True, exist_ok=True)\n(p/'partial.txt').write_text('scientific result')\nprint('started', flush=True)\ntime.sleep(120)\n")
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0)); port = sock.getsockname()[1]
    command = [sys.executable, "-B", "-m", "simshelf", "--workspace", str(store.path), "ui", "--no-open", "--port", str(port)]
    server = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    external = None
    try:
        with httpx.Client(base_url=f"http://127.0.0.1:{port}", timeout=35) as client:
            for _ in range(150):
                try:
                    if client.get("/api/workspace").status_code == 200: break
                except httpx.TransportError: pass
                time.sleep(.05)
            else: raise AssertionError("server not ready")
            auth = headers(client)
            collision = subprocess.run(command, capture_output=True, text=True, timeout=10)
            assert collision.returncode == 1
            assert "already in use" in collision.stderr and "--port" in collision.stderr
            external = subprocess.Popen([sys.executable, "-B", "-m", "simshelf", "--workspace", str(store.path), "record", "-s", sim["id"], "--output-dir", "independent", "--", sys.executable, str(source)], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            for _ in range(100):
                if (root / "independent/partial.txt").exists(): break
                time.sleep(.05)
            assert (root / "independent/partial.txt").exists()
            old = client.get("/api/server").json()
            run = launch(client, sim, auth) if active else None
            if active:
                for _ in range(100):
                    if (root / "outputs/partial.txt").exists(): break
                    time.sleep(.05)
                assert (root / "outputs/partial.txt").exists()
                for stop_runs in (False, True):
                    stale = client.post("/api/server/quit", headers=auth, json={"confirmed": True, "generation": old["generation"], "stop_runs": stop_runs})
                    assert stale.status_code == 400
                assert store.run(run)["status"] == "running"
                assert client.get("/api/server").json()["closing"] is False
                current = client.get("/api/server").json()
                unconfirmed = client.post("/api/server/quit", headers=auth, json={"confirmed": True, "generation": current["generation"], "stop_runs": False})
                assert unconfirmed.status_code == 400
                assert store.run(run)["status"] == "running"
            status = client.get("/api/server").json()
            assert status["active_runs"] == int(active)
            response = client.post("/api/server/quit", headers=auth, json={"confirmed": True, "generation": status["generation"], "stop_runs": active})
            assert response.status_code == 200
            assert server.wait(timeout=25) == 0
            with socket.socket() as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.bind(("127.0.0.1", port))
            assert external.poll() is None
            independent = next(r for r in store.runs() if r["id"] != run)
            assert independent["status"] == "running"
            if run:
                record = finish(store, run)
                assert record["status"] == "interrupted"
                assert record["capture_status"] == "complete"
                assert (root / "outputs/partial.txt").read_text() == "scientific result"
    finally:
        if server.poll() is None:
            server.terminate(); server.wait(timeout=25)
        if external and external.poll() is None:
            external.terminate(); external.wait(timeout=15)


def test_launch_in_validation_cannot_escape_quit(project, monkeypatch):
    import threading
    import simshelf.portal as portal
    store, sim, *_ = project
    jobs = PortalJobs(store)
    entered, release = threading.Event(), threading.Event()
    original = portal.execution_settings
    def validate(*args, **kwargs):
        entered.set()
        assert release.wait(5)
        return original(*args, **kwargs)
    monkeypatch.setattr(portal, "execution_settings", validate)
    with ThreadPoolExecutor(1) as pool:
        future = pool.submit(jobs.start, sim["id"], settings(), None)
        assert entered.wait(5)
        assert jobs.request_shutdown(0, False)
        release.set()
        with pytest.raises(ValueError, match="shutting down"):
            future.result(timeout=5)
    assert store.runs() == []
