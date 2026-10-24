# Issue #135 — Idle Quit and active-work confirmation

Validated on October 24, 2026, on Linux with Python 3.14 and in-app Chromium.
Accepted base: `b8acbe2007de870228aaeff7e85da81064ee4091` (PR #138).
Proposed application version: `0.1.0.53` from accepted `0.1.0.52`.

## Behavior and scope

Quit now checks `/api/server` before showing a dialog. An idle response sends
`confirmed: true`, its reviewed generation and **`stop_runs: false`** directly
to the existing shutdown endpoint. A closing response uses the accepted concise
shutdown page. Active supervisors produce “Stop N active runs and quit SimShelf?”
with Cancel focused. The dialog has an explicit accessible name. Enter on Cancel
and Escape dismiss it and restore focus to Quit; explicit confirmation sends the
reviewed generation and active-work consent. Busy requests prevent dismissal.

A rejected idle request never retries with cancellation consent. It shows the
error and refreshes authoritative state for a new explicit review. Failed status
requests offer Retry; lost shutdown responses retain uncertainty and terminal
recovery guidance. Unavailable launch modes disable shutdown. Successful feedback
is shown only after an accepted response or authoritative `closing` status.

The supervisor count, admission lock, generation guard, cancellation pipes,
final capture, listener shutdown, process ownership and backend implementation
are unchanged. No scientific code, stored records, schema, archive contracts or
historical reports are modified.

## Validation

- `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 .../environments/SimShelf/bin/python
  -m pytest -q -p no:cacheprovider --basetemp /tmp/simshelf-135-tests-unrestricted
  tests/test_shutdown.py tests/test_portal.py tests/test_application_version.py`:
  **39 passed**, one existing Starlette TestClient deprecation warning.
- Final shutdown-only rerun after retaining both stale-consent variants:
  **5 passed**, same warning. Real disposable servers cover idle shutdown,
  active cancellation with retained partial output/final capture, listener
  release, independent CLI recorder survival, stale idle and active consent,
  and fresh active state without cancellation consent. Existing supervisor
  tests cover pending startup/final-capture ownership and admission races.
- `node node_modules/typescript/bin/tsc --noEmit` and
  `node frontend/build.mjs`: passed; distributed JS rebuilt, notices retained.
  Node was absent from the shell PATH; the bundled runtime was used.
- Full-App browser fixture `frontend/quit.browser.test.mjs`, bundled with
  esbuild outside the checkout: idle one-click shutdown; active count/plural;
  Cancel/Enter/Escape; focus restoration; explicit confirmation; idle-to-active
  rejection followed by review; connection loss; status failure/Retry;
  unavailable shutdown. Request logs confirmed idle `stop_runs: false` and
  reviewed active `stop_runs: true`. No browser warning/error logs observed.
- System, Light, Dark, Onyx, Slate and Linen: desktop and 390 × 844 checks
  confirmed Cancel focus, dialog labeling and bounded layout without horizontal
  dialog overflow. System-theme screenshots were visually inspected:
  [desktop](../images/issue-135/active-desktop.png),
  [narrow](../images/issue-135/active-narrow.png).
- Browser checks initially exposed focus loss on dismissal and a rejected idle
  request; both were corrected and the affected workflows rechecked.

## Packaging and environment notes

Wheel and sdist were built from an external source copy, then a second wheel
was built from the extracted sdist. Source Python/static bytes matched the wheel;
rebuilt-wheel package bytes matched. Installed import, CLI, workspace/OpenAPI
version and static serving checks passed with an empty PATH (no Git or Node).
The installed CLI served a fresh empty library; Chromium showed `0.1.0.53`,
one click produced concise shutdown feedback without a modal, and the server
exited with status 0. [Installed shutdown](../images/issue-135/installed-idle-shutdown.png).
Startup was local, but network isolation was not separately enforced. Build and installation artifacts remain
under `/tmp/simshelf-135-package` and are not published.

The sandboxed Python TestClient run stalled without output; the focused suite
passed outside the sandbox. The initial isolated package build could not reach
the registry under network restrictions; the authorized external build passed.
A first dependency-free disposable install lacked FastAPI; declared dependencies
were then installed only into that disposable environment.

## Owner verification

1. Install the issue wheel into a disposable environment and start a new empty
   library. Select Quit once: no modal; concise shutdown feedback; listener exits.
2. Start a trusted disposable long-running script with partial output. Select
   Quit: confirm the active count and Cancel focus. Press Enter or Escape:
   the server/run continue and focus returns to Quit.
3. Select Quit again and explicitly choose Stop runs and quit. Verify interrupted
   run status, attempted final capture, retained output/logs and listener exit.
4. In a second browser, start a run between the first client's idle check and
   shutdown request: cancellation must be rejected until explicitly reviewed.
5. Check the dialog in your preferred theme and narrow window. Keep independent
   backups when exercising real scientific work; use disposable fixtures here.

## Limits

Browser error/race/theme checks use controlled fetch fixtures; real-server tests
exercise the actual lifecycle separately. Windows, macOS, other browser engines,
screen readers, GPU/scientific workloads, detached sessions and uninterruptible
capture were not validated. Shutdown acknowledgement is not proof that every
external process or slow final capture has completed. No release is published.
