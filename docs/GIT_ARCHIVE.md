# Library preservation and the shared local Git archive

**Your simulations, one library.** SimShelf keeps run records, snapshots and
managed copies locally. Its optional shared Master Git Archive preserves reviewed
versions from every simulation. Source development Git repositories remain
independent. Local commits upload nothing; remote synchronization is not supported.

## One global switch, one simulation switch

The local SimShelf library is always active. Runs, snapshots, records, logs and
eligible managed copies do not require Git.

1. Choose **Master Git Archive** in the workspace navigation. Its one **ON/OFF**
   switch controls new automatic Git preservation globally. **Repository —
   Connected/Disconnected/Unavailable** and the repository location are separate
   facts, not extra switches. ON requires a verified local repository. If needed,
   the switch opens setup: choose an existing empty directory outside sources and
   the library, explicitly initialize/connect it, and confirm activation.
2. Open a simulation. **Archive this simulation** is its only participation
   switch, above the simulation tabs. New simulations start OFF. Turning it ON
   for the first time opens a review of eligible captured sources and recursive
   `.json`, `.csv`, `.log` outputs, with existing capture rules and limits.
   Process stdout/stderr is excluded by default. **Cancel** changes nothing;
   **Confirm preservation settings** persists ON only after backend acceptance.
3. Turning participation OFF retains history and the reviewed scope. Turning it
   back ON resumes an unchanged valid policy without another review. Changed or
   unreviewed settings require explicit review; consent is never silently widened.
4. Global OFF keeps the repository connected and every simulation's participation
   preference. Individual switches remain editable: a saved ON preference shows
   an amber toggle and **Master Git Archive disabled**. Turning it OFF remains
   OFF when the master is enabled later. You can also review or resume a valid
   preference while the master is OFF; this does not create archives. Global ON
   restores only saved participants whose repository identity and policy remain
   valid. Unconfigured, unavailable and stale scopes have distinct concise status
   text. Turning OFF is still possible when Git is unavailable; turning ON requires
   the existing repository/scope validation. Local recording continues throughout.

**Preservation settings → Capture and Git options** configures what is captured
and archived: ordered copy/reference/ignore rules, source patterns/selection,
recursive extensions (exact case), process logs and limits. It has no second
activation control. Changes require the existing explicit review. Git never
overrides reference-only or ignored capture choices.

Legacy consent retains its original scope. Its participation switch pauses and
resumes that exact consent; adopting the newer scope requires explicit review.
Existing libraries without the new global preference start globally OFF, retaining
all individual consent and historical events until the owner turns global Git ON.
Settings changes affect future runs; an already frozen run plan is not rewritten.


For simulations that allocate unique directories beneath `outputs`, use that
**fixed parent**. SimShelf inspects nested files without requiring simulation
code changes. The separate launcher-coordinated option requires explicit script
support and can miss independently allocated sibling directories. See
[output allocation](RUNNING.md#unique-output-folders-for-cooperating-scripts).
Files outside the capture folder need a separately reviewed manual attachment;
selection never redirects writes or changes argv.

## What is preserved

Selected sources use exact run-start snapshot bytes. Selected results need a
new/changed output and a verified matching managed copy from this run. Unchanged
old files, reference-only data, absent/unsafe/unstable bytes and budget overruns
are excluded or omitted with reasons. Capture's same-size/same-time limitation
remains; Git does not guess when no matching run-specific copy exists.

Each new initial event also stores a versioned SimShelf-local record: run identity,
exact argv/cwd, outcome, scientific version, source manifest, parameters, capture
result, reviewed policy, evidence identities, omissions and unknown coverage.
Records can contain local paths and research values. They are not new SWSS metadata
and do not replace scientific provenance or recreate an execution environment.

Limits per run, including later revisions:

- 1,000 file entries; 25 MiB per file; 100 MiB total including record payloads.
- 1 MiB per preservation record; 64 KiB per note/caption.
- 1,000 annotation entries, including repeated reviewed revisions.

Capture limits can be lower. Oversized records fail visibly without truncation.
Git history can grow indefinitely, especially with repeated large binary results.
Keep independent backups; references are not copies.

## Read historical evidence

Every run separates **Execution**, **Workspace capture**, and **Master Git
preservation**. A completed process does not imply complete capture or Git
preservation. Verified means verified for the reviewed scope at publication.
Partial, pending, failed, unavailable and not-enabled states remain distinct.
Connection availability is separate from historical preservation.

**Run → Files** combines source snapshots, results, attachments and exact Git
revisions. Matching identity/hash/size yields one row and one primary download;
**Identity and revisions** exposes exact commits and alternate retrieval.
Different content or attachment identities stay separate. Source, Screenshots
and Notes provide specialized views of the same run and link back to Files.

Library downloads verify retained bytes without requiring Git. Git downloads
verify the original repository identity, event commit, path, size and hash.
Failed verification never substitutes a live file or HEAD. **Preservation records
and omissions** shows event payload counts, omitted/unknown evidence and preserved
annotations; **Download verified record** retrieves the exact committed manifest.
A manifest-only historical event explicitly has no scientific file payloads.
Legacy events retain their original bytes and unknown record scope.

## Add later files, notes and captions

Attach screenshots or manual files, and save notes/captions normally. These
operations alone never publish to Git. In **Files → Add evidence after execution**,
select manual managed attachments and/or **Include all saved run-note, name, tag
and version-note revisions**. Selected attachments include saved caption history.
Select a previously preserved attachment again to append a later caption revision.

Choose **Review archive additions**, inspect the exact record and hashes, then
**Preserve reviewed additions** or Cancel. Each approval creates an immutable event;
earlier scientific records and commits remain unchanged. Annotation-only events
are allowed but do not imply preservation of scientific outputs. Counts include
all selected revisions again. Runs without initial Git preservation can still
receive these explicit later events.

## Failure, recovery and retention

Git disabled/unavailable never prevents ordinary recording. Failed and safely
interrupted executions can preserve their available evidence while retaining
their genuine execution outcome. Close writers before finalizing Python contexts.

A pending approved operation retains its ID, frozen record and managed bytes.
**Retry approved preservation** verifies an existing publication or publishes the
same candidate; it never recaptures live outputs or duplicates a confirmed event.
Without a durable candidate, preservation remains incomplete. Correct archive
identity, filesystem safety, lock, free-space and publication-budget checks apply.

Global OFF does not disconnect or delete anything. The separate **Disconnect
repository** action under global setup does not delete data or change saved consent. Reconnect verifies
the remembered path/identity; a missing or replaced repository stays unavailable.
Disconnect before changing locations. New locations require a new policy review;
old events still belong to their original archive. No source Git connection is needed.

Library backups contain retained records, snapshots, copies, logs and approved
pending attachment bytes, but **not the external Git repository**. Preserve it
separately. Restored/moved libraries require explicit reconnection and renewed
policy review. Git alone is not a complete workspace restore source.

Previously authorized removal does not purge Git history. Pending evidence can
keep a managed blob after its gallery association is removed. Destructive Git
maintenance, secure erasure and remote publication remain separate workflows.
Do not concurrently edit the dedicated archive with external tools; advisory
locks cannot control arbitrary same-user writes.

See the [two-level activation validation](validation/issue-118-two-level-archive.md),
[implemented architecture](LIBRARY_PRESERVATION_DESIGN.md) and
[validation evidence](validation/issue-118-library-preservation.md).

## Availability after restart or boot

Refresh archive status rechecks the existing connection; it does not disconnect,
recreate, or remap the repository. Missing paths/files and denied permissions now
have distinct recovery instructions. Restore the mount/access and refresh first.
A changed library binding is different: it requires explicit location review.

On Linux Btrfs, a verified connection retains its existing device-based binding
using auxiliary filesystem/subvolume-ID and inode anchors. This avoids treating
an anonymous device-number change as a new library. Valid preservation settings
retain their original binding bytes; no completed records or archive commits are
rewritten. The first successful verification establishes these anchors in the
existing metadata table, without a schema migration. Missing/unverified locations
cannot establish them. Other filesystems retain the existing device/inode checks.

Start the updated version while the connection is valid, and visit Master Git
Archive and the participating simulations before rebooting. An already stale
legacy hash cannot prove which identity component changed; it is not automatically
repaired. If a library was deliberately moved/restored, disconnect only as part
of that explicit recovery, then select **Review this archive for a changed library
location** before connecting. Review simulation preservation settings afterward.
Trailing slash and non-trailing-slash paths use the same reconnect checks.
Repository replacement, changed filesystem identity, and changed source/library
locations still require review. Cloned filesystems, kernel changes to filesystem
IDs and other unverified environments may conservatively require renewed review.
