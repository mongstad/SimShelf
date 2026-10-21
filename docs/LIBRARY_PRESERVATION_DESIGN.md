# One library, one local preservation workflow

Implemented in application build **0.1.0.43** for issue #118. The
[Phase 1 audit](validation/issue-118-library-preservation-audit.md) remains an
unchanged historical record of the original manifest-only event, byte inspection,
selection behavior and output-allocation mismatch. The
[implementation validation](validation/issue-118-library-preservation.md) records
checks and limits of the implemented workflow.

## Storage and authority

The library retains SQLite execution records, source snapshots, managed blobs,
logs and recovery journals. One optional shared local Master Git Archive stores
reviewed, versioned evidence from all simulations. Source development repositories
remain independent, read-only provenance providers. No remote synchronization,
transport, source rewrite, schema migration or Git history rewriting is introduced.

An execution record describes what ran. Managed copies retain selected bytes.
A Git event describes exactly what was preserved under a reviewed scope. These
are complementary parts of one library; none proves complete scientific
reproducibility. Git alone is not a restorable SimShelf workspace.

## Two-level automatic participation

`preservation.status` is the effective-state authority for both UI and recording
start. Automatic Git requires global ON, a connected identity-verified repository,
individual participation and a valid reviewed policy. Every other state continues
ordinary library recording. `git_archive.automatic_status` delegates to it; both
legacy and format-2 recorders pass the same gate before freezing a run plan.
Changing switches never rewrites a frozen plan, pending approved operation or
historical event. Explicit later additions/retries retain their separate reviewed
recovery semantics; the global switch controls new automatic run preservation.

The additive metadata key `archive_v1:automatic_enabled` defaults to OFF when
absent/invalid. Explicit global ON verifies the connection; OFF changes only this
key. Format-2 participation uses the existing policy's `options.enabled`, not a
second competing flag. Disabling preserves the approved binding/selection so a
valid unchanged policy can resume without reapproval. A disabled unreviewed draft
cannot resume merely because it exists; it must pass the same enabled-policy
validation or receive explicit review.

Legacy ON uses the original active settings. OFF atomically moves the exact
consent to `archive_v1:paused_settings:<simulation>`, clearing its old active key.
Resume revalidates and restores the identical consent; it does not convert legacy
rules to recursive format-2 defaults. Explicit adoption retains legacy evidence
in the new policy. Existing relocation/removal handling includes paused current
settings, while retaining historical records. No schema migration is introduced.
Backups include these metadata preferences; moved/restored libraries still fail
workspace/identity binding checks until explicit reconnection and policy review.
Older binaries do not implement the new global gate: do not downgrade and expect
this switch to govern their recording behavior.

The global repository area lives outside simulations. Repository availability is
status information, with explicit setup/disconnect actions and no connection
switch. Each simulation has one participation switch above its tabs. Advanced
options configure scope only; first participation uses one preview/confirmation.
Backend status drives the switch, and periodic refresh cannot overwrite a pending
review or a newer action response.

## Reviewed policy

`preservation.py` stores format-2 policies in the additive `preservation_v2:`
metadata namespace. A single **Preservation settings** review includes:

- The configured capture parent, ordered copy/reference/ignore rules, copy budgets
  and source snapshot include/exclude patterns.
- Optional Git inclusion of all captured source files, or explicit relative paths.
- Recursive, exact-case output extensions. The proposed defaults are `.json`,
  `.csv` and `.log`; they become permission only after explicit confirmation.
- Explicit inclusion or exclusion of recorded stdout/stderr, independently of
  simulation-authored `.log` outputs.
- Record scope, current source/output matches, exclusions, limits and unknown
  preview coverage. Future matching files remain within the approved policy.

Review is side-effect free. Confirmation compares a fresh review and atomically
saves the capture configuration and new consent under the workspace lock.
A SHA-256 digest binds the exact server review, and confirmation reconstructs
its authoritative values. Exact record JSON is also sent as text for review;
browser numeric rounding cannot alter timestamps or large scientific integers.
Consent binds the workspace, source location/revision/device/inode, capture
configuration and exact shared archive connection. Changed bindings require a
new review. Reconnecting the same original archive can restore existing consent;
connecting a different repository does not retarget historical events.

Legacy `archive_v1:` consent continues with its original semantics until explicit
adoption. Adoption retains that consent inside the new policy and sets the legacy
active setting to null. Older builds cannot mistake the new policy for legacy
permission. Existing run plans/events, annotations, source hashes and completed
rows are not migrated or rewritten. A disabled new policy prevents legacy fallback.
Recording remains available with Git disabled, missing or disconnected.

The old file-selection and legacy archive endpoints remain compatible with
historical clients. The current UI has one combined policy editor; the former
Manage Git files/future-pattern controls no longer supply competing new consent.
Legacy enablement refuses to override an adopted policy. Direct capture-config
changes invalidate new consent rather than silently expanding it.

## Execution and capture

At start, optional preservation preparation freezes the policy, metadata inventory
and bounded output fingerprints. It does not override capture decisions. Source
payloads come from the exact run-start snapshot. Outputs qualify only if their
extension is selected, their effective capture action is copy, they changed from
the pre-run fingerprint, and a matching run-specific managed artifact exists.
Git bytes are read from verified managed copies, never substituted from live
sources or outputs. Reference and ignored bytes remain excluded.

Nested simulation-owned directories beneath a fixed capture parent work without
scientific code changes. Existing capture size/mtime attribution remains in place;
a same-size/same-time rewrite without a matching managed copy is an omission, not
a fabricated preserved result. Required log/capture errors and source warnings
remain visible. Selection does not infer outputs outside the capture root.

Execution finalization (including failed and safely interrupted runs) precedes
optional Git publication. Preservation failures never replace the genuine child
exit code, execution status, scientific version, parameters or source snapshot.

## Format-2 preservation record

Each new event's existing `manifest.json` embeds a bounded `record` object. This
is a **SimShelf-local export**, not a SWSS addition or cross-tool contract.
Simulation-authored provenance and metadata are preserved as unchanged payloads.
The record includes:

- Exact run/simulation identity, original argv token array, cwd, timestamps,
  outcome/exit code, scientific version, snapshot/structure identities, recorded
  parameters and sources, source Git observation and existing launch context.
- The complete captured source manifest with paths, hashes, sizes and modes;
  frozen policy revision and capture result/configuration.
- Selected evidence identities and a disposition ledger for unselected,
  referenced, ignored, absent, unchanged, oversized or unverifiable evidence;
  separately recorded unknown coverage and explicit scope exclusions.
- Reviewed annotation revisions and prior event identities for later additions.
  Machine-local paths are identified as such; absent values are not inferred.

Serialization uses stable UTF-8 JSON with sorted keys and bounded lists. Initial
records exclude later notes/captions until explicit review. The event wrapper
supplies operation ID, kind and creation time; committed files have isolated
simulation/run/event/index paths. Payload file modes are recorded in the source
manifest, not promised as a reconstructed working tree.

Bounds are **1 MiB per record**, **64 KiB per individual note/caption**, and
**1,000 annotation entries cumulatively per run**. Records count against the
existing **100 MiB cumulative run budget**, alongside **1,000 file entries** and
**25 MiB per file**. Repeated revisions count again. Oversized/unsupported records
fail visibly before publication; no text is silently shortened.

## Later evidence

Screenshots/manual files are first attached to the library. Saved notes, tags,
run names, version notes and captions remain separate annotation history.
**Review archive additions** selects manual managed attachments and/or all saved
run-note revisions. The preview shows exact metadata, hashes and annotation
contents. Confirmation freezes one append-only operation. Repeated confirmation
of the same operation is idempotent; a changed review needs a new operation.

Selected attachments include current saved metadata plus recorded caption
history. The current metadata observation is explicitly labeled; the original
attachment timestamp is not misrepresented as the time of a later caption edit.
Previously preserved attachments can be selected again for later caption events.
An annotation-only event is valid, but does not claim scientific file payloads or
retroactively create an initial preservation event.

## Truthful historical views and retrieval

The common run summary separately displays execution, workspace capture, and
initial Git preservation: verified for reviewed scope, partial, pending, failed,
unavailable or not enabled. It includes source/output counts and current archive
access independently. Later event counts never upgrade missing initial evidence.
Legacy manifests have unknown run-record scope and are displayed as partial;
a manifest-only legacy event explicitly has no scientific payloads. No old
manifest or commit is rewritten to add this display interpretation.

Files joins artifacts by exact identity/hash/size and source entries by exact
snapshot path/hash/size. Identical evidence repeated in later events has one row
with multiple exact revisions; different bytes or identities stay separate.
Source, Screenshots and Notes link back to Files for preservation review.

Source and artifact retrieval verifies retained size and SHA-256; artifacts are
frozen into a temporary stream so range/inline responses survive concurrent
removal without unbounded memory. Source previews/diffs verify their retained
bytes too. Git retrieval uses the recorded commit/path, verifies hash/size, and
requires the original archive identity. Record downloads compare the exact
committed manifest with its retained association. Live files and HEAD are never
fallback evidence. A failed library verification is visible; a separately listed
verified Git revision can be chosen explicitly.

## Publication, recovery and backup

The existing workspace-lock → archive-lock order, isolated Git index, raw-object
writes, conditional ref transaction and per-operation ref remain authoritative.
Durable pending intent precedes publication. Post-publication/pre-association
failures retry against the same commit, verify its manifest and all bytes, and
associate it atomically. Conflicting legacy/new pending operations fail closed.
Without durable pending intent, restart reports incomplete preservation and never
recaptures live outputs as if they were historical evidence.

Approved pending attachment blobs remain protected through existing screenshot
cleanup and are included in backups, even after their gallery association is
removed. This conservative retention can leave an unreferenced blob after later
publication; no new destructive garbage-collection workflow is introduced.
Run/simulation removal retains its existing explicit authorization boundaries.

Backups include new metadata, retained snapshots/blobs, logs and pending bytes;
the external bare Git repository must be preserved separately. Restore verifies
the backup and requires explicit archive reconnection and renewed automatic
policy review. A Git archive alone cannot reconstruct annotations not exported,
references, journals, an environment or a complete workspace.

Advisory locks do not control arbitrary same-user writers. No filesystem-wide
transaction, malicious-local-account defense, remote publication or unlimited
history performance is claimed. A checked publication budget and existing
inventory/count/byte limits bound operations; failures remain inspectable.

## Output allocation remains a separate contract

The working **fixed parent** policy inspects simulation-owned unique directories
recursively. The existing `per_run` option preallocates a child and inspects only
that child; it requires explicit support for the existing launcher-coordinated
path. An independently executable simulation that chooses a sibling directory
still leaves the preallocated child unused. Recursive selection cannot correct
that mismatch and does not claim to do so.

The UI distinguishes these choices. No argv rewrite, SWSS change, portable output
protocol or simulation-specific adapter is added. A narrowly scoped future
SimShelf issue could require explicit confirmation of coordination support when
selecting `per_run`, with review of the actual capture target. A portable
acknowledgement protocol, if desired, needs separately approved standards work.
