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

The [review-action revision](validation/issue-56-review-actions-revision.md)
records mutually exclusive actions, locked reviewed inputs, focus restoration,
unchanged consent safeguards and focused installed-browser/package validation.

## Coordinated isolated output folders

See [issue #69 isolated outputs](validation/issue-69-isolated-outputs.md) for
opt-in allocation, environment/API coordination, original-output isolation,
source/archive preservation, focused tests, installed-package/UI checks and limits.
Earlier evidence remains unchanged.

## Generated outputs and source inventory

See [issue #61 source inventory](validation/issue-61-source-inventory.md) for
capture-subtree pruning, separate CSV/JSON archival, unchanged bounds/consent,
focused regressions, installed desktop/narrow checks and owner verification.
Earlier evidence remains unchanged.

## Output declaration drafts and capture preview

See [issue #59 output declarations](validation/issue-59-output-declarations.md)
for the placeholder reproduction, independent capture review, row-specific errors,
focused regressions, installed desktop/narrow checks and owner verification.
Earlier evidence remains unchanged.

## Percentage and fractional progress presentation

See [issue #67 progress units](validation/issue-67-progress-units.md) for precise
percentage display, grouped discrete counts, fractional units, accessibility,
focused regressions and installed desktop/narrow checks. Earlier evidence remains
unchanged.

## Reconnecting moved simulation sources

See [issue #60 source relocation](validation/issue-60-source-relocation.md) for
transactional remapping, path and active-run guards, consent invalidation,
history/backup preservation, installed browser checks and known limitations.
Earlier evidence remains unchanged.

## Adjacent run navigation

See [issue #54 run navigation](validation/issue-54-run-navigation.md) for retained
simulation-scoped browsing context, detail-state isolation, focused tests,
installed-browser checks and limitations. Earlier evidence remains unchanged.

## Secondary run timestamp year

See [issue #68 run timestamp](validation/issue-68-run-timestamp.md) for year display,
unchanged run names and stored records, local year-boundary checks, and installed
desktop/narrow validation. Earlier evidence remains unchanged.

## Stable run duration layout

See [issue #74 duration width](validation/issue-74-duration-width.md) for measured
baseline movement, stable control positions across duration transitions, installed
responsive checks and fixture limitations. Earlier evidence remains unchanged.

## Resizable and collapsible navigation

See [issue #55 sidebar](validation/issue-55-sidebar.md) for bounded pointer/keyboard
resizing, local preferences, full collapse, responsive/theme checks, installed
package evidence and limitations. Earlier evidence remains unchanged.

## Removing a registered simulation

See [issue #52 simulation removal](validation/issue-52-simulation-removal.md) for
schema-1 refusal, atomic removal/retry, retained source/archive/shared data,
backup recovery, installed browser checks and limitations.

See also the [issue #52 settings-dialog review](validation/issue-52-settings-review.md)
for the owner-requested cogwheel, keyboard focus and missing-source recovery checks.

The [title-placement follow-up](validation/issue-52-title-placement.md) records
long-title wrapping, title/icon geometry and keyboard checks for the final layout.

## Live log presentation controls

See [issue #84 log controls](validation/issue-84-log-controls.md) for persistent
wrap/follow preferences, user-scroll behavior, installed-package/browser checks,
owner-requested spacing and label placement, and validation limitations.

## Simulation settings during activity

See [issue #83 settings activity](validation/issue-83-settings-activity.md) for
authoritative activity projection, stale-refresh handling, unchanged backend
guards and installed-browser/package checks. Earlier evidence is unchanged.

## Run navigation caption cleanup

See [issue #85 navigation caption](validation/issue-85-navigation-caption.md) for
caption removal, preserved navigation behavior, installed-browser checks and
package validation. Earlier evidence remains unchanged.

## New run entry-point wording

See [issue #82 New run label](validation/issue-82-new-run-label.md) for the overview
caption, unchanged explicit launch flow, installed-browser and package checks.
Historical evidence remains unchanged.

## Settings and New run action icons

See [issue #91 action icons](validation/issue-91-action-icons.md) for decorative
icons, unchanged review workflows, wrapping and installed-package/browser checks.
Historical evidence remains unchanged.

## Context-specific overview actions

See [issue #93 context actions](validation/issue-93-context-actions.md) for
registration/launch visibility, focused assertions and installed-browser checks.
Historical evidence remains unchanged.

## New run document-plus icon

See [issue #95 document-plus](validation/issue-95-document-plus.md) for the scoped
glyph replacement, installed theme/keyboard checks and package validation.
Historical evidence remains unchanged.

## Run title favorite toggle

See [issue #96 favorite star](validation/issue-96-favorite-star.md) for accessible
title placement, save/poll ordering, installed-browser and package validation.
Historical evidence remains unchanged.

The [issue #96 review revision](validation/issue-96-favorite-review.md) records
history-table indicator placement and silent favorite-save confirmation, with
focused regressions and installed-browser checks.

## Grouped and aligned simulation arguments

See [issue #51 argument editor](validation/issue-51-argument-editor.md) for typed
groups, manual blank/empty distinctions, exact-argv regressions, safe fixture
launches and installed responsive/package checks. Earlier evidence is unchanged.

## SWSS schema-2 companion adoption

See [issue #101 SWSS v2](validation/issue-101-swss-v2.md) for the single-companion
reader, exact-argv integration, source binding and provenance, capture failures,
historical preservation, installed browser/package checks and limitations.
Earlier evidence remains unchanged.

## Searchable parameter lists

See [issue #104 parameter lists](validation/issue-104-parameter-lists.md) for
bounded rows, local filtering, required-first presentation, exact-argv checks,
77-declaration fixtures and installed browser/package validation. Earlier evidence
remains unchanged.

## Compact parameter rows and required feedback

See [issue #109 parameter rows](validation/issue-109-parameter-rows.md) for compact
alignment, required-only markers, omission focus/highlights, exact-argv checks,
installed theme/responsive validation and limitations. Earlier evidence is unchanged.

## Declared default hint clarity

See [issue #107 default hints](validation/issue-107-default-hints.md) for separate
authored help and declared metadata, unknown-default semantics, exact-argv and
installed theme/package checks. Earlier evidence is unchanged.

The [conditional-default revision](validation/issue-107-conditional-defaults.md)
records owner-requested edit/restore visibility, removal of unknown-default labels,
precision-preserving comparisons and focused installed-browser/package checks.

The [unset-default correction](validation/issue-107-unset-defaults.md) records
suppression of placeholder-duplicate footers while preserving explicit empty
strings, disabled drafts and exact argv.

## Explicit output allocation signal

See [issue #112 output policy](validation/issue-112-output-policy.md) for the
additive child environment discriminator, repeated portal/CLI/Python launches,
isolation regressions, installed-package checks and limitations.

## SWSS metadata audit and static CLI investigation

See [issue #114 metadata audit](validation/issue-114-swss-audit.md) for the
coverage matrix, repeatable probes, confirmed nested-value validation gap and
optional AST inspection recommendation. No runtime verifier or contract change
is introduced; earlier evidence remains unchanged.

## SWSS simulation version authority

See [issue #116 simulation versions](validation/issue-116-swss-versions.md) for
companion-derived versions, legacy-only fallback, capture-time checks, preserved
history, source/installed tests and owner verification.


## Library preservation architecture audit

See [issue #118 Phase 1](validation/issue-118-library-preservation-audit.md) for
read-only inspection of the reported Git commit and managed/original bytes,
selection-gap reproductions, A/B/A history, pinned standalone reference launches,
focused regressions and the original one-library proposal. That dated report
remains unchanged. See [issue #118 implementation](validation/issue-118-library-preservation.md)
for the subsequent approved workflow, records, integrity/recovery checks, UI,
package validation and limitations.

The [issue #118 activation UX revision](validation/issue-118-preservation-activation.md)
records prominent per-simulation status and controls, explicit confirmation,
legacy/cancellation safety, theme and narrow-browser checks, and unchanged history.

The [two-level archive revision](validation/issue-118-two-level-archive.md) supersedes
that interaction model with one global toggle and one participation toggle, and
records effective-state, actual Git contents, legacy/recovery, packaged-browser
and backup/lifecycle checks. Earlier dated reports remain unchanged.


## Issue #118 journal duplication regression

The [journal duplication report](validation/issue-118-journal-duplication.md)
records the reproduced sibling-key collision, full-App browser regressions,
all-theme desktop/narrow verification and unchanged historical evidence. Earlier
reports retain their original review-time findings.
