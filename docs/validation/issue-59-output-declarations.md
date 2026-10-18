# Issue #59 — Incomplete output declarations and capture review

Validated 2026-10-18 on Linux with Python 3.14.8 and the in-app Chromium browser.
Accepted base: `3c2af8d` (PR #71 merged, application 0.1.0.19).
Proposed application: **0.1.0.20**. No merge, release or schema migration is part
of this work; owner review is required.

## Reproduction and cause

Reproduced accepted 0.1.0.19 in a disposable workspace with a copy of
`examples/scalar_field`, registered with its actual `simulate.py` entry. Opening
Start simulation and adding a declared path produced the reported generic error
and replaced the resolved capture folder with “Path review unavailable”. Browser
inspection confirmed the input value was `""`; `results/data.csv` was only its
placeholder. There was no entered path for the backend to inspect.

Row initialization deliberately creates an empty fixed-path/File declaration.
The debounced preview sent it immediately to `/execution/outputs`; backend
`output_review` rejected the empty value. The launch UI cleared the entire review,
which also supplied the capture-folder display. This was not rejection of an
existing empty directory. The existing backend accepts prospective files and
directories and does not require a directory to contain files. File/directory
kind is an explicit declaration of script semantics, not inferred flag behavior.

## Changes and boundaries

- Review capture settings independently through the existing protected path-only
  endpoint with no declarations. Key results to simulation/cwd/capture/policy
  inputs, clear stale display on input changes, and ignore superseded responses.
  This request resolves paths only; it does not probe Python or execute source.
- Show an untouched fixed-path row as an incomplete draft with explicit
  “Example:” placeholder and associated guidance. Do not request full mapping
  review until fixed-path drafts are populated. Full review remains required for
  validation, save and start; incomplete rows are never silently filtered out of
  settings. Removing the draft restores the normal review flow.
- Keep capture-folder feedback separate from declaration errors. Backend mapping
  failures include the one-based output row number on preview and execution
  validation/save/launch, without changing path acceptance or capture semantics.
- Update the running guide and architecture, rebuild the shipped UI, and propose
  the next application build. Third-party license notices remain unchanged.

Exact argv, file/directory distinction, stale argument checks, containment,
symlink coverage, outside-output acknowledgement, per-run allocation, capture
rules and historical records are unchanged. No archive or scientific source code
was changed. README/Getting Started and historical validation reports are intact.

## Automated and package checks

- **65 passed**, one existing Starlette/httpx deprecation warning:
  `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 /home/Nozba/Codex/SimShelf/environments/SimShelf/bin/python -m pytest -q -p no:cacheprovider --basetemp /tmp/simshelf-59-final-tests tests/test_output_paths.py tests/test_isolated_outputs.py tests/test_portal.py tests/test_application_version.py`.
- New API regressions cover existing/prospective relative files, empty/populated
  directories, prospective directories, consistent preview/validate results,
  explicit empty-value rejection by preview/save/validate/launch, row numbering,
  removal recovery, and no source/output mutation or unintended run creation.
  Existing focused tests cover literal argv, symlinks/traversal, auth/origin,
  mismatch acknowledgement, capture/failure/backup, process lifecycle and per-run
  folder isolation.
- **7 frontend output tests passed**, esbuild CommonJS bundle in `/tmp`, executed
  directly with Node. Added draft completion/removal and separate capture-error
  presentation checks. TypeScript checking and bundled production build passed.
- Built wheel and sdist from an external disposable source copy. The wheel built
  from sdist and separate direct-source wheel have identical member sets/bytes.
  Verified version metadata, shipped UI, licenses, docs and focused tests.
- Fresh external wheel installation: Python/CLI/API/OpenAPI report 0.1.0.20.
  Local API/UI startup and path-preview responses passed with `PATH=/nonexistent`
  (Git and Node unavailable) and no runtime dependency fetching.

## Browser checks

Baseline and candidate ran on loopback using only `/tmp/simshelf-59-package/`.
The installed candidate was exercised at normal desktop width (1,303 px) and an
explicit 479 px narrow viewport; the temporary viewport override was reset.

- Untouched row: retained accurate capture folder, visibly empty input with
  Example hint, specific inline guidance, validation/save/start disabled.
- Prospective `outputs/new.csv`: coverage preview and Validate interpreter & paths
  accepted it and enabled Start without creating the file.
- Directory declarations `outputs/empty` and `outputs/populated`: accepted by
  preview and launch validation; existing output bytes preserved.
- Clearing a validated row invalidated its plan and disabled actions. Removing
  it restored no-declarations guidance and allowed validation again.
- While a row remained incomplete, changing capture to `new-capture` cleared the
  old path and resolved the new path. `../outside` produced a separate capture
  error. Restoring `outputs` recovered; a prospective file validated at narrow
  width. Text and controls remained readable without layout overlap.
- No browser console errors reported. No solver runs were launched through the
  browser; process execution/capture is covered by the focused integration tests.
  The fixture had zero runs afterward, no prospective files/directories were
  created, and scalar-field source/configuration plus original result bytes were
  unchanged. Both baseline and candidate servers exited after explicit Quit.

Disposable packages, logs and before/desktop/narrow screenshots are retained
under `/tmp/simshelf-59-package/`, outside the checkout.

## Failed attempts and limitations

Initial fixture registration mistakenly used `field.py`; registration rejected
it without creating a simulation. Corrected to the example's `simulate.py`.
The first new API tests sent `interpreter` to the path-only endpoint, whose strict
schema correctly returned 422: 59 passed / 6 failed. Corrected the test payloads;
the subsequent focused run passed all 65. A stale browser handle was reacquired
before reproduction. No application workaround was made for these setup errors.

No Windows/macOS, other browser engines, all-theme sweep, network-isolation
certification, GPU/scientific solver validation or sustained stress testing.
The complete unrelated test suite was not run. Paths remain coverage declarations,
not a guarantee of script output, filesystem permissions, or retention. Independent
capture preview adds one bounded, debounced metadata request when its inputs change.

## Owner verification

1. In a disposable scalar-field copy, open Start simulation with capture folder
   `outputs`. Click Declare output path. Confirm the capture folder remains,
   example text is clearly a hint, and the row explains how to complete/remove it.
2. Enter `outputs/new.csv` as File and validate. Then choose Directory and test an
   existing empty folder, a populated folder and a prospective folder. No targets
   should be created by review or validation.
3. Clear the row: validation/save/start must be blocked. Remove it and validate
   again. Confirm declarations never alter the command preview or redirect writes.
4. Change capture settings while a draft exists; confirm old paths disappear and
   current errors/resolution are accurate. Review desktop and narrow layouts.
5. With a disposable cooperating script, confirm existing outside-path warnings,
   acknowledgement, exact argv and captured results remain correct. Review the
   version gate and PR before any owner-controlled merge.
