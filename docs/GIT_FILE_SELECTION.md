# Review files for future Git commits

Open a simulation's **Git history → Manage Git files**. This is optional and
local. It does not connect Git, initialize a repository, stage files or commit.
It scans the registered simulation folder, not unrelated simulations in a shared
repository. No source or result file contents are read; only names, metadata and
bounded `.gitignore` text are inspected.

## Inclusion preferences

Start with no selections. Review individual files, or expand **Folders and file
types** to select a folder or extension. Python source is suggested, never checked
automatically. File sizes and warnings help you review large files, likely
credentials and possible scientific inputs/results. A JSON configuration or NPZ
checkpoint may be an essential input: SimShelf does not decide it is disposable.

Choose **Save selection** directly beneath the choices. The selected-file count
and **Unsaved changes** / **No unsaved changes** status reflect your edits. Expand
**Selected rules** and an individual rule to inspect current matches optionally.
File rules apply to one path; folder/type rules also cover future matching files.
Saving still validates the displayed inventory and exact matches on the server;
stale files or preferences require **Refresh files / discard edits** before retrying.
Refresh also restores saved choices without saving your edits. Reopen the panel
to modify and save them again. Group-selected checkboxes are disabled: remove the
group rule before making individual choices. Rules remain removable when files
no longer exist. Saving never stages or commits files.

- A file rule applies to that relative path.
- A folder rule applies to its descendants, including future matching files.
- An extension rule applies recursively within this simulation folder, using the
  exact, case-sensitive final extension (`.py`, not an unrestricted glob).
- These are suggestions for a **future reviewed commit**, never permission to
  stage new matching files automatically. No commit action is implemented here.
- **Already tracked**, **Untracked** and **Ignored by existing Git rules** describe
  Git state independently of the checkboxes. Unchecking a tracked file does not
  untrack it. A tracked file may also match an ignore rule and still remain tracked.
- Unselected files are not automatically ignored. Git selection is independent
  of SimShelf **File capture**, scientific version tags and exact run snapshots.

Preferences work without a Git repository or installed Git. Unknown Git state is
shown honestly, and ignore writes are disabled. No repository is initialized.

## Separately reviewed ignore additions

Expand **Optional Git ignore additions**. Read existing local/parent/nested rules
and select exact untracked paths you want Git to ignore. Choose **Preview ignore
additions**, inspect the target and literal additions, then **Apply ignore
additions** explicitly. Cancel changes nothing. Conflicting inclusion intent is
flagged for review; inclusion preferences are never silently changed.

Only the registered folder's `.gitignore` is appended to or created. Rules are
anchored, escaped literal paths, with existing bytes and newline style preserved.
No broad `*` allowlist, extension ignore glob, staging, commit, upload, source
rewriting or result deletion occurs. Existing ignored paths need no duplicate
rule. Tracked files and `.gitignore` files cannot be selected for this action.
Files below nested `.gitignore` rules are conservatively refused: review those
rules with your Git tools. The panel lists authored rules separately from new
proposals. Effective Git classification includes repository exclusions and local
Git configuration; global/system Git configuration is intentionally not loaded.
Arbitrary configured exclude-file contents are not exposed in this panel.

Close other editors modifying ignore rules while applying changes. Changes since
a preview normally require refresh and review. Writes use pinned, no-symlink
directory/file descriptors, exclusive creation for absent files and a nonblocking
advisory lock plus append for existing files. Existing bytes are never replaced or
truncated. These locks do not control unrelated editors: concurrent external writes
are not a filesystem transaction. If a write/fsync fails or a replacement is
detected during append, inspect `.gitignore` before retrying; an empty newly
created file or partial addition can remain. SimShelf does not attempt destructive
rollback of independently authored bytes. Read-only folders fail without changing
Git tracking or scientific records.

## Bounds and persistence

Linux is required for descriptor/lock safeguards. Inventories are limited to
1,000 directory entries, 20 directory levels and five seconds between directory
scans. `.git`, independent nested repositories, symlinks, hardlinks, special files
and unsupported filenames are excluded. Exceeding a scan bound refuses the
inventory instead of presenting a misleading partial selection. Git commands
retain the provenance layer's three-second/4-MiB limits. Files larger than 10 MiB
are flagged, not read or automatically excluded. Ignore files must be regular,
singly linked UTF-8 files at most 64 KiB each. Review lists contain at most 100
inclusion rules or 100 exact ignore additions per action.

Preferences use additive `git_selection_v1:<simulation-id>` metadata, bound to the
source inode/path, repository identity when available, and library location.
There is **no schema migration**. Backups retain preferences; a restored/moved
library or replaced source/repository requires new review rather than applying
old machine-local choices. Older builds ignore this metadata. Disconnecting Git
does not delete preferences or files. Saved scientific versions, snapshots, run
metadata and provenance are untouched. Source repositories and `.gitignore`
files are not backed up by this preference feature.

## Handoff to issue #45

`git_selection.inventory` is a metadata-only snapshot with a revision fingerprint;
`selection_preview` validates typed rules and enumerates exact current matches.
`save_selection` stores only the explicit rules and location binding. Ignore
preview/apply are separate operations. The stable format-1 `git_provenance.observe`
contract is unchanged, and recording does not import this module.

Issue #45 must refresh the inventory, review exact proposed paths and bytes,
resolve ignored/tracked/staged/conflicting state and sensitive/large-file risks,
and obtain separate initialization/staging/commit consent. A saved rule or this
metadata revision is **not** authorization or a content guarantee for a commit.
No Git initialization/commit code is supplied by #44.
