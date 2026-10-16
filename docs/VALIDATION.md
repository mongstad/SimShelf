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
