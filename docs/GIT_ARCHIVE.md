# Library preservation and the shared local Git archive

**Your simulations, one library.** SimShelf keeps run records, snapshots and
managed copies locally. Its optional shared Master Git Archive preserves reviewed
versions from every simulation. Source development Git repositories remain
independent. Local commits upload nothing; remote synchronization is not supported.

## Set up and review preservation

1. Open a simulation's **Preservation settings**. Under **Shared Master Git
   Archive → Archive location and setup**, choose an existing empty directory
   outside the library and all source folders. Explicitly initialize and connect
   it, or reconnect an existing SimShelf archive. It is a dedicated bare repository,
   not a source working tree. Existing arbitrary repositories are refused.
2. Review the capture parent and ordered **Keep a copy / Reference only / Ignore**
   rules, size limits and source snapshot patterns. The first matching capture
   rule wins. Git never overrides reference/ignore choices under the new policy.
3. Choose whether to preserve reviewed evidence in Git. Choose all captured
   source files or exact relative paths, recursive output extensions such as
   `.json`, `.csv`, `.log`, and optional process stdout/stderr. Output types apply
   at any depth beneath the capture folder, with exact case.
4. Choose **Review preservation settings**. Inspect capture and Git decisions
   together, scope, exclusions, limits and current matches. **Confirm preservation
   settings** saves both atomically for future runs. Cancel changes nothing.

Legacy consent keeps its original meaning until you explicitly adopt the new
policy. The saved status distinguishes legacy consent from proposed choices.
Adoption preserves historical events and the old policy evidence; it does not
relabel or recapture old runs. Empty enabled policies are refused.

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

Disconnecting does not delete data or change saved consent. Reconnect verifies
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

See the [implemented architecture](LIBRARY_PRESERVATION_DESIGN.md) and
[validation evidence](validation/issue-118-library-preservation.md).
