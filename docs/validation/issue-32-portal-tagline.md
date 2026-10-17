# Issue #32 — Portal tagline

Validated on 2026-10-17 on Linux. Pending owner review; no merge or release claimed.

Issue #32 was Ready with no open PR. Its existing dedicated branch
`32-ux-update-portal-tagline-to-your-simulations-one-library` was clean and
identical to accepted main `bc6d102` (PR #31). Required repository guidance had
been read in this chat and was verified unchanged since that read.

## Change

The portal overview heading now reads **Your simulations, one library.**
The source audit found one current source occurrence of the retired tagline;
its regenerated JavaScript bundle is updated too. No current tracked application
copy retains it. Typography, placement, CSS, simulation-name headings and behavior
are unchanged. Historical evidence and screenshots were not rewritten.

Normal version gate: accepted `0.1.0.6`, proposed `0.1.0.7`. Changed runtime files:
`frontend/main.tsx`, `src/simshelf/_version.py`, and packaged `assets/app.js`.

## Checks

- `pnpm run typecheck` and `pnpm run build`: passed, bundled Node explicitly on PATH.
- Dedicated development Python, `PYTHONPATH=src`, `-B -m pytest -q
  -p no:cacheprovider --basetemp=/tmp/simshelf32-tests
  tests/test_application_version.py`: **12 passed**. One existing
  Starlette/httpx deprecation warning; no failed checks.
- External disposable build: wheel, sdist and wheel from extracted sdist passed.
  Both wheels report `0.1.0.7`; every packaged static asset is byte-identical to
  the checkout. CSS and both license notice files remain identical to main.
- Fresh disposable wheel installation: Python/CLI version, workspace API,
  OpenAPI and static endpoints passed with Git/Node absent from PATH. Outbound
  connections were denied in the API test process. Build/dependency installation
  used network access beforehand; CLI used the same minimal PATH.
- Source browser: exact heading and version label, Dark 1280x900 and Light
  390x844. Installed browser: exact heading and version label, Dark 320x740.
  Narrow headings fit/wrap using existing styles without horizontal overflow.
- Whitespace, scoped diff and accepted-main version gate checked before handoff.

Local screenshots: `/tmp/simshelf32-dark-desktop.png`,
`/tmp/simshelf32-light-narrow.png`, `/tmp/simshelf32-installed-dark-320.png`.
All workspaces, package environments and test data were disposable external paths.
No user library was opened or modified.

## Limits and owner checks

Linux/in-app Chromium only; no other browser/OS or screen-reader validation.
This wording-only change did not warrant scientific execution, storage, shutdown
or backup regression suites. No new tests mirror the static copy change.

1. Start the branch against a disposable library and reload the portal.
2. Verify **Your simulations, one library.** including the period, and
   **Local · 0.1.0.7**. Inspect Dark/Light at desktop and 390px/320px widths.
3. If using a library with simulations, select one and confirm its own name still
   replaces the overview tagline; return to All simulations to see the slogan.
4. Before merge, fetch main and run
   `python scripts/application_version.py --base-ref origin/main`.
