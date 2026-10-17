# Issue #40 / PR #41: consistent completion labels

Owner review of `9c97d33`, 2026-10-17:
https://github.com/mongstad/SimShelf/pull/41#issuecomment-6232334958

The owner requested Progress 100% and total/total counts for successful runs,
removing the Last reported progress row. This supersedes the previous presentation
only. Both earlier issue-40 evidence reports remain unchanged.

## Implementation

`RunProgress.tsx` derives display values from `status === "completed"` and the
stored finite positive total. The reviewed 5,000/5,463 report now renders a full
bar, 100%, and 5,463 / 5,463 steps. Without a valid total, completion shows 100%
without counts. A valid total is usable even when current is unknown.
The accessible name is Successful process completion; its value text identifies
counts as display values from the stored total, not a measured progress report.
Normal heading Progress, stage/error behavior, CSS and all themes are retained.
Non-completed runs use actual telemetry, or Progress unavailable when unknown.

No backend runtime, storage, parser, logs, scientific records, source, process
status, capture, history, backup or migration code changed. Component inputs are
not mutated. Only disposable fixtures were opened; no owner library/script was
used. Version remains 0.1.0.11 against accepted main 0.1.0.10 at
`32c427a41ceb7b9b17ab74afd33127562804ca7a`.

## Results

- Bundled frontend progress suite: **10 passed**. Exact reviewed example;
  completed zero/partial/full/unknown current; structured/stdout/stderr sources;
  absent/stage-only/null/zero/negative/nonfinite/string total; grouped/fractional
  counts; accessible semantics; unchanged inputs; running/failed/cancelled/
  interrupted partial/100%/unknown displays; optional stages/errors/settings.
- TypeScript and bundled frontend build: passed. CSS and license notices unchanged.
- Dedicated Python focused selection in `tests/test_progress.py` and
  `tests/test_application_version.py`: **18 passed, 82 deselected**. Selection:
  `success_keeps_last_actual_periodic_report or coalescing_final_flush or
  portal_100_percent or application_version`. Real subprocesses remain running
  at 100%, then retain genuine success/failure/cancellation and logs/results.
  One existing Starlette/httpx deprecation warning. No failing revision checks.
- External source-copy wheel/sdist and wheel-from-sdist: metadata 0.1.0.11 and all
  static bytes match. Installed Python/CLI/API/OpenAPI/static checks passed with
  Git/Node absent from PATH and API outbound socket connections denied.
- Installed wheel actual Chromium browser, local port 8844, disposable library
  `/tmp/simshelf40-labels-browser/library`: completed example displays 100% and
  5,463/5,463; completed actual-100% same; failed actual-100% remains Failed;
  interrupted partial remains 91.5% and 5,000/5,463; completed unknown shows
  100% without counts. Browser warning/error log empty.
- System (current OS preference), Light, Dark, Onyx, Slate, Linen at 1280x900 and
  390x844: completed labels/bar fit. Document widths 1265/375 respectively;
  existing run-detail tab strip scroll remains unchanged. Accessibility tree
  identifies successful process completion; DOM verifies explanatory value text.
- After browser checks, read-only API inspection still returned completed/exit 0
  and original current=5000, total=5463, structured source and report timestamp.
  Temporary browser settings restored and owned server stopped.

Local screenshots: `/tmp/simshelf40-labels-{system,light,dark,onyx,slate,linen}-{1280,390}.png`.
DOM state evidence: `/tmp/simshelf40-labels-browser-checks.json`.
Build log: `/tmp/simshelf40-labels-package.log`.

Limitations: Linux Chromium only; no physical screen-reader, other OS/browser,
forced-colors or OS preference switching, full-suite or real scientific workload
retest. Active/cancelled display states use component tests, with process safety
covered by actual backend integration tests. Portal cancellation is Interrupted.
Reused disposable package environment has system-site access; this was not a
new isolated dependency audit. Prior historical failures remain in prior reports.

## Owner checks

1. Restart/reload the revised build. Open the completed 5,000/5,463 example:
   Progress, 100%, full bar, 5,463 / 5,463 steps; no Last reported progress row.
2. Open a completed run without a total: 100% full bar without any step count.
3. Compare running/failed/interrupted partial and 100% runs: actual telemetry and
   genuine statuses remain unchanged; a report never stops a process.
4. Check preferred themes/narrow layout and screen-reader completion wording.
5. Review this existing PR only; no merge or release performed.
