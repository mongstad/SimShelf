# Issue #132: grouped run-header actions

2026-10-23, Linux/Chromium. Accepted main: `b283be8d83197585621b6c4feffd82ea6c52d72f`
(0.1.0.49); proposed application version: 0.1.0.50.

## Change

Stop and Remove previously participated independently in the header's
`space-between` layout, distributing Stop into the middle. They now share a
right-aligned `Run actions` group with an 8px gap. Stop precedes Remove; the title,
favorite and metadata remain together on the left. The existing narrow header
stacks the group beneath the title; the group can wrap if space requires it.
Labels, button styling, disabled predicates, callbacks and request bodies are
unchanged. No new confirmation or backend behavior is introduced.

## Validation

- TypeScript `tsc --noEmit`, `node frontend/build.mjs`, `git diff --check`, and
  `scripts/application_version.py --base-ref origin/main`: passed.
- `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 <venv>/bin/python -m pytest
  tests/test_application_version.py -q -p no:cacheprovider
  --basetemp=/tmp/simshelf-132/version-tests`: 12 passed. Existing Starlette/httpx
  deprecation warning remains.
- Existing `frontend/favorite.test.mjs`, bundled by esbuild to
  `/tmp/simshelf-132/favorite.cjs` and executed with Node: 7 passed.
- Full-app browser fixture on localhost:8132 uses a disposable library under
  `/tmp/simshelf-132`. Middleware projects controlled active/stopping/finalizing/
  completed/failed states over a disposable completed record. The fixture Stop
  route logs the POST and changes the projection; no scientific process is started
  or stopped. This checks UI behavior, not process termination.
- Active: Stop enabled, Remove disabled, correct group order. At 1366px the
  action right edge equals the header right edge; the two buttons have an 8px gap.
  At 390px the group is right-aligned below title/metadata with no overflow.
- Keyboard Tab from Favorite focuses Stop; Enter sends the existing
  `/api/runs/<id>/stop` POST. Pending controls disable, then `Stopping…` and Remove
  remain disabled. Finalizing shows only disabled Remove. Completed and failed
  show only enabled Remove. Keyboard activation opens the existing removal review;
  Cancel was used and no record was deleted or schema upgraded.
- Installed-wheel long-title geometry checks at 1366, 768, 390 and 320px: header
  and action right edges agree, title/actions do not overlap, no document horizontal
  overflow. Five existing themes (Light, Dark, Onyx, Slate, Linen) exercised at
  390px. No browser console errors during checked flows. Viewport override reset.
- Wheel and sdist built externally; wheel rebuilt from extracted sdist has
  identical member names and bytes. Installed with `--no-deps` into disposable
  `/tmp/simshelf-132/installed`, using existing runtime dependencies. Bundled
  JS/CSS and third-party notices match checkout; notices unchanged. Python, CLI,
  API, OpenAPI and browser report 0.1.0.50 with Git/Node absent from PATH.
  In-process TestClient startup/API checks deny socket `connect`/`connect_ex`;
  this is not an OS network-namespace test. Fixture also rerun from installed wheel.

## Screenshots

Installed-wheel fixtures; active states are controlled projections, not science.

| State | Desktop 1366px | Narrow 390px |
| --- | --- | --- |
| Active | [Screenshot](../images/issue-132/active-desktop.png) | [Screenshot](../images/issue-132/active-narrow.png) |
| Completed | [Screenshot](../images/issue-132/completed-desktop.png) | [Screenshot](../images/issue-132/completed-narrow.png) |

## Limits and owner checks

No new unit tests for this reversible markup/CSS change. No full backend suite,
real stop/capture workload, other browser engines/OS, or screen-reader testing.
Existing event handlers and backend files are unchanged. Prior validation evidence,
user workspaces, source snapshots and outputs were not changed.

1. Restart from this branch, reload and confirm 0.1.0.50.
2. Open an expendable active run: Stop should sit immediately before disabled
   Remove at the right; title/favorite/metadata stay left. Try a narrow window and
   long title; the action group must remain readable without overlap.
3. Use keyboard navigation and Stop on that expendable run. Confirm the existing
   stopping state and eventual finalized state, then inspect the removal review
   and cancel. Repeat with a completed/failed record; Stop must be absent.
