# PR #34 console progress revision

2026-10-17, issue #17, existing branch
`17-ux-show-live-simulation-progress-when-reported-by-a-run`.
This supplements [the original validation](issue-17-progress.md), whose evidence
and review-time wording remain unchanged. Proposed build stays **0.1.0.8**;
accepted main remains `2fcfc900d99b59380b4822fc242bfb7389ed2478` (0.1.0.7).

## Scope and decisions

Only text parsing, selected-mode examples, their tests, documentation and the
generated JavaScript change. Schema-4 authorization/design, persistence,
coalescing, ownership, cancellation, backup/restore and structured precedence
are unchanged. No dependency, schema or application-version increment.

The existing opt-in modes remain separate. Step mode recognizes `step N/T`,
`N / T steps`, and `Step N of T`, optionally followed by `(P%)`. Percentage mode
recognizes `P%`, `Progress: P%`, and `P% complete`. Matching is case-insensitive,
whole-line and bounded to 256 bytes, with ASCII spaces/tabs and CR/LF delimiters.
Comma groups must contain exactly three digits after the first group. A supplied
percentage must agree with counts within half the last printed decimal place
(0.5 percentage points for integers, 0.05 for one decimal); decimal arithmetic
avoids binary floating-point comparison artifacts. Counts determine the report.

All six requested candidate formats and the exact indented VB_Phi_Field example
are covered. Headers, unrelated measurement percentages, malformed grouping,
inconsistent values, unlabelled fractions, ANSI decoration, exponent notation,
locale decimal commas and arbitrary suffixes are rejected. A rejected line never
creates telemetry; existing valid telemetry remains the last report. Bare
percentages remain an explicit percentage-mode convention, not automatic detection.

Settings show static recognized examples for the selected mode, hidden for Off.
This avoids a duplicate frontend parser, new API endpoint or unrestricted regex.
Existing run details continue to identify API versus stdout/stderr sources.
See [the user guide](../PROGRESS.md) for the exact contract.

## Focused validation

```sh
PYTHONPATH=/home/Nozba/Codex/SimShelf/SimShelf/src \
  /home/Nozba/Codex/SimShelf/environments/SimShelf/bin/python -B -m pytest -q -p no:cacheprovider \
  --basetemp=/tmp/simshelf17-revision-verified \
  tests/test_progress.py tests/test_recording.py tests/test_portal.py
```

**120 passed in 21.13s**, one existing Starlette/httpx deprecation warning.
The focused set includes storage/recovery/backup progress regressions already in
`test_progress.py`; unrelated suites were not repeated for this parser revision.

- Exact VB sample tested with CR, LF and CRLF at every possible two-chunk split
  and byte-by-byte; final unterminated lines and oversized recognizable lines.
- Supported conventions, indentation, tabs, case, comma grouping, consistency
  tolerance boundaries, invalid totals and rejected scientific percentages.
- Actual CLI child exits 9 with original stdout/stderr bytes preserved; progress
  is interpreted from both streams. Joined structured API retains precedence
  over newly supported comma-count/percentage text.
- Actual portal children report 100%, then remain behind an explicit file gate.
  API still reports Running, no exit code, and Stop available. Releasing the gate
  produces genuine success or exit-7 failure; explicit Stop produces Interrupted
  and SIGTERM exit status. All retain 100% without fabricating success. Original
  output files, capture artifacts and logs are checked; metrics remain empty.
  Late progress writes cannot change finalized execution rows.
- Existing editor structured progress, metrics/parameters and recorder/portal
  integration regressions pass. This revision does not add text parsing to direct
  editor console contexts; editor/API instrumentation and wrapper capture retain
  their established boundaries.

TypeScript `tsc --noEmit`, `node frontend/build.mjs` and **4 frontend tests** passed,
using the runtime's absolute Node path. Tests were bundled with esbuild for Node,
keeping `node:test` and `node:assert/strict` external. They cover unknown/known/error
rendering, source/status, rounding and selected-mode examples. CSS, legal notices,
full third-party licenses, dependency and lock files are unchanged by this revision.

## Installed package and browser

Rebuilt wheel, sdist and wheel from extracted sdist using the external disposable
packaging script. Both wheels match 0.1.0.8 and every current static asset byte.
Reinstalled the revised wheel with `--force-reinstall --no-deps` in the disposable
environment. Python/CLI/API/OpenAPI/static checks pass with Git/Node absent from
PATH and outbound API startup connections denied after dependencies were installed.
The environment uses system-site-packages; no fully isolated dependency audit.

Installed portal, source recorder and disposable synthetic script/library under
`/tmp/simshelf17-revision-browser`, Chromium:

- Observed Running at 100%, 50000/50000, interpreted from stderr, no exit code.
  The child had emitted the exact VB lines, then waited for an explicit file gate.
- Released only the synthetic gate; the child printed `continued after 100%` and
  exited 7. Refreshed portal showed Failed, exit 7 and the same 100% last report.
- Dark desktop 1280px and Light narrow 390px checked. Selected step/percentage
  examples change correctly; Off hides them. Narrow examples wrap within the
  existing scrollable dialog. No console warnings/errors in the final browser log.
- Theme and viewport restored, own tab closed. At cleanup the disposable UI
  server had already ended with SIGTERM (exit 143; cause not established), so the
  targeted stop found no process. All browser checks above completed before this.
  No real VB_Phi_Field simulation or user workspace was executed/changed.

Local temporary screenshots:
`/tmp/simshelf17-revision-running100.png`,
`/tmp/simshelf17-revision-failed100.png`,
`/tmp/simshelf17-revision-examples-light.png`.

## Failures and remaining limits

First focused run: 116 passed, 4 failed. Three new capture assertions mistakenly
used `relative_path` instead of the existing artifact `name`; corrected tests.
One existing structured portal test imported the older environment package because
the test command used relative `PYTHONPATH=src` across child working directories.
Its log confirmed old-schema rejection; reran with absolute source PYTHONPATH.
No production-code change was needed for those failures. Final run is reported above.

No live sample-input preview or arbitrary-regex support was added. Static examples
describe supported conventions; they cannot certify the meaning of arbitrary
simulation text. No other OS/browser, screen reader, real scientific workload,
GPU execution or long-duration performance test. Prior storage/migration limitations
still apply; this revision changes neither the schema nor recovery contract.

## Owner checks

1. In a disposable enabled library, select Step counts and run a trusted script
   producing the supplied indented comma-separated VB lines. Verify 2%, 4%, 6%
   and the console source label; inspect retained raw logs.
2. Try the documented count and percentage examples in their respective modes.
   Unrelated measurement lines and inconsistent pairs should not create progress;
   without an earlier report the display remains unknown. Off must ignore all.
3. Report 100%, then continue working: status must remain Running. Subsequently
   exit nonzero or explicitly Stop and verify Failed/Interrupted, real exit code,
   last 100% and captured outputs. Verify structured reporting still takes priority.
4. Inspect settings examples in Light/Dark at narrow width. Re-fetch main and run
   the accepted-main version gate before merge. Stop for review; no release.
