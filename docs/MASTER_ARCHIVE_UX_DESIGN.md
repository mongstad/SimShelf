# Issue #56 — master archive presentation and portable publishing proposal

Status: Stage A approved by the owner on 2026-10-17. Implementation and validation
are tracked in this issue branch. Stage B remains an unapproved proposal; Stage C
remains deferred to #49.
Audit base: `cfd2b889cb41cb57444f58fe9fb4fa0035258ea8` (merged PR #50).
Issue #56 is the sole Ready item. Its existing dedicated branch starts at this
base, with no open PR at the time of inspection. This proposal preserves #47's
accepted implementation and historical validation evidence.

## Audit and recommendation

Keep one shared master Git archive and retain the workspace as an independent
scientific record store. Unify the interface, not the stored history.

| Component | Current purpose | Cost and backup boundary |
| --- | --- | --- |
| SQLite and journal | Execution records, measurements, annotations, archive associations and recovery intent | Workspace backup retains database state; Git is not a substitute for this record |
| Workspace blobs and snapshot manifests | Exact startup source and managed attachments/results; hash-based sharing | Shared content stored once per hash in the workspace; retained payloads included in workspace backups |
| Dedicated bare Git archive | Selected source/results and explicitly added attachments in immutable run-specific events | Separate Git objects, trees and manifests; not included in workspace backups |
| Optional source Git connection | Read-only observations of an existing source repository | No second copy made by connection; original repository is outside workspace backup |
| File selection preferences | Intent for current files/folders/extensions | Metadata only; does not itself authorize commits |

Code inspected: `git_archive.py` connection, settings, preparation, publication,
recovery and download paths; archive API routes; `store.py` artifact availability;
`GitHistory.tsx`, `GitArchive.tsx` and the Files view in `main.tsx`.

Git publication uses a private index, raw verified bytes, a parent commit and an
atomic ref transaction. Recovery verifies the manifest and every blob before
associating the event. A bare repository has objects/refs but no checked-out file
tree; it is not an ordinary folder containing the displayed run files. Keeping
it separate preserves these boundaries and avoids making baseline recording or
downloads depend on Git. Consolidation would require a different storage,
recovery and backup contract, beyond this issue.

The same bytes can exist in workspace blobs, Git and a workspace backup. Git can
share identical objects and compress them, but disk cost is not reliably twice
the file size: loose objects, tree history, manifests and later packing affect it.
No user library was measured. Report actual directory sizes only through a future
explicit bounded inspection; do not invent storage savings or delete duplicates.
The current cumulative per-run admission limits remain 1,000 entries, 25 MiB per
file and 100 MiB including additions; identical revisions still count toward them.

Current manifests record operation ID/time/kind, simulation/run IDs, file names,
categories, artifact IDs, hashes, sizes, Git paths and omissions. They do **not**
provide a complete portable run record: execution outcome, scientific version,
snapshot identity, parameters and notes are not currently exported. Post-run image
bytes can already be archived as managed attachments, but captions and notes are
not archived by that operation. Do not relabel existing manifests as complete.

## Stage A proposed implementation boundary

### Separate connection and consent states

Keep the existing Git history navigation entry; put the master archive first in
its own section. Show **Master simulation archive connected** with success text
and icon beside the validated path, or **Local archive disconnected** with
**Connect archive locally**. Show **Disconnect archive** directly when connected;
keep initialization controls collapsed and separate from ordinary connection.
Loading, stale binding, wrong identity, missing Git/path and validation errors
must be distinct from a confirmed connected state. Retain the configured path
for recovery without treating its mere presence as proof of availability.

The source section is titled **Source Git history**. Immediately beneath that
heading, above discovery/path/mapping controls, show **Source Git history — Not
connected** or **Source Git history — Connected** and its path. An unmapped
simulation or unavailable repository gets an explicit scoped explanation there.
Move source observations/history into that same section. Remove the generic
disconnected message beneath the master history. Source connection remains
optional and independent of the master archive.

Show per-simulation automatic archival separately: **Disabled**, **Enabled**, or
**Review required / unavailable**. A saved consent object alone is insufficient
to claim effective enablement if its workspace, archive, source, capture settings
or inclusion revision has changed. Add a bounded read-only status projection
using existing validation rules; it neither grants consent nor migrates metadata.
Unknown/error responses clear optimistic availability and expose a refresh action.

### One Run files inventory

Replace the competing archive/recorded-output inventories with one table using
existing filename and policy filters, expanded with explicit storage states:
**Preserved in workspace**, **Archived in Git**, **Reference only**, and existing
missing/skipped details. Both preservation badges can apply to one row.

Join an archive entry to an artifact only by this run's artifact ID plus matching
hash and size, never by filename alone. Identify archive source entries by the
run snapshot path plus verified hash/size; preserve separate event revisions and
their commit provenance. Unmatched Git entries remain visible, including an
attachment later deleted from the workspace. Different same-named files/revisions
remain separate. Do not merge records solely because their bytes happen to match.

Each row has one primary, explicitly labeled download action:

- **Download workspace copy** when that managed copy is available.
- Otherwise **Download Git revision** when the matching archive is connected;
  retain exact event/commit/path addressing and server hash verification.
- Otherwise explain missing copy, disconnected/wrong archive, or reference-only
  state. No download of a live original or silent HEAD substitution.

Optional row details expose the exact commit and an explicitly labeled Git-copy
download when both stores hold the item. This supports checking the archive
without a duplicate competing file row. Connection status is not a guarantee
that every object exists: download-time errors remain visible and never silently
switch stores. Metadata associations may say archived even when access is offline.

Manual attachment selection belongs in the same row, with a shared **Review
archive additions** action. Retain the separate explicit confirmation, operation
ID, stale-review checks and retry behavior. Uploading alone never archives. Keep
omissions and pending/errors in a compact run-archive details section. Preserve
capture summary, gallery and notes editing. Notes should state concisely that
they are currently preserved in the workspace, not exported into Git.

Always retain: **Workspace backups do not include the external Git archive.**
Future-output rules remain capture-directory-relative, with the existing
source-adjacent CSV caveat. No storage migration, Git write protocol change,
source modification, automatic attachment archival or remote operation in Stage A.

## Stage B proposed contract — separate authorization before implementation

Introduce a versioned portable event manifest for new, explicitly reviewed
exports; leave every existing commit/manifest unchanged. An old run may receive
an additive portable export without pretending its initial archive was complete.

Proposed `format: 2` envelope:

- Stable simulation/run/operation IDs, event kind, UTC export timestamp and prior
  event identity. The event's containing commit is resolved externally to avoid
  a self-referential manifest hash.
- An immutable execution section with actual start/end/status/exit code,
  scientific version and exact snapshot ID. Include explicitly reviewed
  parameters; absent legacy fields remain null/unknown, never invented.
- A selected-file list with logical name, category, Git-relative path, SHA-256,
  size and source snapshot/artifact identity. Declare omissions and references
  explicitly; external references are not downloadable archived bytes.
- A post-execution annotation section frozen at review: selected note text,
  captions, screenshot artifact references and stable annotation identities/time.
  These are later annotations, not original execution measurements. A later edit
  requires another reviewed append-only event; no amend or replacement.

Use deterministic UTF-8 JSON with sorted object keys, stable list ordering and a
documented newline convention. Freeze time and content at review, so retry uses
identical bytes. Proposal limits: 1 MiB total annotation/portable metadata per
event, 64 KiB per note/caption and 1,000 annotation entries cumulatively per run;
retain existing file limits and charge portable payload bytes against the
100 MiB cumulative run budget. Reject over-limit reviews, never truncate silently.
These new bounds need owner approval and focused tests before implementation.

The preview must display the exact included notes, screenshots, parameter values
and omission list. Exclude machine-local absolute paths, environment inventories,
command lines and logs by default; do not silently redact selected scientific
content. Warn that filenames, source, notes and selected parameters may themselves
contain sensitive research data. Preview redaction produces export-only content,
never edits to the scientific record. Validate review freshness under the existing
managed-data lock; reuse durable pending intent, operation refs, CAS and exact
verification for publication/recovery.

Ordinary Git retrieval can enumerate manifests with `git --git-dir=/path/to/archive
ls-tree -r --name-only <commit>` and read a chosen historical payload with
`git --git-dir=/path/to/archive show <commit>:<manifest-listed-path>`. A future
documented verifier must enforce safe relative paths, bounds and SHA-256, without
executing exported source. No new import/restore tool is promised in Stage A.

Stage C stays in #49: explicit preview of destination and **all reachable history
being published**, including old revisions, notes and removed workspace items;
privacy/size warnings and separate confirmation. Never push on run completion.
Source-repository initialization in #45 remains a separate concept and workflow.

## Validation plan after Stage A approval

- Focused projection tests: direct artifact association, mismatched hash/size,
  same filename with different revisions, source entries, deleted workspace
  attachment with surviving Git history, missing managed copy, reference/skipped.
- API/backend regressions: master/source connection combinations; wrong identity,
  moved/restored binding, missing Git/repository and stale consent; historical
  downloads after HEAD advances; A/B/A simulation isolation; approved retry.
- Verify workspace download while master/source Git are disconnected; Git-only
  download blocked clearly until correct archive reconnection. Preserve independent
  recording, exit statuses, source bytes, annotations and existing manifests.
- Actual browser checks for all five palettes at desktop/narrow widths; keyboard
  selection/review/cancel, accessible labels/status announcements, filter behavior,
  reload, failure and consent states. Distinguish accessibility inspection from
  physical screen-reader testing if unavailable.
- Rebuild frontend assets/notices; run focused frontend/backend checks and the
  accepted-main version gate. Proposed implementation build is 0.1.0.15 only if
  accepted main remains 0.1.0.14. Build/install external wheel and sdist and inspect
  packaged UI; preserve all prior evidence and record exact limitations.

The owner approved Stage A only: preserve storage and existing functionality,
simplify presentation, validate all themes, and stop for PR review. No portable
manifest or notes export implementation is included.
