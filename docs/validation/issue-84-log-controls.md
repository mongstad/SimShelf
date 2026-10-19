# Issue #84 — Persistent log presentation controls

Prepared for owner review on 2026-10-19 from accepted `064bd1b4a2185240c11e3be953aff773ac7c9c7d`
(merged PR #81). The existing issue branch matched main and was clean; #84 was
then the sole Ready item, with no declared blocked-by dependencies or open PR.
Application version `0.1.0.28`; no release or schema change.

## Changes and decisions

- `LogViewer.tsx` owns stdout/stderr display and serial polling, keyed by run and
  stream. Cleanup rejects late responses and errors; an older request cannot race
  a newer poll. The next poll starts three seconds after the previous completes.
- `logPresentation.ts` validates independent boolean preferences, defaults both on,
  and stores only presentation state in `simshelf-logs` localStorage. A session
  cache survives viewer remounts when storage fails. Preferences are global to
  this browser origin/port; live cross-tab synchronization is not introduced.
- Wrapping uses pre-wrap and anywhere overflow wrapping. Unwrapped text scrolls
  inside the panel. Explicit whitespace/newlines/Unicode remain unmodified.
- Follow changes scrollTop only; horizontal offset survives new chunks. Upward
  wheel/keyboard/touch intent or vertical scrollbar dragging pauses it. Generic
  scroll events, horizontal input and geometry changes cannot themselves pause it.
  Resize and content updates pin only an enabled follower. Re-enabling jumps to
  the bottom. Reaching the bottom manually does not change the saved off state.
- Disabling retains the current scroll offset while polling. Browser clamping on
  shortened content and the existing rolling 200 KB tail can change which text
  is available; this does not freeze/archive old preview text. Reopened viewers
  start at the bottom if enabled, otherwise the top. No per-run offset is stored.
- Native labelled checkboxes sit together at the lower right, 18 px below the log
  panel, with labels to their left per owner feedback during implementation.
  Log content is focusable for keyboard scrolling; focus styles remain inherited.
- `main.tsx`, scoped CSS and rebuilt distributed assets integrate this viewer.
  RUNNING/ARCHITECTURE/VALIDATION document the behavior; historical reports remain
  unchanged. Backend, log endpoints, recorder, progress, data and schema are untouched.
  There is no existing combined stream UI; this change retains stdout and stderr.

## Validation

- `node frontend/logs.test.mjs`: **6 passed**. Covers malformed/partial preferences,
  saved false values, blocked storage remount fallback, append/resize behavior,
  disabled offsets, horizontal/programmatic scrolling, upward keyboard/wheel,
  thumb movement, geometry changes, touch intent, and listener/observer cleanup.
  These use a controlled event/geometry fixture, not physical input hardware.
- TypeScript `tsc --noEmit`, frontend build, accepted-main version gate and
  `git diff --check`: passed. Third-party notices unchanged.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src …/python -m pytest -q -p no:cacheprovider
  tests/test_application_version.py`: **12 passed**, outside the execution sandbox,
  with the existing Starlette/httpx deprecation warning.
- External direct wheel/sdist, wheel rebuilt from extracted sdist, disposable
  installation: passed. Direct and sdist wheel members matched byte-for-byte;
  installed JS/CSS/notices matched source assets. Python, CLI, API, OpenAPI and
  visible portal label reported `0.1.0.28`. Offline TestClient startup/assets
  passed with outbound socket connections denied and Git/Node absent from PATH.
- Installed Linux Chromium fixture used a real child emitting long diagnostics
  with Unicode to stdout and shorter stderr lines every 250 ms. Live append and
  the 200 KB rolling-tail state were exercised. Follow stayed at bottom (0 px gap),
  while keyboard/wheel upward browsing unchecked it. Explicit resume immediately
  returned to bottom. Vertical scrollbar drag paused (3,572 px gap); horizontal
  scrollbar drag moved left to 821 px while follow stayed enabled.
- Word wrap on kept panel scrollWidth equal to clientWidth; off exposed a roughly
  4,339 px-wide line without document overflow. Horizontal keyboard scrolling
  retained follow; resume retained horizontal offset. Disabled browsing persisted
  during append. Native Space toggled both controls and retained checkbox focus.
- Saved Off/Off survived reload, stream switches, completed/failed logs, and a
  different simulation with empty output. On/On remained enabled through viewport
  changes. No previous stream content appeared after the new stream loaded.
- All five palettes were checked at desktop (1280×1000) and narrow (390×844)
  widths. No document horizontal overflow; wrapped narrow panel client/scroll
  widths were both 288 px. Final spacing measured 18 px. Dark narrow focus and
  other palette screenshots retained under `/tmp/simshelf-84/` alongside fixture,
  build logs and disposable packages. No user simulation or workspace was used.

## Failures and limits

Initial source filenames differed only by capitalization and confused esbuild;
renaming the helper to `logPresentation.ts` resolved the build failure. The first
version test accidentally imported an older installed package; explicit source
PYTHONPATH fixed the invocation. The HTTP test client then stalled in the sandbox;
the bounded outside-sandbox rerun passed. The existing environment lacked
setuptools, so packaging used dependencies installed only into the disposable
`/tmp/simshelf-84/venv`. An attempted direct Playwright import was unavailable;
browser validation used the provided in-app browser tools. An initial narrow
scrollbar drag missed the thumb; the measured desktop drag passed. One rapid
Dark screenshot was unusable and was replaced by a settled capture.

Physical touch/trackpads, actual screen readers, other operating systems/browser
engines, full browser-process restart, interrupted-run UI and long-duration
scientific workloads were not exercised. Storage denial/malformed preferences
were unit-tested, not forced in the installed browser. Deliberately delayed/error
network responses were reviewed via lifecycle guards rather than browser fault
injection. The generic renderer does not branch on run status. Unrelated backend
suites and scientific/Git/backup operations were not rerun for this UI-only change.

## Owner verification

1. Restart the candidate portal, reload, and open Logs on a disposable live run
   with long lines. Confirm labels are left of their checkboxes, with comfortable
   spacing below the viewer. With no saved preferences both should be on.
2. Turn Word wrap off, scroll horizontally, and confirm the page does not widen
   and Auto-scroll stays on. Resize the window and confirm follow remains on.
3. Scroll up using wheel, PageUp and the vertical scrollbar. Auto-scroll should
   turn off; new output should not drag you down. Click its checkbox once to
   resume at bottom. Also try the actual trackpad/touch hardware you use.
4. Save both off, switch stdout/stderr, navigate to another simulation/run, and
   reload/reopen the browser at the same origin/port. Both should remain off.
   Check completed/failed/interrupted and empty logs, narrow width, all palettes,
   and Tab/Space focus/activation.

Stop for owner review. No merge, issue closure, Done transition or publication.
