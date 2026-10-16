# SimShelf

Your local simulation library and run journal. Keep running Python from a terminal
or editor, then use your browser to find, compare, and annotate the results.

Stage 1 includes terminal and editor recording, explicit simulation versions,
exact source snapshots, parameters, scalar measurements, screenshots, notes,
file-capture policies, and portable workspace backups. Everything is local.

## Open the app

From this directory:

```bash
./start.sh
```

The app opens at **http://127.0.0.1:8740**. Keep the terminal running while using
the browser. Closing the browser does not interrupt separately recorded runs.
Press Ctrl+C in the server terminal to stop the interface.

The launcher uses `.simshelf/` in this checkout as the workspace. On first use it
creates `.venv/` and installs the Python package if necessary. Python 3.11 or
newer is required; the built browser interface is included, so Node.js is not
needed to use the application.

For a different local workspace:

```bash
SIMSHELF_HOME=/path/to/my-library ./start.sh
```

The workspace contains the database and retained files, not your source project.
Keep it on a local disk. Register simulation source folders separately.

## Record your first simulation

Activate this installation and point the recorder at the same workspace as the UI:

```bash
source .venv/bin/activate
export SIMSHELF_HOME="$PWD/.simshelf"
simshelf add /path/to/my-simulation --name "Scalar field" --entry field.py
```

The command prints a stable simulation ID, such as `scalar-field`. You can also
register a folder with **Add simulation** in the browser. The folder is inspected
in place; source files are not moved or rewritten.

From your simulation directory, wrap your usual command:

```bash
simshelf record --simulation scalar-field --name "Lower damping" -- \
  python field.py --dt 0.002 --seed 42 --damping 0.05
```

The recorder preserves the command as an argument array, its working directory,
source snapshot, exit status, stdout, stderr, and selected new or changed outputs.
It streams output to your terminal and returns the simulation's exit code.
Ctrl+C and termination signals are forwarded to the child process on Linux.

The interface is optional during recording. Use `simshelf list --simulation
scalar-field` to inspect recorded runs without a browser.

Named command-line flags are **inferred**, not a complete account of the script's
resolved configuration. Defaults and values computed inside Python are captured
with the Python API below. The exact command is retained even when flag inference
is imperfect. A wrapper-only run reports the recorder's Python environment,
clearly labeled as such; it does not claim to know an arbitrary child environment.

## Record from an editor

Install SimShelf in the interpreter your editor uses, for example with
`python -m pip install -e /path/to/this/checkout`. Then:

```python
import simshelf

SIMSHELF_VERSION = "0.1.0"

# Parse your arguments first, including defaults and the actual random seed.
with simshelf.run(
    "scalar-field",
    workspace="/path/to/my-library",
    parameters=vars(args),
    name="Lower damping",
) as run:
    # Your simulation loop goes here.
    run.metric("energy", energy, step=step, sim_time=t, unit="J")
    run.attach("outputs/overview.png", caption="Final field")
    run.note("The wave remains coherent near the outer boundary.")
```

Use the same registered simulation ID and workspace in your editor and browser.
Omit `workspace` when `SIMSHELF_HOME` is already set. Plain `simshelf` commands
without either setting use `~/.local/share/simshelf`.

The Python API captures the actual interpreter and installed packages. If the
script is also launched with `simshelf record`, it joins the wrapper's existing run
rather than creating a second record. An exception marks the run failed and is
re-raised; SimShelf does not hide it. An editor context records Python text stdout
and stderr. Use the wrapper for subprocess/native output. For concurrent jobs,
prefer separate processes; overlapping editor console contexts in separate
threads of one process are not supported.

Log measurements at a useful interval rather than on every cell update. This
initial implementation journals each measurement synchronously. Full time-series
charts are planned for Stage 2; Stage 1 shows the latest retained measurements.

## Versions: you decide what counts as a new simulation

Put one literal assignment near the top of the registered entry file:

```python
SIMSHELF_VERSION = "0.1.0"
```

The tag is optional. Without it, runs belong to **unversioned**, with source
snapshots still preserved. `--version-file model.py` can select another Python
file during registration. The version file must be included in source capture.
SimShelf reads the tag by parsing the file; it never imports or executes it.

There are three distinct records:

| Record | Meaning | When it changes |
| --- | --- | --- |
| Simulation version | Your chosen name for the model, such as `0.1.0` | Only when you explicitly change the tag |
| Source snapshot | The selected source file bytes and permissions | When those bytes or permissions change |
| Python structural fingerprint | A conservative review aid based on the parsed source | When Python structure or included non-Python bytes change |

Examples:

- Adding a Python comment or changing formatting keeps the same simulation
  version and structural fingerprint, while preserving a different exact snapshot.
- Adding a progress bar or print statement keeps the same simulation version,
  but is shown as **Code changed within version**. Add a version note explaining
  the change when useful.
- Changing the numerical update without changing the tag also stays in that
  version, with the same visible change notice. Bump the tag when you decide it
  represents a new model revision.
- Changing runtime arguments creates a new run. It does not by itself change
  the simulation version or source snapshot.

The first run under each tag is the comparison baseline. Later runs can show an
exact source diff against it. Repeated identical snapshots are stored once.
Strings and docstrings are preserved by the structural comparison. Non-Python
files are compared exactly. Comparison uses a versioned Python AST representation,
so interpreter upgrades can conservatively report changes.

**A matching structural fingerprint is not proof of identical behavior.** Runtime
dependencies, external files, code that reads its own source, random state, and
hardware can matter. The source snapshot records the files at startup. SimShelf
does not isolate execution from source edits you make while a process runs.

Completed execution metadata stays fixed. Notes, tags, screenshots, captions,
cover images, and version explanations can be added later; annotation history is
retained separately.

## Choose which outputs to preserve

In a simulation's **File capture** tab, configure its output subfolder and rules.
Rules are tested in order; **the first match wins**. Patterns use `/` separators,
and `**/*.png` includes both nested PNGs and PNGs at the output folder's root.

- **Keep a copy:** preserve the file inside SimShelf; include it in backups.
- **Reference only:** retain its original path, size, modification time, and
  originating computer. The original is not copied or hashed.
- **Ignore:** leave it out of the run record. The original is never deleted.

The default rules copy common raster images, JSON, and CSV, ignore temporary
files/cache contents, and reference other outputs. The defaults allow 25 MB per
file and a 200 MB automatic copy budget per run. Oversized files appear as skipped
with a reason; the simulation's success is separate from capture completeness.
The preview shows current matches and estimated copy size. Rule changes affect
future runs; each run retains the rules it started with.

Final capture compares the output folder before and after execution, using size
and modification time, and captures only new or changed files. Unchanged old
outputs are excluded. A file rewritten with both the same size and timestamp
cannot be distinguished by this lightweight inventory. Close output files before
attaching them; atomic rename is a good way to finalize an output.

Symbolic links are excluded. Source capture excludes the output folder,
environment/cache/tool directories, and common secret filenames. Review the
source patterns for your project. Capture does not infer external inputs or
dependencies outside the registered folder.

References show **available**, **changed**, **missing**, or **another computer**.
They are not backups. Changing the browser's file-list filter never changes
capture rules or removes anything.

### Concurrent runs

Give simultaneous runs distinct output folders **and point both the simulation
and the recorder at the correct folder**:

```bash
simshelf record -s scalar-field --output-dir outputs/seed-42 -- \
  python field.py --seed 42 --output outputs/seed-42

simshelf record -s scalar-field --output-dir outputs/seed-43 -- \
  python field.py --seed 43 --output outputs/seed-43
```

The wrapper exposes the absolute capture path through `SIMSHELF_OUTPUT_DIR`.
The Python API exposes `run.output_dir` and accepts `output_dir="outputs/seed-42"`.
A script using the wrapper and API together inherits the wrapper's output folder.
SimShelf rejects concurrent runs watching the same or overlapping output folders to
prevent mixing their results. It does not rewrite arbitrary scripts' output paths.

## Screenshots, comparison, and notes

Select runs in the table or gallery and choose **Compare runs**. The comparison
shows code snapshots and recorded parameters, with differences highlighted.
Search includes run names, IDs, version labels, parameters, notes, and tags.
Numeric parameter filters accept scientific notation. Parameter and screenshot
filters apply to the loaded records; the footer states the loaded count. The first
200 runs load by default, with more available up to 1,000; text/status/version
searches query all stored records before that limit.

Open a run's **Screenshots** tab to upload, drag, or paste PNG/JPEG/WebP/GIF images.
Add captions and choose a cover. Other saved files can be downloaded from **Files**.
HTML and SVG attachments are offered as downloads rather than executed in the app.

## Backup and restore

Use **Back up workspace** in the browser or:

```bash
simshelf backup /path/to/simshelf-backup.zip
simshelf restore /path/to/simshelf-backup.zip --to /path/to/restored-library
simshelf --workspace /path/to/restored-library ui
```

Backups use SQLite's consistent backup API, include the source snapshots,
retained copies, annotations, and frozen terminal logs, and verify file checksums
on restore. External reference files are not included. A run active at backup time
is marked interrupted in a restored workspace; it is unchanged in the original.
Restore requires a new or empty directory and checks archive paths and hashes
before installing the workspace. The initial restore limit is 10 GB uncompressed.

Run `simshelf doctor` to replay durable events that were not indexed and to mark
dead local recorders interrupted. On Linux, process start identities guard
against PID reuse. The browser performs this recovery periodically as well.

## Try the included example

The example needs only Python and SimShelf. It computes a small damped scalar
wave, writes actual field images and summary files, and keeps raw fields as
references. Create four real runs in a separate demo workspace:

```bash
.venv/bin/python scripts/create_demo.py
.venv/bin/simshelf --workspace .demo-workspace ui
```

One run deliberately fails to demonstrate retained partial results. The default
workspace is unaffected. Running the demo command again appends another set of
runs; it never clears existing history.

## Share the source project

Recorded runs and simulation registrations are local data. The source project is
provided without a workspace database, captured source, retained results, or
browser screenshots. Launching the app creates a fresh empty workspace; the
example generator is optional.

The Git ignore rules exclude standard workspaces, generated outputs, local
environments, caches, database files, logs, and machine-local settings. Keep
custom workspace folders and backups outside the source checkout. Review any
screenshots before adding them to documentation: they can display personal paths
and run details. Source distributions exclude the generated capture folders.

## Develop and verify

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
pnpm install
pnpm run typecheck
pnpm run build
.venv/bin/python -m pytest -q
.venv/bin/python -m build
```

React/TypeScript source lives in `frontend/`. The build emits bundled assets into
`src/simshelf/static/`, which are packaged with Python. Runtime UI resources are
served locally; no CDN connection is required. Python dependencies are declared
in `pyproject.toml`; `requirements-dev.lock` records the tested development
environment. `pnpm-lock.yaml` records the frontend dependencies.

This is a single-user local application, bound to loopback. Browser writes use a
same-origin token, and registered paths/source manifests constrain file access.
Remote hosting, user accounts, Git synchronization, browser job launching, full
time-series plots, and 3D viewing are outside Stage 1.

See [architecture](docs/ARCHITECTURE.md) for storage and versioning contracts and
[validation](docs/VALIDATION.md) for the checks performed on this build.
