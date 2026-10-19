# Issue #93 — Context-specific overview actions

Prepared for owner review on 2026-10-19. Accepted base `8a39cc6` (PR #92),
application version `0.1.0.33`. Sole Ready issue; existing branch clean and equal
to accepted main. PR #92 merged and completed branch already cleaned up.
Existing New run label/icon predecessor work is included in main.

## Change and decisions

Extracted the existing header action group into OverviewActions for focused
render assertions. The displayed simulation determines context: All simulations
renders Add simulation and Terminal / editor; a selected simulation renders
Terminal / editor and New run…. Hidden actions are absent from the DOM, without
placeholder spacing. Missing-source selections retain disabled New run….
Existing icons, classes, callbacks, source availability checks and terminal
eligibility are preserved. Sidebar + and empty-library registration remain.
Getting Started now names All simulations/sidebar + as registration entry points.
No backend, API, storage, recorded history or scientific execution changes.

## Validation

- Three focused frontend assertions passed: empty/populated All simulations,
  selected available simulation and missing source. They verify button absence,
  retained labels/icons, primary styling and correct disabled states. Bundled
  `frontend/overview-actions.test.mjs` with esbuild and ran it with Node.
- TypeScript, frontend build and 12 application-version tests passed. Existing
  Starlette/httpx deprecation warning only. Version/whitespace checks passed.
  Bundled CSS and all third-party notices/licenses unchanged.
- External wheel, sdist, rebuilt-from-sdist wheel and disposable installation
  passed. Direct/rebuilt wheel members byte-identical; installed assets/licenses
  match source. Python/CLI/API/OpenAPI/portal show 0.1.0.33. Offline startup/assets
  passed with sockets denied and Git/Node absent from PATH. Existing dependency
  environment reused read-only by the disposable environment.
- Installed Chromium at localhost:8793, initially empty disposable library under
  `/tmp/simshelf-93/`: All simulations offers Add simulation and disabled Terminal /
  editor, no New run…. Keyboard Enter opens registration; registering the supplied
  disposable main.py succeeds. Selected view shows only Terminal / editor and
  New run… in its header; sidebar + still opens the existing Add dialog (canceled).
- Terminal instructions retain the selected simulation ID/source folder. Tab from
  Terminal / editor reaches New run…; Enter opens the selected simulation's
  existing configuration, with final Start simulation disabled pending validation.
  Returning to All simulations removes New run… entirely; Tab from header Add
  simulation reaches Terminal / editor. No hidden action enters the focus order.
- Desktop 1280x900 Dark and narrow 390x844 Light screenshots inspected for both
  contexts: two adjacent buttons, no empty gap. Across all five themes at narrow
  width, both contexts have exactly two appropriate actions and no header/document
  overflow. Desktop selected-view labels/counts also checked in every theme.
  Existing run-table scrolling remains confined to its container. No captured
  browser console errors; viewport override reset.
- Database contains one explicitly registered simulation and zero runs; source
  bytes unchanged after checks. Evidence: `/tmp/simshelf-93/`, including
  `selected-desktop.png`, `all-desktop.png` and narrow Light captures.

## Limitations and owner checks

No validation failures. Linux/Chromium only; other OS/browser engines, physical
screen readers/touch and long scientific workloads untested. Missing-source
eligibility checked in frontend assertions, not a live moved-folder scenario.
Final launch/Stop and unrelated backend/scientific suites were not rerun: their
handlers and implementation are unchanged. Historical reports remain unchanged.

1. On All simulations, confirm Add simulation works and New run… is absent.
2. Select a simulation; confirm header Add simulation is absent and New run… opens
   configuration without starting. A missing source should still block launch.
3. Use sidebar + from the selected view, then cancel; check Terminal / editor
   instructions still refer to the correct simulation.
4. Tab through header actions and inspect desktop/narrow spacing in your theme.

Stop for owner review; no merge, issue closure, Done transition or release.
