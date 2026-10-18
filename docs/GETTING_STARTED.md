# Your first SimShelf run

[Project overview](../README.md) · [All guides](README.md)

This walkthrough uses a disposable copy of the included scalar-wave example and
an empty library. It does not register or run your research project. SimShelf is
experimental: keep independent backups and verify scientific results yourself.
These instructions target Linux/Bash; Windows and macOS are not validated.

## 1. Set up SimShelf

Open a terminal in the downloaded/cloned **SimShelf checkout** (the directory
containing `start.sh` and `pyproject.toml`). Check Python, then explicitly install
the application into its dedicated environment:

```bash
python3 --version
./start.sh --setup
```

Python must be **3.11 or newer**, with `venv` and pip available. Setup normally
needs internet access for dependencies; it does not modify an active environment
or your scientific interpreter. Normal startup does not install anything.
For missing prerequisites, see [dependency help](#requirements-and-dependency-help).

With a checkout at `/path/to/SimShelf/SimShelf`, defaults are:

```text
/path/to/SimShelf/
  SimShelf/                 application source
  environments/SimShelf/    SimShelf's Python environment
  workspaces/SimShelf/      normal persistent library
```

The library stores the database and retained files; it is not your simulation
source folder. Keep both libraries and environments outside the checkout on a
local disk. [Setup](SETUP.md) explains overrides and legacy-library recovery.

## 2. Prepare a safe example and open the portal

In that same terminal:

```bash
SIMSHELF_TUTORIAL="$(mktemp -d /tmp/simshelf-tutorial-XXXXXX)"
mkdir "$SIMSHELF_TUTORIAL/scalar"
cp examples/scalar_field/simulate.py examples/scalar_field/simshelf.toml "$SIMSHELF_TUTORIAL/scalar/"
SIMSHELF_EXAMPLE_PYTHON="$(dirname "$PWD")/environments/$(basename "$PWD")/bin/python"
printf 'Source folder: %s\nPython: %s\nLibrary: %s\n' \
  "$SIMSHELF_TUTORIAL/scalar" "$SIMSHELF_EXAMPLE_PYTHON" "$SIMSHELF_TUTORIAL/library"
./start.sh --workspace "$SIMSHELF_TUTORIAL/library"
```

Keep the printed paths. The default interpreter calculation assumes no
`SIMSHELF_DEV_ROOT`/`SIMSHELF_DEV_ENV` override; if you configured one, use the
`bin/python` inside the environment reported by setup instead. This example
imports `simshelf`, so deliberately use the application environment for this
small tutorial. Your scientific projects should use their own suitable interpreter.

The browser opens **http://127.0.0.1:8740**. If it does not, open that URL manually.
Keep the terminal running. If the port is in use, check the existing server;
use `./start.sh --workspace "$SIMSHELF_TUTORIAL/library" --port 8741` for a separate
instance and open its printed URL. Do not stop an unfamiliar process.

`/tmp` is disposable and may be cleared by the operating system. Use this example
only for practice. For real work, choose a persistent library and source directory.

## 3. Register the example

1. Choose **Add simulation**.
2. Enter the printed **Source folder**, give it the name `First scalar run`,
   and set its entry file to `simulate.py` (relative to that source folder).
3. Add it and select it in the sidebar. Registration inspects files but does not
   execute the simulation or move its source.

On wider windows, drag the sidebar’s right edge to reveal longer names, or focus
the edge with Tab and use Left/Right arrows (Home/End select the width limits).
The button beside **Personal workspace** collapses or expands navigation and keeps
keyboard focus. Your browser remembers the expanded width and collapsed state
for this portal address. Smaller windows temporarily constrain the width; narrow
screens keep stacked navigation and hide the resize handle. These preferences
do not change your library or runs.

## 4. Choose Python and start

1. Open **Start simulation**. Choose the printed interpreter under **Detected
   interpreters**, or use **Enter custom path** and paste its absolute path.
   SimShelf does not automatically choose an interpreter for you.
2. Choose **Check selected Python**. Optionally choose **Check dependencies**;
   this example has no requirements declaration, so an unknown dependency result
   is expected. The check does not import the simulation or prove it will run.
3. In **Simulation parameters**, this example currently falls back to manual entry.
   Choose **Paste arguments**, paste `--simulation first-scalar-run --steps 40 --size 16`, inspect the six tokens
   and choose **Replace arguments**. Alternatively add three parameter/value rows.
   The example uses `--simulation` to join its registered record. In this empty
   library, the specified name gives ID `first-scalar-run`; if you choose another
   name, copy its ID from **Terminal / editor** and use that instead.
   Leave all other options absent to use script defaults. On scripts with supported
   declarations, enable only the discovered overrides you want; default hints do
   not themselves add arguments. [Parameter discovery](PARAMETER_DISCOVERY.md)
   explains why some declarations require manual review.
4. Keep the working directory `.` and capture folder `outputs`. Leave `--output`
   unset: this example honors SimShelf's supplied output directory. Give the run
   a name such as `First example`. Review the command preview and use
   **Validate interpreter & paths**, then **Start simulation**.

No progress migration or Git connection is needed. The bundled example logs
steps and measurements but does not report supported percentage/total telemetry;
**Progress unavailable** while running is expected. A short run may finish before
you see it running. Successful completion displays a full progress bar based on
process completion, not an invented intermediate report. [Optional progress](PROGRESS.md)
requires separate library consent; a reported 100% never stops a process or proves success.

## 5. Inspect and annotate the result

Open the new run. Check **Completed**, the command/parameters and source context.
In **Logs**, expect step output and no traceback. In **Files**, expect managed
`field-overview.png`, `summary.csv` and `summary.json`; raw `field-*.bin` results
are references under the example's capture policy. Download the CSV and inspect
its measurements. References require the original files and are not backup copies.

Add a note in the run's notes editor and save it. In **Screenshots**, upload the
example's `outputs/field-overview.png` as a manual attachment, then add a caption.
The automatic captured image and this attachment have different histories.
Reload and confirm your note and attachment remain. A second run with a changed
`--damping` lets you select both runs and **Compare runs**.

For other scripts, make the **actual output destination** agree with the capture
folder. SimShelf does not redirect arbitrary writes. A CSV written beside source
is not automatically captured when capture is `outputs`. Copy, reference and
ignore policies are distinct; inspect capture omissions even after a successful
run. See [capture guidance](DATA.md#choose-which-outputs-to-preserve).

## 6. Back up and close

Use **Back up workspace** for a library ZIP. It includes retained managed copies,
source snapshots and annotations, not external reference files or the separate
shared Git archive. Back up original source/results and that archive independently.
[Backup and restore](DATA.md#backup-and-restore) gives CLI restore instructions
into a new or empty library; there is currently no portal restore workflow.

Closing the browser leaves the server and simulations running. **Quit SimShelf**
asks for confirmation: **Cancel** is safe; **Stop runs and quit** cancels this
server's portal runs and requests final capture. Ctrl+C in its terminal follows
the same cancellation path. Terminal/editor recorders are independent. Restart
with the same explicit `--workspace` path to reopen this tutorial library.

## Requirements and dependency help

### Application versus simulation Python

SimShelf's application dependencies are FastAPI, Uvicorn, python-multipart and
packaging, resolved from `pyproject.toml` by explicit setup (the checkout setup
also installs development tools). The built browser assets are included; Node.js
is unnecessary for normal use. Setup requires disk space for this environment;
retained copies, snapshots, logs, backups and optional Git history grow separately.
No universal minimum CPU/RAM/GPU or fixed disk allowance has been validated.

A simulation may need NumPy, CuPy or other packages **in its selected interpreter**.
Installing SimShelf does not install these. Passive discovery does not execute
candidates. Explicit checks execute only the trusted selected Python with bounded,
isolated probes. Dependency checks read supported requirements/pyproject metadata;
unknown, missing and incompatible results are different. They do not prove imports,
CUDA/GPU operation, dynamic dependencies or scientific correctness.

If your trusted project supplies a requirements file, you can explicitly prepare
an environment you own (replace the example paths):

```bash
python3 -m venv /path/to/new-simulation-env
/path/to/new-simulation-env/bin/python -m pip install -r /path/to/trusted-project/requirements.txt
/path/to/new-simulation-env/bin/python --version
```

Select that exact `bin/python` in SimShelf. Review requirements and package sources
first; installation can run package build code and need network access. Follow
your project's and packages' upstream instructions for GPU/platform-specific
stacks. Do not use `sudo pip`, change system Python, or install guessed packages
based only on import names. SimShelf offers checks, not automatic installation.
See the [Fedora Python guide](https://developer.fedoraproject.org/tech/languages/python/python-installation.html)
for user-managed environments.

### Python and Git on Fedora

Check locally:

```bash
python3 --version
python3 -m venv --help
git --version
command -v git
```

On Fedora, if missing, explicitly install the relevant system packages:

```bash
sudo dnf install python3 python3-pip
sudo dnf install git
```

These are optional administrator commands for your computer; SimShelf never runs
them. Git's [Linux installation guide](https://git-scm.com/downloads/linux) covers
other distributions. Current validation uses Fedora 44, Python 3.14.8 and Git
2.56.0; Python 3.11 is the declared floor, not a claim of a tested version matrix.

Git is found on the **server process's PATH**. Recording, snapshots, notes and
workspace backups work without it. Source history/discovery requires an existing
ordinary repository or supported worktree. File selection can save preferences
without Git; tracked/ignored status requires Git. The shared archive explicitly
initializes its own dedicated bare repository and requires Linux `/proc` support.
It never initializes your source repository or synchronizes remotely.

There is no enforced numerical Git minimum or validated older-version matrix.
The archive uses `init --initial-branch`, transactional `update-ref --stdin` and
`core.fsync=all`, as well as ordinary object/index commands; use a current supported
distribution Git. Git 2.56.0 is the tested build, not an invented compatibility
floor. If your Git rejects an operation, leave archival off and inspect the error;
recording remains independent. See [archive limits](GIT_ARCHIVE.md).

### Troubleshooting

| Symptom | Next step |
| --- | --- |
| `python3` missing or older than 3.11 | Install a supported Python with venv/pip using your distribution; retry explicit setup. |
| Setup cannot download packages | Check network/package-index access; retry the same setup. Normal startup does not repair dependencies. |
| Environment is unowned | Select a new external `SIMSHELF_DEV_ENV`; do not delete or repurpose another environment. Use the override for setup and launch. |
| Legacy `.simshelf` warning | Follow [legacy recovery](DATA.md#continue-or-migrate-a-legacy-checkout-workspace); do not discard that data. |
| Interpreter missing after move/restore | Choose the correct existing absolute `bin/python` and revalidate. Saving a path does not recreate an environment. |
| Dependency check is unknown | Check declarations and upstream instructions. Unknown does not mean installed or missing. |
| Run fails with an import or argument error | Inspect stderr and the real exit status; fix the selected environment/arguments yourself and record a new run. |
| Git unavailable despite installation | Check PATH in the terminal that starts SimShelf, restart it after changes, and retry explicitly. Do not auto-initialize or reconnect. |
| Run succeeds but outputs are missing | Check the script's actual destination, capture folder, rules, size limits and omissions. Success does not guarantee preservation. |

Linux/Chromium is the validated platform family. Other operating systems/browser
engines, GPU scientific workloads and long/high-volume sessions are not certified.
See [validation](VALIDATION.md) for dated evidence, not a production guarantee.

## Remove a registration

To remove a simulation and all its library runs, select it, open the **Simulation settings**
cogwheel beside its title and choose **Remove simulation…**. Review the scope and type its exact name. Back up first
if you may need the history. Original source and output folders remain untouched;
active runs block removal and schema-1 libraries are refused without migration.
See [simulation removal](SIMULATION_REMOVAL.md) for retained Git archive data,
recovery and retry behavior.
