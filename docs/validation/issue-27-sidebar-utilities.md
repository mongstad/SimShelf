# Issue #27 — Sidebar utility actions

Validated on 2026-10-17 on Linux. Pending owner review; no merge or release claimed.

## Scope and accepted base

The SimShelf Project's first and only Ready item was #27. Its existing dedicated
branch `27-ux-add-quit-icon-and-subtly-emphasize-sidebar-utility-actions` was clean
and identical to accepted main `f2e4333` (including shutdown PR #25, screenshot
PR #30 and migration-policy PR #29). No open PR existed. PR #30 was verified
merged; its issue #24 branch was already absent. Fetch pruned the deleted #28
remote tracking reference without changing historical evidence.

`frontend/main.tsx` adds a power glyph through the existing 18px, 1.6-stroke icon
renderer, with visible text and decorative SVG semantics. Both utility buttons
reuse their existing callbacks, order and disabled state. `frontend/style.css`
raises their resting text/icon contrast, uses a neutral Quit hover/focus treatment
and a restrained teal Backup treatment. Disabled buttons retain reduced opacity
and no hover fill. At narrow widths, reduced padding/gap and nonshrinking icons
allow labels to wrap. Appearance and local-workspace markup/styles are unchanged.
No backend, dialog, lifecycle, storage, dependency or scientific-data changes.

The application version gate proposes `0.1.0.6` from accepted `0.1.0.5`.
Bundled JS/CSS are regenerated; license notices are byte-identical to main.

## Validation

- `pnpm run typecheck` and `pnpm run build`: passed using the bundled Node runtime
  explicitly on PATH. Initial attempts failed because the shell lacked Node;
  no application failure was involved.
- Dedicated Python, `PYTHONPATH=src`, `-B -m pytest -q -p no:cacheprovider`, external
  basetemp, `tests/test_application_version.py tests/test_shutdown.py
  tests/test_capture_backup.py`: **24 passed**. One existing Starlette/httpx
  deprecation warning. These include shutdown safeguards and backup/capture
  behavior; no new tests that merely mirror the visual implementation were added.
- Browser source checks: Dark/Light at 1280x900, Light at 390x844 and Dark at
  320x740. Matching 18px icons, aligned desktop columns, visible neutral/teal
  keyboard focus, correct tab order, readable wrapped labels, no horizontal
  overflow at either narrow width. Pointer and keyboard activation retain the
  existing action. Quit opens the unchanged confirmation with Cancel focused;
  Cancel and Escape return without shutdown. Backup downloads a ZIP (ZIP integrity
  checked). Explicit Quit confirmation shuts down the disposable server, exit 0.
- Installed wheel browser checks: both themes at 390x844; version label, icons,
  keyboard sequence, Quit confirmation and Cancel. No browser warning/error logs.
- Packaging in `/tmp/simshelf27-package`: wheel and sdist built, then another wheel
  built from extracted sdist. Both wheels report `0.1.0.6` and contain every static
  asset byte-for-byte. Initial non-isolated build failed because setuptools was
  absent; standard isolated builds passed. The disposable installed environment
  initially lacked FastAPI (a nested venv does not inherit the parent venv's
  packages); installing declared runtime dependencies there resolved this.
- Installed Python/CLI, workspace API, OpenAPI and HTML/JS/CSS/license endpoints
  passed with Git/Node absent from PATH and outbound socket connections denied
  in the test process. CLI ran with the same minimal PATH. Packaging dependency
  installation used network access; offline checks were performed afterward.
- Application version check against freshly fetched `origin/main`, whitespace
  check, changed-file review and notice comparison passed before handoff.

Local screenshots (disposable evidence, not shipped application assets):
`/tmp/simshelf27-dark-desktop.png`, `/tmp/simshelf27-light-desktop.png`,
`/tmp/simshelf27-light-narrow.png`, `/tmp/simshelf27-dark-320.png`,
`/tmp/simshelf27-installed-dark.png`, `/tmp/simshelf27-installed-light.png`.

## Limits and owner verification

Linux and the in-app Chromium browser only. No screen-reader, other browser/OS,
long-session or large-library validation. The transient Preparing backup disabled
state was reviewed in code rather than held for a browser screenshot. Active-run
shutdown was covered by existing focused tests, not a new scientific browser run.
All browser fixtures were empty disposable libraries; existing user data was not
opened or modified. Historical validation reports remain unchanged.

1. Start the branch against a disposable library, reload and verify Local · 0.1.0.6.
2. In Dark and Light, inspect Quit and Backup at desktop and 390px/320px widths.
   Confirm consistent icon alignment, legibility, restrained hover colors and no
   displacement of Appearance/local-workspace indicators beyond existing layout.
3. Tab through Quit, Backup and Appearance; inspect focus. Enter on Quit should
   open the existing confirmation with Cancel focused. Try Cancel and Escape;
   both leave the server available.
4. Back up the disposable library and inspect its downloaded archive. With no
   valuable work running, explicitly confirm Quit and verify the server stops.
5. Before merge, fetch accepted main and rerun
   `python scripts/application_version.py --base-ref origin/main`.
