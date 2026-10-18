"""Output declarations and explicit isolated-folder allocation; never redirect writes."""
from pathlib import Path
import os

from .common import contained
from .config import validate_config


def validate_output_policy(policy):
    if not isinstance(policy, str) or policy not in ("fixed", "per_run"):
        raise ValueError("Choose fixed or per_run output policy")
    return policy


def isolated_base(root, relative):
    """Reject symlinks even when they resolve inside the source root."""
    validate_config({"output_dir": relative})
    path = Path(root)
    for part in Path(relative).parts:
        path = path / part
        if path.is_symlink() or (path.exists() and not path.is_dir()):
            raise ValueError("Per-run output folders require real directories, without symbolic links")
    return path


def allocate_output(root, relative, run_id):
    """Exclusive creation; never reuse or remove an existing original output."""
    import re
    if not re.fullmatch(r"[0-9a-f]{32}", run_id):
        raise ValueError("Invalid output run identifier")
    isolated_base(root, relative)
    name = "run_" + run_id
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    fd = os.open(root, flags)
    try:
        for part in Path(relative).parts:
            try:
                os.mkdir(part, dir_fd=fd)
            except FileExistsError:
                pass
            child = os.open(part, flags, dir_fd=fd)
            os.close(fd)
            fd = child
        os.mkdir(name, dir_fd=fd)  # No exist_ok: a collision must never reuse data.
        child = os.open(name, flags, dir_fd=fd)
        try:
            stat = os.fstat(child)
        finally:
            os.close(child)
    except OSError as exc:
        raise ValueError(f"Cannot allocate isolated output folder: {exc}") from exc
    finally:
        os.close(fd)
    result = (Path(relative) / name).as_posix()
    verify_output(root, result, (stat.st_dev, stat.st_ino))
    return result, (stat.st_dev, stat.st_ino)


def verify_output(root, relative, identity):
    path = isolated_base(root, relative)
    stat = path.stat()
    if (stat.st_dev, stat.st_ino) != identity:
        raise ValueError("Isolated output folder was replaced; capture cannot safely continue")


def _output_review(simulation, cwd, arguments, output_dir, mappings, output_policy):
    validate_output_policy(output_policy)
    root = Path(simulation["root"])
    if not isinstance(cwd, str) or not cwd or "\0" in cwd or Path(cwd).is_absolute():
        raise ValueError("Working directory must be relative to the simulation root")
    directory = contained(root, cwd)
    if not directory.is_dir():
        raise ValueError("Working directory does not exist")
    config = validate_config({**simulation["config"], "output_dir": output_dir})
    capture = contained(root, config["output_dir"])
    if output_policy == "per_run":
        isolated_base(root, config["output_dir"])
    if not isinstance(arguments, list) or len(arguments) > 256 or any(not isinstance(a, str) or "\0" in a or len(a) > 8192 for a in arguments) or sum(map(len, arguments)) > 65536:
        raise ValueError("Invalid argument array")
    if not isinstance(mappings, list) or len(mappings) > 32:
        raise ValueError("Use at most 32 output mappings")
    targets = []
    for mapping in mappings:
        if not isinstance(mapping, dict) or set(mapping) != {"argument_index", "value", "kind", "format"}:
            raise ValueError("Output mappings require argument_index, value, kind and format")
        index, value = mapping["argument_index"], mapping["value"]
        kind, form = mapping["kind"], mapping["format"]
        if kind not in ("file", "directory") or form not in ("token", "equals"):
            raise ValueError("Choose file/directory and token/equals output mapping")
        if not isinstance(value, str) or not value or len(value) > 8192 or "\0" in value:
            raise ValueError("Declare a nonempty output path")
        if index is not None:
            if type(index) is not int or not 0 <= index < len(arguments) or arguments[index] != value:
                raise ValueError("Output argument changed: review its mapping again before launching")
        elif form != "token":
            raise ValueError("A declared fixed path must use token format")
        prefix = ""
        if form == "equals":
            prefix, sep, value = value.partition("=")
            if not sep or not prefix or not value:
                raise ValueError("An equals mapping needs an option=path token")
            prefix += "="
        # Paths are literal, as with shell=False: no tilde/variable expansion.
        lexical = directory / value
        resolved = lexical.resolve()
        try:
            resolved.stat()  # Detect inaccessible paths/loops; absent targets are normal before launch.
        except FileNotFoundError:
            pass
        inside = resolved.is_relative_to(capture)
        # Inventory skips symlink files/directories below capture, even if their
        # targets resolve within it. Only inspect the declared path's ancestry.
        symlink = any(p.is_symlink() for p in (lexical, *lexical.parents) if p != capture and p.is_relative_to(capture))
        covered = inside and not symlink
        reason = "Inside capture folder; rules and limits still apply" if covered else (
            "Symbolic link path is excluded from capture" if symlink else "Outside capture folder; not inventoried or retained there")
        suggested = capture / lexical.name if kind == "file" else capture
        replacement = prefix + os.path.relpath(suggested, directory)
        if output_policy == "per_run":
            covered = False
            reason = "Fixed declared path does not follow the per-run folder. The script must honor SIMSHELF_OUTPUT_DIR or joined run.output_dir; other writes are not captured."
        targets.append({**mapping, "resolved_path": str(resolved), "covered": covered,
                        "reason": reason, "suggested_argument": replacement if output_policy == "fixed" and index is not None and (kind == "directory" or lexical.name not in ("", "..")) else None})
    return {"output_path": str(capture), "output_policy": output_policy, "targets": targets,
            "requires_acknowledgement": any(not t["covered"] for t in targets)}


def output_review(simulation, cwd, arguments, output_dir, mappings, output_policy="fixed"):
    try:
        return _output_review(simulation, cwd, arguments, output_dir, mappings, output_policy)
    except (OSError, RuntimeError) as exc:
        raise ValueError(f"Cannot inspect declared output path: {exc}") from exc
