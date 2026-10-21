# Issue #118 / PR #119 — discoverable Git preservation activation

Date: 2026-10-21. Review revision to the existing issue branch, based on
`3a7112d972456c0279001a774d73e89003930d4b`. Accepted `origin/main` was refreshed
at `40fa289509f99aad80d2d4dc3ac89663bb2b91e5`. Build stays **0.1.0.43**; a review
revision does not increment the same PR again. Earlier audit and implementation
evidence is unchanged.

## Change and boundaries

The per-simulation status and Enable/Disable controls are directly below the shared
Master Git Archive status. Green Enabled uses the existing connected-status class;
Disabled is neutral; Unavailable is a warning with a reason. A shared connection
does not activate a simulation. Capture/source/extension controls remain accessible
below in **Capture and Git options**; archive path/setup details are also below.

Enable opens the existing backend preview using saved capture configuration,
all eligible captured sources and recursive `.json`, `.csv`, `.log` outputs.
It excludes process stdout/stderr by default. Preview/cancel never save consent;
confirmation uses the existing save endpoint and reloads confirmed backend status.
Disable uses the existing endpoint and leaves historical evidence intact. Keyboard
focus enters the review heading and returns to its invoking control. Legacy
consent remains in force until explicit confirmation or explicit disable.

Only frontend components, styling, component assertions, distributed assets and
current usage/validation documentation change. No backend/data/schema, SWSS,
scientific simulation, archive history or remote-Git changes.

## Automated checks

- TypeScript `tsc --noEmit`: passed.
- `node frontend/build.mjs`: passed; shipped JS/CSS rebuilt, notices unchanged.
- Bundled Node tests: **34 passed** (archive 13, preservation 7, source Git 3,
  outputs 7, screenshots 4). New assertions cover prominent ordering, separate
  states, unavailable controls, failed status loading and legacy consent display.
- Focused source integration: **4 passed, 24 deselected** using
  `tests/test_preservation.py -k 'consent_is_explicit or disabled_disconnected or preservation_api or browser_review'`
  together with `tests/test_application_version.py`. The selector deselected the
  version tests; they were subsequently run separately: **12 passed**.
- `python scripts/application_version.py --base-ref origin/main`: passed,
  candidate .43 vs accepted .42.
- `git diff --check`: passed.

Temporary checks and package outputs are outside the checkout under
`/tmp/simshelf119-ux`. Tests use `PYTHONPATH=src`, the existing SimShelf environment,
no bytecode/cache writes, and external pytest base directories. The frontend suites
were bundled with existing esbuild and run through Node's test runner.

## Real-browser checks

Used the actual locally served built application and an independent disposable
library/archive with two fixture simulations: `alpha` has legacy consent and
`beta` has a disabled new policy. Both have an existing Git event. No owner library,
archive, scientific source or output was opened for mutation.

- Desktop at 1280×900 (also 1265×712) and narrow 390×844. All six appearance modes
  inspected: System (resolved dark), Light, Dark, Onyx, Slate and Linen. Enabled
  was inspected in every desktop theme; Disabled in every narrow theme. Enabled,
  Disabled and Unavailable were exercised at desktop/narrow widths. The narrow
  document had no horizontal overflow (375 px content within 390 px viewport).
  Both statuses and Enable were visible above the capture controls; after the
  compact spacing correction the narrow Enable button ended at y=751 of 844.
- Connected + Disabled remained distinct. Enable opened source/output review with
  all two eligible source files and nested JSON/CSV/log matches; existing copy,
  reference and ignore rules and safety limits were retained.
- Enter activation, heading focus, Cancel and restored Enable focus passed.
  Cancel left the exact saved policy and capture configuration unchanged.
- Explicit confirmation remained Disabled while pending, then became Enabled
  from the backend response. Reload and reopening settings still showed Enabled.
- Disable became Disabled and returned focus to Enable. Disconnect made the status
  Unavailable and disabled Enable. Reconnect kept the simulation Disabled.
- Legacy alpha stayed Enabled with an explicit legacy notice. Both prominent and
  advanced review/cancel paths retained its exact old consent, created no new
  policy, and returned focus to their own review buttons. While disconnected,
  Disable remained available and review was disabled.
- Capture and Git options opened with Enter and exposed all existing controls.
  Tab from the shared connection switch reached Enable, with a visible focus ring.
- Final browser tab recorded no console warnings/errors. Screenshots are local
  artifacts: `desktop-{theme}.png`, `narrow-{theme}.png`, `narrow-enabled.png`,
  `desktop-unavailable.png`, `narrow-unavailable.png`, `final-desktop.png`.

After all browser operations, direct assertions verified the exact alpha legacy
policy unchanged, no alpha new-policy adoption, beta capture configuration and
disabled options unchanged, the archive HEAD unchanged, and SHA-256 hashes of both
original committed preservation records unchanged. This validates that toggling
and cancellation did not append, rewrite or delete historical Git evidence.

## Failures and limits

Two old component label expectations failed during development after the shared
status copy and redundant heading changed. They were updated to assert the new
explicit status and all focused suites then passed. A sandboxed version-test run
stalled and was interrupted; the explicit source-import run outside that sandbox
passed all 12 tests. Backend tests emit the existing Starlette/httpx deprecation
warning. One disposable test-server process ended during browser work; it was
restarted against the same fixture and the interrupted browser checks completed.

This is Linux/Chromium validation, not native mobile, Firefox, Safari, screen-reader
or OS high-contrast certification. System mode resolved dark; both explicit Light
and Dark modes were inspected. Browser checks used the built source application;
installed-package byte identity/import checks are recorded below. Unrelated full
backend suites, external scientific simulations and production libraries were not
rerun for this frontend-only revision. Earlier broader PR evidence remains dated
and is not presented as rerun here.

## Owner verification

1. Open an existing simulation's Preservation settings. Immediately identify the
   shared connection and the simulation-specific state, without expanding options.
2. For a disabled simulation, choose Enable. Review sources, recursive outputs,
   copy/reference/ignore exclusions and limits, then Cancel; verify still Disabled.
3. Enable again and explicitly Confirm. Verify Enabled, reload, and verify again.
4. Disable and verify previous run commits/downloads are still present. Reconnect
   the shared archive and verify this simulation remains Disabled.
5. Inspect a legacy simulation and cancel its review; confirm its prior consent
   remains. Repeat the visual/keyboarding checks at a narrow width and preferred
   theme. Use disposable evidence for any activation test.

Stop at owner review of the existing PR; no merge or publication is authorized.

## Package check

External sdist → wheel build and isolated target installation passed. The wheel's
`preservation.py`, static index, rebuilt JS and CSS match the working source bytes;
metadata and imported installed package both report 0.1.0.43. Source distribution
includes the frontend, preservation source/tests and implementation evidence,
without node_modules, user libraries or Python caches. Runtime dependencies were
reused; this was not a fresh dependency-resolution or additional installed-browser
run. These validation artifacts were built before this final evidence entry:

- Wheel SHA-256: `06cc4711559a016ea96e0d21844e14bf9610fa8d8ea938897c18fdb5cf551576`.
- Sdist SHA-256: `caa565c3e3902218528f051989d22894c2e3616f5f8c490e2395908cf06f5165`.

No package was published.
