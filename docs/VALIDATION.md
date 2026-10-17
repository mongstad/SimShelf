# Stage 1 validation

Validated on 2026-10-14 on Linux with Python 3.14.8 and Node.js 24.19.0.
This is local development validation, not a cross-platform or scale certification.

## Automated checks

`python -m pytest -q`: **24 passed**.

The checks exercise real temporary workspaces and, where appropriate, child
Python processes. They cover:

- Explicit version changes; comment/formatting snapshots; progress/logging code
  changes within a version; strings/docstrings; safe tag parsing; deduplication.
- Editor recording, terminal wrapping, resolved parameters, one shared record
  when combining wrapper and API, failed-run outputs, logs, and exit status.
- Concurrent runs with distinct output folders; rejection of shared or nested
  capture roots; SIGTERM forwarding; dead-recorder recovery; idempotent replay.
- Copy/reference/ignore rules, changed-file collection, capture budgets, and
  rejection of paths outside the registered source folder.
- Backups containing snapshots, logs, notes, and retained files; active-run
  restoration; checksum failure without installing a partial workspace.
- API annotations/uploads, same-origin write protection, source diffs, searches,
  and inert downloads for active content.

The suite emits one dependency deprecation warning: Starlette recommends its
newer HTTP test-client integration. It does not affect the tested application
requests. The restricted execution sandbox stalled the test client's asynchronous
portal; the complete suite passed when run outside that sandbox.

`pnpm run typecheck` and `pnpm run build`: **passed**. The bundled browser UI is
included in the Python package, so using the app does not require Node.js.

`python -m build`: **passed**, producing a wheel and source distribution. A
separate temporary installation of the wheel passed API folder registration,
editor recording, version/parameter retention, and serving the packaged HTML,
JavaScript, and CSS. The source archive includes frontend source, its lockfile,
the launcher, examples, and test fixtures; generated run outputs are excluded.

## Browser checks

Checked the running local app in the Codex in-app browser, using real output from
the included scalar-wave example: three completed runs and one intentional
failure. Browser checks covered:

- Table/gallery navigation and run details.
- The launcher's empty workspace and first-use guidance.
- Editing notes and reloading to confirm persistence.
- Uploading an image after completion, editing its caption, and confirming that
  it remains in the screenshot gallery. Fixed and rechecked the upload count in
  the success message.
- Comparing two runs, with the damping parameter highlighted as a difference.
- Filtering damping numerically with scientific notation (`< 2e-2`).
- Version history showing one explicit version across four runs.
- Capture-rule preview showing copies and references for actual output files.
- No browser console errors during the checked workflows.

Both the full browser and narrow side panel were inspected at their normal
viewport sizes. The narrow panel displayed the responsive stacked layout. Other
browser engines, operating systems, and long-running/high-volume workloads have
not been validated. Demo data can be regenerated in `.demo-workspace/`; repeated
demo generation appends records.

## Source-sharing cleanup

On 2026-10-16, local test registrations, runs, snapshots, journals, logs, generated
example outputs, browser captures, distribution archives, caches, and development
environments were removed before repository creation. Application code and
reusable example scripts were preserved. No recorded simulations or runs are
shipped with the source tree; launch the app to create an empty workspace.

The historical checks above describe the original prototype validation. Local
browser captures were removed because they included machine-specific paths.

## Later portal execution validation

The original prototype checks above remain historical. See
[issue #5 portal execution](validation/issue-5-portal-execution.md) for the
subsequent local launch/stop capability, process ownership, recovery and browser
checks.

## Later argument editor validation

See [issue #11 argument editor](validation/issue-11-argument-editor.md) for paired
rows, paste tokenization, exact argv round trips, browser checks and packaged
assets. Earlier reports above retain their original review-time wording.

## Later output destination validation

See [issue #14 output destinations](validation/issue-14-output-paths.md) for
explicit mappings, mismatch acknowledgement, capture-inspection wording,
retention counts, browser checks and installed-package verification.

## Later interpreter discovery validation

See [issue #10 interpreter checks](validation/issue-10-interpreters.md) for passive
discovery, explicit version/dependency metadata checks, environment isolation,
browser/package checks, limitations and real NumPy/CuPy owner-verification steps.

## Later application version validation

See [issue #18 application versioning](validation/issue-18-application-version.md)
for the authoritative version, accepted-main increment checks, source/wheel
consistency and existing portal-label validation. Earlier evidence is unchanged.

## Later parameter discovery validation

See [issue #16 parameter discovery](validation/issue-16-parameters.md) for static
and explicit-schema discovery, opt-in argv overrides, source/installed browser
checks and scientific-default limitations. Earlier reports are preserved.

## Later explicit shutdown validation

See [issue #12 explicit shutdown](validation/issue-12-shutdown.md) for protected
Quit confirmation, lifecycle races, independent recorders, actual port release,
browser checks and installed-package verification. Earlier evidence is unchanged.

## Later deliberate run removal validation

See [issue #15 run removal](validation/issue-15-run-removal.md) for transactional
removal, retained baseline semantics, cleanup recovery/concurrency tests,
source/installed browser checks, compatibility limits and owner verification.
Earlier evidence is unchanged.


## Later screenshot deletion validation

See [issue #24 screenshot deletion](validation/issue-24-screenshot-deletion.md)
for ownership boundaries, schema-3 audit/replay behavior, focused tests and
source/installed browser checks. Earlier reports remain unchanged.

## Later optional progress validation

See [issue #17 progress](validation/issue-17-progress.md) for explicit schema-4
enablement, bounded telemetry, recovery/backup tests, source/installed browser
checks, limitations and owner verification. Earlier reports remain unchanged.

For PR #34's later parser refinement, see
[issue #17 console revision](validation/issue-17-console-revision.md): expanded
conservative formats, observational-only 100% lifecycle checks and revised
installed-browser/package evidence.

The later [compact progress panel revision](validation/issue-17-panel-revision.md)
records frontend-only rendering, theme contrast, grouped counts and installed
desktop/narrow browser validation. Earlier reports remain unchanged.

## Later optional palette validation

See [issue #35 color themes](validation/issue-35-themes.md) for Onyx, Slate and
Linen, unchanged original-theme comparisons, contrast tests, desktop/narrow
browser evidence, package checks and the existing schema-4 dialog limitation.

## Later completed-progress clarification

See [issue #40 completed progress](validation/issue-40-completed-progress.md) for
last-reported labeling, read-only investigation, lifecycle regressions and
all-theme desktop/narrow source and installed-package checks.

The owner's follow-up is recorded separately in
[issue #40 completed-bar revision](validation/issue-40-completion-bar-revision.md):
full successful-completion bars, unchanged historical telemetry, accessible
semantics, focused regressions and packaged browser checks.

The subsequent [completion-label review](validation/issue-40-completion-labels-review.md)
records owner-requested 100% and total/total presentation, preserved stored reports,
all-theme installed browser checks and focused lifecycle validation.

## Optional local Git foundation

See [issue #9 local Git](validation/issue-9-local-git.md) for the owner-approved
staged scope, nullable provenance contract, Git safety/recording/restore tests,
portal connection/history checks, package evidence and deferred remote operations.

The [issue #9 discovery revision](validation/issue-9-discovery-revision.md) records
automatic read-only repository detection, explicit mapping consent, fallback and
installed-browser checks. Original foundation evidence is preserved.

## Include-first Git file selection

See [issue #44 Git file selection](validation/issue-44-git-file-selection.md) for
explicit preferences, separately approved ignore additions, safety tests, package
and installed-browser evidence, limitations and owner checks. Earlier reports
remain unchanged.

The [direct-save revision](validation/issue-44-direct-save-revision.md) records
simplified selection saving, preserved server validation, optional grouped-match
inspection and focused installed-browser/package checks.

## Shared per-run Git archive

See [issue #47 shared archive](validation/issue-47-shared-archive.md) for explicit
consent, capture-relative future rules, immutable post-run additions, historical
downloads, failure/recovery checks and installed-browser/package evidence.

## Unified master archive presentation

See [issue #56 Stage A](validation/issue-56-master-archive-ux.md) for independent
connection/consent states, coherent file revisions, focused regressions and
all-theme installed-browser/package evidence. Earlier reports remain unchanged.

The [automatic archival toggle revision](validation/issue-56-archival-toggle-revision.md)
records the single-control workflow, explicit consent, state/focus handling,
running-plan isolation and focused installed-browser/package checks.

The [master connection toggle revision](validation/issue-56-master-toggle-revision.md)
records explicit identity-checked reconnection, collapsed setup, independent
consent, failure/restart checks and all-theme desktop/narrow validation.

The [location lock and remembered directory revision](validation/issue-56-location-lock-revision.md)
records backend replacement rejection, atomic connection preferences, restart
persistence, unchanged schema and focused browser/download regressions.
