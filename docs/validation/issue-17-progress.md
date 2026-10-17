# Issue #17 — optional simulation progress

Review-time evidence, 2026-10-17. Proposed application build **0.1.0.8** from
accepted main `2fcfc900d99b59380b4822fc242bfb7389ed2478` (0.1.0.7).
Owner separately authorized the explicit schema-4 opt-in described in
[the design](../PROGRESS_DESIGN.md). No user library was migrated during testing.

## Implementation and boundaries

- Structured `run.progress(current, total, stage=...)` works for editor recordings
  and joined CLI/portal runs. Known totals display a bar; missing totals remain
  unknown. Final status stays independent of the last report, including 100%.
- Explicit `step` and `percent` adapters parse bounded, whole plain-text lines,
  including CR updates, without changing retained stdout/stderr. Default is off;
  structured reports take precedence. No argument-derived totals, regex execution
  or ETA inference.
- Only explicit confirmed enablement upgrades schemas 1–3 to 4. Active runs block
  migration. Startup does not migrate. Older builds reject opted-in libraries.
- A separate latest-state table and atomic checkpoint keep telemetry out of
  scientific events, measurements and immutable finalized execution records.
  Normal writes coalesce to at most one per second per run; final flush is exempt.
  Recovery, concurrent writers, backup/restore and run/screenshot deletion retain
  the existing scientific-data boundaries.

## Automated checks

Linux, dedicated development Python, disposable directories under `/tmp`:

```sh
PYTHONPATH="$PWD/src" /home/Nozba/Codex/SimShelf/environments/SimShelf/bin/python -B -m pytest -q -p no:cacheprovider \
  --basetemp=/tmp/simshelf17-final-verified \
  tests/test_progress.py tests/test_recording.py tests/test_capture_backup.py \
  tests/test_removal.py tests/test_screenshots.py tests/test_portal.py \
  tests/test_shutdown.py tests/test_application_version.py
```

**125 passed in 27.37s**, one existing Starlette/httpx deprecation warning.
Coverage includes explicit consent and rollback, schemas 1/2/3, invalid reports,
resets, infrequent updates, 10,000 coalesced reports, concurrent threads/processes,
checkpoint interruption/replay, delayed reports, failure/interruption, raw CR logs,
structured priority, CLI/portal joining and reconnect, capture/metrics/annotations,
active backups, corrupt restored telemetry rejection and deletion cleanup.

TypeScript `tsc --noEmit` and `node frontend/build.mjs` passed (the package scripts'
underlying commands, invoked with the runtime's absolute Node path). The three tests in
`frontend/progress.test.mjs` passed after esbuild bundling for Node: unknown values,
accessible escaped known values/status/source, invalid totals and early rounding.
No dependency or lockfile changes. Full third-party licenses are byte-identical;
generated `app.js.LEGAL.txt` only reorders the existing React/JSX notice blocks.

## Source and installed browser checks

Chromium via the local browser, own synthetic model and disposable libraries:

- Legacy-library settings: compatibility/recovery disclosure, Cancel initial
  focus, consent required, cancellation without enablement, explicit enablement,
  and no repeated migration prompt once schema 4 is active.
- Actual portal text run: observed live 43%, 53%, 58%, retained across reload,
  then completed at 100%. Raw log interpretation is identified as such.
- Actual editor runs: active unknown state without percentage; structured stage
  `Solve` and live 4%, subsequently interrupted with final 22% retained.
- Dark desktop, Light 390px, and installed Dark 320px layouts: progress remains
  readable without document horizontal overflow (305px document at 320px).
- Installed restored library: interrupted 22% report, stage/source/time and
  application 0.1.0.8 verified in Dark narrow and Light desktop. Final browser
  warning/error log was empty. Theme/viewport restored and own tab closed.

Local screenshots (temporary, not distributed package artifacts):
`/tmp/simshelf17-source-dark-live.png`,
`/tmp/simshelf17-source-unknown-live.png`,
`/tmp/simshelf17-source-structured-live.png`,
`/tmp/simshelf17-installed-dark-320.png`, and
`/tmp/simshelf17-installed-light-final.png`.

## Packaging and compatibility

Built wheel and sdist from an external disposable source copy, then a wheel from
the extracted sdist. All metadata reports 0.1.0.8; all bundled static bytes match
between both wheels. Installed the wheel into an external disposable environment
(system-site-packages enabled; this was not a fully isolated dependency audit).
Python, CLI, workspace API, OpenAPI and static routes passed with Git/Node absent
from PATH; API startup checks denied outbound socket connections after dependency
installation. Browser used the installed wheel with the same minimal PATH.

Verified backup/restore before enabling the source fixture. Backed up four runs
after enablement and restored with the installed wheel: two completed and two
interrupted, all latest progress equal. Archived accepted-main source was verified
as actual imported version 0.1.0.7: it rejects schema-4 startup and restore without
creating the restore destination. No historical backup or source/output changed.

Fresh fetch before handoff found accepted main unchanged; the application-version
gate passed against `origin/main`.

## Failures, corrections and limits

- Restricted-sandbox HTTP TestClient stalled; interrupted and reran the focused
  checks outside that restriction. Final suite passed.
- Initial test assumptions were corrected for existing Stop HTTP 202 and stale
  concurrent report suppression. A corrupt-backup fixture initially edited only
  a WAL sidecar; switched fixture to DELETE journal mode before archiving, then
  confirmed corrupt telemetry rejection. Unknown-progress frontend test caught
  an unnecessary `100%` in explanatory copy; removed it and reran successfully.
- Final review corrected the no-report persistence-error heading on finished
  runs from Running to Progress unavailable, with a frontend regression assertion.
  Typecheck, frontend tests and bundled/package assets were rebuilt afterward.
  This shell had no npm on PATH, so final frontend checks used Node directly.
- An initial old-main archive command used the wrong working directory. Its
  apparent pass was discarded; reran with explicit repository path and verified
  imported module/version before accepting compatibility evidence.
- Two disposable UI server sessions ended with SIGTERM during the validation
  period. A Light screenshot then showed Failed to fetch. Cause was not proven;
  restarted installed UI after tests and verified the successful final screenshot
  and empty browser error log. The failed image is not used as passing evidence.
- This verifies Linux/Chromium only, not other platforms, browsers or screen
  readers. Bounded synthetic workloads are not week-long performance validation.
  Writes can wait on the workspace lock/fsync; do not report per particle. Abrupt
  process death can lose the pending second. Telemetry stores latest state, not a
  full history; stdout/stderr ordering and arbitrary terminal formats are not
  inferred. External reference-only scientific outputs are still not backups.

## Owner verification

1. Use a disposable or verified-restored library. Stop all recorders, including
   older builds. Back up and restore-check before selecting Start simulation →
   Progress reporting → Enable progress reporting for this library. Verify the
   incompatibility warning and consent requirement; Cancel should change nothing.
2. Follow [the progress guide](../PROGRESS.md) with a harmless model. Report
   current/total and a stage; observe a live bar, reload, reset the stage/current,
   then fail or stop the run. Verify last progress and final status stay distinct.
3. Run without reports: expect Running and no percentage. Select the `step`
   adapter for CR-delimited `step 10/100` output; check retained logs, then confirm
   default/off ignores the same output. Do not use a production scientific run
   for the first check.
4. Inspect Dark/Light at desktop and narrow widths, keyboard access to settings,
   and source labeling. Reopen settings: schema-4 consent should not repeat.
5. Back up and restore the test library into a new destination; compare records,
   measurements, annotations, copied files and latest progress. Verify the old
   build rejects this opted-in library. Recheck the accepted-main version gate
   before merge. Review only; no release/publication is authorized by this PR.
