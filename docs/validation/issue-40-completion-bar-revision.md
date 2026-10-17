# Issue #40 / PR #41: completed visual bar revision

Review revision, 2026-10-17. Proposed version remains **0.1.0.11**; accepted main
is **0.1.0.10**, commit `32c427a41ceb7b9b17ab74afd33127562804ca7a`.
The owner's follow-up supersedes the original partial-bar presentation. The
[original investigation and validation](issue-40-completed-progress.md) is retained
unchanged as historical evidence.

## Behavior and boundaries

Only `run.status === "completed"` fills the visual bar (`value=100`, `max=100`).
Below it, **Last reported progress** shows the actual reported percentage and
thousands-separated counts. The original 4,000 / 4,123 example still shows 97%.
Optional stages remain visible. Completed runs without valid telemetry have a
full bar and **Progress unavailable**, without invented reported numbers.
The redundant successful-process sentence is removed.

The completed bar's accessible name is **Successful process completion**. Its
`aria-valuetext` distinguishes process completion from the actual last report,
or explicitly says no report is available. Fractional count formatting matches
visible counts. Non-completed runs keep their actual native progress value/max.
No new CSS, backend runtime, schema, persistence, logs, scientific data, execution,
cancellation or backup changes. No user workspace was opened for this revision.

## Focused validation

- Bundled `frontend/progress.test.mjs` with esbuild and ran Node: **9 passed**.
  Covers completed partial/zero/100%, absent/invalid/stage-only reports; actual
  running/failed/cancelled/interrupted percentages including 100%; metadata
  invariance; grouped/fractional counts; accessible completion versus telemetry;
  optional stages, errors, conservative rounding and existing settings examples.
- TypeScript `tsc --noEmit`: passed. `frontend/build.mjs`: passed.
  Tracked browser JS rebuilt; CSS and both license notices unchanged.
- Dedicated Python, `PYTHONPATH=src`, pytest selection:
  `tests/test_progress.py tests/test_application_version.py -k
  'success_keeps_last_actual_periodic_report or coalescing_final_flush or
  portal_100_percent or application_version'`: **18 passed, 82 deselected**.
  Actual subprocess regressions verify running at 100%, then genuine success,
  exit-7 failure or cancellation/interruption; unchanged logs and scientific
  results; real final telemetry flush without invented reports. One existing
  Starlette/httpx deprecation warning. No failing checks in this revision.
- External source copy -> wheel and sdist -> wheel from sdist: passed. Both wheels
  have version 0.1.0.11 and byte-identical checkout static assets, including notices.
  Reinstalled wheel in `/tmp/simshelf40-package/env`. Installed Python/CLI/API/
  OpenAPI/static checks passed with Git/Node absent from PATH and API outbound
  socket connections denied. Reused disposable environment has system-site access;
  this is not a fully isolated dependency-install test.
- Fresh `git fetch --prune origin` and application version gate: passed.

## Actual browser checks

Used only the existing disposable `/tmp/simshelf40-browser/library` fixtures;
source served on local port 8842, installed wheel on 8843.

- Completed 97%: full 100/100 bar; Last reported progress 97%; 4,000 / 4,123
  steps; Integration stage. Completed actual 100% retains 4,123 / 4,123 history.
- Completed unknown: full bar and Progress unavailable; no reported numbers.
- Failed at 100%: Failed header and actual 4,123 / 4,123 bar.
- Interrupted at 97%: Interrupted header and actual 4,000 / 4,123 bar.
- Light, Dark, Onyx, Slate, Linen at 1280x900 and 390x844: full bar and historical
  row remain distinct and fit. Narrow document width 375 within 390 viewport;
  run-detail tab strip retains its existing horizontal scrolling. No CSS changes.
- Installed wheel checked at desktop Dark and narrow Light; same completed 97%
  presentation and version 0.1.0.11. Browser warning/error log empty.
- Browser accessibility tree exposes successful-completion progress indicator;
  DOM verifies actual historical `aria-valuetext`. No physical screen-reader test.

Local screenshots: `/tmp/simshelf40-revision-desktop-{light,dark,onyx,slate,linen}.png`,
`/tmp/simshelf40-revision-narrow-{light,dark,onyx,slate,linen}.png`,
`/tmp/simshelf40-revision-installed-dark.png`,
`/tmp/simshelf40-revision-installed-narrow.png`.
State evidence: `/tmp/simshelf40-revision-browser-checks.json`.
Package build log: `/tmp/simshelf40-revision-package.log`.

Limitations: Linux in-app Chromium only; no Windows/macOS, Firefox/WebKit,
physical assistive technology, forced-colors recheck, long scientific run or
full-suite rerun. Running/cancelled UI states were covered by component tests;
real process lifecycle behavior by backend integration tests. SimShelf records
portal cancellation as Interrupted. Original owner scientific script was not run.

## Owner verification

1. Open the owner's completed 4,000 / 4,123 run: bar is completely filled;
   **Last reported progress** remains **97%**, with original counts below it.
   No extra successful-process sentence appears.
2. Open completed runs with an actual 100% report and with no report: the former
   retains historical counts; the latter has a full bar without invented numbers.
3. Check Running, Failed and Interrupted runs with partial or 100% telemetry:
   bars retain actual values and headers retain genuine process status.
4. Check Light/Dark and a narrow window; with your screen reader, confirm that
   the full bar announces successful completion separately from the last report.
5. Review PR #41 only. No merge, release, new issue or next queue item was performed.
