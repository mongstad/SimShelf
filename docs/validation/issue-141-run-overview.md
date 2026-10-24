# Issue #141 — Run Overview diagnostic placement

October 24, 2026. Accepted base: `a75d7abdc66b3f24e9f8c57bd2ac782d6bc031a3`
(PR #140). Proposed application version: `0.1.0.55` from `0.1.0.54`.

## Result and boundaries

Healthy Overview no longer renders the routine execution/capture/Git panel,
Capture inspection summary, duplicated capture status in Run record or long
capture diagnostics. Title status, progress, tabs, visual reference, source
provenance, run record, recorded command and measurements remain.

Files contains one capture summary with the recorded inspected folder, copied /
referenced / ignored / skipped / unchanged counts, exclusions, per-run scope,
declared output coverage and specific capture errors. Its existing archive view
now displays aggregate Git preservation status, scope counts, annotation/event
counts and repository access, alongside existing records, omissions, source
preview and exact historical downloads. Full execution errors moved to Logs.
Routine explanations were shortened; the status distinctions are documented in
[DATA.md](../DATA.md#reading-run-status).

Overview shows short, separate notices for pending/unfinished capture, partial or
incomplete capture, unknown status, reported errors, skipped or zero eligible
files, outside-capture declarations, missing/changed/other-computer files, and
pending/partial/failed/unavailable Git preservation or repository access. Loading
is labeled Checking, never success. Intentional absence of Git preservation adds
no routine warning. Failed/interrupted execution retains a brief Logs action.

Warnings use the existing recorded fields and read-only archive endpoint.
Pending capture does not assert that a worker is actively finalizing. Historical
Git verification remains distinct from current repository availability. Warning
buttons open Files and focus its detail region. Status/alert semantics and the
existing polling/unmount invalidation are retained. A failed archive refresh
clears stale preservation/connection display while retaining historical events
and library downloads; a later successful refresh restores the current status.

No backend, schema, recorder, capture, archive publication, argv, stop/remove,
source/configuration or scientific-data semantics changed. Earlier reports and
screenshots were not edited.

## Screenshots

Before captures use accepted-main frontend files recovered from Git into a
separate temporary directory. Before/after use identical synthetic run responses
and the real App; no research files or user library were inspected. Desktop
viewport: 1280 × 720; narrow: 390 × 844. Native captures may exclude scrollbars.

| View | Before | After |
| --- | --- | --- |
| Healthy desktop | [Before](../images/issue-141/before-desktop.jpg) | [After](../images/issue-141/after-desktop.jpg) |
| Healthy narrow | [Before](../images/issue-141/before-narrow.jpg) | [After](../images/issue-141/after-narrow.jpg) |

Additional views: [Files desktop](../images/issue-141/files-desktop.jpg),
[partial capture warning](../images/issue-141/partial-narrow.jpg),
[focused Files details](../images/issue-141/files-narrow.jpg),
[installed Overview](../images/issue-141/installed-overview.jpg),
[installed Files](../images/issue-141/installed-files.jpg).

## Validation

- TypeScript check and production frontend build passed; distributed JS/CSS were
  rebuilt and third-party notice bytes unchanged. Accepted-main version gate and
  diff checks passed.
- Six esbuild-bundled frontend files executed directly with Node: **50 tests
  passed** (Overview warnings/details, archive identity/downloads, capture
  presentation, progress, navigation and active-annotation request ordering).
  Tests include immutable input checks and independent execution/capture/Git
  states, including unknown historical counts and changed/missing references.
- `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 /home/Nozba/Codex/SimShelf/environments/SimShelf/bin/python -m pytest -q -p no:cacheprovider --basetemp /tmp/simshelf-141-python tests/test_application_version.py tests/test_preservation.py tests/test_api.py`:
  **30 passed, 1 skipped**, one existing Starlette TestClient deprecation warning.
  The skipped standalone decay-reference test requires an externally supplied
  pinned reference path; none was supplied. No conformance claim is made.
- Real-App DOM fixture: **11 desktop scenarios passed** (healthy, partial,
  incomplete, running, stopping, post-exit capture pending, Git pending, failed,
  interrupted, archive inspection failure and repository unavailable). Checks
  cover clean Overview, accessible Files routing/focus, counts/errors, source
  preview, Logs, annotations/records and read-only requests. Healthy polling
  transitions to pending and recovers; Files inspection failure clears stale
  status without losing library downloads, then recovers.
- Partial-capture scenario passed at verified 390-pixel width. Enter on its
  warning button opened and focused Files. All six themes passed layout checks
  at 1280 and 390 pixels without horizontal page overflow. System and Linen
  visual samples were inspected. No application console warning/error logs were
  observed in the final live-state checks.
- External wheel/sdist builds and wheel rebuild from extracted sdist passed.
  Python/static package bytes agree. Installed import/CLI, workspace/OpenAPI
  versions and static serving passed with Git/Node absent from PATH.
- Two tiny, explicitly controlled standard-library fixture processes ran in a
  new disposable installed library with exit codes 0 and 2. Both had complete
  capture; original source and historical CSV download bytes were checked.
  Installed Chromium displayed 0.1.0.55, a clean healthy Overview, Files details,
  and a separate exit-code-2 warning with Logs access. No scientific workload,
  user library, archive publication or schema migration was performed.

Reproduce browser checks with
`node scripts/test_run_overview_browser.mjs /tmp/simshelf-141-check`, serve the
result on loopback, and open `?state=healthy&test=1` (PASS/FAIL in `#results`).
Other states: `partial`, `incomplete`, `running`, `stopping`, `finalizing`,
`pending`, `failed`, `interrupted`, `unavailable`, `repository-unavailable`.
The fixture rejects non-GET application requests.

## Failures, limits and owner checks

An existing capture-copy assertion initially expected the old wording; it was
updated to assert the same non-preservation guarantee in the shorter text.
Two initial browser expectations incorrectly required a capture warning for a
failed/interrupted process with healthy capture; corrected to require the
separate execution warning. All affected checks then passed.

Linux/Python 3.14/Chromium only. Other OS/browser engines, screen readers, real
scientific/GPU workloads and an exhaustive theme/state combination were not
validated. Network-isolated startup was not separately tested; installed startup
was local after dependency installation. Unrelated exhaustive backend tests were
not repeated for this presentation change. Fixture UI checks do not establish
scientific reproducibility, runtime SWSS conformance or complete output coverage.
No release or package publication occurred.

Owner verification:

1. Open a healthy completed run: confirm status/progress, visual reference, run
   record and command remain, with neither routine diagnostic panel on Overview.
2. Open Files: inspect recorded path/counts, exclusions, errors and unknown older
   counts; inspect Git status, repository access, records/omissions, annotations,
   source preview and exact historical downloads.
3. Inspect partial/incomplete and pending runs. Activate the brief Files route
   with Enter and verify focus moves to the detail region. Completed execution
   must not be presented as capture/Git success.
4. Inspect failed/interrupted execution and follow View logs. Check stopping and
   post-exit pending capture as well as archive unavailability/recovery.
5. Repeat at narrow width and in your preferred theme. Do not alter real outputs,
   interrupt scientific work or disconnect a valuable archive solely for review;
   use disposable fixtures for lifecycle/failure scenarios.
