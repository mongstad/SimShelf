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
from .output_paths import output_review, validate_simulation_output_policy
from .interpreters import probe_interpreter


def execution_settings(simulation: dict, data: dict, *, probe=False) -> dict:
    if not isinstance(data, dict) or set(data) - {"interpreter", "cwd", "arguments", "output_dir", "output_mappings", "progress_mode", "output_policy", "parameter_review"}:
        raise ValueError("Use interpreter, cwd, arguments, output_dir and optional output_mappings execution settings")
    from .swss import review
    metadata = review(simulation, data.get("parameter_review"))
    validate_simulation_output_policy(simulation, data.get("output_policy", "fixed"), metadata)
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
    from .progress import TEXT_MODES
    progress_mode = data.get("progress_mode", "off")
    if not isinstance(progress_mode, str) or progress_mode not in TEXT_MODES:
        raise ValueError("Choose off, step or percent progress parsing")
    settings["progress_mode"] = progress_mode
    mappings = data.get("output_mappings", [])
    policy = data.get("output_policy", "fixed")
    review = output_review(simulation, cwd, arguments, output, mappings, policy)
    settings["parameter_review"] = data.get("parameter_review")
    settings["output_policy"] = policy
    settings["output_mappings"] = mappings
    result = {"parameter_metadata": metadata, "output_review": review, "settings": settings, "command": [str(python), str(script), *arguments],
              "cwd": str(directory), "output_path": str(contained(root, output))}
    if probe:
        try:
            info = probe_interpreter(str(python), timeout=3)
        except (OSError, ValueError) as exc:
            raise ValueError(f"Could not validate Python interpreter: {exc}. Choose a working Python environment.") from exc
        result["validation"] = {**info, "message": "Python responds. Dependency metadata checks are advisory; imports are checked only when the script starts."}
    return result


class PortalJobs:
    def __init__(self, store: Store):
        self.store = store
        self.lock = threading.RLock()
        self.jobs: dict[subprocess.Popen, dict] = {}
        self.closing = False
        self.generation = 0

    def control(self, run_id: str) -> dict:
        with self.lock:
            job = next((j for p, j in self.jobs.items() if j.get("run_id") == run_id and p.poll() is None), None)
            return {"can_stop": bool(job), "stop_requested": bool(job and job["stopping"])}

    def start(self, simulation: str, settings: dict, name: str | None, acknowledge_outputs: bool = False) -> dict:
        if not sys.platform.startswith("linux"):
            raise ValueError("Portal launching currently requires Linux. CLI/editor recording remains available.")
        from .relocation import source_binding
        registered = self.store.simulation(simulation)
        plan = execution_settings(registered, settings, probe=True)
        from .progress import enabled
        with self.store.connection() as conn:
            if plan["settings"]["progress_mode"] != "off" and not enabled(conn):
                raise ValueError("Enable progress reporting for this library before launching a text adapter")
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
            self.generation += 1
            self.jobs[process] = {"run_id": None, "stopping": False, "simulation_id": simulation}
            payload = {"workspace": str(self.store.path), "simulation": simulation,
                       "settings": plan["settings"], "name": name, "acknowledge_outputs": acknowledge_outputs,
                       "source_binding": source_binding(registered)}
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

    def active_simulations(self):
        with self.lock:
            return {j["simulation_id"] for p, j in self.jobs.items()
                    if p.poll() is None and j.get("simulation_id")}

    def shutdown_status(self):
        with self.lock:
            return {"generation": self.generation, "active_runs": sum(
                p.poll() is None for p in self.jobs), "closing": self.closing}

    def request_shutdown(self, generation: int, stop_runs: bool):
        # Serialize consent against admission, including supervisors still starting.
        with self.lock:
            if self.closing:
                return False
            status = self.shutdown_status()
            if generation != status["generation"]:
                raise ValueError("Runs changed since confirmation. Review Quit SimShelf again.")
            if status["active_runs"] and not stop_runs:
                raise ValueError("Active portal runs require explicit Stop runs and quit confirmation.")
            self.closing = True
            for process in list(self.jobs):
                self._cancel(process)
            return True

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
