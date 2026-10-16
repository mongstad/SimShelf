"""Local portal execution: validation and server-owned recorder supervisors."""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import selectors
import subprocess
import sys
import threading
import time

from .common import contained
from .config import validate_config
from .store import Store
from .output_paths import output_review


def execution_settings(simulation: dict, data: dict, *, probe=False) -> dict:
    if not isinstance(data, dict) or set(data) - {"interpreter", "cwd", "arguments", "output_dir", "output_mappings"}:
        raise ValueError("Use interpreter, cwd, arguments, output_dir and optional output_mappings execution settings")
    interpreter = data.get("interpreter", "")
    if not isinstance(interpreter, str) or not interpreter or "\0" in interpreter:
        raise ValueError("Select an absolute path to the simulation's Python interpreter")
    # Keep the symlink spelling: resolving venv/bin/python loses its environment.
    python = Path(interpreter).expanduser()
    if not python.is_absolute() or not re.fullmatch(r"(?:python|pypy)(?:\d+(?:\.\d+)*)?(?:\.exe)?", python.name, re.I):
        raise ValueError("Select an absolute Python executable path (for example, /path/to/venv/bin/python)")
    if not python.is_file() or not os.access(python, os.X_OK):
        raise ValueError("Python interpreter is missing or not executable. Select an existing environment; nothing is installed automatically.")
    root = Path(simulation["root"])
    entry = simulation.get("entrypoint")
    if not root.is_dir() or not entry or Path(entry).suffix != ".py":
        raise ValueError("Register an existing source folder with a Python entry file before launching")
    script = contained(root, entry)
    if not script.is_file():
        raise ValueError("Registered Python entry file is missing")
    cwd = data.get("cwd", ".")
    if not isinstance(cwd, str) or not cwd or "\0" in cwd or Path(cwd).is_absolute():
        raise ValueError("Working directory must be a relative folder inside the registered simulation (use . for its root)")
    directory = contained(root, cwd)
    if not directory.is_dir():
        raise ValueError("Working directory does not exist inside the registered simulation")
    arguments = data.get("arguments", [])
    if not isinstance(arguments, list) or len(arguments) > 256 or any(
        not isinstance(arg, str) or "\0" in arg or len(arg) > 8192 for arg in arguments
    ) or sum(len(arg) for arg in arguments) > 65536:
        raise ValueError("Use at most 256 text argument tokens, no NUL bytes, and at most 64 KB total")
    output = data.get("output_dir", simulation["config"]["output_dir"])
    config = validate_config({**simulation["config"], "output_dir": output})
    contained(root, config["output_dir"])
    settings = {"interpreter": str(python), "cwd": cwd, "arguments": arguments, "output_dir": output}
    mappings = data.get("output_mappings", [])
    review = output_review(simulation, cwd, arguments, output, mappings)
    settings["output_mappings"] = mappings
    result = {"output_review": review, "settings": settings, "command": [str(python), str(script), *arguments],
              "cwd": str(directory), "output_path": str(contained(root, output))}
    if probe:
        try:
            check = subprocess.run([str(python), "-I", "-S", "-c",
                                    "import sys,json; print(json.dumps({'version':sys.version.split()[0], 'prefix':sys.prefix}))"],
                                   shell=False, capture_output=True, text=True, timeout=3)
            info = json.loads(check.stdout) if check.returncode == 0 else None
            if not isinstance(info, dict) or not isinstance(info.get("version"), str):
                raise ValueError("Interpreter did not report a Python version")
        except (OSError, subprocess.SubprocessError, ValueError) as exc:
            raise ValueError(f"Could not validate Python interpreter: {exc}. Choose a working Python environment.") from exc
        result["validation"] = {**info, "message": "Python responds. Script dependencies are checked only when the run starts."}
    return result


class PortalJobs:
    def __init__(self, store: Store):
        self.store = store
        self.lock = threading.RLock()
        self.jobs: dict[subprocess.Popen, dict] = {}
        self.closing = False

    def control(self, run_id: str) -> dict:
        with self.lock:
            job = next((j for p, j in self.jobs.items() if j.get("run_id") == run_id and p.poll() is None), None)
            return {"can_stop": bool(job), "stop_requested": bool(job and job["stopping"])}

    def start(self, simulation: str, settings: dict, name: str | None, acknowledge_outputs: bool = False) -> dict:
        if not sys.platform.startswith("linux"):
            raise ValueError("Portal launching currently requires Linux. CLI/editor recording remains available.")
        plan = execution_settings(self.store.simulation(simulation), settings, probe=True)
        if plan["output_review"]["requires_acknowledgement"] and not acknowledge_outputs:
            raise ValueError("Declared outputs are outside capture coverage. Edit paths or explicitly acknowledge before launching.")
        with self.lock:
            if self.closing:
                raise ValueError("Server is shutting down; no new runs can start")
            if len(self.jobs) >= 32:
                raise ValueError("This server already owns 32 recorders; wait for a run to finish")
            process = subprocess.Popen([sys.executable, "-B", "-m", "simshelf.portal_worker"],
                                       stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.DEVNULL, start_new_session=True, shell=False)
            self.jobs[process] = {"run_id": None, "stopping": False}
            payload = {"workspace": str(self.store.path), "simulation": simulation,
                       "settings": plan["settings"], "name": name, "acknowledge_outputs": acknowledge_outputs}
            threading.Thread(target=self._reap, args=(process,), daemon=True).start()
            try:
                process.stdin.write((json.dumps(payload) + "\n").encode())
                process.stdin.flush()
            except OSError as exc:
                self._cancel(process)
                process.stdout.close()
                raise ValueError(f"Recorder could not initialize: {exc}") from exc
        try:
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdout, selectors.EVENT_READ)
                if not selector.select(30):
                    raise ValueError("Recorder startup timed out. Cancellation requested; check Runs for any retained record.")
                reply = json.loads(process.stdout.readline())
            if "error" in reply:
                raise ValueError(reply["error"])
            with self.lock:
                if process in self.jobs:
                    self.jobs[process]["run_id"] = reply["run_id"]
            return {"run_id": reply["run_id"]}
        except (OSError, ValueError, KeyError) as exc:
            with self.lock:
                self._cancel(process)
            raise ValueError(f"Could not start simulation: {exc}") from exc
        finally:
            process.stdout.close()

    def _reap(self, process):
        process.wait()
        with self.lock:
            self._cancel(process)
            self.jobs.pop(process, None)

    def _cancel(self, process):
        if process in self.jobs:
            self.jobs[process]["stopping"] = True
        if not process.stdin.closed:
            try:
                process.stdin.close()  # EOF also occurs if the server is killed.
            except OSError:
                pass

    def stop(self, run_id: str) -> dict:
        self.store.run(run_id, detail=False)
        with self.lock:
            process = next((p for p, j in self.jobs.items() if j.get("run_id") == run_id and p.poll() is None), None)
            if process is None:
                raise ValueError("This server does not own an active recorder for this run. CLI/editor runs must be stopped at their original process.")
            self._cancel(process)
        return {"stop_requested": True}

    def close(self):
        with self.lock:
            self.closing = True
            processes = list(self.jobs)
            for process in processes:
                self._cancel(process)
        deadline = time.monotonic() + 15
        for process in processes:
            try:
                process.wait(timeout=max(0, deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                # The independent supervisor still owns cancellation/final capture.
                # Killing it here could orphan scientific processes or lose evidence.
                pass
