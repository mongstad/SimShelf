# Issue #55 — Resizable and collapsible navigation

Prepared for owner review on 2026-10-18 from accepted `f4da9b8` (merged PR #78).
Application version `0.1.0.26`; no release or workspace schema change.

## Implementation and decisions

The existing navigation sits in a sticky frame with an independent scroll area
and a nine-pixel edge separator. Pointer capture bounds drag handling to that
separator. Release, cancellation, lost capture, window blur/leave and viewport
resize clear drag state; text selection and sidebar clicks are suppressed while
dragging. No run-selection, recorder, Git, backup or API handlers were changed.

Expanded width defaults to 228 px, ranges from 200 to 480 px, and is temporarily
constrained to leave 480 px for content where possible. At the narrowest desktop
breakpoint the minimum sidebar width takes precedence. Below/equal to 650 px,
the existing full-width stacked navigation remains; resizing is not offered.
A small branding wrap prevents internal horizontal overflow at the minimum width.

The header button has explicit Collapse sidebar / Expand sidebar accessible
names, expanded state and a controlled-region relationship. It remains mounted
and keeps focus through either operation. Collapse hides the entire frame and
removes its grid column, with no permanent rail. The separator exposes orientation,
current/min/max width and keyboard Left/Right (10 px), Home/End controls.

`simshelf-sidebar` localStorage holds only width and collapsed state, alongside
existing browser-local UI preferences. Invalid/nonfinite values fall back safely;
widths are bounded and storage failures leave the controls usable for the session.
A smaller viewport does not overwrite the saved expanded width. Preferences are
per browser origin (including port); there is no workspace/database migration.

## Validation

- `node frontend/sidebar.test.mjs`: **3 passed**, covering malformed stored values,
  bounded widths, retained collapse preference and viewport shrink/restore.
  The equivalent `node --test` invocation reports the file as one passing test.
- TypeScript `tsc --noEmit` and bundled frontend build passed; licenses unchanged.
- `tests/test_application_version.py`: **12 passed**, with the existing
  Starlette/httpx deprecation warning. Accepted-main version and whitespace gates
  passed. The unrelated exhaustive backend suite was not run for this UI change.
- External sdist, wheel rebuilt from sdist, direct wheel and disposable installation
  verified. Direct/sdist wheel members match byte-for-byte; installed JS/CSS and
  notices match the checkout. Python/CLI/API/OpenAPI report `0.1.0.26`. Offline
  TestClient startup/assets passed with outbound socket connections denied and
  Git/Node absent from PATH. Optional httpx2 was installed only in the test env.
- Installed Linux/Chromium fixtures contained zero, one and 24 simulations, a long
  name and a completed run. At 1280×900, pointer drag changed 480 to 360 px, with
  no selected text or residual drag class. Navigation still selected the intended
  simulation. Keyboard Home/End reached 200/480; arrows changed width by 10 px.
- Collapse reclaimed all 1280 px, hid sidebar controls, and retained focus on the
  now-named Expand sidebar button. Enter/Space and pointer activation worked.
  Width 360 and collapsed state survived reload; a replacement tab after fixture
  restart retained width 200. A saved 480 temporarily became 320 at 800×800 and
  returned to 480 at 1280×900. At minimum width, sidebar client/scroll widths both
  measured 184 px with its vertical scrollbar, confirming no internal overflow.
- Light, Dark, Onyx, Slate and Linen inspected at desktop and 390×844; System
  also exercised. No document horizontal overflow in the checked layouts.
  Narrow navigation uses its existing horizontally scrollable simulation row;
  full collapse removes the stacked block. Long names are revealed at wider
  settings and remain ellipsized when space is limited.
- Run selection/detail tabs and Files view remained usable. Add simulation dialog
  inspected at narrow width; Quit dialog opened/cancelled on the one-run fixture.
  This fixture launch intentionally lacks a Quit callback, so final shutdown was
  not exercised. Back up workspace successfully downloaded a ZIP after resize,
  collapse and run navigation. No user simulation was executed or changed.

Screenshots and disposable fixtures are retained outside the checkout under
`/tmp/simshelf-55-package/`. `desktop-*.png` record all five palettes;
`narrow-*-settled.png` supersede early captures taken during color transitions
(the Light capture did not need replacement). These are local review artifacts,
not distributed research data.

## Failures, corrections and limitations

The first build invocation lacked Node on PATH; the supplied runtime's absolute
path passed. An over-broad browser heading selector was corrected. Early rapid
viewport/theme screenshots caught transient paint/transition states and were
rechecked after settling. One temporary fixture process exited with status 143;
its connection-error tab could not be reused by the browser tool, so the fixture
was restarted and a new tab used. This did not require an application change.
The minimum-width browser check found branding overflow; allowing that row to
wrap fixed it, and the corrected assets were rebuilt and packaged again.

Physical touch hardware, actual screen readers, window-leave/OS-focus interruption
during a held drag, other browsers/OSes, browser-wide restart and long scientific
jobs were not exercised. Pointer cancel/blur/leave cleanup was reviewed in code.
Persistence across reload/server restart was checked; cross-tab live synchronization
is not introduced. Git archival transactions, scientific execution and every
existing dialog/chart/download combination were not rerun. The changes leave
those handlers and data contracts intact, without claiming exhaustive coverage.

## Owner checks

1. Restart the candidate portal and reload. Drag the sidebar edge wider/narrower
   with a long simulation name; release over content and outside the window.
   Confirm selection is unchanged and ordinary clicks resume.
2. Tab to the separator; use Left/Right and Home/End. Activate Collapse sidebar,
   then Expand sidebar with Enter/Space. Check focus and the restored width.
3. Reload collapsed, expand, shrink the window to about 800 px and then widen it.
   The last expanded desktop width should return. At about 390 px, navigation
   should stack, with collapse/expand still available and no resize handle.
4. Check all five palettes, a long list, a run's tabs/files and an open dialog.
   Verify Add simulation, Appearance, backup and Quit remain reachable expanded.

Stop for owner review; no merge, issue closure, Done transition or publication.
