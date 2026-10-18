# Issue #67: progress units and percentage display

Review candidate 0.1.0.21, 2026-10-18, based on accepted main
`c9122e5a9a615d22bd7483f8a72d2952db532b30` (0.1.0.20).
Issue #67 was the top and only Ready item. Its existing dedicated branch matched
main and was clean. PR #72 was merged and its branch housekeeping already complete.
Progress predecessors (#17/#34 and #40/#41) are ancestors of accepted main.

## Decisions and scope

The previous component labeled every numeric pair as steps, including text
percentage reports represented as current/100. The UI now consults the existing
frozen run `progress_mode` only for stdout/stderr reports. Structured telemetry
still takes precedence. Percent reports show their precise percentage alone;
integer structured/count-adapter pairs retain grouped step labels. Fractional
pairs use neutral units, including successful-completion display counts.
Unknown/legacy text modes use units rather than guessing from a total of 100.
Unknown totals retain Progress unavailable and any stage, without invented counts.

Native progress values/math, completion projection, stages and errors remain
unchanged. Percentage text uses actual reported precision (including 0.002%);
count-derived percentage rounding remains unchanged. Accessible value text states
the unit and distinguishes successful process completion from measured reports.
The count formatter retains JavaScript numeric precision rather than imposing a
12-decimal-place display cutoff. No backend runtime, parser, cache, storage,
process lifecycle, migration, source, SWSS document or historical evidence changed.

## Validation

- Frontend progress component suite: **14 passed**. Covers 0/0.002/0.2/25.5/99.99/100
  percentages, stdout/stderr, frozen modes and structured precedence, grouped
  counts, fractional precision, legacy mode fallback, unknown totals, completion,
  failed/interrupted/cancelled/running states, escaped stages and input immutability.
- TypeScript and frontend build passed; bundled third-party license bytes unchanged.
- `tests/test_progress.py tests/test_application_version.py`: **103 passed** with
  one existing Starlette/httpx deprecation warning. Includes real process lifecycle,
  parser selection, API precedence, checkpoint/recovery and version behavior.
  Added exact `Progress: 0.2%`, `0.002%` and `Step 8 of 8000` parser regressions.
  The initial pre-addition run was 100 passed. No failing test runs.
- External source-copy sdist, wheel-from-sdist and direct wheel built successfully;
  wheel members and bytes match. Fresh external environment installed the wheel.
  Python/CLI/workspace API/OpenAPI all report 0.1.0.21. Packaged HTML/JS and notices
  are present. API startup/serving passed with outbound socket connections denied
  and PATH excluding Git/Node. No publication performed.
- Installed Chromium UI at 1280x900: failed 0.2% and interrupted 0.002% have no
  steps; active 0.2% remains Running; step report shows 8 / 8,000 steps;
  structured fractional report with percent adapter shows
  0.123456789012345 / 2 units; completed percentage shows 100% without counts;
  completed fractional shows 2.34567 / 2.34567 units; unknown total remains
  unavailable. DOM accessible value text matches these distinctions.
- Narrow 390x844: fractional counter fits (panel client/scroll width both 341),
  and 0.002% remains visible. Existing horizontally scrolling detail tabs remain.
  System theme checked; no CSS changes. Browser warning/error log empty.
- Stored run rows matched their pre-browser snapshot. All eight raw telemetry
  pairs retained their original fixture values, including completed partial
  reports. Disposable fixture server used an external workspace and source stub;
  no scientific simulation was executed for browser testing.

Artifacts retained locally under `/tmp/simshelf-67-package/`: build/install logs,
`browser-checks.json`, `percentage-desktop.png`, `fractional-narrow.png`, packages
and disposable fixtures. Temporary viewport override reset after validation.
The owned server logged complete shutdown (command exit 143). An initial socket
closure check was denied by the restricted sandbox; the permitted retry confirmed
port 8867 was released. This was a tooling restriction, not an application failure.

Limitations: Linux Chromium only; no physical screen-reader, other OS/browser,
all-theme visual matrix, long scientific workload or unrelated full-suite retest.
Browser states use synthetic records via the recording API; real child-process
and cancellation behavior is covered by the Python integration suite. Structured
integer pairs retain the existing step convention because the API has no explicit
unit; fractional pairs use units. No new unit inference or parser auto-detection.

## Owner verification

1. Restart the candidate and reload; confirm Local · 0.1.0.21.
2. With Percentage parsing selected, inspect a running or failed report
   `Progress: 0.2%`: see 0.2% without a /100 step count. Check 0.002% too.
3. With Step counts selected, inspect `Step 8 of 8000`: see 8 / 8,000 steps.
4. Inspect fractional structured progress (even with a percentage text adapter):
   precision retained and units instead of steps; unknown total stays unavailable.
5. Compare completed, failed and interrupted runs: only successful completion
   projects 100%; accessible completion text says it is not measured telemetry.
   Confirm the original report is retained, and check preferred theme/narrow layout
   and screen-reader announcements.
6. Review this PR only; merging and publication remain owner actions.
