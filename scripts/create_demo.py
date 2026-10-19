"""Record real example simulations into a separate, clearly named demo library."""
import argparse
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

from simshelf.recording import record_command
from simshelf.store import Store

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
development_root = Path(os.environ.get("SIMSHELF_DEV_ROOT", ROOT.parent)).expanduser().resolve()
parser.add_argument("--workspace", type=Path, default=Path(os.environ.get(
    "SIMSHELF_HOME", development_root / "workspaces" / (ROOT.name + "-demo"))))
parser.add_argument("--output-root", type=Path,
                    default=development_root / "test-output" / ROOT.name)
args = parser.parse_args()
output_root = args.output_root.expanduser().resolve()
if output_root.is_relative_to(ROOT):
    parser.error("--output-root must be outside the source checkout")
output_root.mkdir(parents=True, exist_ok=True)
# Each batch keeps its own source and referenced outputs. Never overwrite a
# previous batch or copy generated output from an older checkout-local demo.
example = Path(tempfile.mkdtemp(prefix="scalar-demo-", dir=output_root))
for name in ("simulate.py", "swss.toml"):
    shutil.copy2(ROOT / "examples/scalar_field" / name, example / name)
store = Store(args.workspace)
sim = store.add_simulation(example)
batch = str(time.time_ns())
for name, damping, dt, fail in [
    ("Gentler damping", .015, .15, False),
    ("Stronger damping", .08, .15, False),
    ("Smaller time step", .025, .08, False),
    ("Partial results after a failure", .025, .15, True),
]:
    output = f"outputs/{batch}-{damping}-{dt}-{'failed' if fail else 'ok'}"
    command = [sys.executable, "simulate.py", "--simulation", sim["id"], "--damping", str(damping), "--dt", str(dt), "--steps", "100"]
    if fail:
        command += ["--fail-at", "45"]
    ident, code = record_command(store, sim["id"], command, name=name, tags=["example"], cwd=sim["root"], output_dir=output)
    if code != (1 if fail else 0):
        raise SystemExit(f"Unexpected demo exit code {code}")
    print(f"Recorded {name}: {ident[:8]}")
print(f"\nDemo workspace: {store.path}\nOpen it with start.sh --workspace PATH (quote paths containing spaces).")
