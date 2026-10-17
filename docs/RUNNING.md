# Run from the portal, terminal or editor

[Documentation](README.md) · [Getting started](GETTING_STARTED.md) · [Project overview](../README.md)

Commands using `./start.sh` assume your terminal is in the SimShelf source checkout.

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
See [simulation parameters](PARAMETER_DISCOVERY.md) for schema examples,
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

## Follow simulation progress

Run details show progress when the simulation supplies it; otherwise the panel
shows Progress unavailable. Successfully completed runs display 100% and, when
available, the stored total as both step counts. This completion display never
rewrites the original report. Reported progress never determines execution status
or proves success. Enable progress explicitly for a
library, then use `run.progress(current=..., total=..., stage=...)` or opt in to
interpreting supported step/percentage text in Start simulation. This optional
feature upgrades that library to schema 4; older builds cannot reopen it. Verify
a backup and stop older writers first. See [progress reporting](PROGRESS.md)
for consent, formats, recovery and limits.

## Quit or reopen SimShelf

Closing or refreshing a browser tab leaves the local server and simulations running.
Reopen the displayed localhost URL to reconnect. To shut down this server, use
**Quit SimShelf** in the sidebar. Confirmation shows the number of active portal
recorders, including startup/final capture. **Cancel** is the safe
default; **Stop runs and quit** explicitly requests cancellation and final capture.
The confirmation uses **Stop runs and quit** even when no portal recorders are active. The portal then shows shutdown
feedback; close the tab and restart using the launcher when needed.

CLI/editor recorders are independent and continue outside the portal. Quitting
never deletes records or outputs. Cancellation can leave partial results; inspect
run and capture status after restarting. Slow capture can outlive the server's
bounded shutdown wait. Detached processes and operating-system failures remain
outside its guarantees. A new launch during confirmation requires review again.

Ctrl+C / SIGTERM in the original server terminal still initiates the same portal
cancellation path. Custom ASGI/service hosts do not support the portal Quit action;
stop them in their original terminal or service manager. Starting a second server
on an occupied port reports the URL to check and the alternative `--port` option;
it never kills the existing process or assumes that port belongs to SimShelf.

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
