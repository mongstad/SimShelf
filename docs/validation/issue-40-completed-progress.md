# Issue #40 — completed runs and last reported progress

2026-10-17. Top and only Ready item, on the existing dedicated branch
`40-ux-clarify-last-reported-progress-on-completed-simulation-runs`. Clean start at
accepted main `32c427a41ceb7b9b17ab74afd33127562804ca7a` (0.1.0.10). Prior PR #38
was verified merged and its branch already removed; progress predecessor PR #34
was merged. No open PR or branch conflict. Proposed version: **0.1.0.11**.

## Investigation

Read the owner-identified run through a read-only SQLite connection and its
retained logs, without opening a Store, reconciling, migrating, executing the
simulation or changing the library. It was completed with exit code 0, step
adapter enabled and no progress persistence error. Its stdout contained periodic
reports at 1,000, 2,000, 3,000 and 4,000 out of 4,123; the last line reported
97.0%. No later step report was present; stderr was empty. Stored latest telemetry
was exactly 4,000/4,123 from stdout. This evidence supports a missing final report,
not a parser or persistence defect. No owner logs or scientific data were copied
into this repository.

The recorder drains terminal streams, considers the final unterminated line, then
closes the progress writer before finalizing. Writer close flushes pending actual
telemetry. Neither parser nor lifecycle invents a 100% report. New regression
cases confirm a successful short process retains 4,000/4,123 when that is its last
report and persists 4,123/4,123 when explicitly supplied.

## Change

`frontend/RunProgress.tsx` labels known progress **Last reported progress** only
when status is completed and current is below total. It retains the actual
percentage, native progress value/max, grouped counts and optional stage, with one
muted line: **Process completed successfully.** The bar's accessible name also
identifies it as last reported. Completed-at-total, running, failed, interrupted
and unknown presentations remain unchanged. Rendering does not mutate report or
run metadata; source/time remain internal.

No CSS, parser, backend runtime, schema, recording, process, capture or backup
changes. Existing theme tokens, compact sizing and progress contrast are reused.
Updated frontend tests, two backend regression cases, current progress guidance
and design description, version, and packaged JS. Static CSS and license notices
are byte-identical to accepted main. Historical evidence is unchanged.

## Validation

- `node node_modules/typescript/bin/tsc --noEmit`: passed.
- `node frontend/build.mjs`: passed; third-party notices unchanged.
- `esbuild frontend/progress.test.mjs --bundle --platform=node --format=cjs
  --outfile=/tmp/simshelf40-progress.test.cjs`, then Node on that bundle:
  **7 passed**. Covers 97%, zero and rounded-near-total completed reports,
  structured/stdout/stderr sources, exact unchanged counts/value/max, 100%,
  active/failed/interrupted states, unknown/invalid progress, optional stages,
  errors and unchanged metadata.
- With dedicated Python and absolute checkout `PYTHONPATH`, ran
  `-B -m pytest -q -p no:cacheprovider --basetemp=/tmp/simshelf40-focused
  tests/test_progress.py tests/test_application_version.py -k
  'success_keeps_last_actual_periodic_report or coalescing_final_flush or
  portal_100_percent or application_version'`: **18 passed, 82 deselected**.
  This includes the two new final-report cases, coalescing/final flush, real
  portal processes held alive after 100% then completed/failed/cancelled, and
  all 12 version tests. Retained log bytes and exit/status behavior verified.
  One existing Starlette/httpx deprecation warning.
- Built wheel, sdist and wheel from extracted sdist under
  `/tmp/simshelf40-package`; all metadata versions 0.1.0.11. Both wheels' static
  assets match checkout bytes. Installed wheel externally; Python/CLI/API/OpenAPI
  and static-resource checks passed with Git/Node absent from PATH and outbound
  API startup connections denied after dependency installation.
- Linux/Chromium source UI: completed 97% detail inspected in Light, Dark, Onyx,
  Slate and Linen at 1280x900 and 390x844; System checked under current OS mode.
  Narrow panel is 343x139px, inside a 375px document at 390px viewport; heading,
  right-aligned percentage, grouped counts, stage and short completion line fit.
- Installed UI: completed 97% shows last reported label, actual value 4000 and
  max 4123, and completion line. Completed 100% keeps ordinary Progress; failed
  100% stays Failed; stopped 97% stays Interrupted; completed unknown stays
  Progress unavailable without a bar. Version label 0.1.0.11. Desktop/narrow
  views checked. Browser warning/error log empty. Restored System, reset viewport
  and closed the test tab. All browser writes used disposable synthetic records.

Temporary evidence: `/tmp/simshelf40-source-<theme>.png`,
`/tmp/simshelf40-narrow-<theme>.png`, `/tmp/simshelf40-installed-dark.png`, and
`/tmp/simshelf40-installed-narrow.png`. Screenshots use synthetic records, not
owner research data.

## Failures and limitations

The first disposable-wheel setup reused a no-dependencies installation command
from a previously populated environment; this fresh environment lacked FastAPI,
so its first startup check and server attempt failed. Installed the wheel's
specified dependencies and test-client dependency in that disposable environment
only, then repeated installed checks successfully. No application change was
needed. The environment uses system-site-packages, not a fully isolated dependency
audit. No failed invocation is counted as a pass.

Some immediate theme screenshots caught existing button color transitions;
progress text/bar fit was inspected separately. No CSS was changed. OS preference
switching, other browser engines/OSes, screen readers, long-running scientific
workloads and unrelated backend suites were not tested. The reported successful
process completion is not a claim that every scientific result or output was
validated. No scientific simulation was rerun to investigate the owner's record.

## Owner verification

1. Restart/reload this build and open the completed VB Phi Field run. Confirm
   Completed remains in the header and Last reported progress shows the original
   97%, 4,000 / 4,123 steps, plus Process completed successfully.
2. Compare completed-at-100%, failed-after-100%, interrupted partial and unknown
   runs. None should gain invented counts, a different status or a success line
   from telemetry alone.
3. Inspect desktop/narrow layouts and your preferred theme; check optional stage
   and any existing progress-error message remain visible.
4. Fetch accepted main and rerun `python scripts/application_version.py --base-ref
   origin/main` before merge. Owner review only; no merge or release authorized.
