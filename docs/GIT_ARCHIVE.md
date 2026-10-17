# Shared local Git archive

SimShelf can keep one dedicated local Git archive for several simulations. Each
opted-in run gets an initial commit; later, explicitly approved attachments get
additional commits belonging to that same run. Scientific version, source Git
revision, exact source snapshot and archive commit are different records.

## Set up and enable

1. Create an empty directory outside the SimShelf application, library and all
   simulation source folders. In **Git history → Shared master Git archive →
   Archive location and setup**, enter its absolute path, select initialization and
   choose **Initialize and connect archive**. No remote is contacted. This is a
   dedicated **bare** Git repository: files are viewed through SimShelf, not a
   working-tree checkout. Existing arbitrary/source repositories are refused.
   You can reconnect an existing SimShelf archive without initializing it.
2. In **Manage Git files**, save the existing file/folder/type choices. These
   preferences alone do not authorize automatic commits. Select source files
   that are also included in SimShelf's source snapshot. Other selected outputs
   need **Keep a copy** capture coverage.
3. Expand **Automatic archival settings**. Optionally enter **Future outputs**, one filename or pattern per line. These
   are relative to the configured **capture directory**, not the source root.
   `result.csv` matches that directory's file; `logs/*.csv` matches CSV filenames
   immediately inside its `logs` subdirectory. No recursive `**`, directory
   wildcard, traversal or absolute path is accepted. Edit/remove lines to revise.
4. Switch **Automatic archival** on beside the simulation status (or choose
   **Review archival settings**). Inspect the selection and copy overrides, then
   choose **Confirm archival settings**. The switch stays off until confirmation. Future-output matches
   request Keep a copy ahead of ordinary capture policy for new opted-in runs;
   configured capture size limits still apply. Global saved capture rules are
   not rewritten. Each run freezes its consent and effective copy overrides.

**For VB_Phi_Field-style layouts:** if the capture directory is `outputs`, a CSV
written beside `VB_Phi_Field.py` is outside automatic coverage. Declaring
`result.csv` looks for `outputs/result.csv`, not that source-adjacent CSV. Configure
the script to write into the capture directory, or attach the outside file to the
completed run manually. SimShelf never relocates files or launches a discovery run.

Changed capture settings, source identity, inclusion preferences or repository
connection require consent review again. Disable stops opt-in for future runs;
already started runs retain their frozen consent. Disconnect prevents publication
and retrieval until explicitly reconnecting the correct archive.

## What gets archived

Selected source bytes come only from the exact run-start snapshot. Selected
outputs must be newly created or content-changed, verified managed copies for
this run. Unchanged old files, references, missing files, unsafe links, unstable
bytes and budget overruns are reported as omissions, not substituted from earlier
runs. Hash checks supplement ordinary capture's size/mtime comparison. If ordinary
capture omitted a same-size/same-timestamp rewrite, the archive reports no verified
copy rather than guessing. Empty wildcard matches are reported too.

Limits are cumulative per run, including source and all later additions:
**1,000 file entries, 25 MiB per file, 100 MiB total**. Revisions count again even
if Git internally deduplicates bytes. Existing capture limits can be lower.
Git is suited to source/configuration and modest text results such as CSV, not
multi-GB NPZ/WVZ data. History retains old objects and can grow indefinitely.
Normal capture copies plus Git objects consume separate storage.

Portal/CLI runs archive after normal final capture and genuine process
finalization, including failures and safely finalized interruptions. Python/editor
contexts must close their output writers before exiting the context. Detached
writers and unrelated editors are unsupported; detected changes fail closed.
Archive success/failure never changes execution status, metrics, parameters,
scientific version, source snapshot, logs or the child exit code.

## Add files after execution

Open **Run → Files → Add files after execution**. Attach a screenshot or analysis
file using the existing managed attachment mechanism; the existing Screenshots
upload works too. No rerun is needed. In the Run files list, select managed manual attachments, choose
**Review archive additions**, then **Archive selected attachments**, or cancel.
Uploading alone does not create a Git commit. References and automatic captured
artifacts cannot be reclassified as manual additions.

Each approved addition is a new immutable commit/event. The original commit is
never amended. Identical filenames get distinct event/entry paths; the Files tab
keeps every revision with its original filename. Runs recorded before enablement
can have attachment-only commits, without claiming an earlier initial archive.

Downloads resolve the selected event's recorded commit and path, verify SHA-256
and size, and serve inert attachments. Advancing HEAD or overwriting live CSVs
cannot change the returned historical bytes. The browser chooses the destination.
An unavailable repository/object or failed verification is an error, never a
fallback to the current file. Run lists show commit counts; Git history lists only
this simulation's archive associations (latest 200 runs).

## Failure, recovery and retention

A pending approved operation retains its operation ID and original managed-byte
references. **Retry approved archive** verifies any already published commit before
associating it, avoiding duplicate commits after a crash between Git publication
and database association. Retries never recapture live files. Unpublished Git
objects can remain after failure; no automatic destructive cleanup occurs.

If the recorder died before a durable candidate manifest was prepared, initial
archival is incomplete. SimShelf does not scan possibly reused output directories
on recovery. Attach verified files manually. Missing managed candidate bytes
prevent a new publication; an already published verified commit can still recover.
Initialization failures may leave a partial dedicated directory: inspect it rather
than overwriting it. Git commands have 15-second bounds; publication has a checked
two-minute budget. A busy archive returns a retryable error.

Library backups preserve archive associations and ordinary retained copies, but
**do not contain the external Git archive**. Back up that directory separately.
Restored/moved libraries require explicit reconnection and renewed automatic
consent. Historical associations and IDs remain unchanged. No schema migration
is involved; additive versioned metadata is separate from execution records.
Older builds ignore archival metadata and will not perform archival work.

Removing a run or attachment does **not** purge Git history. Run removal hides
its archive inventory from normal run APIs, while the external repository retains
its bytes. Secure erasure, pruning, remote synchronization and destructive archive
maintenance require separate workflows and authorization. Do not concurrently
edit the dedicated repository with external tools. Advisory locks serialize
SimShelf writers, not arbitrary same-user filesystem modifications. Conditional
ref updates detect conflicting Git publications; no general filesystem
transaction or protection against a hostile local account is promised.


## Understand the connection and Run files states

The master archive is independent of **Source Git history**. Its green connected
indicator means its local binding and repository checks passed, not that every
historical object was read. Source Git status appears directly under its own
heading. Source Git can stay disconnected while the master archive works.
**Automatic archival** is separate per-simulation consent: Enabled, Disabled, or
Review required / unavailable. Refresh status after changing paths or preferences.
Changing the set of files matching an approved folder/type rule does not itself
invalidate that consent. Viewing status never grants consent or creates commits.

**Run → Files** lists workspace attachments and archived revisions together. An
attachment that matches an archive entry by identity, hash and size has one row
with both storage labels. Different historical revisions remain separate even
when their filenames match. Use **Archived in Git** to filter, or expand
**Revision details** for the exact commit and alternate Git download.

**Download workspace copy** does not need either Git connection. **Download Git
revision** needs the original master archive and verifies the recorded commit,
path, size and hash. It never substitutes HEAD or a live source file. Errors leave
the run unchanged. Missing/disconnected Git does not hide the historical metadata.
References retain their original path; SimShelf does not serve external bytes.
Source entries with a matching workspace snapshot offer **View in Source**; this
is the existing bounded text preview, not a new source export feature.

A connection check is a point-in-time hint; download verifies the object again.
If a configured archive becomes unavailable, its path remains visible for recovery.
Choose **Refresh archive status**, or explicitly reconnect it. Archive initialization
is collapsed by default; the master connection switch remains visible.

Notes remain in the workspace and workspace backups, not in current Git archive
manifests. Image attachments can already be explicitly archived, but this does not
export their captions. Portable notes/manifests and remote publishing remain
separate future work. See the [Stage A design](MASTER_ARCHIVE_UX_DESIGN.md).


### Automatic archival toggle

One switch beside **Automatic archival — simulation name — Enabled/Disabled**
controls future runs of that simulation only. Switching off uses the existing
consent-disabling operation without an extra confirmation. Earlier commits and
consent frozen for active runs remain unchanged; other simulations are unaffected.
Disabling clears saved consent, so review/re-enter future-output rules before
reactivation. Existing file-selection preferences are retained independently.

Switching on requests a fresh preview; it does not itself enable commits. Cancel
leaves the previous state intact. Confirm only after reviewing current selection,
source/capture settings and capture-relative rules. Stale or invalid reviews are
rejected, and errors refresh the displayed state from the server. If the server
cannot confirm state, the control reports unavailable instead of claiming success.

**Automatic archival settings** is collapsed by default. It keeps future rules
and **Review archival settings** available for deliberate changes while enabled.
Closing a review or completing an operation returns keyboard focus to its trigger;
Cancel receives initial review focus. The switch exposes its checked state to
assistive technology. Status is distinct from the master archive connection.


### Master archive connection toggle

The **Master simulation archive** switch controls shared repository access, not
per-simulation consent. Its green Connected status and path describe the master
archive; the separately labeled Automatic archival switch describes future-run
consent for the selected simulation.

Switching OFF disconnects without deleting the repository, historical events,
managed copies or saved simulation consent. Existing frozen run plans are not
rewritten. New publication and Git downloads require a valid connection;
workspace-managed downloads remain independent. Existing publication/recovery
safeguards continue to govern work already in progress.

Switching ON explicitly reconnects the remembered original path and identity when
available in the current Git history panel. It never initializes a repository or
runs at startup. Missing/replaced repositories are rejected; check the original
location or deliberately use **Archive location and setup**. The backend verifies
the expected path, repository identity and library binding before reconnecting,
and rejects a conflicting connection changed elsewhere.

Disconnect removes the existing active connection record. No new persistent
reconnection preference is introduced: after reloading or leaving the panel,
ON opens setup if the prior path/identity is no longer available. Enter the known
archive path and **Confirm archive location**, or explicitly select initialization
for an existing empty dedicated directory. Changing location never moves files.

Reconnecting the exact original archive can make previously granted consent
usable again; it does not grant new consent. A different archive or changed
source/capture selections still requires the separate automatic-archival review.
