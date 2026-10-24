# Preserve and review your simulation data

[Documentation](README.md) · [Getting started](GETTING_STARTED.md) · [Project overview](../README.md)

Commands using `./start.sh` assume your terminal is in the SimShelf source checkout.

## Versions: you decide what counts as a new simulation

For SWSS simulations, the version comes from `[swss].simulation_version` in
`swss.toml`; no Python tag is required or compared. Invalid, unsupported or stale
companions record **unversioned** when using manual argv, with metadata diagnostics
retained. They do not fall back to a legacy tag. Schema version and source hashes
remain separate from the declared simulation version.

For scripts **without a companion**, optionally put one literal assignment near
the top of the registered entry file:

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
| Simulation version | Your chosen name for the model, such as `0.1.0` | When you change the applicable declaration |
| Source snapshot | The selected source file bytes and permissions | When those bytes or permissions change |
| Python structural fingerprint | A conservative review aid based on the parsed source | When Python structure or included non-Python bytes change |

SWSS authors follow the standard’s source-version policy, including source-package
changes. SimShelf never bumps simulation versions automatically. For legacy tags:

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

The first run under each version is the comparison baseline. Later runs can show an
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

In a simulation's **Preservation settings**, configure its output parent and rules,
then review and confirm capture and optional Git inclusion together. See
[the preservation guide](GIT_ARCHIVE.md) for recursive output selection, truthful
completeness and later note/caption events.
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

### Reading run status

Overview keeps process status and progress separate from capture and Git
preservation. Completed execution does not prove all outputs were retained or
archived. Brief notices link to Files when capture is pending, incomplete or
needs attention, or Git preservation/access is uncertain.

Files shows the recorded inspected folder, counts, capture errors and limitations,
plus preservation status, source/annotation evidence, omissions and exact
historical downloads. Capture complete means inspection finished without reported
errors within its configured scope. Verified Git preservation describes the
reviewed scope at publication; current repository access is reported separately.
Intentional absence of Git preservation is recorded in Files without a routine
Overview warning. Full execution errors and terminal output are in Logs.

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

On a finished run, **Delete screenshot** removes a manually attached managed image
with confirmation. Captured outputs and external references are protected. Shared
image/source bytes remain while needed; original files and execution evidence stay
intact. There is no undo, and existing backups keep their old contents. The first
explicit screenshot deletion enables schema 3; stop older servers/recorders first,
as older builds cannot reopen that library. See [screenshot deletion](SCREENSHOT_DELETION.md)
for ownership, recovery, missing files and cleanup limitations.

## Remove obsolete runs

Open a finalized run and choose **Remove run…**, or select several runs in the
list/gallery and choose **Remove selected…**. Review the names, IDs, statuses and
count. **Cancel** is the default. Confirm only after backing up anything you may
need: removal deletes run records, notes, measurements, logs and unshared managed
copies. Running/finalizing runs must finish or be stopped before removal. A batch
containing an ineligible or unknown run is rejected as a whole.

Original source projects, Git history, original outputs and external reference
files are never deleted. Shared managed content remains while another record
needs it. A removed baseline's snapshot remains available for surviving runs'
source comparisons; their historical classifications do not change. Future runs
compare with the earliest surviving run, or establish a new baseline if none
remain. Counts, version history, favorites and comparison selections reflect the
remaining runs.

The first confirmed removal updates the library format; older SimShelf builds
cannot reopen it. Stop older servers/recorders using this library first. There is
no automatic migration on startup. A minimal deletion audit remains; this is not
secure erasure or an undo feature. Existing backups still contain old data, and
restoring one into a separate library can recover it. New backups exclude removed
payloads but retain audit entries and any baseline snapshots still needed.

If removal succeeds but file cleanup reports a problem, the records stay removed;
periodic recovery or `simshelf doctor` retries cleanup. Resolve the reported file
permissions or unexpected symlink without deleting original scientific files.
Long captures/backups can delay removal. See [run removal](RUN_REMOVAL.md)
for retention, locking and compatibility details.

## Backup and restore

Use **Back up workspace** in the browser. Restore currently uses the CLI, not
the portal. With the launcher, select the library explicitly:

```bash
./start.sh --workspace /path/to/my-library --cli backup /path/to/simshelf-backup.zip
./start.sh --cli restore /path/to/simshelf-backup.zip --to /path/to/restored-library
./start.sh --workspace /path/to/restored-library
```

If `simshelf` is installed on your PATH and selects the intended workspace:

```bash
simshelf backup /path/to/simshelf-backup.zip
simshelf restore /path/to/simshelf-backup.zip --to /path/to/restored-library
simshelf --workspace /path/to/restored-library ui
```

Backups use SQLite's consistent backup API, include the source snapshots,
retained copies, annotations, and frozen terminal logs, and verify file checksums
on restore. External reference files and the separate shared Git archive are not included.
Back up original source/results and the external archive independently. See
[archive recovery and backup boundaries](GIT_ARCHIVE.md#failure-recovery-and-retention). A run active at backup time
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

For cooperating scripts, [unique per-run output folders](RUNNING.md#unique-output-folders-for-cooperating-scripts)
automatically coordinate the recorder's capture target with `SIMSHELF_OUTPUT_DIR`
and joined `run.output_dir`. This is opt-in; it does not redirect fixed script
paths, preserve outside writes, or change copy/reference/ignore budgets.
