# SimShelf

Your local simulation library and run journal. Run Python from the local browser portal, a terminal
or an editor, then use your browser to find, compare, and annotate the results.

SimShelf includes local portal, terminal and editor recording, explicit simulation versions,
exact source snapshots, parameters, scalar measurements, screenshots, notes,
file-capture policies, and portable workspace backups. Everything is local.

## Open the app

From a fresh checkout, explicitly set up its dedicated Python environment once:

```bash
./start.sh --setup
./start.sh
```

The app opens at **http://127.0.0.1:8740**. Keep the terminal running while using
the browser. Closing the browser does not interrupt recorded runs. Stopping the server cancels
its portal-launched runs; terminal/editor recorders remain independent.
Press Ctrl+C in the server terminal to stop the interface.

Python 3.11 or newer is required. The launcher keeps its environment and default
workspace outside the checkout. For a checkout at `/path/to/SimShelf/SimShelf`:

```text
/path/to/SimShelf/
  SimShelf/                 source checkout
  environments/SimShelf/    dedicated development Python environment
  workspaces/SimShelf/      persistent library
  workspaces/SimShelf-demo/ optional demo library
  test-output/SimShelf/     optional demo sources and outputs
```

`--setup` explicitly creates or updates only the launcher's dedicated environment.
Normal startup never installs dependencies. An active editor/terminal virtual
environment is not modified. Existing environments without this checkout's
ownership marker are refused; select a new path instead. A failed setup can be
retried with the same command. The built browser interface is included, so Node.js
is not needed to use the application.

Workspace precedence for the launcher is `--workspace PATH` (before `--cli` or
`--demo`), then `SIMSHELF_HOME`, then the external default above. Relative paths
resolve from the invoking terminal directory; `~` is expanded. Empty overrides
are rejected. `SIMSHELF_DEV_ROOT` changes the parent development directory and
`SIMSHELF_DEV_ENV` selects a dedicated environment path, which must be outside the
checkout. Set the same overrides for setup and subsequent commands. Environments
belong to one checkout: a different clone needs its own environment path. Library
paths are independent of code revisions; updating source does not move records.

For a different local workspace:

```bash
SIMSHELF_HOME=/path/to/my-library ./start.sh
```

The workspace contains the database and retained files, not your source project.
Keep it on a local disk. Register simulation source folders separately.

## Start a simulation in the browser

Once SimShelf is running, no terminal recording command is needed:

1. Choose **Add simulation**, enter the existing local source folder and its Python
   entry file (relative to that folder), and add it. Registration never executes code.
2. Select the simulation in the sidebar and choose **Start simulation**. Choose
   an existing interpreter from **Detected interpreters**, or use **Enter custom
   path**. Project environments and system/PATH candidates are listed without
   running them. Your saved selection is preserved; nothing is selected for you.
   Only select code and interpreters you trust. **Check selected Python** reports
   its version; optional **Check dependencies** compares declared requirements
   with that environment's installed-distribution metadata.
3. Add paired runtime arguments: parameter `--seed`, value `42`. Use **Add flag /
   positional** for a single token such as `--headless`. **No value** adds no token;
   a blank field passes an explicit empty argument. Type spaces directly, without
   shell quotes. **Split**, **Pair with next**, and the arrow buttons let you
   organize and reorder arguments without guessing your script's syntax.
   Grouping is only a view of adjacent tokens; saved settings retain exact argv.
   Alternatively, **Paste arguments** accepts a quoted argument string such as
   `--seed 42 --label 'with spaces' --headless`. Review the tokens and choose
   **Replace arguments**, or cancel. Paste arguments only, without Python or the
   script name. Unclosed quotes and trailing backslashes must be corrected.
   Single/double quotes and backslashes group text; variables, wildcards, shell
   operators and substitutions remain literal. Backslash-newline continues a
   line. The command preview reflects unsaved edits; expand **Exact argv** to
   inspect token boundaries. Editing settings requires validation again.
4. Check the working directory (relative to the source folder, `.` by default),
   capture folder and optional run name. **Validate interpreter & paths** checks
   Python without importing the simulation. It cannot certify installed script
   dependencies. **Save settings** remembers the selection without launching.
5. Choose **Start simulation** to save the settings and execute the registered
   script. Run details show its ID, live status and elapsed time. Open **Logs** for
   stdout/stderr, updated every three seconds; inspect parameters, metrics, source
   and retained files after completion.

If the registered entry is missing or wrong, choose an existing `.py` file inside
that source folder and click **Update registered entry**. This changes registration
only, never source or the registered version file. Previous runs keep their entry
command and source snapshot. Validate the new execution settings before starting.

The interpreter must already exist; SimShelf never installs packages, activates or
modifies a simulation environment. Plain scripts do not need SimShelf installed.
Scripts that import `simshelf` need it available in their selected interpreter.
A missing dependency or invalid argument produces a failed run with the real exit
code and stderr; fix the selected environment or arguments explicitly and start a
new run. Saved interpreter paths are machine-specific and are revalidated on each
launch, including after restoring a backup.

The capture folder is relative to the registered source root, even with a different
working directory. Point the script at the same output location using its own
arguments or `SIMSHELF_OUTPUT_DIR`. It must not overwrite another job's results.
The existing **File capture** rules control copies/references/ignored files. Runs
with overlapping capture folders are rejected; distinct folders allow concurrent
runs. SimShelf does not redirect arbitrary script writes or rewrite source.

### Discover available parameters

**Start simulation → Simulation parameters** combines discovered options and saved
arguments in one editor. Supported parameters show a name/value pair, concise
help and a default hint. Enable optional parameters to pass them; disabled defaults
contribute no arguments. Boolean flags need no value. Required options and known
conflicts are checked before saving/launching. Saved aliases, equals/separate forms
and order remain intact; unknown, repeated or positional arguments use manual rows
in the same editor. Rescan preserves edits and warns about changed declarations.
See [simulation parameters](docs/PARAMETER_DISCOVERY.md) for schema examples,
manual fallback and validation limits.

### Choose and check a Python environment

**Rescan interpreters** refreshes a bounded list: saved selection, project `.venv`
and `venv`, server PATH, server environment hints, accessible Conda registry
entries, and SimShelf's runtime. The runtime is labeled separately; it may not
have your scientific packages. Detection does not run candidates or activation
scripts. Versions remain unknown until you explicitly check a trusted executable.
A missing saved interpreter stays selected and is clearly flagged. Use a custom
absolute path for other managers or locations; discovery is not exhaustive.

**Check selected Python** and **Check dependencies** execute the selected Python
with isolated startup, with time/output limits. They do not run your simulation,
import installed packages, install anything, or evaluate `.pth` startup hooks.
A selected executable can itself contain arbitrary code, so choose only one you
trust. Saving and launching retain the existing explicit interpreter validation.
Checks are advisory and shown for the current selection in the current dialog;
changing selection or rescanning clears them and requires launch revalidation. Save settings remembers the path, not a guarantee
that its environment will remain unchanged.

Dependency checks support ordinary PEP 508 declarations in `requirements.txt`,
static `[project].dependencies`, and `[project].requires-python` in
`pyproject.toml`. They compare against the selected interpreter's distribution
metadata, never SimShelf's package set. Missing, incompatible, not-applicable and
unknown results remain distinct. With no declarations, requirements are unknown.
Optional extras, transitive dependencies, Conda solver files, nested requirements,
editable/URL installs and dynamic declarations are not resolved. Unsupported or
incomplete metadata is explained. User-site and `PYTHONPATH` packages are not
inspected. Checks work offline after SimShelf's dependencies are installed.

A matching NumPy or CuPy distribution does **not** prove it imports successfully,
that GPU/CUDA access works, or that a run will succeed. GPU execution is not part
of these checks. Use your existing trusted scientific environment and verify GPU
work separately. Fix environments yourself or choose another; SimShelf never
modifies them. This feature adds `packaging` as a SimShelf runtime dependency;
if upgrading an older checkout environment without it, explicitly run
`./start.sh --setup` to update only SimShelf's dedicated environment.

### Check where outputs will land

In **Start simulation → Output destinations**, inspect the resolved capture folder.
For a recognized option such as `--wvz`, choose **Map argument … as file** only
if that is how your script uses it. Choose directory for an output-folder option.
For a custom flag, select **Declare output path**, then its path argument token.
Use **Option=path** for a combined token, or declare a fixed path for scripts
that have no output argument. Multiple declarations are supported. All paths
resolve from the selected working directory; no shell expansion is performed.

Review any **Outside capture folder** warning. **Use suggested path** explicitly
changes the mapped argument to point inside capture; it does not move files,
create folders, or change source. Check that your script supports that destination
and will not overwrite existing results. Alternatively edit capture/arguments,
or check **Proceed with declared outputs outside capture coverage** to run
intentionally without capturing those locations. After changing an argument,
confirm its mapping again when prompted. Settings are remembered for future
launches; completed run records are unchanged.

Undeclared writes remain unknown. Declarations check path coverage, not whether a
script will actually write there or whether rules will retain its files. The
portal never scans extra locations automatically. Additional external files
cannot be registered as references from this editor; preserve them separately
or configure a future run's capture folder explicitly.

Run **Overview** and **Files** show the frozen capture folder and inspection
counts: copied, referenced, ignored, skipped and unchanged. **Complete** describes
inspection without reported errors; it does not mean every script output was
backed up. Zero observed files is stated explicitly. Only copied files are in
backups; references require their original files. Later attachments are separate
from automatic-capture counts. Failed/interrupted runs can still retain files;
check their capture status and errors as well as execution status.

**Stop run** requests cancellation of a portal run owned by this server. It sends
SIGTERM to the script's process group, then SIGKILL after three seconds if needed,
and attempts final output capture. The run is marked interrupted, even if it
handles termination and exits zero. Closing a browser tab leaves the run active;
stopping/restarting or killing the server requests the same cancellation through
an independent recorder supervisor. A new server can observe previous runs while
they finish cancellation/capture. Terminal/editor runs must be stopped at their
original process. Recovery never reports unfinished capture as successful.

Portal execution currently requires Linux and ordinary foreground Python scripts.
Do not use scripts that daemonize or move child processes into separate sessions:
those processes escape the owned process group. Killing the recorder supervisor
itself, system failure, and uninterruptible operating-system I/O can prevent final
capture or cleanup; interrupted/incomplete records are not proof every external
process stopped. No environment recreation or exact reproducibility is promised.

## Record your first simulation

Use the launcher CLI to select the same environment and workspace as the UI:

```bash
./start.sh --cli add /path/to/my-simulation --name "Scalar field" --entry field.py
```

The command prints a stable simulation ID, such as `scalar-field`. You can also
register a folder with **Add simulation** in the browser. The folder is inspected
in place; source files are not moved or rewritten.

From your simulation directory, wrap your usual command:

```bash
/path/to/SimShelf/SimShelf/start.sh --cli record --simulation scalar-field --name "Lower damping" -- \
  python field.py --dt 0.002 --seed 42 --damping 0.05
```

The recorder preserves the command as an argument array, its working directory,
source snapshot, exit status, stdout, stderr, and selected new or changed outputs.
It streams output to your terminal and returns the simulation's exit code.
The child command uses your terminal's `PATH`, so `python` can remain your
simulation interpreter; use its absolute path when needed. The launcher does not
activate its development environment in your shell.
Ctrl+C and termination signals are forwarded to the child process on Linux.

The interface is optional during recording. Use `./start.sh --cli list --simulation
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
Omit `workspace` when `SIMSHELF_HOME` is already set. Set it to the launcher's
external workspace path when recording from an editor. Plain installed `simshelf` commands
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

### Continue or migrate a legacy checkout workspace

If `.simshelf` exists in the checkout, default startup stops and prints its path.
It never silently switches you to an empty library. Continue explicitly:

```bash
./start.sh --workspace "$PWD/.simshelf"
```

To migrate, first stop the UI and all recorders writing to that library. Choose a
new archive name and a new or empty destination outside the checkout:

```bash
./start.sh --workspace "$PWD/.simshelf" --cli backup ../legacy-library-backup.zip
./start.sh --workspace "$PWD/.simshelf" --cli restore ../legacy-library-backup.zip --to ../workspaces/migrated-library
./start.sh --workspace ../workspaces/migrated-library
```

Check simulation/run counts, parameters, source snapshots, notes, screenshots and
logs in the restored library. Set `SIMSHELF_HOME` to its absolute path for future
launcher, CLI and editor use. Keep the original and backup until you have verified
the result; the launcher never removes them. A failed restore does not overwrite
an existing library. External references and registered simulation source paths
are not relocated or backed up: keep those original folders available. Backups
exclude unreferenced workspace files, so retain the original if it contains extras.
Active runs restore as interrupted; stop writers before this migration.

A custom workspace remains available through `SIMSHELF_HOME` or `--workspace`.
Existing checkout-local `.venv` environments are left alone and are not reused.

## Try the included example

The example needs only Python and SimShelf. It computes a small damped scalar
wave, writes actual field images and summary files, and keeps raw fields as
references. Create four real runs in a separate demo workspace:

```bash
./start.sh --demo
./start.sh --workspace ../workspaces/SimShelf-demo
```

One run deliberately fails to demonstrate retained partial results. The default
workspace is unaffected. Running the demo command again appends another set of
runs; it never clears existing history. Each invocation copies the two example
source files to a new external `test-output/SimShelf/scalar-demo-*` folder, which
also retains its outputs and is registered as a separate simulation. Keep these
folders while their reference-only files are useful. The demo honors an explicit
`SIMSHELF_HOME` or `--workspace`; unset it to use the separate default demo library.
Use `./start.sh --demo --output-root /external/path` to select another output root.

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
./start.sh --setup
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$PWD/src"
DEV_PYTHON="$(dirname "$PWD")/environments/$(basename "$PWD")/bin/python"
pnpm install --frozen-lockfile
pnpm run typecheck
pnpm run build
"$DEV_PYTHON" -B -m pytest -q -p no:cacheprovider --basetemp="$(mktemp -d /tmp/simshelf-tests-XXXXXX)/pytest"
# Build in a disposable source copy, since setuptools writes build metadata.
BUILD_ROOT="$(mktemp -d /tmp/simshelf-build-XXXXXX)"
git archive HEAD | tar -x -C "$BUILD_ROOT"
"$DEV_PYTHON" -B -m build "$BUILD_ROOT" --outdir "$BUILD_ROOT/dist"
```

Adjust `DEV_PYTHON` if using `SIMSHELF_DEV_ROOT` or `SIMSHELF_DEV_ENV`. The launcher
loads current checkout source without an editable installation; setup builds its
installed package from a temporary copy, keeping packaging metadata external.
The archive build above tests committed code; use an external copy including your
changes to validate uncommitted work. Conventional `pip install -e` remains
supported when explicitly requested, but setuptools may write ignored `.egg-info`
metadata into that source tree. Use an external source copy if it must stay pristine.
Do not install into an unrelated simulation interpreter without choosing to do so.
`requirements-dev.lock` is the historical tested dependency set; setup resolves the
ranges in `pyproject.toml`. Frontend development installs `node_modules` locally;
this is separate from Python launch/record/test defaults.

React/TypeScript source lives in `frontend/`. The build emits bundled assets into
`src/simshelf/static/`, which are intentionally tracked and packaged with Python.
The build also regenerates complete bundled dependency licenses; keep those and
`app.js.LEGAL.txt` with the assets. See [third-party notices](THIRD_PARTY_NOTICES.md).
Runtime UI resources are served locally; no CDN connection is required. Python
dependencies are declared
in `pyproject.toml`; `requirements-dev.lock` records the tested development
environment. `pnpm-lock.yaml` records the frontend dependencies.

This is a single-user local application, bound to loopback. Browser writes use a
same-origin token, and registered paths/source manifests constrain file access.
Remote hosting, user accounts, Git synchronization, environment provisioning, full
time-series plots, and 3D viewing remain outside the current feature set.

See [architecture](docs/ARCHITECTURE.md) for storage and versioning contracts and
[validation](docs/VALIDATION.md) for the checks performed on this build.

See [the issue #1 source audit](docs/validation/issue-1-source-audit.md) for
repository cleanup, history exposure, and package validation evidence.

See [issue #2 validation](docs/validation/issue-2-external-development.md) for
external launcher paths and legacy-workspace recovery checks.

See [issue #5 validation](docs/validation/issue-5-portal-execution.md) for portal
execution, cancellation, recovery and browser checks.

## SimShelf application version

The upper-right **Local · version** label and `simshelf --version` identify the
application, independently of your simulation's `SIMSHELF_VERSION` tag. The label
uses the running server's version; restart and reload after updating. Application
updates do not renumber existing simulations or rewrite previous runs.

See [application versioning](docs/APPLICATION_VERSIONING.md) for the single version
source, transition from the historical `0.1.0` baseline, deterministic PR build
increments and separately authorized immutable releases.
