from __future__ import annotations

import importlib.metadata
import json
import math
import os
import platform
import signal
import socket
import subprocess
import sys
import threading
import time
import traceback
import uuid
from pathlib import Path

from .capture import capture_outputs, output_inventory, save_file
from .common import json_text, now, process_identity
from .source import blob_path, git_context, read_version, source_snapshot
from .store import Store


def environment() -> dict:
    packages = sorted({(dist.metadata.get("Name", "unknown"), dist.version) for dist in importlib.metadata.distributions()})
    return {"python": sys.version.split()[0], "executable": sys.executable, "platform": platform.platform(), "packages": [{"name": name, "version": version} for name, version in packages], "source": "python-api"}


def cli_parameters(command: list[str]) -> dict:
    """Best-effort named flags only. Exact argv is stored independently."""
    values, i = {}, 0
    while i < len(command):
        arg = command[i]
        if arg.startswith("--") and len(arg) > 2:
            key, sep, value = arg[2:].partition("=")
            if not sep:
                if i + 1 < len(command) and not command[i + 1].startswith("--"):
                    i += 1
                    value = command[i]
                else:
                    value = "true"
            try:
                value = json.loads(value)
                json_text(value)
            except (ValueError, TypeError):
                pass
            if key in values:
                values[key] = values[key] + [value] if isinstance(values[key], list) else [values[key], value]
            else:
                values[key] = value
        i += 1
    return values


class ConsoleTee:
    def __init__(self, original, path):
        self.original, self.file, self.saved = original, path.open("w", encoding="utf-8"), 0

    def write(self, text):
        result = self.original.write(text)
        if self.saved < 10 * 1024**2:
            retained = text[:10 * 1024**2 - self.saved]
            self.file.write(retained)
            self.saved += len(retained)
            self.file.flush()
        return result

    def flush(self):
        self.original.flush()
        self.file.flush()

    def __getattr__(self, name):
        return getattr(self.original, name)


class Run:
    def __init__(self, simulation: str, *, workspace=None, name=None, parameters=None, tags=None, command=None, cwd=None, output_dir=None, join=True, capture_console=True, launch=None):
        self.launch = launch
        self.store = Store(workspace)
        self.simulation = self.store.simulation(simulation)
        if output_dir is not None:
            from .config import validate_config
            self.simulation["config"] = validate_config({**self.simulation["config"], "output_dir": str(output_dir)})
        active = os.environ.get("SIMSHELF_RUN_ID") if join else None
        self.joined = bool(active)
        self.id = active or uuid.uuid4().hex
        self.name = name
        self.parameters = parameters or {}
        if not isinstance(self.parameters, dict):
            raise ValueError("Parameters must be a dictionary")
        json_text(self.parameters)
        self.tags = tags or []
        self.command = command or [sys.executable, *sys.argv]
        self.cwd = str(Path(cwd or Path.cwd()).resolve())
        self.before = {}
        self.started = False
        self.finished = False
        self.started_clock = time.monotonic()
        self.capture_console = capture_console
        self.console_streams = []

    @property
    def output_dir(self) -> Path:
        from .common import contained
        return contained(Path(self.simulation["root"]), self.simulation["config"]["output_dir"])

    def __enter__(self):
        if self.joined:
            parent = self.store.run(self.id, detail=False)
            if parent["simulation_id"] != self.simulation["id"] or parent["status"] != "running":
                raise ValueError("Active wrapper run belongs to a different simulation or has ended")
            self.simulation["config"] = parent["capture_config"]
            self.store.emit(self.id, "environment", environment())
            if self.parameters:
                self.log_parameters(self.parameters)
            self.started = True
            return self
        snapshot = source_snapshot(self.store.path, self.simulation)
        version_file = self.simulation.get("version_file")
        captured_version = next((f for f in snapshot["files"] if f["path"] == version_file), None)
        version = read_version(Path(self.simulation["root"]), version_file, captured=blob_path(self.store.path, captured_version["blob"]).read_bytes() if captured_version else None)
        self.before, initial_errors = output_inventory(self.simulation)
        self.initial_capture_errors = initial_errors
        self.started_clock = time.monotonic()
        data = {"id": self.id, "simulation_id": self.simulation["id"], "name": self.name or time.strftime("Run %b %d · %H:%M:%S"), "status": "running", "started_at": now(), "ended_at": None, "duration": None, "exit_code": None, "version": version, "snapshot_id": snapshot["id"], "structure_id": snapshot["structure_id"], "source_warnings": snapshot["warnings"], "command": self.command, "cwd": self.cwd, "parameters": self.parameters, "parameter_sources": {key: "python" for key in self.parameters}, "tags": self.tags, "notes": "", "version_note": "", "cover_id": None, "git": git_context(Path(self.simulation["root"])), "environment": environment(), "capture_config": self.simulation["config"], "capture_status": "pending", "capture_errors": initial_errors, "owner": {"pid": os.getpid(), "host": socket.gethostname(), "identity": process_identity(os.getpid())}}
        if self.launch:
            if self.simulation["entrypoint"] not in {file["path"] for file in snapshot["files"]}:
                raise ValueError("The entry file must be included in source capture before portal launch")
            data["launch"] = self.launch
        data["capture_root"] = str(self.output_dir)
        self.store.emit(self.id, "start", data)
        if self.capture_console:
            logdir = self.store.path / "logs" / self.id
            logdir.mkdir(parents=True, exist_ok=True)
            for stream in ("stdout", "stderr"):
                original = getattr(sys, stream)
                tee = ConsoleTee(original, logdir / f"{stream}.log")
                self.console_streams.append((stream, original, tee))
                setattr(sys, stream, tee)
        self.started = True
        return self

    def log_parameters(self, values: dict, source="python"):
        json_text(values)
        self.store.emit(self.id, "parameters", {"values": values, "source": source})

    def metric(self, name: str, value: float, *, step=None, sim_time=None, unit=None):
        if not name or len(name) > 200 or not math.isfinite(float(value)):
            raise ValueError("Measurements need a name and a finite numeric value")
        if sim_time is not None and not math.isfinite(float(sim_time)):
            raise ValueError("Simulation time must be finite")
        self.store.emit(self.id, "metric", {"name": name, "value": float(value), "step": step, "sim_time": sim_time, "unit": unit})

    def attach(self, path, *, policy="copy", caption="") -> dict:
        if policy not in ("copy", "reference"):
            raise ValueError("Attachment policy must be copy or reference")
        return save_file(self.store, self.id, Path(path), policy=policy, caption=caption, limit=int(self.simulation["config"]["max_file_mb"] * 1024**2))

    def note(self, text: str):
        self.store.emit(self.id, "annotation", {"notes": text})

    def finish(self, exit_code=0, *, status=None, error=None):
        if self.joined or self.finished:
            return
        status = status or ("completed" if exit_code == 0 else "failed")
        try:
            capture = capture_outputs(self.store, self.id, self.simulation, self.before)
            capture["capture_errors"] = getattr(self, "initial_capture_errors", []) + capture["capture_errors"]
            if capture["capture_errors"]:
                capture["capture_status"] = "partial"
        except Exception as exc:
            capture = {"capture_status": "incomplete", "capture_errors": [str(exc)]}
        self.store.emit(self.id, "finish", {"status": status, "ended_at": now(), "duration": time.monotonic() - self.started_clock, "exit_code": exit_code, "error": error, **capture})
        self.finished = True

    def __exit__(self, exc_type, exc, tb):
        for stream, original, tee in self.console_streams:
            setattr(sys, stream, original)
            tee.file.close()
        error = "".join(traceback.format_exception(exc_type, exc, tb)) if exc else None
        exit_code = (exc.code if isinstance(exc, SystemExit) and isinstance(exc.code, int) else 1) if exc else 0
        status = "interrupted" if isinstance(exc, KeyboardInterrupt) else None
        self.finish(exit_code, status=status, error=error)
        return False


def record_command(store: Store, simulation: str, command: list[str], *, name=None, tags=None, cwd=None, output_dir=None, cancel=None, on_started=None, quiet=False, launch=None) -> tuple[str, int]:
    if not command:
        raise ValueError("Pass a command after --, for example: -- python field.py --seed 42")
    store.reconcile()
    recorder = Run(simulation, workspace=store.path, command=command, name=name, tags=tags, cwd=cwd, output_dir=output_dir, join=False, capture_console=False, launch=launch)
    recorder.__enter__()
    store.emit(recorder.id, "environment", {**environment(), "source": "recorder environment (child interpreter not yet reported)"})
    recorder.log_parameters(cli_parameters(command), source="command-line (inferred)")
    env = os.environ.copy()
    env["SIMSHELF_HOME"] = str(store.path)
    env["SIMSHELF_RUN_ID"] = recorder.id
    env["SIMSHELF_OUTPUT_DIR"] = str(recorder.output_dir)
    env["PYTHONUNBUFFERED"] = "1"
    logdir = store.path / "logs" / recorder.id
    logdir.mkdir(parents=True, exist_ok=True)
    if not quiet:
        print(f"SimShelf recording {recorder.id[:8]} · version {store.run(recorder.id, False)['version']}", file=sys.stderr)
        print(f"Run link: http://127.0.0.1:8740/#run/{recorder.id}", file=sys.stderr)
    exit_code, interrupted, errors = 1, False, []
    process = None
    threads = []
    old_handlers = {}
    def forward(signum, _frame):
        nonlocal interrupted
        interrupted = True
        if cancel is not None:
            cancel.set()
        if process is not None and process.poll() is None:
            try:
                if os.name == "posix":
                    os.killpg(process.pid, signum)
                else:
                    process.send_signal(signum)
            except ProcessLookupError:
                pass
    def tee(pipe, target, path):
        saved = 0
        try:
            with path.open("wb") as stream:
                while chunk := pipe.read1(8192):
                    try:
                        buffer = getattr(target, "buffer", None)
                        if buffer:
                            buffer.write(chunk)
                            buffer.flush()
                        elif target is not None:
                            target.write(chunk.decode(errors="replace"))
                            target.flush()
                    except (OSError, ValueError):
                        pass
                    remaining = 10 * 1024**2 - saved
                    if remaining > 0:
                        stream.write(chunk[:remaining])
                        stream.flush()
                        saved += min(len(chunk), remaining)
                    if len(chunk) > remaining and "Terminal log truncated at 10 MB per stream" not in errors:
                        errors.append("Terminal log truncated at 10 MB per stream")
        finally:
            pipe.close()
    try:
        if threading.current_thread() is threading.main_thread():
            for signum in (signal.SIGINT, signal.SIGTERM):
                old_handlers[signum] = signal.signal(signum, forward)
        if on_started:
            on_started(recorder.id)
        if cancel is not None and cancel.is_set():
            interrupted, exit_code = True, 130
            return recorder.id, exit_code
        process = subprocess.Popen(command, cwd=recorder.cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=os.name == "posix", shell=False)
        for pipe, target, name_ in ((process.stdout, None if quiet else sys.stdout, "stdout.log"), (process.stderr, None if quiet else sys.stderr, "stderr.log")):
            thread = threading.Thread(target=tee, args=(pipe, target, logdir / name_), daemon=True)
            thread.start()
            threads.append(thread)
        if cancel is None:
            exit_code = process.wait()
        else:
            stopping_at = None
            while process.poll() is None:
                if cancel.wait(.1):
                    interrupted = True
                    if stopping_at is None:
                        stopping_at = time.monotonic()
                        try:
                            os.killpg(process.pid, signal.SIGTERM)
                        except ProcessLookupError:
                            pass
                    elif time.monotonic() - stopping_at >= 3:
                        try:
                            os.killpg(process.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                        break
                    time.sleep(.05)
            exit_code = process.wait()
            # Also stop descendants that outlived the main script. Detached new
            # sessions are outside this process-group ownership contract.
            try:
                os.killpg(process.pid, signal.SIGKILL)
                if not interrupted:
                    interrupted = True
                    errors.append("The script exited with descendants still running; the remaining process group was stopped.")
            except ProcessLookupError:
                pass
        for thread in threads:
            thread.join(timeout=5)
        if any(t.is_alive() for t in threads):
            errors.append("A child process kept a terminal pipe open; log capture may be incomplete")
    except Exception as exc:
        if cancel is None and not isinstance(exc, OSError):
            raise
        exit_code = 1
        errors.append(str(exc))
    finally:
        if cancel is not None and process is not None and process.poll() is None:
            interrupted = True
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            exit_code = process.wait()
        for signum, handler in old_handlers.items():
            signal.signal(signum, handler)
        recorder.finish(exit_code, status="interrupted" if interrupted or exit_code < 0 else None, error="\n".join(errors) or None)
    return recorder.id, 128 + abs(exit_code) if exit_code < 0 else exit_code
