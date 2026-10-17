# Simulation progress

Run details show **Progress** when a simulation supplies a valid
current/total pair. Unknown totals show no percentage. Elapsed wall-clock time
stays beside the run status. Finalized runs keep their last report, which may be
less than 100%; even a 100% report does not establish successful execution.
Progress is optional telemetry, separate from measurements, parameters and source
identity. It does not add pause/resume or change cancellation semantics.

## Enable a library explicitly

Progress reporting requires schema 4. First stop all runs and older servers or
recorders using the library. Back up the library and verify restore into a
separate new/empty folder: compare simulation/run counts, source snapshots,
parameters, measurements, notes, screenshots and logs. Reference-only external
files are not backed up and must be kept separately. Retain the original backup.

In **Start simulation → Progress reporting (optional)**, choose **Enable progress
reporting…**. Read the compatibility notice, confirm you verified the backup and
stopped older writers, then choose **Enable progress reporting for this library**.
Cancel leaves the library unchanged. Existing active runs block enablement.
Alternatively, after performing the same preparation:

```sh
simshelf --workspace /path/to/library enable-progress --confirm
```

The command's help and refusal without `--confirm` disclose the upgrade. Startup,
browsing, ordinary recording, selecting an adapter and calling the API never
implicitly upgrade a library. Once enabled, older SimShelf builds cannot reopen
it. There is no in-place downgrade. To use an older build, restore the pre-upgrade
backup to a separate library; it will not include subsequent work.

## Structured reports (preferred)

After enabling the library, use the existing Python run context:

```python
with simshelf.run("my-simulation", workspace="/path/to/library") as run:
    for step in range(101):
        # Perform the simulation work here.
        run.progress(current=step, total=100, stage="Solve")
```

The same API works when joining a portal or CLI recording. The selected
interpreter must already have the new SimShelf package available; nothing is
installed into a scientific environment automatically. Existing scripts without
progress calls continue unchanged.

Current/total accept finite numbers from zero through 1e15; totals must be
positive and current must not exceed total. Booleans, invalid totals and nonfinite
values raise `ValueError`. Omit total for unknown progress; omit both numbers for
a stage-only report. Stage labels are limited to 160 characters without control
characters. Changing totals or moving backward starts no implicit new run: it
replaces the displayed report. Use a stage name to explain phases or resets.

Reports coalesce to at most one ordinary durable write per second across writers
for a run. A short-lived timer flushes a pending report when calls become
infrequent, and context exit/finalization flushes the last pending value (which
may be within that second). Only the latest state and one recovery checkpoint are
retained, not a progress time series. Unexpected process termination can lose the
unflushed update. Final capture does not fabricate a final progress value.

Storage failures emit a bounded warning, retain the pending value for retry and
are recorded in the owning recorder's final `progress_error` when available.
Joined child errors are visible in its stderr/logs. Progress persistence does not
change the scientific exit code. Invalid API arguments are caller errors, like
invalid measurements, and can raise in the caller. Durable writes use the existing
workspace lock; slow disks or a long backup/capture can delay a write. Avoid
reporting on every particle/cell, and measure overhead in your workload.

## Interpret an existing script's text

In **Start simulation → Progress reporting**, choose one supported format, or
leave **Interpret terminal progress** set to **Off**. This setting is saved for
future launches and frozen in each new run's `progress_mode`. CLI equivalent:

```sh
simshelf --workspace /path/to/library record -s my-simulation --progress step -- python model.py
simshelf --workspace /path/to/library record -s my-simulation --progress percent -- python model.py
```

Supported formats match a whole line, case-insensitively, with spaces/tabs allowed
around separators and at the edges. Choose the corresponding adapter explicitly:

| Adapter | Accepted examples |
| --- | --- |
| Step counts | `step 1000/50000`, `step 1,000/50,000 (2.0%)`, `250 / 1000 steps`, `Step 500 of 1000` |
| Percentage | `25%`, `25.5%`, `Progress: 25%`, `50% complete` |

Count values may use correctly grouped comma thousands separators (`1,000`, not
`1,00`) and decimal points. Count formats may end in one parenthesized percentage.
It must agree with current/total to within half a unit of its printed precision:
`33%` allows 0.5 percentage points, `33.3%` allows 0.05. Counts remain the source
of the displayed fraction. Invalid totals, malformed grouping and inconsistent
percentages reject the entire line. No locale-specific decimal commas, exponent
notation or arbitrary extra text are recognized.

For example, `Headless run: target step 50,000` stays ordinary log text, while
`  step 1,000/50,000 (  2.0%)` is recognized by the step adapter. `Energy loss: 50%`,
`Convergence error: 25%` and `Mass retained: 80%` are ignored by both adapters.
Bare `25%` remains supported only in explicitly selected percentage mode; choose
that mode only when such standalone lines mean execution progress in your script.
The settings show examples for the selected adapter, not a separate parser or
an unrestricted regex preview.

Reports are observational: even 100% never stops, cancels or finalizes a run.
The process can continue producing results and can still fail with its real exit
status. Unsupported lines do not create a report; if a valid earlier report
exists it remains displayed, otherwise progress shows **Progress unavailable**.

Newlines and carriage returns terminate a report; a final unterminated line is
also considered. Invalid, decorated, ANSI-colored or overlong lines (over 256
bytes) are ignored. Both stdout and stderr are inspected; their relative ordering
is not guaranteed. Raw retained log bytes and log-size limits are unchanged.
Structured API reports take priority over parsed text for the rest of that run.

The compact panel shows **Progress**, percentage, grouped step counts and an
optional stage. Source and report time remain stored internally but are not shown
in the panel. Parsed text is a user-selected interpretation, not a validated
scientific measurement. The existing run header provides execution status.
There is no custom regex, arbitrary log-number inference, total inferred from
`--steps`, ETA, or automatic source modification. Unsupported formats remain
ordinary logs. Source changes are required only if you choose to instrument the
Python API; the supported text adapter can use existing script output unchanged.

## Recovery and limits

A transaction enables schema 4 and its separate latest-progress table. Bounded
atomic checkpoints use sequence numbers and the existing managed-data lock;
replay cannot replace a newer state or resurrect a removed/finalized run. Existing
scientific journal entries, annotations and measurements are not compacted.
Backup recovers pending checkpoints, snapshots progress in SQLite, and excludes
the replaceable checkpoint itself. Restore retains latest progress and marks
previously active runs interrupted, as before. Run removal deletes its progress;
screenshot removal does not alter progress or downgrade the library schema.

The panel retains the latest report, including after finalization; it does not
display report age. A run can make progress between reports or stop reporting
altogether. Never infer liveness,
physical simulation time, success or complete output capture from the bar.
Linux is the validated recorder platform. Browser polling remains approximately
three seconds. Long-job bounds are tested with synthetic updates; scientific
performance, week-long runs and other operating systems are not certified.

See [storage design](PROGRESS_DESIGN.md) and
[issue #17 validation](validation/issue-17-progress.md).
