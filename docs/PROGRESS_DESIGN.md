# Issue #17 progress storage design

Owner separately authorized this explicit schema-4 opt-in design on 2026-10-17.
The issue implementation follows this contract; no user library is migrated by
development or validation. See [Progress reporting](PROGRESS.md) for usage.

## Explicit opt-in and compatibility

Schema 4 is activated only by an explicit **Enable progress reporting for
this library** action, before starting a progress-enabled run. Startup, browsing,
parameter discovery and ordinary recording must not migrate a library. The UI and
CLI must disclose that older builds will no longer open it, recommend a verified
backup, and require stopping older servers/recorders first. The operation refuses
active runs and is transactional and idempotent. Selecting a parser or calling a
new progress API is not implicit migration consent.

Schema 4 gives progress a separate latest-state table and recovery contract.
Using scientific metrics or user annotation history as a telemetry store would
misrepresent those records. Older builds do not understand a new progress journal
record and their run-removal path would leave a new table's payload behind; they
must therefore reject the opted-in library rather than appear fully compatible.

## Telemetry contract and bounded work

- Optional `run.progress(current=..., total=..., stage=...)` supplies structured
  telemetry for editor contexts and scripts joining CLI/portal recordings.
- Finite nonnegative current and positive total produce a percentage only when
  current <= total. Missing totals remain unknown; invalid input is rejected.
  Stage labels are bounded text. Changed totals or backward/reset reports replace
  the last state; they are not interpreted as monotonic global progress.
- Last-reported progress is separate from run status. A 100% report is not success;
  finalized/interrupted runs retain the last accepted report without forcing 100%.
  Source and report time remain stored internally. The owner-requested compact
  panel shows percentage, grouped counts and optional stage. For completed runs,
  successful process completion fills the bar to 100%, independently of telemetry.
  Completed runs display 100% and the stored finite positive total as both current
  and total counts. Their accessible description identifies these as completion
  display values, not measured telemetry. The original report stays unchanged.
  Completed runs without a valid total show 100% without step counts. Other states
  retain actual telemetry, or Progress unavailable without invented values.
  Execution status remains in the run header.
- Coalesce updates to at most one durable update per second per run, flushing the
  final pending update before finalization. Keep only latest telemetry and one
  bounded recovery checkpoint per run, not an unbounded stream of progress events.
  Checkpoints are explicitly replaceable telemetry, not scientific journal history.
- Use the existing workspace lock and SQLite transaction for cross-process
  ordering, lifecycle eligibility and migration. Atomic checkpoint publication
  precedes DB application; sequence numbers make replay idempotent and prevent
  stale checkpoints replacing newer state. Never alter original run events.
- Progress persistence errors must not silently terminate stdout/stderr draining
  or change scientific exit codes. Report failures separately and honestly.

## Plain-script interoperability

Offer auto/disabled/step-count/percentage text adapter selection in saved
launch settings and CLI recording. Fresh portal settings prefer auto after
explicit library enablement; saved settings and CLI defaults retain their
previous behavior. Auto selects the first valid format and stream, ignores
competing formats/streams, and excludes bare percentages. Its detected format
is additive latest-report JSON metadata, with no storage migration. See
[the detailed detection rules](PROGRESS.md#interpret-an-existing-scripts-text).
Recognize bounded, anchored supported formats,
including carriage-return-delimited updates; never infer progress from arbitrary
numbers, parameters, or an untrusted regex. Keep raw log bytes unchanged. Retain
the distinction between interpreted text and structured API reporting internally.
Structured reports take precedence if both sources are present. No source edits,
imports, dependency installs, ETA, pause/resume or stop-semantics changes.

## Recovery, backup and deletion

- Validate and replay pending checkpoints before dead-owner finalization. Reject
  writes to finalized/removed runs; run tombstones prevent resurrection.
- A failed enable transaction leaves schema 1–3 and all records intact; a failed
  update leaves either the previous state or a recoverable complete checkpoint.
- Backup uses the existing workspace lock and SQLite snapshot after recovery;
  schema-4 backups retain the latest progress. Restore verifies schema/integrity
  into staging, retains progress and marks active runs interrupted as before.
- Restore pre-upgrade backups only into a separate new/empty library, keeping the
  original library and archive intact. Verify run counts, snapshots, parameters,
  metrics, attachments, annotations and logs. External references are not backed up.
- Run deletion removes the associated progress row/checkpoint transactionally
  with existing tombstone/cleanup rules. Screenshot deletion must never lower a
  schema-4 library to schema 3. Preserve surviving scientific history and originals.

## Validation requirements

Cover explicit migration consent/no startup migration, old-build rejection,
rollback/failure injection, serialization, invalid/unknown totals, resets/stages,
coalescing and final flush, bounded long-job storage, crash/replay, stale updates,
finalized/deleted-run protection, API/CLI/editor/portal interoperability, both text
streams and carriage returns with unchanged logs, failure/cancellation/reconnect,
backup/restore and removal. Browser source/installed checks cover known/unknown
progress, retained final progress, dark/light and narrow views. Follow application
versioning, packaging and notice checks. Report untested environments honestly.
