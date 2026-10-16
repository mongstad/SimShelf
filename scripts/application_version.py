"""Explicit development-only version check/bump against accepted Git history."""
from __future__ import annotations

import argparse
import ast
from pathlib import Path
import re
import subprocess
import tomllib

ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = "src/simshelf/_version.py"


def read_version(text):
    for node in ast.parse(text).body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__version__" for t in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError("Missing literal application version")


def next_version(base, change="build"):
    if not isinstance(base, str) or not re.fullmatch(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)(?:\.(?:[1-9][0-9]*))?", base):
        raise ValueError("Expected MAJOR.MINOR.PATCH[.BUILD] with positive BUILD")
    parts = [int(v) for v in base.split(".")]
    if len(parts) == 3:
        parts.append(0)
    index = {"major": 0, "minor": 1, "patch": 2, "build": 3}[change]
    parts[index] += 1
    for i in range(index + 1, 4):
        parts[i] = 1 if i == 3 else 0
    return ".".join(map(str, parts))


def accepted_version(root, ref):
    # Resolve once, then read only that immutable tree; never fetch or change refs.
    commit = subprocess.check_output(["git", "rev-parse", "--verify", ref + "^{commit}"], cwd=root, text=True).strip()
    paths = subprocess.check_output(["git", "ls-tree", "--name-only", commit, VERSION_FILE], cwd=root, text=True)
    path = VERSION_FILE if paths.strip() else "pyproject.toml"
    text = subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=root, text=True)
    return read_version(text) if path == VERSION_FILE else tomllib.loads(text)["project"]["version"]


def main(argv=None, root=ROOT):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-ref", required=True, help="Freshly verified accepted main commit/ref")
    parser.add_argument("--change", choices=["build", "patch", "minor", "major"], default="build")
    parser.add_argument("--write", action="store_true", help="Explicitly set the next version; otherwise check only")
    args = parser.parse_args(argv)
    try:
        base = accepted_version(root, args.base_ref)
        expected = next_version(base, args.change)
        path = root / VERSION_FILE
        current = read_version(path.read_text())
        if args.write:
            if current not in (base, expected):
                raise ValueError(f"Conflicting current version {current}; base {base}, expected {expected}. Review manually.")
            if current != expected:
                path.write_text(path.read_text().replace(f'"{current}"', f'"{expected}"'))
        elif current != expected:
            raise ValueError(f"Expected {expected} after accepted {base}; found {current}")
        print(f"Application version {expected}; accepted base {base} ({args.base_ref})")
        return 0
    except (ValueError, OSError, subprocess.CalledProcessError, KeyError) as exc:
        print(f"Version check failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
