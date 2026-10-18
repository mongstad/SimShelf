# Issue #60: reconnect a moved source folder

Review candidate 0.1.0.22, 2026-10-18, from accepted main
`52a0af6fc82593ac181dfe71c272c40b583d20df` (0.1.0.21).
Issue #60 was the top and only Ready item. Its existing dedicated branch was clean
and matched main. PR #73 was merged; its branch cleanup was already complete.
The #39/#58 documentation predecessor is merged (`66678f9`). No historical
reports, scientific scripts or SWSS documents were edited.

## Implementation and decisions

The simulation page shows its current path and Locate source folder… when missing,
or Change source location when available. An accessible native dialog accepts an
absolute path, previews old/new locations and requires explicit confirmation.
There is no arbitrary local-folder browser. Cancel/invalid previews do not write.
The UI discloses retained historical paths, potentially missing references and
required re-review of Git consent and launch settings. Location-bound Git and
capture views remount after a root change so old previews cannot remain displayed.

New protected POSTs validate source/entry/version paths using no-follow metadata
checks, reject parent traversal and overlapping workspace/other registration/
configured master archive paths, and refuse this simulation's active runs. A
review digest binds the full registration, destination identity and relevant Git
preferences. Confirmation rechecks under the managed-data lock and a single
SQLite transaction. It changes the root and an additive location revision, drops
only this simulation's Source Git mapping, file preferences and automatic archive
settings, and leaves the master connection and historical archive events alone.
No schema migration, directory move, source write or environment installation.

Capture rules and execution preferences are retained. Invalid interpreter/cwd/
output settings produce preview advice and remain subject to ordinary launch
validation; preview does not execute Python. Recorder entry checks the source
binding under the same managed lock. Portal validation passes its binding through
the supervisor to recorder entry; stale plans, including move-away-and-back, fail
before recording or executing a child. Registration add/update share that lock.

## Automated validation

- Initial relocation + portal selection: 44 passed.
- Expanded relocation, portal, Git archive, Git selection and version selection:
  120 passed. Includes injected transaction failure/rollback, source disappearance,
  missing entry/version, symlink roots/ancestors/files/output, traversal,
  collisions/nesting, active/unrelated runs, stale preview/recorder/supervisor,
  valid fresh portal launch, settings retention and backend token/origin checks.
- Recorder, isolated-output and capture/backup boundary selection: 32 passed.
- Final relocation selection after adding master-archive overlap rejection:
  29 passed (one additional case; 153 distinct Python cases across these checks).
- These runs emitted the existing Starlette/httpx TestClient deprecation warning.
  No Python regression test failed. Tests use external disposable workspaces.
- Two frontend render regressions passed, covering accessible path entry,
  review-before-confirm flow, escaped paths, history/reference/consent disclosure.
  TypeScript and frontend build passed. Third-party notices are unchanged.
- Real history check compares run/artifact/annotation/metric/applied-event rows and
  journal/snapshot/blob/log bytes before and after relocation. Copy downloads,
  original reference paths, historical archive bytes and master connection remain
  intact. Backup/restore preserves new registration and historical snapshots/copies.
  Returning to the original source path does not restore cleared consent.

## Installed package and browser

External source-copy sdist and wheel-from-sdist plus direct wheel built; wheel
members and bytes match. A fresh external environment installed the candidate.
Python/CLI/workspace API/OpenAPI report 0.1.0.22; packaged HTML/JS/CSS/notices and
relocation module are present. Installed API startup and actual preview/confirmation
passed with outbound socket connections denied and Git/Node absent from PATH.

Installed Chromium, 1280x900 and 390x844, disposable library/source only:
- Four recorded runs with source snapshots, notes, captured CSVs, external
  references and per-run archive commits remain visible when their source is moved.
- Missing-source path/action, invalid folder, missing model.py, workspace overlap
  and another-registration collision all give visible errors. Cancel after a
  successful preview leaves the missing-source state unchanged.
- Explicit confirmation at narrow width updates the same simulation, restores the
  launch action and reports success with four unchanged historical runs. Narrow
  dialog client/scroll width both 341; long paths wrap and actions are reachable.
- Active-run relocation is visibly refused. Available-source Change source
  location remains discoverable. Focus enters the labelled path field; native
  modal keyboard containment and Cancel are retained.
- After restart, the registration remains at the new path. With Git available,
  the master archive is Connected and automatic archival is Disabled. The first
  no-Git browser pass correctly reported the configured archive unavailable.
- SQL comparison after browser confirmation matched all pre-check historical rows,
  master connection and archive-event values. Managed copies remained readable;
  reference-only artifacts still pointed to old-source and were missing.
- Final reloaded browser warning/error log was empty. System theme checked.
  Temporary viewport overrides were reset after responsive checks.

One repeated package smoke attempt reused its already relocated fixture and
created a second registration at the old path; its assertion failed on the correct
collision refusal. Updated the harness to use a fresh disposable workspace/source
pair per invocation; the check passed. One browser locator matched both the page
and dialog alert; scoped it to the dialog and continued. These were validation
harness issues. No user data was touched or discarded to recover.
A later final reload found the fixture server stopped (exit 143 with complete
shutdown logs, no application exception). Restarted it; the browser error page
could not be controlled by the browser tool, so a fresh localhost tab was used.
The final bundle loaded successfully with the persisted registration and no
console warnings/errors. Owned fixture servers were stopped after checks.

Artifacts remain under `/tmp/simshelf-60-package/`: source/build/install logs,
packages, smoke/fixture scripts, original SQL snapshot, preview-desktop.png and
success-desktop.png. Earlier screenshots are retained as review-time evidence.

## Limits and owner verification

Linux Chromium only; physical screen-reader, other OS/browser, all-theme matrix,
network filesystems and long scientific workloads are unverified. No unrelated
full suite was run. Preview validates structure and identity, not scientific
project equivalence. External filesystem mutations are not locked by SimShelf;
do not move/replace folders during confirmation or launch. Only the configured
and remembered master archive paths are known to the boundary check. Invalid
machine-local execution preferences require correction before the next launch.

1. Restart/reload and confirm Local · 0.1.0.22. Use a backed-up disposable project
   with completed runs and copies/references; stop that simulation's active runs.
2. Move/copy its source yourself. Select the existing simulation, inspect the old
   path and choose Locate source folder… (or Change source location).
3. Try a missing folder, missing entry/version, library path or another simulation's
   path: clear refusal, original registration unchanged. With an active run, expect
   refusal. Review a valid path and Cancel; no change.
4. Review again, check old → new paths and consent/reference warnings, then confirm.
   Verify same simulation/run IDs, notes/version history, saved copies and archived
   downloads. Reference-only paths intentionally remain original and may be missing.
5. Check Source Git mapping/file selections/automatic archival require fresh review;
   master archive stays connected. Inspect launch interpreter/cwd/output settings
   and validate before running a trusted disposable script from the new location.
6. Reload/restart; check persistence, narrow layout and preferred theme/accessibility.
   Back up and restore into a separate disposable library if testing recovery.
7. Review this PR only. Merge/release remain owner actions.
