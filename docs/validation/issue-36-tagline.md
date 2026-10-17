# Issue #36 — sidebar tagline

2026-10-17. Top and only Ready issue on the SimShelf Project board. Existing
dedicated branch `36-ux-consolidate-portal-tagline-beneath-sidebar-branding` began
clean at accepted main `454d3084afc53c03ce8229aefdfa784484be6434`. Prior PRs #33
(chosen slogan) and #34 are merged; issue #17 branch cleanup was already complete.
No conflicting PR or branch was present. Proposed build: **0.1.0.9**, next after
accepted 0.1.0.8. No schema, scientific or backend behavior change.

## Changes

- `frontend/main.tsx`: chosen tagline appears once underneath the sidebar brand;
  overview h1 is All simulations; selected simulation names and authored
  descriptions remain, without either fixed promotional subtitle.
- `frontend/style.css`: original icon/title/local row remains a flex row; tagline
  is muted 11px, normal-weight text beneath it. Its 19px height uses existing brand
  bottom space at desktop. Sidebar widths, controls, heading typography and
  responsive breakpoints remain unchanged. At the narrow sidebar breakpoint the
  tagline balances into two readable lines; mobile has room for one line.
- Authoritative version and distributed JavaScript/CSS rebuilt. License notices
  and full third-party licenses unchanged; historical evidence untouched.

## Validation

- TypeScript `tsc --noEmit` and `node frontend/build.mjs`: passed, using the
  runtime's absolute Node executable. `git diff --check`: passed.
- Source search confirms exactly one tagline occurrence and neither removed
  fixed subtitle. Direct browser checks cover this small copy/layout change;
  no redundant implementation-mirroring unit test was added.
- `PYTHONPATH=/home/Nozba/Codex/SimShelf/SimShelf/src` with the dedicated Python,
  `-B -m pytest -q -p no:cacheprovider --basetemp=/tmp/simshelf36-version-tests
  tests/test_application_version.py`: **12 passed**, one existing Starlette/httpx
  deprecation warning. No unrelated backend suite repeated.
- Built wheel/sdist and wheel from extracted sdist from an external disposable
  source copy under `/tmp/simshelf36-package`. Both wheels report 0.1.0.9 and all
  bundled static asset bytes match the checkout. Installed wheel externally;
  Python/CLI/API/OpenAPI/static checks passed with Git/Node absent from PATH and
  outbound API startup connections denied after dependencies were installed.
  Environment uses system-site-packages, not a fully isolated dependency audit.
- Installed Chromium browser: Dark and Light at 1280px desktop and 390px mobile;
  Light at 800px verifies the 175px sidebar and balanced tagline wrap. Tagline
  count is one; mobile brand font 21px versus tagline 11px. Document width 375px
  within 390px viewport. Existing table scrolling remains separate.
- Selected a synthetic simulation with an authored description: exact description
  retained beneath its name. Selected one without: no subtitle. Navigation active
  selection and existing controls remain; Enter on the focused brand link returns
  to All simulations with visible focus. Portal version shows 0.1.0.9.
- Browser warning/error log empty. Restored System theme/viewport and closed own
  tab. Disposable source files were registered but never executed; no user library,
  output, database, source snapshot or historical report was edited.

Temporary screenshots: `/tmp/simshelf36-dark-desktop.png`,
`/tmp/simshelf36-light-desktop.png`, `/tmp/simshelf36-light-sidebar.png`,
`/tmp/simshelf36-dark-mobile.png`, `/tmp/simshelf36-light-mobile.png`.

No failed checks. Linux/Chromium only; other browser engines, screen readers and
operating systems were not tested. No newer palettes exist in accepted main;
issue #35 remains Backlog and is outside this change.

## Owner verification

1. Open the overview: All simulations h1, no promotional subtitle, chosen tagline
   once beneath the sidebar brand with icon/name/local badge retained.
2. Select simulations with and without descriptions. Confirm names stay primary,
   authored descriptions remain exact, and no fixed fallback slogan appears.
3. Check Dark/Light at desktop, 800px and 390px; inspect the muted tagline, local
   badge's existing breakpoint behavior, navigation selection and keyboard focus.
4. Re-fetch accepted main and rerun the application version gate before merge.
   This PR proposes 0.1.0.9 only; no release, merge or additional issue is authorized.
