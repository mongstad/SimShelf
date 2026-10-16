"""Source-checkout launcher. Uses only the standard library before explicit setup."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

PROJECT = Path(__file__).resolve().parents[1]


def configured(name: str, fallback: Path) -> Path:
    value = os.environ.get(name)
    if value is not None and not value.strip():
        raise ValueError(f"{name} must not be empty")
    return Path(value).expanduser().resolve() if value is not None else fallback.resolve()


def layout(project: Path, workspace: str | None = None, *, demo: bool = False) -> tuple[Path, Path]:
    root = configured("SIMSHELF_DEV_ROOT", project.parent)
    environment = configured("SIMSHELF_DEV_ENV", root / "environments" / project.name)
    if environment.is_relative_to(project):
        raise ValueError("The development environment must be outside the source checkout")
    if workspace is not None:
        if not workspace.strip():
            raise ValueError("--workspace must not be empty")
        library = Path(workspace).expanduser().resolve()
    elif "SIMSHELF_HOME" in os.environ:
        library = configured("SIMSHELF_HOME", root / "workspaces" / project.name)
    else:
        legacy = project / ".simshelf"
        if legacy.exists() or legacy.is_symlink():
            raise ValueError(
                f"Legacy workspace found: {legacy}\n"
                "Select it explicitly with --workspace to continue, or follow the "
                "README backup/restore migration procedure. Nothing has been moved."
            )
        library = (root / "workspaces" / (project.name + "-demo" if demo else project.name)).resolve()
        if library.is_relative_to(project):
            raise ValueError("The default workspace must be outside the source checkout")
    return environment, library


def ownership(environment: Path, project: Path) -> bool:
    marker = environment / ".simshelf-development.json"
    if not environment.exists():
        return False
    try:
        if json.loads(marker.read_text()) == {"checkout": str(project)}:
            return True
    except (OSError, ValueError):
        pass
    raise ValueError(
        f"Refusing to modify or use an unowned environment: {environment}. "
        "Choose a new SIMSHELF_DEV_ENV path; your active interpreter is not changed."
    )


def setup(environment: Path, project: Path) -> None:
    if not ownership(environment, project):
        environment.mkdir(parents=True, exist_ok=False)
        (environment / ".simshelf-development.json").write_text(
            json.dumps({"checkout": str(project)}) + "\n"
        )
    subprocess.run([sys.executable, "-m", "venv", str(environment)], check=True)
    # Build from a disposable copy: pip/setuptools must not write egg-info/build
    # products into the authoritative checkout. Runtime uses current source below.
    with tempfile.TemporaryDirectory(prefix="simshelf-setup-") as temporary:
        source = Path(temporary)
        for name in ("pyproject.toml", "README.md", "LICENSE", "THIRD_PARTY_NOTICES.md"):
            shutil.copy2(project / name, source / name)
        shutil.copytree(project / "src" / "simshelf", source / "src" / "simshelf",
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        subprocess.run([str(environment / "bin/python"), "-m", "pip", "install",
                        str(source) + "[dev]"], check=True)
    print(f"Development environment ready: {environment}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--setup", action="store_true", help="Explicitly create/update the dedicated environment")
    modes.add_argument("--cli", action="store_true", help="Pass remaining arguments to the CLI instead of the UI")
    modes.add_argument("--demo", action="store_true", help="Record the example outside the checkout")
    parser.add_argument("--workspace", help="Workspace (takes precedence over SIMSHELF_HOME)")
    argv = sys.argv[1:]
    # Stop launcher parsing at the mode: flags such as --help belong to the CLI.
    mode_index = next((i for i, value in enumerate(argv) if value in ("--cli", "--demo")), None)
    if mode_index is None:
        args, remaining = parser.parse_known_args(argv)
    else:
        args = parser.parse_args(argv[:mode_index + 1])
        remaining = argv[mode_index + 1:]
    try:
        # Setup does not open a workspace and must remain available for legacy recovery.
        environment, library = layout(PROJECT, args.workspace if not args.setup else str(PROJECT.parent), demo=args.demo)
        if args.setup:
            if remaining:
                parser.error("--setup does not accept extra arguments")
            setup(environment, PROJECT)
            return 0
        if not ownership(environment, PROJECT) or not (environment / "bin/python").exists():
            raise ValueError("Development environment is not ready. Run ./start.sh --setup explicitly first.")
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", SIMSHELF_HOME=str(library))
        env["PYTHONPATH"] = str(PROJECT / "src") + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
        python = str(environment / "bin/python")
        if args.demo:
            command = [python, "-B", str(PROJECT / "scripts/create_demo.py"), *remaining]
            if args.workspace:
                command += ["--workspace", str(library)]
        else:
            command = [python, "-B", "-m", "simshelf", "--workspace", str(library)]
            command += remaining if args.cli else ["ui", *remaining]
        os.execve(python, command, env)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"SimShelf: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
