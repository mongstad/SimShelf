# Issue #35 — optional color palettes

2026-10-17. Issue #35 was the top and only Ready item. The existing dedicated
branch `35-ux-add-sleek-color-only-portal-themes-including-near-black` began clean
at accepted main `f6f38855f99904ed4b4335edcecdd2735ddfd6fe`. PR #37 was verified
merged; its local/remote branch was already absent. No open PR, stale branch,
unmerged predecessor or conflicting work was present. Proposed build **0.1.0.10**
follows accepted 0.1.0.9.

## Implementation and decisions

- `frontend/style.css`: three additive root palettes, with native dark/light color
  schemes. Existing progress colors move to inherited root tokens so each palette
  can provide its own solid fill/track. Forced-colors overrides remain in place.
- `frontend/main.tsx`: three additional Appearance options, using the existing
  preference storage and selection effect without new state or dependencies.
- `frontend/themes.test.mjs`: palette scope/completeness and contrast regression
  checks. `README.md`: concise appearance guidance. Rebuilt tracked JS/CSS and
  updated the authoritative version. Full licenses and legal notices unchanged.
- **Onyx**: near-black surfaces, restrained teal accent. **Slate**: cool blue-gray
  surfaces and muted cool teal. **Linen**: warm off-white surfaces and sage accent.
  Short labels preserve the native selector's original intrinsic width. Initial
  Midnight / Deep Slate labels widened it by 17px and were corrected before handoff.
- Logo shape, SVG path, size, text, typography and layout are untouched. Its existing
  accent/background tokens supply subtle palette adaptation, as the owner requested.
  No scientific, process, persistence, schema, backup or deletion behavior changes.

## Automated and package validation

Commands used the dedicated Python and the runtime's absolute Node executable;
all temporary outputs were outside the checkout.

- `node frontend/themes.test.mjs`: **2 passed**. Only color tokens and color-scheme
  may appear in new theme blocks. Text, muted, accent, amber, red and blue tokens
  each meet 4.5:1 against the five tested content surfaces; primary label/background
  meets 4.5:1; progress fill/track meets 3:1. This is focused token coverage, not an
  exhaustive accessibility certification of existing components.
- `node node_modules/typescript/bin/tsc --noEmit` and
  `node frontend/build.mjs`: passed.
- `esbuild frontend/progress.test.mjs --bundle --platform=node --format=cjs
  --outfile=/tmp/simshelf35-progress.test.cjs`, then Node on that bundle:
  **5 passed**, covering unknown/known/final progress and existing presentation.
- `PYTHONPATH=<checkout>/src <dedicated-python> -B -m pytest -q -p no:cacheprovider
  --basetemp=/tmp/simshelf35-version-tests tests/test_application_version.py`:
  **12 passed**, existing Starlette/httpx deprecation warning only.
- An inverse-diff check removed just the new palette blocks and moved progress
  defaults back to their old selector: the result equals accepted-main CSS
  byte-for-byte. No font, geometry, breakpoint, animation or component rule changed.
- Wheel, sdist and wheel-from-sdist built in `/tmp/simshelf35-package`. Metadata
  reports 0.1.0.10; both wheels' complete static assets match the checkout bytes,
  including notices. Installed externally. Python/CLI/API/OpenAPI/static checks
  passed with Git/Node absent from PATH and outbound API startup connections denied.
  The disposable environment uses system-site-packages; this is not a fully
  isolated dependency audit. No package was published.

## Browser validation

Linux/Chromium, disposable synthetic libraries only. No user source was executed
or user library changed. Tested source UI and final installed wheel.

- All three palettes: sidebar/logo/navigation, headings, status badges, table,
  disabled controls, run detail tabs, screenshot gallery, 6% progress with grouped
  counts and stage label, unknown progress, launch form and parameter editor.
  Invalid integer input showed the existing red validation message; keyboard Tab
  showed visible focus. Form edits were discarded, never launched or saved.
- Schema-1 screenshot confirmation: readable warning, neutral Cancel, restrained
  red Delete button, keyboard focus and safe Cancel/Escape in all three palettes,
  at desktop and 390px. No deletion was performed; image remained attached.
- Source and final installed overview at 1280x900 and 390x844. Final palettes have
  identical element bounds, font family/size/weight/style, letter/line spacing,
  padding/margins, border widths/radii, display and gaps across theme switches.
  Mobile document width is 375px within the 390px viewport; existing table scrolling
  remains. Original 76x26 desktop Appearance selector retained.
- Same-viewport Light/Dark screenshots compared against accepted main: all pixel
  differences confined to the top-right version badge (0.1.0.9 → 0.1.0.10).
  Computed colors/typography matched for Light, Dark and System. System was tested
  under the current OS preference; both light-dark branches and System wiring are
  unchanged by the source comparison. OS preference switching was not automated.
- Onyx/Slate/Linen each restored after reload in the installed build. Portal label
  showed 0.1.0.10 without Git/Node on server PATH. Final browser warning/error log
  empty. Restored System, reset viewport and closed all test tabs.

Final same-view palette previews (temporary local evidence, supplied to owner):
`/tmp/simshelf35-onyx-final.png`, `/tmp/simshelf35-slate-final.png`,
`/tmp/simshelf35-linen-final.png`; corresponding mobile views use
`/tmp/simshelf35-<palette>-narrow-final.png`.
Earlier surface screenshots under `/tmp/simshelf35-*` retain the preliminary
Midnight/Deep Slate labels; their colors are identical to final Onyx/Slate.

## Failures and limitations

- Initial Linen muted text on its selected/soft background missed 4.5:1; darkened
  the token and reran both theme tests successfully.
- Initial test invocations used a wrong pytest working directory, an unsupported
  `--no-browser` flag, and an external ESM bundle unable to resolve React. Corrected
  to checkout cwd, `--no-open`, and a self-contained CJS bundle. No passing claims
  are based on those failed invocations. Direct Node test execution exposed the
  assertion detail hidden by the initial sandboxed test-runner invocation.
- Early rapid color comparisons sampled existing button transitions. Stable
  screenshots/computed values were rechecked. A stale browser asset cache retained
  preliminary labels after rebuild; final package checks used a fresh local address.
- The disposable baseline server received SIGTERM (exit 143), causing a failed
  detail fetch. Cause not established. Restarted it and completed the comparison;
  failed-fetch views were not used as passing visual evidence.
- **Existing accepted-main defect:** `DeleteScreenshot.tsx` accepts schema 1/2/3
  only, so schema-4 libraries show “Could not check library compatibility” and a
  disabled Delete button. Reproduced in accepted main 0.1.0.9 and this branch. This
  color-only issue deliberately does not alter that behavior. Recommend a separate
  owner-authorized fix; no issue/PR was created for it. Schema-1 fixture was used
  to verify enabled destructive styling and compatibility-warning appearance.
- Other engines/OSes, screen readers, forced-colors hardware and long sessions were
  not tested. No broad backend/scientific suite repeated for this palette change.
  Existing historical reports, user data and simulation output are preserved.

## Owner verification

1. Restart/reload this build. Select Onyx, Slate and Linen in Appearance; compare
   the same overview, logo, active navigation, statuses and table. Reload each
   choice and confirm persistence. Switch back to System/Light/Dark.
2. Inspect a run with progress and screenshots, then a launch dialog (do not launch
   unless intended). Check fields, disabled options, validation colors and Tab focus.
3. At desktop and a narrow window, verify unchanged control/layout dimensions,
   readable surfaces, visible progress fill and logo identity. In a schema-1/2/3
   test library, open screenshot deletion and cancel; never delete valuable data
   just to test colors. Schema-4's pre-existing limitation is described above.
4. Fetch main and rerun `python scripts/application_version.py --base-ref origin/main`
   before merging; this PR proposes 0.1.0.10. Owner review only; no merge or release.
