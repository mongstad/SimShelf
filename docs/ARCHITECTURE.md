# Stage 1 architecture

## Local components

- A Python CLI launches existing commands with `shell=False`, streams logs, and
  finalizes a run without requiring the browser service.
- The Python context API records resolved parameters, measurements, and explicit
  attachments, and joins an active wrapper through its run ID.
- FastAPI provides the local UI API and serves the compiled React/TypeScript app.
- SQLite stores simulations, runs, artifact manifests, measurements, annotation
  history, and event deduplication IDs. Schema version 1 is checked at startup.
- Source snapshots and retained artifacts share a SHA-256-addressed blob store.

```text
workspace/
  simshelf.sqlite3       searchable records and annotation history
  journal/<run-id>/      atomically written JSON events for recovery
  snapshots/<hash>.json  source manifest, byte hashes, structural fingerprint
  blobs/<prefix>/<hash>  immutable source and retained artifact bytes
  logs/<run-id>/         stdout.log and stderr.log
  staging/              temporary file copies, never final artifact references
```

Recorders apply journaled events directly using short SQLite transactions.
The UI periodically replays unapplied events. Event IDs make replay idempotent.
Semantic validation failures remove their rejected event rather than leaving
something that could unexpectedly apply later. An operational database failure
leaves its durable event available for `doctor` to recover.

The database is authoritative for queries; journals provide write recovery, not
a distributed synchronization protocol. Git export/import is deliberately deferred.

## Version contract

`SIMSHELF_VERSION` is a single top-level literal string in the registered version
file. It is parsed from bytes captured in the source snapshot; the source module
is never executed to discover its version. Explicit tag changes define named
versions. Missing tags use `unversioned`.

The exact snapshot hashes the sorted manifest of included relative paths,
file hashes, sizes, and modes. Comment/formatting edits change the exact snapshot.
For `.py` files a second fingerprint uses `ast.dump(..., include_attributes=False)`.
Comments and formatting disappear; literals, docstrings, calls, and numerical
operations remain. Non-Python source files use their exact byte hashes. Parse
failures conservatively use bytes and add a warning. The interpreter/algorithm
version is included in the fingerprint.

The first run for a simulation/version is its baseline. Subsequent records show:

1. `same`: same source snapshot;
2. `text-only`: different snapshot, same structural fingerprint;
3. `changed`: structural fingerprint differs.

These are review signals, not automatic semantic versions or reproducibility
guarantees. Progress reporting is visible as changed code, but never forces a
new simulation version. Users can add a version explanation without altering
captured execution metadata.

## Capture contract

Every run freezes its capture configuration. Final collection considers new or
size/mtime-changed regular files under its declared output folder. Rules use the
first match. Ignoring files never deletes originals. Referenced files are not
served through the HTTP file endpoint; copied content is served by its recorded
artifact ID and content hash. HTML/SVG and unknown types download as inert bytes.

Active recorders cannot share overlapping capture roots. This is enforced under the same
SQLite write transaction as run creation. Distinct per-run output folders allow
concurrent processes without overwriting or mixing result records.

Source capture freezes selected files at startup, without executing them. It does
not run the simulation from an isolated checkout. Lazy imports or source
introspection after later edits can therefore differ from the startup snapshot.
Neither external inputs nor absolute dependencies are automatically copied.

## Lifecycle and recovery

Run states are `running`, `completed`, `failed`, and `interrupted`. Completion
captures an independent status for outputs: `complete`, `partial`, or `incomplete`.
Finalized parameter and environment events do not mutate the execution record.
Annotations and new attachments remain appendable with history.

Ownership stores host, PID, and Linux process start ticks. Recovery only checks
processes on the original host, and marks vanished recorders interrupted without
claiming that final output collection succeeded. Interrupted state is not proof
that every descendant or remote task has stopped.

## Backup contract

A consistent SQLite backup determines the retained artifact and source manifest
set. The archive contains the corresponding blobs and frozen log copies, with a
SHA-256 manifest. Unreferenced intermediate objects and external output references
are excluded. Restore validates membership, paths, checksums, database integrity,
and schema into a staging directory before installing a new workspace. Active
records in the backup become interrupted on restore.

## Stage 1 limits

- Single-user localhost application, Linux runtime validation; other platforms
  have not been validated.
- Per-run inventory is capped at 20,000 files; source capture at 100 MB total and
  32 MB per source file; browser uploads at 25 MB per file.
- Terminal wrapper logs retain at most 10 MB per stream; browser tail previews
  show the last 200 KB. Python text console contexts are intended for one active
  recording context per process, or nested contexts used deliberately.
- Browser source previews are limited to 1 MB per file. Basic run detail reads
  the first 5,000 measurements. Detailed charts/downsampling are Stage 2 work.
- Full workspace restore is capped at 10 GB uncompressed and 100,000 archive
  members. Source and local reference locations are retained, not relocated.
- No automatic dependency-environment recreation or claim of bitwise replay.
