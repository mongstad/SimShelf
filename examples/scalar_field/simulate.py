"""A dependency-free damped scalar wave example for SimShelf.

The version tag describes the intended model. Change it deliberately when you
want a new named version; comments and progress messages need no version bump.
"""

SIMSHELF_VERSION = "0.1.0"

import argparse
import csv
import json
import math
import os
import random
import struct
import time
import zlib
from pathlib import Path

import simshelf


def write_png(path, field, size):
    """Write an RGB visualization of the actual field using a fixed color scale."""
    pixels = bytearray()
    scale = 5
    for y in range(size):
        row = bytearray([0])
        for x in range(size):
            value = max(-1, min(1, field[y * size + x]))
            if value >= 0:
                color = (int(25 + value * 214), int(47 + value * 142), int(61 + value * 48))
            else:
                color = (int(25 - value * 76), int(47 - value * 133), int(61 - value * 142))
            row.extend(bytes(color) * scale)
        pixels.extend(row * scale)
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    payload = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size * scale, size * scale, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(pixels)) + chunk(b"IEND", b"")
    temporary = path.with_suffix(".tmp")
    temporary.write_bytes(payload)
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--simulation", default="scalar-field-example")
    parser.add_argument("--dt", type=float, default=0.15)
    parser.add_argument("--damping", type=float, default=0.025)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--size", type=int, default=64)
    parser.add_argument("--steps", type=int, default=120)
    parser.add_argument("--sleep", type=float, default=0)
    parser.add_argument("--output", default=None)
    parser.add_argument("--fail-at", type=int, default=None, help="Deliberately fail at this step to demonstrate retained partial results")
    args = parser.parse_args()
    if not 8 <= args.size <= 256 or args.steps < 1:
        parser.error("Use size 8–256 and at least one step")
    root = Path(__file__).resolve().parent
    output = Path(args.output or os.environ.get("SIMSHELF_OUTPUT_DIR", str(root / "outputs" / f"editor-{time.time_ns()}")))
    if not output.is_absolute():
        output = root / output
    relative = output.resolve().relative_to(root).as_posix()
    with simshelf.run(args.simulation, name=f"Damping {args.damping} · seed {args.seed}", parameters=vars(args), output_dir=relative) as run:
        output = run.output_dir
        output.mkdir(parents=True, exist_ok=True)
        rng = random.Random(args.seed)
        n = args.size
        field = [math.exp(-((x-n*.5)**2+(y-n*.5)**2)/(n*.09)**2) * (1+rng.uniform(-.015,.015)) for y in range(n) for x in range(n)]
        velocity = [0.] * (n*n)
        measurements = []
        run.note("Damped wave example. Compare field shape and the recorded squared amplitude across runs.")
        for step in range(args.steps):
            update = field.copy()
            for y in range(1,n-1):
                for x in range(1,n-1):
                    i=y*n+x
                    laplacian=field[i-1]+field[i+1]+field[i-n]+field[i+n]-4*field[i]
                    velocity[i] += args.dt * (laplacian-args.damping*velocity[i])
                    update[i] += args.dt * velocity[i]
            field=update
            if step%20==0 or step==args.steps-1:
                amplitude=sum(v*v for v in field)/(n*n)
                run.metric("mean_squared_amplitude",amplitude,step=step,sim_time=round(step*args.dt,8))
                measurements.append([step,step*args.dt,amplitude])
                write_png(output / "field-overview.png",field,n)
                (output/f"field-{step:04}.bin").write_bytes(struct.pack(f"<{len(field)}f",*field))
                print(f"step {step:4}  time {step*args.dt:7.3f}  mean squared amplitude {amplitude:.6g}",flush=True)
            if args.fail_at is not None and step>=args.fail_at:
                raise RuntimeError("Requested example failure; partial files remain recorded.")
            if args.sleep:
                time.sleep(args.sleep)
        with (output/"summary.csv").open("w",newline="") as stream:
            writer=csv.writer(stream)
            writer.writerow(["step","simulation_time","mean_squared_amplitude"])
            writer.writerows(measurements)
        (output/"summary.json").write_text(json.dumps({"steps":args.steps,"dt":args.dt,"damping":args.damping,"seed":args.seed,"mean_squared_amplitude":measurements[-1][2]},indent=2))


if __name__ == "__main__":
    main()
