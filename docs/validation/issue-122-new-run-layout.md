# Issue #122 — New run descriptions and spacing

Validated 2026-10-22 on Linux, Python 3.14 and Chromium. This is presentation
validation, not scientific conformance or cross-platform certification.

## Scope and baseline

Issue #122 was the only Ready item on the SimShelf Project. No open PR existed.
Its existing dedicated branch matched accepted main
`fa9768db580c69f67dfb951856e7db5fddcff591`; the tree was clean. PR #125 was
merged and its completed branch already absent. Required #120 behavior was
accepted through PR #123, an ancestor of this main. Proposed build: 0.1.0.46
from 0.1.0.45. Historical reports were not edited.

Entry, interpreter discovery/checks, capture settings and command review now
have explicit presentation groups. Scoped spacing distinguishes 6px helper gaps,
10px related actions, 22px separate settings and 28px major sections. Stacked
fields retain separation; desktop columns retain top alignment. Existing compact
parameter rows and optional disclosure behavior remain intact.

Shorter text retains interpreter/code trust, advisory checks, no-shell execution,
unknown output coverage, references-not-backups and launch/cancellation warnings.
SWSS policy reasons, binding/conformance distinctions, changed-declaration warnings,
required-parameter feedback and progress-migration consent are unchanged. Extended
workflow explanations remain in RUNNING.md and PARAMETER_DISCOVERY.md.

No handler, request payload, argument transformation, validation condition,
allocation policy, backend behavior, scientific record or schema was changed.
Bundled assets were rebuilt; third-party notices are byte-identical to main.

## Checks

- `pnpm run typecheck` and `pnpm run build`: passed with the existing bundled Node
  runtime added to this command's PATH.
- Bundled `arguments`, `interpreters`, `outputs`, `parameterPresentation` and
  `ParameterHint` tests through esbuild to disposable CommonJS, then ran
  `node --test --test-isolation=none /tmp/simshelf-122/tests/*.cjs`:
  **29 passed**, no skips.
- `frontend/swss-output.browser.test.mjs`: **6 passed**, no console errors, at
  desktop and 390px narrow width. Five existing cases preserve exact argv, explicit
  saved-policy correction, adoption/rescan invalidation, unverified/stale metadata
  and failed refresh gating. Added checks cover helper attachment, section gaps,
  capture-setting separation, column/stack alignment, unchanged-entry disabled
  state, trust/unchecked copy, expanded progress and incomplete mapping gating.
  This harness uses the real React components and CSS with fixture HTTP responses.
- `PYTHONPATH=src .../python -m pytest -q tests/test_application_version.py
  --basetemp=/tmp/simshelf-122/version-tests`: **12 passed**, one existing
  Starlette/httpx deprecation warning.
- `python scripts/application_version.py --base-ref origin/main`: passed.
- Built wheel and sdist from an external disposable source copy, rebuilt a wheel
  from extracted sdist and installed the first wheel under `/tmp/simshelf-122`.
  Wheel members match the rebuilt wheel; Python/static members match source,
  installed files and sdist. Metadata reports 0.1.0.46.
- Installed server with no Git/Node on PATH: CLI, workspace API, OpenAPI and UI
  report 0.1.0.46; served JS/CSS/license bytes match the wheel. Startup worked
  without dependency downloads. No fresh-OS installation claim is made.
- Screenshot inspection of wide desktop and 390×844 narrow layouts: field/helper
  grouping, two-column/stacked alignment, wrapping, visible keyboard focus,
  disabled entry/check/start buttons, expanded progress/paste, incomplete output
  mapping and real missing-interpreter error. No dialog horizontal overflow.
  Screenshots and build logs are local temporary evidence under
  `/tmp/simshelf-122`; no machine-specific screenshots are committed.

## Failures and corrections

Initial typecheck could not locate Node; the default Python lacked `build`, and
the application environment lacked setuptools. Used existing Node and application
build frontend with isolated temporary build dependencies; did not change either
application or scientific environments. Sandbox socket restrictions prevented the
first HTTP fixture server; reran localhost servers with approved permissions.
Node's isolated test run reported a generic file failure; rerunning without test
process isolation exposed one stale text assertion. Updated it for the concise
wording and retained the allocation-at-launch disclosure; all 29 then passed.

Visual review caught two inherited CSS conflicts: the capture label's zero margin
won over setting separation, and the narrow grid reset gaps to zero. Scoped rules
and geometry assertions now cover both; final desktop/narrow reruns passed.

## Limits and owner verification

No scientific simulation was launched, no user library was used, and no historical
records/source snapshots/databases/outputs were changed. The installed UI used a
new disposable registration; browser regressions use fixture responses. Full
backend execution/storage suites were not rerun for this presentation-only change.
Other browsers, operating systems, screen readers, every theme and exhaustive
parameter/dependency combinations were not visually tested.

1. Open **New run…** for a disposable registration at desktop and narrow width.
   Check entry, Python, working directory/run name and capture helper ownership.
2. Tab through controls; expand progress, declaration notes, paste and Exact argv.
   Check readable wrapping, visible focus and disabled states without overflow.
3. Enter a missing interpreter and check it. Confirm the error stays visible.
   Add an empty output mapping; confirm guidance and validation blocking, then
   remove it. Do not enable a library migration just to review the layout.
4. With SWSS metadata and a saved incompatible launcher policy, verify the existing
   explicit fixed-parent correction and warnings remain. Check required fields
   and exact argv using a trusted disposable fixture before any launch.
