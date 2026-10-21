# Issue #118 — Phase 1 library preservation audit

Audited 2026-10-21 on Linux, CPython 3.14.8, against SimShelf
`40fa289509f99aad80d2d4dc3ac89663bb2b91e5` / `0.1.0.42`.
This is current-behavior evidence and an [architecture proposal](../LIBRARY_PRESERVATION_DESIGN.md),
not the approved Phase 2 implementation or a preservation/scientific certification.

## Issue, branch and predecessor checks

The [SimShelf Project](https://github.com/users/mongstad/projects/2) had 65 items;
[#118](https://github.com/mongstad/SimShelf/issues/118) was first and the only
Ready issue. Its full body specifies Phase 1 owner review before Phase 2.
It had no comments, formal blockers or associated PR, and the repository had no
open PR. The existing branch was
`118-arch-unify-the-simshelf-library-and-local-master-git-archive-into-one-preservation-workflow`.
Local branch, remote branch, `main` and `origin/main` all matched the audit base;
both divergence counts were `0 0` and the initial working tree was clean.

Prior PRs [#113](https://github.com/mongstad/SimShelf/pull/113) and
[#117](https://github.com/mongstad/SimShelf/pull/117) were merged; their heads
were verified ancestors of accepted main. Their branches were already absent
locally/remotely. `git fetch --prune origin` left only main and #118, so there
was no further branch deletion or historical-evidence cleanup to perform.
Archive predecessors #47/PR #50 and #56/PR #57 were closed/merged, and merge
commits `cfd2b889cb41cb57444f58fe9fb4fa0035258ea8` and
`61f9cff2c8cae2e2ed0ebbbf58ba1c97e79f6047` are ancestors of main.
#45 is independent source-repository work; #49 remains deferred remote sync.
Neither is treated as a merged prerequisite or implemented here.

## The reported historical run: inspected, not inferred

The owner's abbreviated commit resolved to
`fd164a95221f8f299d1fdb70c9603ffaa9a11e8c`, event
`0a3a75473a1c4166b8923c9c9a0b2e05`, run
`8ca3391a10fd4fb7b11529d40b4d7522`, created
`2026-10-21T16:19:09.070755+00:00` (18:19 Oslo).

The actual manifest, its Git tree, its parent delta, recorded artifacts, managed
bytes, original output bytes and source snapshot were inspected. No application
`Store` or backup/recovery method was opened on the user's library: those paths
can initialize or reconcile data. Instead, with no WAL present, the stable database
file was copied into a disposable directory and queried with `mode=ro` and
`PRAGMA query_only=ON`. Absence of WAL and identical original database bytes were
checked before/after. Git inspection used the existing isolated, transport-disabled
Git wrapper with read-only `ls-tree`, `diff-tree`, `show` and `cat-file` operations.

The full machine-local path map and inspection report remain external to the
repository. Here `L` means the inspected library root, `S` the recorded simulation
root, and `G` the repository path from that run's archive event. No original
scientific contents, database copy or personal absolute path is published here.

| Evidence | Observed location / result |
| --- | --- |
| Execution | `L/simshelf.sqlite3`, run above: completed, exit 0, scientific version 0.1.3, exact command/cwd retained. |
| Capture | Fixed `S/outputs`; complete, 3 copied, 3,030 bytes; zero referenced/ignored/skipped/unchanged and no capture errors. |
| Original outputs | `S/outputs/run_20261021T161908Z_677a6122c8c64eafbdb984f848c828e8/`; three files listed below. |
| Managed bytes | `L/blobs/<first-two-hash-characters>/<full-sha256>`; all three hashes, sizes and original-byte equality verified. |
| Source | `L/snapshots/365146e7da3ab6c56d3b8593f7ee9b1340eb5bf725da6175528d9394392970e1.json`, with verified `simulate.py` and `swss.toml` blobs. |
| Git event | `G`, exact commit above; target event contains only `simulations/simulatetwo/runs/8ca3391a10fd4fb7b11529d40b4d7522/0a3a75473a1c4166b8923c9c9a0b2e05/manifest.json`. |
| Commit scope | Parent delta: that single manifest. Entire tree: 29 files including previous events. This is an empty payload event, not an empty Git repository. |
| Manifest | `files=[]`, `skipped=[]`; no execution record, source or output payload. SHA-256 `3f8294949360fbf9b8515e22982525bb6098bb9bb483828f81e2aade66c922fc`. |
| Frozen versus current rules | Run has `archive_capture_rules=[]`. Finalized initial state is only `captured`; full initial selection plan is no longer retained there. Current settings have empty source rules and six shallow future rules; they are not proof of launch-time settings. |

| Output filename within the run directory | Bytes | Verified SHA-256 |
| --- | ---: | --- |
| `provenance.json` | 1,783 | `79d18079cbc3a81720d819fd07b43662c73183f165a2e9d8e9d61c9b48177490` |
| `run_20261021T161908Z_v0.1.3_677a6122c8c64eafbdb984f848c828e8.log` | 627 | `cd472101763712df0596557870afce81fc67e01fb88e42f77db3665b9dd97195` |
| `summary.json` | 620 | `6e78eb8a6825214a1f91ed11c8275e2437f6c9bb1896bec547f559289c7c54b6` |

The source files contain 9,166 and 2,793 bytes, respectively, matching the pinned
public reference digests below. All three outputs and both source files are
retained in the library; **none belongs to this run's Git event**. The audit did
not search for accidental identical objects elsewhere and does not call unrelated
Git objects valid archival of this run.

Across 241 inspected files (database, snapshot, relevant managed/original bytes,
and the dedicated repository's files), before/after byte hashes, inode/device,
mode, size, mtime and ctime were equal. Access times were not asserted. This is
a bounded audit of these paths, not a claim that another active application
cannot later change user data. Nothing was migrated, relabeled, restored into,
recovered, reconnected or republished in the live library/archive.

## Mechanism and reproduction matrix

Relevant current implementation:

- [Store registration](../../src/simshelf/store.py),
  [recorder launch/finalization](../../src/simshelf/recording.py),
  [source snapshot](../../src/simshelf/source.py),
  [capture](../../src/simshelf/capture.py).
- [Git selection](../../src/simshelf/git_selection.py): capture descendants are
  pruned from source inventory; preferences are independent consent inputs.
- [Archive](../../src/simshelf/git_archive.py): `future_rules`, `future_match`,
  `selected_output`, `fingerprint_outputs`, `prepare`, `finalize`, `publish`,
  `download`; [backup membership](../../src/simshelf/backup.py).
- [Run file/archive rendering](../../frontend/GitArchive.tsx): `runFileRows`
  joins by artifact identity/hash/size; event headings display “Initial run
  archive” even with zero files. No new browser observation is claimed.

The new [audit tests](../../tests/test_library_preservation_audit.py) execute
harmless standard-library fixtures in disposable roots. They inspect actual
manifests/trees and download payloads by recorded commit, verifying hash, size
and managed-byte equality. The tests characterize accepted behavior; passing
them does not mean the proposed correction exists.

| Current reviewed policy | Capture | Git event | Meaning |
| --- | --- | --- | --- |
| Empty source rules, no future rules | 3 copied | 0 payloads; no omissions; no archive error | Reproduces the reported misleading event shape. |
| Two source files, no output selection | 3 copied | 2 source, 0 result; no omissions | A source-only commit can coexist with complete managed capture. |
| Two sources plus `*.csv`, `*.json`, `*.log`, `outputs/*.csv`, `outputs/*.json`, `outputs/*.log` | 3 copied | 2 source, 0 result; 6 unmatched-pattern reasons | Patterns are capture-relative and shallow, not recursive. |
| Two sources plus `.json` / `.log` / `.csv` extension preferences | 3 copied | 2 source + all 3 result payloads | Existing extension matching reaches descendants, but is a distinct policy path. |
| A/B/A with nested JSON/log/CSV and text extension preferences | 4 copied per run | 3 distinct commits, 6 payloads each | HEAD retains earlier paths; reopening the store preserves execution records, event identity and historical downloads; original files stay equal. |
| Disconnect after an archived run, then run again | 3 copied in second run | Second run has no event and a separate archive error | Managed bytes remain available; old Git download refuses until explicit identity-checked reconnection. Retry cannot invent a missing frozen plan. |
| Independent script with `per_run` | 0 copied; partial capture | No claim of output retention | Script-owned output directory is a sibling of the empty launcher root. Exact argv and exit 0 remain genuine. |

`run_*/*.json`, `**/*.json` and `outputs/**` are explicitly rejected future rules.
An output never selected for fingerprinting is absent from the candidate set and
therefore absent from the omission list. This explains how ordinary capture can
succeed while an empty manifest also publishes successfully. Exact original
selection history cannot be reconstructed beyond the retained evidence.

## Real reference and output-policy boundary

Accepted standards main was verified live as
`285ab0d6c06cc3b88e421a2c00577e72c650c750`. The
[standalone scalar-decay 0.1.3 package](https://github.com/mongstad/Simulation-Standards/tree/285ab0d6c06cc3b88e421a2c00577e72c650c750/examples/decay)
was read, hash-pinned and copied into temporary fixture directories. Tests execute
only those copies with `--rate=0.005 --steps=10 --no-series`, without changing
source, `swss.toml`, scientific parameters/algorithms or the standards checkout.

| Pinned file | SHA-256 |
| --- | --- |
| `simulate.py` | `48a0b582d8bceb007a547dfc891333ad62d766114ffd17eb8284128e04780f41` |
| `swss.toml` | `44f9bc668492b4f0957fe77a958e7f9b952da7379867c3bbdf9c16b34f9c6a98` |

Fixed parent capture: completed/exit 0, version 0.1.3, exact argv, three copied
outputs and complete capture; two source + three output files verified in Git
under reviewed source/text extension rules. `per_run`: same genuine execution,
zero copied outputs, partial capture with missing-required-log reason, two source
files in Git and no result payloads; the actual output directory is a sibling of
the empty allocated root. This is an independent capture-root coordination issue,
not a Git write failure, and is explicitly separated in the proposal.

These are two short integration runs, not numerical validation, concurrent
independent fixed-parent capture, full SWSS conformance or proof for all scripts.
The pinned-reference tests skip explicitly if the environment variable below is
absent; a different source digest fails rather than silently testing a new revision.

## Validation commands and outcomes

From the SimShelf checkout, with its existing development interpreter selected:

```bash
SIMSHELF_AUDIT_DECAY_REFERENCE=/path/to/pinned/standards/examples/decay \
  PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python -m pytest -q \
  -p no:cacheprovider --basetemp /tmp/simshelf-118-focused \
  tests/test_library_preservation_audit.py tests/test_git_archive.py \
  tests/test_git_selection.py tests/test_capture_backup.py \
  tests/test_isolated_outputs.py tests/test_application_version.py
python -B scripts/application_version.py --base-ref origin/main
git diff --check
```

- **106 passed, 1 warning, 23.66 s**, including all 10 new audit cases and both
  real reference policies; no skips or expected failures in this invocation.
  Existing tests cover concurrent simulations/overlap refusal, failed/cancelled
  execution, post-run additions, idempotent recovery, unsafe links/config,
  corrupt/missing objects, limits, source isolation and backup/restore boundaries.
  Processes/API tests ran outside the restricted execution sandbox with disposable
  data; `PYTHONPATH=src` ensured the checked-out implementation was tested.
- Existing Starlette/httpx test-client deprecation warning remains. No dependency
  was installed or upgraded and no unrelated interpreter was modified.
- Initial new-test run: **7 failed, 1 passed** because the audit helper omitted
  explicit cwd, so its child wrote outside the intended temporary source roots.
  The helper now supplies `simulation['root']`. Eight generated directories were
  matched to their temporary run logs/argv and moved intact to a disposable
  external evidence directory; no user data was deleted. Corrected initial eight
  tests passed before adding the two pinned-reference cases and running the suite.
- Direct read-only SQLite opening on the restricted live path, then an in-memory
  deserialize of its WAL-format header, each reported “unable to open database
  file.” The stable, no-WAL temporary-copy query succeeded. No live application
  initialization/recovery or database write was used as a workaround.
- The first sandboxed Project CLI call failed with “unknown owner type”; the
  authenticated read outside the network restriction succeeded. One dependency
  query used an unsupported CLI field and was corrected before confirming state.
- The implementation version command reports **expected 0.1.0.43, found
  0.1.0.42**. This is a Phase 1 documentation/test audit, like accepted #114;
  application source and version remain unchanged. The command is not claimed
  to pass. Phase 2 must propose the next build from then-current accepted main.

`git diff --check` passed. All 110 local links in the touched documents resolve;
previous ARCHITECTURE/VALIDATION content remains an exact prefix, and runtime,
frontend and repository guidance files are unchanged.
No frontend/runtime assets changed, so no bundle rebuild, wheel/sdist rebuild,
fresh-install smoke, browser/keyboard/theme run, full suite, Windows/macOS,
GPU, performance, full library restoration or scientific certification was done.
The tests exercise current backend behavior; all new UI/record/policy/recovery
semantics in the proposal remain unimplemented and unvalidated.

## Owner verification and approval boundary

1. Review the [design](../LIBRARY_PRESERVATION_DESIGN.md), especially store
   authority, new consent, recursive captured-evidence scope, exact run record,
   later notes/captions, compatibility and backup limitations. Approve/revise
   that concrete Phase 2 scope before implementation; review the separate
   output-allocation recommendation independently.
2. For the original run, inspect Files and Source without retrying or editing
   consent. Download the three retained files and compare the table's hashes.
   The private local report supplies exact original/library/archive paths.
3. With the known archive directory, use only local read commands:

   ```bash
   git --git-dir="$ARCHIVE_DIR" diff-tree --root --no-commit-id --name-only -r fd164a95221f8f299d1fdb70c9603ffaa9a11e8c
   git --git-dir="$ARCHIVE_DIR" ls-tree -r --name-only fd164a95221f8f299d1fdb70c9603ffaa9a11e8c
   git --git-dir="$ARCHIVE_DIR" show fd164a95221f8f299d1fdb70c9603ffaa9a11e8c:simulations/simulatetwo/runs/8ca3391a10fd4fb7b11529d40b4d7522/0a3a75473a1c4166b8923c9c9a0b2e05/manifest.json
   ```

   Confirm the one-file delta and empty lists, distinguishing the older entries
   in the cumulative tree. Do not amend, republish or erase this historical event.
4. Reproduce the selection matrix in a disposable library/archive, then compare
   A/B/A commits and historical downloads after reopening. Optional pinned fixture
   execution uses only temporary copies with the exact two hashes above.
5. Keep the PR as a Phase 1 draft until the agreed Phase 2 work is authorized and
   complete. The required `Closes #118` reference is for the completed issue;
   merging this audit alone would prematurely close unfinished Phase 2 work.

No runtime correction, source/standards edit, migration, remote Git operation,
release, merge, auto-merge, issue closure or Done transition is part of this audit.
