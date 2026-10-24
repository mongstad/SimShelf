# SimShelf architecture

## Local components

- A Python CLI launches existing commands with `shell=False`, streams logs, and
  finalizes a run without requiring the browser service.
- The Python context API records resolved parameters, measurements, and explicit
  attachments, and joins an active wrapper through its run ID.
- FastAPI provides the local UI API and serves the compiled React/TypeScript app.
- SQLite stores simulations, runs, artifact manifests, measurements, annotation
  history, and event deduplication IDs. Schema versions 1–4 are checked at startup. Run removal selects schema 2,
  screenshot deletion selects schema 3, and explicit library progress enablement
  selects schema 4; none of these upgrades happens on ordinary startup.
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

## Local portal execution

The portal extends the original Stage 1 boundary with explicit local Python-script
execution. Registration and GET requests do not execute code. Token-protected,
same-origin POST/PUT actions validate an explicitly selected Python interpreter,
save execution settings, launch, or request stop. Validation invokes only an
isolated Python version probe (`-I -S -B`), with a three-second timeout, not the script.
Interpreters are existing absolute Python executable paths; symlink spelling is
retained so virtual environments keep their identity. No package installation.

Interpreter discovery is passive and Linux-validated: a bounded set of project,
saved, PATH, environment-hint and Conda registry paths is inspected without
running executables or activation scripts. It returns at most 64 candidates,
examines at most 32 PATH directories and 32 registry lines, ignores relative PATH
entries, and preserves virtual-environment spelling/identity while deduplicating
aliases. SimShelf's runtime is marked separately and never auto-selected.

Explicit, token-protected `interpreter/check` and `dependencies/check` POSTs
require a confirmed selection. A fixed standard-library-only probe runs via
argv with `shell=False`, isolated startup, no bytecode writes and cwd `/`.
Standalone checks have a five-second/512-KB output budget; launch validation
reuses the same version probe with its existing three-second budget. Probe process
groups are cleaned up on timeout/error. Executable trust remains the user's
responsibility; these flags are not a sandbox for a malicious interpreter.

Dependency probing reads bounded `.dist-info/METADATA` files from the selected
interpreter's standard site-package locations, without importing packages or
processing startup hooks. At most 4,000 directory entries and 256 KB per metadata
file are inspected. Partial/legacy/path-hook metadata is reported conservatively.
Static requirements/TOML files are limited to 256 KB each and 256 requirements;
symlink declarations and nested/URL/editable/Conda solver inputs are not followed.
The server's `packaging` library parses requirements and version constraints;
markers use a complete environment supplied by the target probe, never a fallback
to server metadata. No declarations means unknown requirements, not readiness.
GPU access, imports and actual execution remain untested by metadata checks.
Results are ephemeral UI advice; only the existing selected interpreter path is
persisted. No recording, snapshot, schema, environment provisioning or backup
contract changes are introduced.

Execution settings live in the simulation's existing JSON record: interpreter,
relative working directory, argv tokens and relative capture folder. Old records
need no schema migration. The entry remains a registered, existing `.py` file
inside the simulation root and must appear in source capture. Updating an entry
never changes source bytes or the registered version file. Settings changes affect
future launches only; each run keeps its exact command/cwd/capture configuration.
Backups include settings, but machine-local paths must be checked after restore.

Optional execution `output_mappings` declare at most 32 file/directory targets.
Each records either an argv index plus its exact token (whole token or text after
`=`), or a fixed path. Changed tokens require explicit remapping. The same-origin
`execution/outputs` POST inspects only declared path metadata/ancestry and capture
configuration; it does not probe Python, run source, scan extra roots, or mutate
argv. Common flag names are suggestions requiring explicit file/directory
confirmation, not inferred output semantics. Relative declarations resolve from
cwd without tilde/environment expansion, preserving symlink/parent traversal.
Targets outside capture or through skipped symlinks require a per-launch
acknowledgement; both server and supervisor recheck before recording. A missing
mapping leaves actual output coverage unknown and does not block ordinary runs.
The launch UI reviews the capture base independently of mapping drafts, keyed to
current simulation/cwd/capture/policy inputs. Empty fixed-path rows receive inline
guidance and block validation/save/start until completed or removed; they are
never silently omitted from persisted settings. Mapping diagnostics identify the
row. The backend still rejects empty declarations on preview, save and launch;
prospective paths and existing empty directories remain supported.

Settings preserve mappings in existing simulation JSON. Each portal run freezes
its launch-time path review and acknowledgement in `launch`, alongside the
existing immutable capture root/configuration. This is an expectation, not proof
of output creation or retention. Capture storage, rules, limits, overlap ownership
and backup membership remain unchanged. UI counts derive from existing automatic
capture counts; old records without counts remain explicitly unknown. No extra
capture roots or post-run external-reference registration are introduced: these
would need separate ownership, provenance and backup rules.

Synchronous API handlers run in FastAPI's thread pool. A server-owned supervisor
process calls the same `record_command` path as the CLI; it reserves capture roots
through the existing transactional start event. That supervisor is the recorded
owner (PID, host, start identity), so a replacement UI server does not prematurely
mark an alive recorder dead. `SIMSHELF_RUN_ID` lets a script's Python API join the
same record. The child environment is still labeled unknown until it reports
itself; interpreter validation is not dependency or reproducibility validation.

The browser argument editor pairs adjacent tokens for display only. Splitting or
pairing rows preserves the exact ordered string array; a null display value is
absent and an empty string is an explicit token. Grouping is rederived on reopen,
not stored as a second command representation. Paste import tokenizes quotes and
escapes locally, without expansion or shell execution, and requires a reviewed
replacement. Pending paste and argument edits invalidate launch validation.

Parameter discovery is a read-only GET over the root `swss.toml` schema-2
companion. A shared bounded, descriptor-relative reader validates portable
identity, rows and optional source hashes without an AST or code execution.
No alternate metadata source is silently merged. Missing/invalid data offers
explicit manual argv; static inspection is a separate explicit API choice.
The SimShelf version-1 extension initializes registration capture settings;
portable fields cannot be overridden. Existing saved settings remain deliberate
user choices. Legacy configuration files are refused for new runs.

Typed previews carry a declaration/binding fingerprint through validation,
supervisor startup and recording. Runs retain exact companion bytes/hash and
review provenance in their existing JSON data, separately from resolved values.
A later manual bypass retains the previously saved typed evidence. Source capture
must contain the same companion bytes; subsequent source mutation remains possible.
Old run records and schema versions are untouched. SWSS-described runs
require a copied log for complete capture; missing/ignored/reference-only/oversized
logs produce incomplete capture independently of process success.
See [parameter discovery](PARAMETER_DISCOVERY.md) for schema, limits, extension
semantics and implementation claims.

The browser sends argument arrays, never shell code. Execution is exactly
`[selected_python, registered_absolute_script, *arguments]` with `shell=False`.
There is no browser-supplied Python `-c`, shell, scheduler or remote-command mode.
Each run receives its root-constrained working directory and capture path.
Scientific code is executable and must be trusted by the local user. Source can
still change during execution, as in terminal/editor recording.

Each server retains its supervisors' control-pipe write ends; explicit stop,
normal server shutdown, or abrupt server death closes the pipe. The independent
supervisor observes EOF and cancels its owned script process group: SIGTERM,
then SIGKILL after three seconds. Cancellation before child creation records an
interrupted run without executing the script. Remaining in-group descendants are
stopped even when the main script exits first; such a run is interrupted rather
than reported successful. Final capture is attempted and reports its own outcome.
Stop is available only for live supervisors owned by that server, never by trusting
a browser-provided PID. Closing the tab does not close the control pipe.

The server accepts at most 32 active supervisors and waits up to 30 seconds for
startup acknowledgement. A startup timeout requests cancellation and tells the
user to check retained runs rather than implying execution never began. Shutdown
requests all cancellations and waits up to 15 seconds; supervisors still completing
capture remain independent rather than being killed and losing evidence. A new
server observes their run state and resumes normal journal/dead-owner recovery.
CLI/editor process ownership and stop behavior are unchanged.

This initial supervisor requires Linux. Scripts that daemonize or create separate
sessions escape its process-group boundary and are unsupported. Direct supervisor
termination, machine failure or uninterruptible I/O can prevent cleanup/capture;
interrupted state is not a guarantee all external processes stopped. Restart does
not resume simulations or recreate environments. Completed records stay immutable.

## Explicit server shutdown

The CLI reserves a loopback listener before opening a browser, then owns a single
Uvicorn Server instance. Its injected callback sets that instance's exit request;
there is no PID endpoint or signal to unrelated processes. Custom `create_app`
hosts have no callback and report portal Quit as unavailable.

`GET /api/server` reports live supervisor count (including startup/capture), launch
generation and capability. `POST /api/server/quit` requires loopback peer access,
the existing session token/origin checks, explicit confirmation, and consent to
stop active runs. The supervisor lock atomically checks the reviewed launch
generation and closes launch admission. In-flight validation cannot start a run
after this gate; newly admitted runs invalidate prior consent. Repeated Quit is
idempotent. Cancellation closes the existing control pipes immediately; response
background work requests server exit after the acknowledgement. Normal lifespan
cleanup retains the existing 15-second shared wait and independent capture owner.
No new recorder lifecycle, auto-restart, unload handler or data migration exists.
The browser stops polling after acknowledgement and describes shutdown as requested,
not proof of completed capture or termination of detached processes. Failed/lost
responses advise checking the original terminal before restarting.

## Application version contract

The application version is a literal in `simshelf/_version.py`. Setuptools reads
that attribute without importing runtime dependencies; Python and CLI import it,
and FastAPI exposes it through its metadata and `/api/workspace`. The existing
upper-right portal label consumes that response, with an unavailable state before
connection. No runtime Git, Node, build counter or installed-metadata lookup is
involved. Source and installed-wheel behavior share the same contract.

[Application versioning](APPLICATION_VERSIONING.md) defines the historical
`0.1.0` baseline, numbered builds, explicit accepted-main check and owner-controlled
release process. This value is independent of storage schema, scientific tags and
exact source/Git identity; changing it never migrates or rewrites run records.

## Version contract

For a valid, non-stale SWSS companion, `[swss].simulation_version` supplies the
recorded simulation version. `schema_version` identifies the metadata format.
The application-local Python tag is not a second SWSS version authority and is
not compared during discovery. Binding verification remains separate from the
declared label; matching bytes do not prove scientific or parser correctness.

Recording uses the reviewed companion evidence, checks its bytes against the
source snapshot and rejects bound-source changes observed during capture. An
invalid, unsupported or stale companion yields `unversioned` for an explicit
manual run, retaining available metadata diagnostics and captured source bytes.
It does not silently use a legacy tag. Previous records are never relabeled.

Only without a companion does `SIMSHELF_VERSION`, a single top-level literal string
in the registered version file, supply the version. It is parsed from captured
bytes, never executed; absent tags use `unversioned`.

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

## Deliberate run removal

[Run removal](RUN_REMOVAL.md) specifies transactional hard deletion plus minimal
audit tombstones, journal replay exclusion, queued file cleanup, shared baseline
retention and schema-2 compatibility. Managed-data locks serialize snapshot/start,
attachment publication, event replay, backups and reclamation across Linux
threads/processes. Live simulations do not hold the lock for their lifetime.
Source/log reads hold it while resolving and reading; artifact downloads freeze verified bytes into an
open temporary stream so concurrent unlink cannot break bytes or range requests. Removal
never mutates surviving execution metadata or traverses original output paths.


## Deliberate screenshot deletion

[Screenshot deletion](SCREENSHOT_DELETION.md) limits removal to manually attached
managed raster images on finalized runs. Separate schema-3 tombstones and annotation
entries preserve original attachment history and suppress replay; completed run rows
and captured scientific outputs stay unchanged. Reference-aware cleanup shares the
run-removal lock/queue and never unlinks source/shared content still in use. Only an
explicit successful deletion activates schema 3; schema-1/2 startup stays compatible.
The list/gallery derives a surviving cover without rewriting historical annotations.


## Optional progress telemetry

[Progress reporting](PROGRESS.md) uses a separate latest-state table and bounded
atomic `journal/<run-id>/progress.json` checkpoint after explicit schema-4 consent.
It is not a scientific metric or annotation event. Managed-data locking serializes
checkpoint publication, sequence allocation, replay, finish, backup and removal.
One-second coalescing plus final flush bounds durable work; one row/checkpoint per
run bounds retained telemetry. Older finalized run rows remain unchanged.
Structured API input takes precedence over explicit whole-line text adapters;
stdout/stderr bytes and process ownership remain unchanged. Lifecycle status is
independent of reported fraction. The UI uses report source plus the run's frozen
`progress_mode` to distinguish text percentages from counts; structured reports
remain independent of the adapter. Fractional counters and legacy text reports
without a known adapter use neutral units. Completion is a display projection,
and no report, parser, cache or storage semantics change. The [design](PROGRESS_DESIGN.md) specifies the
separately authorized migration and recovery boundaries.

## Optional local Git provenance

[Local Git history](GIT_PROVENANCE.md) defines a nullable provider-neutral format-1
interface and an explicitly confirmed, single-repository mapping. Settings use an
additive metadata key without a schema migration. Future runs freeze observations
with their exact snapshot ID; old records stay unchanged. Inspections are bounded
and read-only, compare raw bytes without filters, and never invoke transports.
Restored/moved library bindings require reconnection. No-Git recording remains
independent; local commits and remote synchronization are deferred follow-ups.


## Legacy Git file preferences

[Legacy Git file selection](GIT_FILE_SELECTION.md) is separate from recorder provenance:
bounded metadata inventories and typed file/folder/extension rules produce exact
current-path previews. These endpoints preserve existing clients; current UI
configuration uses the combined preservation review below. The configured base capture subtree is pruned before source
inventory traversal;
its boundary metadata and configured path participate in the review revision.
Git classification is scoped to inventoried literal files; output descendants
cannot consume source inventory entries. Other source/configuration paths remain
visible regardless of snapshot or Git ignore patterns. Separate future-output
consent and per-run archive budgets are unchanged.
Explicit saves use additive, location-bound metadata; no
schema migration or completed-record write occurs. Optional exact-path ignore
additions require a separate refreshed review and append only to the registered
source folder's `.gitignore`, using descriptor checks and advisory locking. No
Git index/history/network mutation is exposed. External editor concurrency and
partial-write limitations are documented; #45 must independently review and
authorize any future staging/commit.

## Explicit shared archive

[Archive design](GIT_ARCHIVE_DESIGN.md) adds versioned metadata and an optional
post-finalization publisher, independent of scientific run records. Frozen
consent and capture-relative future rules feed verified managed copies; an isolated
Git index and atomic ref transaction publish immutable per-run events. Post-run
attachments use separate approved additions. Historical downloads verify the
recorded commit/path/hash. No storage schema migration or source Git writes occur.


Issue #56 adds read-only archive/consent status projections and a unified Run files
presentation. Attachment associations require identity, size and hash; separate
archive events keep their historical download addresses. The source Git section
retains its independent connection. Publication, recovery, storage and scientific
records remain unchanged. The later format-2 local records described below add
reviewed notes without defining portable semantics. See the
[approved Stage A design](MASTER_ARCHIVE_UX_DESIGN.md).

Archive connection changes require explicit disconnection first. A location-bound
last-successful connection preference (path, repository identity and workspace
binding) uses the existing versioned metadata namespace, without a schema change.
Connection and preference updates share one SQLite transaction under the workspace
lock. This preference never triggers startup connection, changes scientific run
records or grants archival consent; reconnection still validates repository identity.

## Coordinated isolated outputs

Issue #120 restricts launcher allocation independently of typed/manual argv.
The same bounded SWSS discovery projects metadata/binding status and local policy
eligibility. Valid associated metadata recommends fixed-parent capture; metadata
alone establishes no coordinated-root agreement. Present but invalid, stale,
unsupported or unassociated metadata leaves ownership unknown and also refuses
`per_run` until explicitly corrected/reviewed. Manual fixed-parent runs remain
available. No metadata means both existing policies remain available.

Save/validate, output preview, launch/supervisor and recorder entry enforce the
restriction. Recorder entry rechecks adoption after source capture, before
allocation. Existing saved choices are never migrated: the dialog keeps an
incompatible selection blocked until the user explicitly chooses fixed output
and validates/saves it. Rescans invalidate validation, including manual mode.
The indicator separates metadata validity from listed-byte binding and makes no
scientific conformance claim. A supplied SWSS companion requires a copied new or
changed log; unchanged historical logs cannot satisfy that run's evidence check.
Filesystem checks do not isolate later external edits. Shared-parent overlap
guards remain in force; this does not establish simultaneous-run attribution.

Issue #69 adds explicit `output_policy="per_run"` execution settings and matching
CLI/Python options; omitted settings remain `fixed`. Under the recorder start
lock, the run UUID names an exclusively created child of the configured capture
parent. Descriptor-relative creation uses no-follow directory opens. Validation
is passive; allocation happens only at start. The frozen `capture_config` and
`capture_root` point to that child, while additive `output_policy`/`output_base`
run metadata retain the choice. `SIMSHELF_OUTPUT_DIR` and joined `run.output_dir`
use the same child. At the shared `record_command` child-launch boundary,
`SIMSHELF_OUTPUT_POLICY` is assigned from the validated recorder policy alongside
`SIMSHELF_OUTPUT_DIR`, overriding inherited values. `fixed` denotes a shared
capture parent (possibly absent or occupied); `per_run` denotes the exclusively
preallocated root. This additive SimShelf adapter does not change SWSS or
independent in-process API contexts. Argv and cwd are unchanged. No schema upgrade is involved.

Source snapshot exclusion uses the base capture configuration, so sibling run
outputs cannot enter snapshots merely because isolation is enabled. Archive
consent is compared against that base configuration; its initial fingerprints,
final capture and future selection use the exact run folder. Rules and budgets
remain capture-relative. Existing transactional overlap rejection still applies.
Directory identity is checked before child execution and final capture; missing,
symlinked or replaced folders produce failure/incomplete capture instead of
silently collecting another folder. This does not sandbox arbitrary script writes
or external directory changes during capture. Failed-start empty directories are
preserved, and unknown outside writes remain unknown. See the
[user workflow](RUNNING.md#unique-output-folders-for-cooperating-scripts).

## Explicit source relocation

Issue #60 introduces token-protected preview/confirm POSTs for remapping an
existing registration. Preview checks absolute paths, no-follow directory/file
metadata, entry/version files, capture boundaries and registration collisions.
The review digest binds registration, target identity and location-bound Git
settings. Confirmation repeats validation under the managed-data lock and one
SQLite transaction, refuses active runs and updates only registration root plus
an additive location revision. It removes that simulation's source Git mapping,
file-selection preferences and archive settings; other mappings, master connection
and historical archive events remain intact. No schema migration or source writes.

Recorder entry checks the registration location revision under the same lock.
Portal supervisors carry the source binding through validation and recorder entry,
so pending launches cannot cross relocation or a move-away-and-back unnoticed.
Registration add/update also take this lock. Historical rows, blobs, journals,
references and captured paths are never rewritten. Existing launch checks still
validate saved execution preferences before use; relocation does not probe Python.
External directory mutations are not locked by SimShelf: the user must not move
or replace folders concurrently with review/confirmation/launch.

## Run-detail navigation

Issue #54 captures the loaded visible run IDs and simulation ID when a list item
opens. Previous/Next use that immutable frontend sequence, independent of polling.
Client-side timestamp/run-ID ordering resolves ties. Direct-link fallback reads
at most 1,000 runs scoped to the fetched run's simulation; late fallback responses
are discarded after navigation. Back scopes the list to the captured simulation.
RunDetails is keyed by run ID, isolating all detail state and asynchronous updates,
including nested archive/file components. No API, execution, Git or schema changes.

## Simulation removal

`simulation_removal.py` implements explicit unregistering for existing schemas
2/3/4; schema 1 is refused before recovery or writes. A preview revision covers
the authoritative simulation, runs, dependent records and relevant metadata.
The workspace lock spans reconciliation, revalidation and a single database
transaction. That transaction shares run-removal record/tombstone/cleanup-queue
logic, removes only the selected simulation's associations and registration, and
adds a minimal `deleted_simulation:<id>` retry audit. No schema is changed.
Registration cannot reuse an audited ID, and start events require a live
registration. Late optional archive results cannot recreate deleted-run metadata.
Reference-aware managed-file cleanup follows commit and survives interruption;
source directories and Git archive repositories are never opened by removal.
See [the user workflow](SIMULATION_REMOVAL.md) and its validation evidence.

## Log viewer presentation

Issue #84 isolates the log viewer by run/stream and serializes its existing
three-second polling with an unmount guard for late results/errors. Browser-local
`simshelf-logs` preferences control wrapping and follow, with session fallback
when storage fails. Follow reacts to explicit upward input, not generic scroll
events; horizontal position is retained while following. Layout/resize updates
pin only an enabled follower. No log endpoint, capture, schema or scientific
record changes are involved. Only the existing stdout/stderr views are exposed.

## Simulation settings activity

Issue #83 adds a read-only `administration_active` field to simulation list
responses. It uses the same predicate as removal: nonterminal runs or pending
capture block administration. The query checks all runs for each simulation,
independently of list pagination, filters and recorder ownership. A read
transaction keeps counts/activity consistent; no new stored field or schema is
introduced. The API also includes live server-owned supervisors, identified by
simulation from admission until process exit. Live supervisor sets are sampled
before and after the database read, using the existing lock only for those
observations; source/database I/O never holds the lifecycle lock. Their union
covers startup before a run ID and post-record finalization conservatively.

The title cogwheel uses native disabled semantics until current activity is
known to be false. Query changes immediately invalidate old refreshes; obsolete
responses/errors cannot replace newer eligibility, and failed refreshes disable
the control until a successful poll. Ordinary polls do not blink a known state.
This remains periodically refreshed guidance, not a reservation or authorization
boundary: external activity can start after a response. Existing transactional
removal/relocation guards, already-open dialogs and missing-source recovery stay
unchanged. Schema-1 removal remains unavailable even when the cogwheel is enabled.


## One-library preservation workflow

[Library preservation](LIBRARY_PRESERVATION_DESIGN.md) implements one capture/Git
review, recursive managed-output inclusion and format-2 local records. Separate
`preservation_v2:` policies, pending operations and events preserve legacy consent
semantics without a schema migration. Explicit adoption saves capture and new
consent atomically and disables the legacy active setting; old plans/events stay
unchanged. Existing publication locks, operation refs and byte verification apply.

Automatic preservation now uses one effective-state gate: global ON, verified
shared repository, individual participation, and valid reviewed scope. The global
preference defaults OFF when absent; connection alone never activates Git. The
single simulation switch retains exact reviewed choices when paused, including
legacy consent. Simulation preferences can be edited while the global gate is
OFF; ON still validates repository and reviewed scope, while OFF remains available
without Git. The compact header distinguishes saved preference from effective
activity, with amber ON when the master is disabled. Both preferences are included in backups; location/identity checks
still prevent implicit activation after restore. Active runs retain frozen plans.
See [two-level state details](LIBRARY_PRESERVATION_DESIGN.md#two-level-automatic-participation).

Run summaries distinguish execution, capture and policy-relative Git completeness.
Legacy manifest-only events remain unchanged and explicitly have no scientific
payloads. Files joins snapshots, copies and Git revisions by exact identity/hash;
source/artifact retrieval verifies retained bytes. Later saved notes, captions and
manual attachments require reviewed append-only events, with bounded records and
cumulative budgets. Pending attachment blobs survive existing cleanup and backup.
Backups still exclude the external Git repository; Git alone cannot restore a
workspace. Source Git remains independent. See the unchanged
[Phase 1 audit](validation/issue-118-library-preservation-audit.md) and the
[implementation validation](validation/issue-118-library-preservation.md).

## Stable archive location observations

`location_identity.py` retains verified legacy device tokens for Btrfs locations
under additive `location_device_v1:` metadata. Keys bind hostname, canonical path,
filesystem/subvolume ID and inode. Successful archive/preservation verification or
explicit setup can establish an anchor; failed checks cannot. Checks read existing
anchors without rewriting consent, completed records or archive objects. A new
filesystem at a previously observed path gets a distinct string token, avoiding
both device/inode reuse and JSON integer precision loss. Other filesystems keep
existing checks. The auxiliary metadata is backup-compatible and does not change
schema versions. Old builds do not gain the reboot recovery behavior.

Reconnect checks canonicalize paths in the backend. An explicit `remap` choice is
required to adopt a changed library binding at the remembered archive path; a
trailing slash cannot switch from verified reconnect to implicit remapping.
Archive marker/configuration and location safety checks still apply to remapping.
