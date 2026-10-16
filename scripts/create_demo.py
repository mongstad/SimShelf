"""Record real example simulations into a separate, clearly named demo library."""
import argparse
import sys
import time
from pathlib import Path

from simshelf.recording import record_command
from simshelf.store import Store

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--workspace", type=Path, default=ROOT / ".demo-workspace")
args = parser.parse_args()
store = Store(args.workspace)
sim = store.add_simulation(ROOT / "examples/scalar_field")
batch = str(time.time_ns())
for name, damping, dt, fail in [
    ("Gentler damping", .015, .15, False),
    ("Stronger damping", .08, .15, False),
    ("Smaller time step", .025, .08, False),
    ("Partial results after a failure", .025, .15, True),
]:
    output = f"outputs/{batch}-{damping}-{dt}-{'failed' if fail else 'ok'}"
    command = [sys.executable, "simulate.py", "--damping", str(damping), "--dt", str(dt), "--steps", "100"]
    if fail:
        command += ["--fail-at", "45"]
    ident, code = record_command(store, sim["id"], command, name=name, tags=["example"], cwd=sim["root"], output_dir=output)
    if code != (1 if fail else 0):
        raise SystemExit(f"Unexpected demo exit code {code}")
    print(f"Recorded {name}: {ident[:8]}")
print(f"\nOpen this demo: simshelf --workspace {store.path} ui")
