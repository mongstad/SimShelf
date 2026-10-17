# Optional local Git history

SimShelf works without Git, an account or a remote. Git inspection is disconnected
by default. Exact source snapshots and scientific version tags remain independent
of Git. Existing recorded Git fields are retained as historical observations.

## Connect existing sources

1. Register each simulation using its existing source folder. Prefer a folder per
   simulation project, with all its Python/configuration files together.
2. Select a simulation and open **Git history**. SimShelf discovers its containing
   local repository from the registered source folder, including parent repositories
   and standard linked worktrees. **Repository found** shows the resolved root.
   An independent nested repository is proposed instead of its parent.
3. Review the mapping. The current simulation is selected by default; other
   registered simulations in that same repository are optional. Changing selection
   requires **Preview connection** again. Discovery never connects anything.
4. Choose **Connect locally** explicitly, or Cancel. One repository can map several
   registered simulations. To change mappings, disconnect and review again.
5. **No Git repository found** means no repository was discovered; nothing is
   initialized. Missing Git, inaccessible sources or unsafe configurations show
   an unavailable state without affecting recording. **Enter repository path
   manually** remains an optional fallback, with the same preview safeguards.
6. **Refresh history** reads the current branch, commit, changes and up to 20
   commits affecting the simulation folder. Detached HEAD and conflicts are shown.

Discovery is a read-only suggestion endpoint, separate from the provenance
contract. It never writes settings, source or Git. To bound large registration
lists, eligibility checks stop after 100 additional registrations or ten seconds
between candidates (an in-flight bounded Git inspection may finish afterward).
A partial-results notice recommends manual mapping for unchecked simulations.

Disconnect Git preserves all files, commits and recorded provenance. New runs no
longer inspect Git. Missing Git, inaccessible folders or unavailable objects do
not prevent recording. A new repository without a first commit is reported as
unavailable; create its first commit with your normal Git tools if desired.

The connected repository is not backed up by SimShelf. Backups retain run snapshots
and recorded provenance, and include the optional connection settings. A restored
or relocated library requires explicit disconnection/reconnection before Git is
inspected. Repository paths are machine-specific and revalidated every time.
No storage-schema upgrade is needed; old builds ignore the optional settings.
Older builds retain their former automatic Git metadata behavior for new runs.

## What the observations mean

- **Scientific version:** your `SIMSHELF_VERSION` declaration, never changed by Git.
- **Exact source snapshot:** immutable bytes captured for a particular run.
- **Git commit/branch:** locally observed revision and branch, possibly detached.
- **Repository / simulation changes:** raw tracked bytes, executable bits, index
  changes and non-ignored untracked paths. A change elsewhere in the repository
  does not mean this simulation's captured source changed.
- **Captured source vs Git:** compares only captured files and executable bits
  against the recorded commit. A match does not cover uncaptured files, inputs,
  dependencies or execution-time source edits, and is not reproducibility proof.

Inspection deliberately does not run clean/smudge filters, diff drivers, hooks,
credential helpers, fsmonitor or transport commands. Therefore CRLF conversions,
Git LFS pointers and custom filters can conservatively appear as raw-byte changes.
Symlinks, submodules and unreadable/oversized tracked paths make inspection
incomplete; unknown is never presented as clean. Files can change during an
inspection, so this is an observation, not a transaction locking another editor.
The exact snapshot remains authoritative for captured bytes.

Inspection is bounded: three seconds per Git subprocess, 4 MiB command output,
10,000 tracked files, 32 MiB per file and 100 MiB tracked bytes. Exceeding a limit
reports unavailable; no files are modified to recover. Linux/Git 2.56 is tested.
Git/source/worktree mutation and import/copy operations are not exposed.

## Provider-neutral interface for issue #7

`git_provenance.observe(store, simulation, snapshot=None, history=False)` returns
format 1 with these stable fields:

| Field | Meaning |
| --- | --- |
| `availability` | `disabled`, `unmapped`, `unavailable`, or `available` |
| `reason` | Optional local diagnostic, never raw Git stderr/remote credentials |
| `repository` | Nullable local `{root, identity}`; identity binds resolved root and Git directory inode |
| `subdirectory` | Nullable stable registered-folder mapping, `.` for repository root |
| `commit`, `branch` | Nullable full SHA and local branch; null branch means detached when available |
| `dirty`, `simulation_dirty` | Boolean, or null for unknown |
| `snapshot_id` | Exact supplied snapshot ID, otherwise null |
| `snapshot_relation` | `unknown`, `captured_files_match_commit`, `captured_files_differ` |
| `history` | At most 20 folder-scoped `{commit, timestamp, subject}` entries on request |

Available observations also include `comparison=raw_bytes`, change/untracked
counts, `conflicts`, and `incomplete`. Consumers must check availability before
using fields, and treat null dirty state as unknown. SHA lengths may be 40 or 64.
No hosted-provider identifiers, authentication or remote URLs enter the contract.
Runs freeze this optional observation at source capture; old run records are
never backfilled. The existing `git.commit/branch/dirty` fields stay compatible.

The portal uses token-protected connection preview/connect/disconnect endpoints
under `/api/workspace/git`, plus read-only `/api/simulations/{id}/git`. Connection
settings use an additive metadata key, transactional updates and the workspace
lock; recording never modifies settings or Git. Mapping previews are revalidated
at confirmation. Restores/moves or repository replacement invalidate the binding.

## Approved staged scope

The owner authorized the local foundation first for issue #9. Local commits and
remote fetch/pull/push require separately authorized follow-ups. Those follow-ups
must add previews, explicit consent, exclusions/privacy checks, authentication and
divergence handling before exposing any write/synchronization action. This PR
has no partial push workflow or remote-authentication UI. Linking an already
registered folder is supported; source importing/copying is deferred. Run-summary
or artifact export remains a distinct future issue. The stable local interface is
ready for #7 without depending on these later operations.
