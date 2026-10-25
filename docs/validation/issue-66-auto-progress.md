# Issue #66 — Conservative automatic console progress

October 25, 2026. Accepted base: `b35f7a3edc08f07ccade0fb4c2b7e00b4451baa1`
(PR #142). Proposed application version: `0.1.0.56` from `0.1.0.55`.

## Result and boundaries

Fresh portal execution settings prefer **Auto-detect** after explicit library
progress enablement. Without enablement, fresh launches submit Off; the disabled
selector explains that interpretation stays off. Existing saved modes, including
Off and legacy settings without a mode, remain unchanged. CLI/Python/API omitted
mode defaults remain Off. CLI accepts explicit `--progress auto`. No schema change
or implicit migration, scientific source edits, historical record rewrites,
output/capture policy changes or SWSS contract changes are introduced.

Auto accepts the existing whole-line step forms and labeled percentage forms
(`Progress: 25%`, `50% complete`). Bare `25%` requires explicit Percentage mode.
Invalid totals, nonfinite/malformed/decorated/overlong lines, inconsistent count
percentages and unrelated scientific values remain ordinary log text. The first
valid report observed by either reader thread selects one format and one stream
under a shared lock, before writer coalescing. Other streams/formats are ignored
for that run. Simultaneous streams have no guaranteed observation order. A new
run selects afresh. Valid resets and changed totals on the selected stream/format
replace the latest value; no monotonicity or implicit phase is invented.

Runs freeze the chosen `progress_mode`; auto reports retain additive `text_mode`
metadata in existing latest-state/checkpoint JSON. Rendering uses this only for
auto text reports, preserving percentage precision and count units. Missing
metadata stays neutral. Structured reports, including stage-only reports, retain
priority over pending and persisted text. Coalescing, final flush, byte-for-byte
logs, independent process outcomes and existing completion display remain intact.
Older schema-4 builds can read this additive JSON but do not implement auto mode
or its unit display; use a build supporting auto when reusing those settings.

## Validation

- `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 /home/Nozba/Codex/SimShelf/environments/SimShelf/bin/python -m pytest -q -p no:cacheprovider --basetemp /tmp/simshelf-66-python-unrestricted tests/test_progress.py tests/test_application_version.py`:
  **125 passed**. An additional stage-only structured-priority regression passed
  separately with `tests/test_progress.py -k stage_only` (**1 passed**).
- The same command with `tests/test_portal.py tests/test_capture_backup.py
  tests/test_output_paths.py` and a separate temporary directory: **47 passed**.
- Installed-wheel progress suite, with `PYTHONPATH=/tmp/simshelf-66-package/installed`
  and cwd `/tmp`: **113 passed** before the extra stage-only test was added.
  These checks use disposable libraries and controlled child processes, not
  scientific workloads or user data. Python runs emitted the existing Starlette
  TestClient deprecation warning.
- Tests cover supported forms/chunk boundaries/CR/LF/final tails, false positives,
  malformed reports, both possible stream owners, interleaved formats, resets,
  saved/omitted modes, no implicit schema upgrade, immutable old run bytes,
  backup/restore, structured priority, 100%-then-success/failure/cancellation,
  I/O failure, exact logs, recovery and bounded telemetry.
- `pnpm run typecheck` and `pnpm run build`: passed. Distributed assets rebuilt;
  third-party license/notice bytes unchanged. The application version gate and
  `git diff --check` passed.
- Esbuild bundled `frontend/progress.test.mjs` to disposable CommonJS; executing
  it directly with Node: **15 passed**, including auto units/precision, lifecycle
  projection, missing detected metadata, structured priority and immutable input.
- Real React/DOM fixture: **7 scenarios passed** for fresh auto, saved
  Off/Step/Percentage/Auto/legacy-missing modes, mode-change invalidation,
  old-library ordinary launch, canceled enablement, explicit backup consent and
  validation invalidation after enablement. No process launch is allowed by the
  mock routes. Run `node scripts/test_progress_auto_browser.mjs /tmp/progress-auto-check`,
  serve that directory on loopback and open it; `#results` reports the outcomes.
- External wheel/sdist builds and wheel rebuild from extracted sdist passed.
  All **36 Python/static files** match checkout bytes across artifacts; all
  metadata versions are `0.1.0.56`. Packaging tools were installed only in a new
  disposable `/tmp` environment. Installed import/CLI, workspace/OpenAPI version,
  HTML and static serving passed with Git and Node absent from PATH.
- Installed Linux Chromium: fresh New run selected Auto-detect; two controlled
  exit-code-3 fixtures displayed **0.1%** without counts and **8 / 100 steps**,
  independently of Failed status. Raw retained logs matched original bytes.
  No installed application console warnings/errors were observed. Screenshots:
  [Auto-detect](../images/issue-66/installed-auto.png),
  [percentage](../images/issue-66/installed-percent.png),
  [counts](../images/issue-66/installed-counts.png).

## Failures and limits

The restricted Python run stalled at the first asynchronous TestClient test and
was interrupted; the focused suite completed outside the sandbox. One boundary
command named nonexistent `test_backup.py` and ran no tests; it was corrected to
`test_capture_backup.py`. The first packaging attempt lacked build tooling; a
disposable build environment resolved it. The installed smoke script initially
looked for `application_version` instead of the existing `version` response key;
correcting that script made its checks pass, without a product change.

The browser fixture initially omitted manual-argv selection and used an incorrect
checkbox selector. Those harness errors were corrected before all seven passes.
Two React `act` timing warnings were observed during fixture development; the
installed production app had none. The Node `--test` runner initially reported
only the wrapper file; direct bundle execution exposed all 15 individual tests.

Browser inspection used the current desktop Light view (1265 × 712 screenshot);
narrow layouts, other themes/engines/platforms, screen readers and week-long or
high-throughput scientific workloads were not revalidated. No release or external
archive publication was performed. Auto can remain on the first observed stream
even if the simulation later moves its real progress elsewhere; explicit modes
are available for that case. Supported text still represents an interpretation,
not proof of scientific progress, liveness, success or complete capture.

## Owner verification

1. Use a disposable library and a new plain Python simulation registration with
   no saved execution settings. Before enabling progress, check that ordinary
   launch works with interpretation off and no schema change occurs.
2. In that disposable library, explicitly enable progress through the existing
   confirmation flow. A fresh New run should select Auto-detect; saved Off,
   Step counts, Percentage and older settings should retain their choices.
3. Select a trusted existing interpreter and manual argv for the plain fixture.
   Have it print `Energy loss: 25%`, `25%`, `Progress: 0.1%`, then `Progress: 100%`,
   with a one-second delay between reports and a final pause before exit code 3.
   Only labeled reports should produce progress; 100% must not stop it or hide
   the eventual failure. Check Logs for unchanged text.
4. In a new run print `Step 8 of 100`; verify counts rather than `/ 100` fictional
   percentage steps. Change the selected mode, save and reopen it; the choice
   must persist and mode changes must invalidate prior validation.
5. Try competing stdout/stderr and interleaved formats. Verify that one observed
   stream/format owns auto telemetry; use an explicit mode if your script needs
   to report on both streams. Structured API reports must take priority.
6. Confirm historical runs, source snapshots, annotations, measurements and
   outputs remain unchanged. Review this PR before deciding whether to merge.
