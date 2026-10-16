"""Fixed isolated probe, executed only after explicit interpreter selection.

No site startup, package imports, project code, activation scripts or installs.
"""
import json
import os
from pathlib import Path
import platform
import sys
import sysconfig


def read_regular(path, limit=262144):
    if path.is_symlink() or not path.is_file():
        raise ValueError("non-regular or symlink metadata skipped")
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError("metadata size limit")
    return data.decode("utf-8", errors="replace")


def inspect():
    executable = Path(sys.executable).absolute()
    prefix = executable.parent.parent
    cfg = prefix / "pyvenv.cfg"
    config = {}
    warnings = []
    if cfg.is_file():
        try:
            config = dict(line.lower().split("=", 1) for line in read_regular(cfg, 16384).splitlines() if "=" in line)
            config = {k.strip(): v.strip() for k, v in config.items()}
        except (OSError, ValueError) as exc:
            warnings.append(str(exc))
    elif not (prefix / "conda-meta").is_dir():
        prefix = Path(sys.prefix)
    info = {"version": platform.python_version(), "prefix": str(prefix), "executable": str(executable)}
    if len(sys.argv) < 2 or sys.argv[1] != "metadata":
        return info
    paths = set()
    for base in (prefix,):
        for key in ("purelib", "platlib"):
            paths.add(sysconfig.get_path(key, vars={"base": str(base), "platbase": str(base)}))
        for lib in ("lib", "lib64"):
            paths.add(str(base / lib / ("python%d.%d" % sys.version_info[:2]) / "site-packages"))
    if config.get("include-system-site-packages") == "true":
        for key in ("purelib", "platlib"):
            paths.add(sysconfig.get_path(key, vars={"base": sys.base_prefix, "platbase": sys.base_prefix}))
    distributions = []
    scanned = set()
    entries = 0
    for path in sorted(paths):
        folder = Path(path)
        try:
            resolved = folder.resolve()
            if resolved in scanned or not folder.is_dir():
                continue
            scanned.add(resolved)
            with os.scandir(folder) as children:
                for child in children:
                    entries += 1
                    if entries > 4000:
                        raise ValueError("package directory entry limit reached")
                    if child.name.endswith((".pth", ".egg-link", ".egg-info")):
                        warnings.append("Path hooks, editable or legacy metadata are not evaluated")
                    if not child.name.endswith(".dist-info"):
                        continue
                    if child.is_symlink() or not child.is_dir(follow_symlinks=False):
                        warnings.append("Non-regular distribution metadata skipped")
                        continue
                    text = read_regular(Path(child.path) / "METADATA")
                    headers = text.split("\n\n", 1)[0].splitlines()
                    name = next((line[6:].strip() for line in headers if line.startswith("Name: ")), "")
                    version = next((line[9:].strip() for line in headers if line.startswith("Version: ")), "")
                    if name and version and len(name) <= 200 and len(version) <= 200:
                        distributions.append([name, version])
                    else:
                        warnings.append("Incomplete distribution metadata")
        except (OSError, ValueError) as exc:
            warnings.append("Metadata search incomplete: " + str(exc))
    env = {"implementation_name": sys.implementation.name,
           "implementation_version": "%d.%d.%d" % sys.implementation.version[:3], "os_name": os.name,
           "platform_machine": platform.machine(), "platform_python_implementation": platform.python_implementation(),
           "platform_release": platform.release(), "platform_system": platform.system(),
           "platform_version": platform.version(), "python_full_version": platform.python_version(),
           "python_version": "%d.%d" % sys.version_info[:2], "sys_platform": sys.platform, "extra": ""}
    info.update(distributions=distributions, marker_environment=env,
                warnings=sorted(set(warnings)), paths=sorted(str(p) for p in scanned))
    return info


if __name__ == "__main__":
    print(json.dumps(inspect()))
