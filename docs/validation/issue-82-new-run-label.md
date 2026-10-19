# Issue #82 — New run entry point

Prepared for owner review on 2026-10-19. Accepted base `07bf255` (PR #88),
application version `0.1.0.31`. The sole Ready issue used its existing clean
branch at accepted main. PR #88 is merged and its branch cleanup was already
complete. No additional predecessor work is required by this label-only issue.

## Change

The overview primary button now reads exactly **New run…**, including its
accessible name. The same enabled/disabled conditions, tooltip and click handler
open the existing configuration dialog. Its **Start simulation** confirmation,
execution behavior and separate **Stop run** control are unchanged. Updated
current Getting Started, Running, Parameter Discovery and Progress guide entry
points while preserving final-start instructions and all historical reports.
Rebuilt bundled JS and advanced the application version; CSS/licenses unchanged.

## Validation

- TypeScript `tsc --noEmit`, frontend build, 12 application-version tests, version
  gate and whitespace checks passed. Existing Starlette/httpx deprecation warning.
  No new unit test for a literal caption; direct installed-browser checks cover it.
- External direct wheel, sdist and wheel rebuilt from sdist passed. Direct/rebuilt
  wheel members match byte-for-byte; installed static assets/licenses match source.
  Python/CLI/API/OpenAPI and portal label show 0.1.0.31. Offline startup/assets
  passed with socket connections denied and Git/Node absent from PATH. Disposable
  runtime reused read-only existing test dependencies, without modifying them.
- Installed Chromium on localhost:8782, fresh disposable simulation/library under
  `/tmp/simshelf-82/`: All simulations shows disabled New run…; selecting the
  simulation enables it. Keyboard Enter opens the same Start a simulation dialog
  and focuses Close. Interpreter, arguments and output-policy controls remain.
  Before confirmation, database run count was zero and the fixture execution
  marker did not exist: opening did not start a process.
- Selected `/usr/bin/python`, validated interpreter/paths, then explicitly clicked
  Start simulation. Run details showed Running and Stop run. Stop produced
  Interrupted, exit -15 and complete capture inspection. Reopened via keyboard
  at narrow width and closed without starting; database still contains exactly
  one run. The fixture marker confirms execution only after the explicit launch.
- All five themes (Dark, Light, Onyx, Slate, Linen) checked for the button caption
  at desktop 1280x900 and narrow 390x844. Narrow button geometry stayed 83x36px
  with no document horizontal overflow. Desktop screenshots visually inspected;
  narrow layout visually inspected in Dark/Linen, geometry checked in all themes.
  Early rapid theme captures caught CSS transitions; settled desktop captures
  supersede them. Existing table overflow remains confined to its own scroller.
  No captured browser console errors. Viewport override reset.
- Local screenshots and disposable package evidence: `/tmp/simshelf-82/`;
  `overview-final.png` shows the final Dark overview.

## Limitations

No failed validation. Cleanup signals found the fixture server already absent;
the session log confirmed completed application shutdown. Other OS/browser engines, physical screen readers/touch,
long scientific workloads and the full execution matrix were not rerun. No
backend, storage or scientific behavior changed; this is not new execution
certification. Historical screenshots/reports retain their original labels.

## Owner checks

1. Select a simulation and confirm New run… opens configuration without starting.
2. Close it; confirm no new run. Reopen with Enter and check the accessible name.
3. With a disposable script, validate then explicitly Start simulation; inspect
   run details and Stop run separately.
4. Check your preferred theme and narrow window for comfortable button layout.

Stop for owner review; no merge, issue closure, Done transition or release.
