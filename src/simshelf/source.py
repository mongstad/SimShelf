from __future__ import annotations

import ast
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

from .common import atomic_write, contained, digest, json_text, match

IGNORED_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".simshelf", ".cache", ".pytest_cache", ".demo-workspace", ".qa-workspace", ".aws", ".ssh", ".agents", ".codex"}
VERSION_TAG = "SIMSHELF_VERSION"


def read_version(root: Path, version_file: str | None, *, captured: bytes | None = None) -> str:
    if not version_file:
        return "unversioned"
    path = contained(root, version_file)
    if captured is None and (not path.is_file() or path.is_symlink()):
        raise ValueError(f"Version file not found: {version_file}")
    try:
        tree = ast.parse(captured if captured is not None else path.read_bytes(), filename=version_file)
    except SyntaxError:
        # A syntax error is an execution failure worth recording, not a reason to lose the run.
        return "unversioned"
    values = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == VERSION_TAG for target in node.targets):
            values.append(node.value)
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == VERSION_TAG:
            values.append(node.value)
    if not values:
        return "unversioned"
    if len(values) != 1 or not isinstance(values[0], ast.Constant) or not isinstance(values[0].value, str):
        raise ValueError(f"{VERSION_TAG} must be one top-level literal string; code is never executed to read it")
    value = values[0].value.strip()
    if not value or len(value) > 80 or any(ord(c) < 32 for c in value):
        raise ValueError("Simulation version must contain 1–80 printable characters")
    return value


def put_blob(workspace: Path, data: bytes) -> str:
    key = digest(data)
    path = workspace / "blobs" / key[:2] / key
    if not path.exists():
        atomic_write(path, data)
    return key


def blob_path(workspace: Path, key: str) -> Path:
    if len(key) != 64 or any(c not in "0123456789abcdef" for c in key):
        raise ValueError("Invalid content identifier")
    return workspace / "blobs" / key[:2] / key


def stable_bytes(path: Path, limit: int = 32 * 1024 * 1024) -> bytes:
    for _ in range(3):
        before = path.stat()
        if before.st_size > limit:
            raise ValueError(f"Source file exceeds 32 MB: {path.name}; exclude large data from source capture")
        data = path.read_bytes()
        after = path.stat()
        if (before.st_mtime_ns, before.st_size) == (after.st_mtime_ns, after.st_size):
            return data
    raise ValueError(f"File kept changing while being captured: {path.name}")


def source_snapshot(workspace: Path, simulation: dict) -> dict:
    root = Path(simulation["root"])
    config = simulation["config"]
    output = contained(root, config["output_dir"])
    files, structures, warnings = [], [], []
    total = 0
    for directory, dirs, names in os.walk(root, followlinks=False):
        parent = Path(directory)
        dirs[:] = sorted(d for d in dirs if d not in IGNORED_DIRS and not (parent / d).is_symlink() and not (parent / d).resolve().is_relative_to(workspace) and (parent / d).resolve() != output)
        for name in sorted(names):
            path = parent / name
            rel = path.relative_to(root).as_posix()
            if path.is_symlink() or not path.is_file():
                continue
            if any(match(rel, p) for p in config["source_exclude"]) or not any(match(rel, p) for p in config["source_include"]):
                continue
            data = stable_bytes(path)
            total += len(data)
            if total > 100 * 1024 * 1024:
                raise ValueError("Source snapshot exceeds 100 MB; narrow the source patterns")
            key = put_blob(workspace, data)
            files.append({"path": rel, "blob": key, "size": len(data), "mode": stat.S_IMODE(path.stat().st_mode)})
            structure = data
            if path.suffix == ".py":
                try:
                    tree = ast.parse(data, filename=rel)
                    structure = ast.dump(tree, include_attributes=False).encode()
                except (SyntaxError, UnicodeError):
                    warnings.append(f"{rel}: could not parse Python; compared exact bytes")
            structures.append([rel, digest(structure), stat.S_IMODE(path.stat().st_mode)])
    if not files:
        raise ValueError("No source files matched. Check the simulation folder and source patterns.")
    if simulation.get("version_file") and simulation["version_file"] not in {f["path"] for f in files}:
        raise ValueError("The version file must be included in the source snapshot")
    snapshot_id = digest(json_text(files).encode())
    structure_id = digest(json_text({"algorithm": f"python-ast-{sys.version_info.major}.{sys.version_info.minor}-v1", "files": structures}).encode())
    result = {"id": snapshot_id, "structure_id": structure_id, "files": files, "warnings": warnings}
    atomic_write(workspace / "snapshots" / f"{snapshot_id}.json", json_text(result).encode())
    return result


def git_context(root: Path) -> dict:
    def git(*args):
        try:
            return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, timeout=3, check=True).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            return None
    commit = git("rev-parse", "HEAD")
    return {"commit": commit, "branch": git("branch", "--show-current") if commit else None, "dirty": bool(git("status", "--porcelain")) if commit else None}


def read_snapshot(workspace: Path, snapshot_id: str) -> dict:
    if len(snapshot_id) != 64 or any(c not in "0123456789abcdef" for c in snapshot_id):
        raise ValueError("Invalid snapshot identifier")
    return json.loads((workspace / "snapshots" / f"{snapshot_id}.json").read_text())
