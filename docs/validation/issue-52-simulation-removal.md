# Issue #52 — remove a registered simulation

Review-time evidence for proposed build **0.1.0.27**, based on accepted main
`e1a5730b538aa3ecf2a7e0a35ab9427d29f3191b` (merged PR #79). Issue #52 was the only
Ready SimShelf Project item. Its existing dedicated branch was clean and at that
accepted base before implementation. The owner explicitly required schema-1
refusal with **no migration**, including zero-run simulations.

## Implementation and boundaries

- Page-level review dialog, exact manual name, stable ID, dependent-record counts,
  Cancel default, Enter safety, dismissal focus return and double-submit guard.
- Token/origin-protected strict API validates current name, review revision and
  active/finalizing state under the workspace lock. All selected records are
  removed in one transaction; existing run deletion logic queues safe cleanup.
- Remove registration, runs, annotations, metrics/progress, capture selection,
  source-Git mapping and per-run archive associations. Retain minimal deletion
  audits; reject late start events and archive metadata resurrection. Re-registering
  a removed source receives a new ID.
- Shared managed files remain referenced; cleanup failures are reported and retried.
  Original sources, external outputs, source Git and shared archive bytes remain.
  There is no archive purge, history rewrite, secure erase or schema upgrade.
- UI clears selection/detail/filter context and filters late polling results.
  Bundled frontend rebuilt with third-party notices retained.

## Automated and installed checks

Linux, Python 3.14. All fixtures/artifacts/environments were outside the checkout.

```sh
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 /path/to/dev/python -m pytest \
  tests/test_simulation_removal.py tests/test_removal.py tests/test_relocation.py \
  tests/test_git_archive.py tests/test_capture_backup.py tests/test_application_version.py \
  -q -p no:cacheprovider --basetemp=/tmp/simshelf-52-tests-final
```

**117 passed**, one existing Starlette/httpx deprecation warning. The schema-4 and active-run tests
were then strengthened with a real progress row and pending capture finalization; rerunning the entire new test file
passed **21 tests** with the same warning. Covered:

- Schema 1 unchanged/refused with zero or one run; schemas 2/3/4 retained.
- Empty/wrong/case/space names, missing confirmation, stale rename/new run/note,
  token/origin rejection, strict malformed body rejection and identical retry.
- Concurrent recorder startup during source capture; active and finalizing refusal; late journals/start/archive results.
- Completed/failed records, shared snapshots/copies, retained deleted baselines,
  reference-only CSV and original NPZ/WVZ/source-Git sentinel bytes.
- An actual connected bare Git archive hashed by complete file contents before and
  after removal; unavailable archive associations; other simulation intact.
- Injected transaction rollback, cleanup permission failure and retry, simulated
  crash after commit followed by startup recovery, backup before/after restoration.
- A 1,001-run synthetic fixture removed in one transaction (not a performance claim).

TypeScript `tsc --noEmit`, frontend build, `git diff --check` and the application
version gate against freshly fetched `origin/main` passed. Main remained at the
accepted base above.

Built an sdist, wheel from sdist, and direct wheel using a disposable source copy
under `/tmp/simshelf-52-package`. Direct and sdist-built wheel member names and
bytes matched. A fresh external installed environment passed Python, CLI,
`/api/workspace`, OpenAPI, root page and bundled JS/notices checks. The smoke test
removed Git/Node from PATH and rejected outbound socket connections; API startup
worked offline. Dependencies were installed before this offline check.

## Installed browser and retained data

Used disposable loopback portals on ports 8878 and 8879, with a backed-up test
library; no owner library or simulation was used.

- Dialog visually inspected in Light, Dark, Onyx, Slate and Linen; System also
  rendered. Desktop 1280×900 and narrow Linen 390×844 checked. Narrow dialog scrolled
  vertically and had equal client/scroll widths (341 px), with no inner horizontal
  overflow.
- Empty, wrong-case and trailing-space names disabled removal. Exact name enabled
  it; Enter in the field did not submit. Cancel/Escape left records intact. After
  the focus correction, Escape returned focus to **Remove simulation…**.
- Active simulation showed refusal and disabled input/action. Schema-1 zero-run
  simulation showed refusal; direct database verification found schema 1, all four
  registrations and no simulation-deletion audit.
- Removed a two-run simulation, then a zero-run simulation. Both disappeared from
  sidebar/overview; return to All simulations showed surviving B and active run.
  Version label displayed 0.1.0.27.
- Installed Python verification compared B's full run payloads and all original
  source/output file SHA-256 hashes with pre-removal baselines: unchanged. Before
  backup restored A; after backup retained B and excluded removed registrations.

Local screenshots and fixture evidence remain under `/tmp/simshelf-52-package`;
these temporary artifacts are not repository history or release assets.

## Failures, corrections and limits

The initial new-test run had two fixture failures from calling a nonexistent
annotation helper; fixtures now use the public journal event path. Browser Escape
initially lost focus to the document; the scoped trigger-focus correction passed
in the installed frontend. Preview initially omitted retained deleted-baseline
snapshots; it now includes them, with a regression test. Final checks above passed.

No Windows/macOS, physical touchscreen, screen-reader, long-running multi-process
stress, huge research library or forced OS/power-loss test was performed. Crash
recovery and overlapping recorder startup used controlled injected/threaded tests.
Browser fixtures used small completed runs; failed-run, shared-object and real
Git archive preservation were exercised by backend integration tests. Only the
Linen theme received the narrow-width visual check. No schema migration, archive
purge or production data deletion was attempted.

## Owner verification

1. Start this branch in a **disposable restored copy of an existing schema-2/3/4
   workspace**, keeping the original backup. Register/use two disposable sources
   A and B; give A multiple completed/failed runs, notes, images and file copies.
2. Select A → **Remove simulation…**. Verify name/ID/counts and source/archive
   retention language. Try empty, wrong-case and space-padded names; Cancel and
   Escape. Confirm dismissal focus and no records lost.
3. Keep a test run active; verify removal refuses. Stop it normally and wait for
   finalization. Reopen review, type A's exact name and remove. Verify All
   simulations, sidebar, search/gallery/history and B's retained records/files.
4. Check originals, external outputs, source Git and shared archive are unchanged.
   Verify a new backup/restored copy excludes A and an older backup can recover A.
5. Repeat with a zero-run registration. In a separate schema-1 test library,
   verify refusal and unchanged schema. **Do not migrate it for this check.**
6. Review keyboard/narrow/theme behavior on your normal browser before merging.

Stop for owner review; no merge, auto-merge, release or Project completion performed.
