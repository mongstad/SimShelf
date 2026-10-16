"""Passive interpreter discovery and explicit, bounded metadata checks."""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import selectors
import signal
import subprocess
import sys
import time
import tomllib

from packaging.requirements import Requirement, InvalidRequirement
from packaging.specifiers import SpecifierSet, InvalidSpecifier
from packaging.utils import canonicalize_name
from packaging.version import Version, InvalidVersion

PYTHON_NAME = re.compile(r"(?:python|pypy)(?:\d+(?:\.\d+)*)?(?:\.exe)?", re.I)


def interpreter_path(value):
    if not isinstance(value, str) or not value or "\0" in value:
        raise ValueError("Select an absolute Python executable path")
    path = Path(value).expanduser()
    if not path.is_absolute() or not PYTHON_NAME.fullmatch(path.name):
        raise ValueError("Select an absolute Python executable path")
    if not path.is_file() or not os.access(path, os.X_OK):
        raise ValueError("Interpreter is missing or not executable. Select another existing environment; nothing is installed automatically.")
    return path


def discovery(simulation):
    candidates, seen = [], {}
    def add(value, source, retain_missing=False):
        if len(candidates) >= 64:
            return
        path = Path(value).expanduser()
        if not path.is_absolute() or not PYTHON_NAME.fullmatch(path.name):
            return
        path = Path(os.path.abspath(path))
        try:
            available = path.is_file() and os.access(path, os.X_OK)
            if not available and not retain_missing and not path.is_symlink():
                return
            prefix = path.parent.resolve().parent
            kind = "Virtual environment" if (prefix / "pyvenv.cfg").is_file() else "Conda environment" if (prefix / "conda-meta").is_dir() else "Unclassified executable"
            key = (str(prefix.resolve()) if kind != "Unclassified executable" else "", str(path.resolve()))
            runtime = path == Path(sys.executable) or (kind != "Unclassified executable" and prefix.resolve() == Path(sys.prefix).resolve())
            if key in seen:
                existing = seen[key]
                if source not in existing["sources"]:
                    existing["sources"].append(source)
                existing["simshelf_runtime"] |= runtime
                return
            item = {"path": str(path), "sources": [source], "kind": kind,
                    "available": available, "simshelf_runtime": runtime,
                    "version": None, "state": "Not probed" if available else "Missing or not executable"}
            seen[key] = item
            candidates.append(item)
        except (OSError, RuntimeError, ValueError):
            if retain_missing:
                candidates.append({"path": str(path), "sources": [source], "kind": "Unknown", "available": False, "simshelf_runtime": False, "version": None, "state": "Path unavailable"})
    saved = simulation.get("execution", {}).get("interpreter") if simulation.get("execution") else None
    if saved:
        add(saved, "Saved selection", True)
    for folder in (".venv", "venv"):
        add(Path(simulation["root"]) / folder / "bin/python", "Project " + folder)
    for variable in ("VIRTUAL_ENV", "CONDA_PREFIX"):
        value = os.environ.get(variable)
        if value and Path(value).is_absolute():
            add(Path(value) / "bin/python", "Server " + variable)
    registry = Path.home() / ".conda/environments.txt"
    try:
        if registry.is_file() and not registry.is_symlink():
            with registry.open() as stream:
                text = stream.read(32769)
            if len(text) <= 32768:
                for line in text.splitlines()[:32]:
                    if Path(line).is_absolute():
                        add(Path(line) / "bin/python", "Conda registry", True)
    except OSError:
        pass
    for directory in os.environ.get("PATH", "").split(os.pathsep)[:32]:
        if not directory or not Path(directory).is_absolute():
            continue
        for name in ("python", "python3", "pypy3", *("python3." + str(n) for n in range(8, 16))):
            add(Path(directory) / name, "Server PATH")
    add(sys.executable, "SimShelf runtime")
    return {"candidates": candidates, "message": "Passive, bounded discovery; no executable was run. Versions appear only after you explicitly check a trusted selection. No interpreter is selected automatically."}


def probe_interpreter(value, *, metadata=False, timeout=5):
    python = interpreter_path(value)
    if not sys.platform.startswith("linux"):
        raise ValueError("Interpreter checks are currently validated on Linux only")
    code = Path(__file__).with_name("interpreter_probe.py").read_text()
    try:
        process = subprocess.Popen([str(python), "-I", "-S", "-B", "-c", code, "metadata" if metadata else "version"],
                                   shell=False, cwd="/", stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, start_new_session=True)
    except OSError as exc:
        raise ValueError("Could not start selected interpreter: " + str(exc)) from exc
    data = {process.stdout: bytearray(), process.stderr: bytearray()}
    deadline = time.monotonic() + timeout
    try:
        with selectors.DefaultSelector() as selector:
            for pipe in data:
                selector.register(pipe, selectors.EVENT_READ)
            while selector.get_map():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise ValueError("Interpreter check timed out; choose a working trusted interpreter")
                for key, _ in selector.select(remaining):
                    chunk = os.read(key.fileobj.fileno(), 8192)
                    if not chunk:
                        selector.unregister(key.fileobj)
                    else:
                        data[key.fileobj].extend(chunk)
                        if sum(map(len, data.values())) > 524288:
                            raise ValueError("Interpreter check exceeded the output limit")
            process.wait(timeout=max(.01, deadline - time.monotonic()))
        if process.returncode:
            raise ValueError("Interpreter check failed; verify that the selected Python is usable")
        try:
            result = json.loads(data[process.stdout])
            if not isinstance(result, dict) or not isinstance(result.get("version"), str) or not isinstance(result.get("prefix"), str):
                raise ValueError("Invalid response")
        except (ValueError, TypeError) as exc:
            raise ValueError("Interpreter did not return valid version metadata") from exc
        return result
    except subprocess.TimeoutExpired as exc:
        raise ValueError("Interpreter check timed out") from exc
    finally:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()
        for pipe in data:
            pipe.close()


def declarations(root):
    requirements, warnings, files = [], [], []
    python_spec = None
    for name in ("requirements.txt", "pyproject.toml", "environment.yml", "environment.yaml"):
        path = Path(root) / name
        if not path.exists() and not path.is_symlink():
            continue
        files.append(name)
        try:
            if path.is_symlink() or not path.is_file():
                raise ValueError("symbolic links/non-regular declarations are not read")
            with path.open("rb") as stream:
                raw = stream.read(262145)
            if len(raw) > 262144:
                raise ValueError("declaration exceeds 256 KB")
            text = raw.decode("utf-8")
            if name == "requirements.txt":
                entries = [re.split(r"\s+#", line, maxsplit=1)[0].strip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]
            elif name == "pyproject.toml":
                project = tomllib.loads(text).get("project", {})
                entries = project.get("dependencies", [])
                candidate_spec = project.get("requires-python")
                if project.get("optional-dependencies") or project.get("dynamic"):
                    warnings.append("Optional/dynamic pyproject dependencies are not resolved")
                if not isinstance(entries, list) or any(not isinstance(e, str) for e in entries):
                    raise ValueError("project.dependencies must be a string list")
                if candidate_spec is not None and not isinstance(candidate_spec, str):
                    raise ValueError("requires-python must be text")
                python_spec = candidate_spec
            else:
                warnings.append(name + ": Conda solver declarations are not evaluated; check them with your environment tools")
                continue
            for entry in entries:
                if len(requirements) >= 256:
                    raise ValueError("at most 256 requirements are checked")
                requirements.append((name, entry))
        except (OSError, ValueError, TypeError, AttributeError) as exc:
            warnings.append(name + ": " + str(exc))
    return requirements, python_spec, files, warnings


def check_dependencies(simulation, interpreter):
    info = probe_interpreter(interpreter, metadata=True)
    requirements, python_spec, files, warnings = declarations(simulation["root"])
    if not isinstance(info.get("distributions"), list) or not isinstance(info.get("marker_environment"), dict):
        raise ValueError("Installed-distribution metadata is unavailable from this interpreter")
    marker_keys = {"implementation_name", "implementation_version", "os_name", "platform_machine", "platform_python_implementation", "platform_release", "platform_system", "platform_version", "python_full_version", "python_version", "sys_platform", "extra"}
    if not marker_keys <= info["marker_environment"].keys() or any(not isinstance(info["marker_environment"][key], str) for key in marker_keys):
        raise ValueError("Target interpreter marker metadata is incomplete; compatibility is unknown")
    if not isinstance(info.get("warnings"), list) or any(not isinstance(w, str) for w in info["warnings"]):
        raise ValueError("Installed-distribution metadata is unavailable")
    if any(not isinstance(item, list) or len(item) != 2 or any(not isinstance(value, str) for value in item) for item in info["distributions"]):
        raise ValueError("Installed-distribution metadata is malformed")
    warnings.extend(info["warnings"])
    installed = {}
    for name, version in info["distributions"]:
        installed.setdefault(canonicalize_name(name), set()).add(version)
    rows = []
    if python_spec:
        try:
            state = "satisfied" if Version(info["version"]) in SpecifierSet(python_spec) else "incompatible"
        except (InvalidSpecifier, InvalidVersion):
            state = "unknown"
        rows.append({"requirement": "Python " + python_spec, "source": "pyproject.toml", "installed": info["version"], "status": state})
    for source, text in requirements:
        row = {"requirement": text, "source": source, "installed": None, "status": "unknown"}
        try:
            req = Requirement(text)
            if req.url:
                row["note"] = "Direct URLs/local/editable installs are not resolved"
            elif req.marker and not req.marker.evaluate(environment=info["marker_environment"]):
                row["status"] = "not-applicable"
            else:
                versions = installed.get(canonicalize_name(req.name), set())
                row["installed"] = ", ".join(sorted(versions)) or None
                if len(versions) > 1:
                    row["note"] = "Conflicting installed metadata; verify the environment"
                elif not versions:
                    row["status"] = "unknown" if info.get("warnings") else "missing"
                    row["note"] = "Not found in inspected distribution metadata" + ("; search is incomplete" if info.get("warnings") else "")
                elif req.extras:
                    row["note"] = "Base distribution found; extra dependencies are not resolved"
                else:
                    row["status"] = "satisfied" if Version(next(iter(versions))) in req.specifier else "incompatible"
        except (InvalidRequirement, InvalidVersion, ValueError, KeyError) as exc:
            row["note"] = "Unsupported or invalid declaration; review manually"
        rows.append(row)
    return {"interpreter": interpreter, "python": info, "files": files, "requirements": rows,
            "warnings": sorted(set(warnings)), "undeclared": not files,
            "message": "Advisory installed-distribution metadata only. No packages were imported or installed. User-site and PYTHONPATH packages are not inspected. Package presence does not verify imports, GPU/CUDA access, optional dependencies or successful execution."}
