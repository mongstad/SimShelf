# Shared local Git archive

SimShelf can keep one dedicated local Git archive for several simulations. Each
opted-in run gets an initial commit; later, explicitly approved attachments get
additional commits belonging to that same run. Scientific version, source Git
revision, exact source snapshot and archive commit are different records.

## Set up and enable

1. Create an empty directory outside the SimShelf application, library and all
   simulation source folders. In **Git history → Shared master Git archive → Set
   up archive repository**, enter its absolute path, select initialization and
   choose **Initialize and connect archive**. No remote is contacted. This is a
   dedicated **bare** Git repository: files are viewed through SimShelf, not a
   working-tree checkout. Existing arbitrary/source repositories are refused.
   You can reconnect an existing SimShelf archive without initializing it.
2. In **Manage Git files**, save the existing file/folder/type choices. These
   preferences alone do not authorize automatic commits. Select source files
   that are also included in SimShelf's source snapshot. Other selected outputs
   need **Keep a copy** capture coverage.
3. Optionally enter **Future outputs**, one filename or pattern per line. These
   are relative to the configured **capture directory**, not the source root.
   `result.csv` matches that directory's file; `logs/*.csv` matches CSV filenames
   immediately inside its `logs` subdirectory. No recursive `**`, directory
   wildcard, traversal or absolute path is accepted. Edit/remove lines to revise.
4. Choose **Review automatic archive**, inspect the selection and copy overrides,
   then **Enable automatic archive for this simulation**. Future-output matches
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
upload works too. No rerun is needed. Select managed manual attachments, choose
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
