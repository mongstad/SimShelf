# Issue #12 explicit shutdown

2026-10-17. Pending owner review; no merge or release claimed.
Accepted main: `febea30a80fa6e6fe54f0ff63d3dd07d09c9fb5f` (PR #22).
Issue #12 was the only Ready item on the SimShelf Project board. Its existing
branch matched clean local/remote main; no open PR existed. #5/PR #8 was verified
merged and an ancestor. PR #22 was merged; its issue branch was already removed.
Historical reports and user workspaces were preserved.

## Implementation and decisions

Sidebar Quit opens confirmation with the current owned-recorder count, including
startup/capture. Cancel receives initial keyboard focus. Explicit stop-and-quit
cancels only server-owned supervisors using their existing pipes; CLI/editor
recorders remain independent. Success stops browser polling and explains that
shutdown is requested, with partial/slow capture and detached-process limits.
Closing/reloading a tab never triggers shutdown.

The actual CLI Uvicorn instance receives an exit callback after acknowledgement.
Custom hosts without that callback show an unsupported-mode explanation. The API
requires loopback access and existing token/origin safeguards. Launch-generation
consent and admission share the supervisor lock; stale confirmation is rejected,
in-flight validation cannot bypass shutdown, and repeated quit is idempotent.
The existing bounded wait, signal escalation, journal and capture paths remain.
The CLI reserves its listen socket before opening a browser and gives actionable
port-collision guidance. No PID-kill API, new recorder lifecycle, migration,
installation, automatic restart or scientific-data modification is introduced.
Application build advances from 0.1.0.2 to 0.1.0.3 under the existing policy.

## Validation

- Focused Python: 39 passed across `tests/test_shutdown.py`, `tests/test_portal.py`
  and `tests/test_application_version.py`. Real Linux subprocess cases cover idle
  and active Quit, actual port reuse, a SIGTERM-ignoring portal child, interrupted
  state and retained partial output, an independent terminal recorder surviving,
  and occupied-port guidance. API/unit cases cover tokens, foreign origins/peers,
  unsupported hosts, explicit/stale consent, concurrent duplicate Quit, blocked
  launches, in-flight validation, pending startup and bounded capture timeout.
  Existing supervisor tests cover normal stop, concurrent launch ownership,
  server death, descendant cleanup and recovery. The existing Starlette/httpx
  deprecation warning remains.
- TypeScript check and production frontend build passed. Full dependency notices
  are unchanged; generated abbreviated legal comments retain all entries, reordered
  by the changed module import order.
- Headless Chromium source browser checks passed: close/reopen/refresh leaves a
  real portal run active; Cancel is focused and preserves the run; confirmation
  reports one owned recorder; stop-and-quit releases the port and retains partial
  output; restart shows interrupted; idle Quit releases the port again. Desktop
  1280x900 and narrow 390x844 screenshots were inspected, with no dialog overflow
  or browser page errors. Test sources, workspaces and screenshots remain in
  disposable `/tmp/simshelf12-*` folders, outside the checkout.

- Wheel and sdist builds passed, including wheel construction from the sdist.
  Metadata, bundled assets/licenses and required source files were verified.
  The installed wheel passed the same complete browser workflow with Git and Node
  absent from the server PATH, including the 0.1.0.3 portal label and real port
  release. Python/installed metadata/CLI/OpenAPI versions agree. App creation
  passed with outbound socket connections blocked. Application-version policy
  check against freshly fetched `origin/main` passed.

Reproduction: use the external development Python with `PYTHONPATH=src` and
`PYTHONDONTWRITEBYTECODE=1`; run `-m pytest tests/test_shutdown.py
 tests/test_portal.py tests/test_application_version.py -q -p no:cacheprovider`
with `--basetemp` outside the checkout. Run `pnpm run typecheck`, `pnpm run build`
and `python scripts/application_version.py --base-ref origin/main`. Build from
an external source copy as described in README. Browser harness and inspected
screenshots are external development artifacts; the owner steps below reproduce
its product workflows without Playwright.

## Failures encountered

The initial frontend tool invocation lacked Node on PATH; rerunning with the
bundled Node path passed. The first Python pass had 36 passes and two fixture
teardown failures: the independent test child also ignored SIGTERM. Restricting
that behavior to the portal child fixed cleanup without changing application
behavior. An added in-flight-validation regression brought the final count to 39.
The expected Playwright browser binary was absent; an isolated Chromium download
under `/tmp` supplied it (Playwright uses its Ubuntu fallback on this Linux host).
Browser validation initially found that native dialog opening overrode Cancel's
autofocus. Explicit focus after dialog opening fixed it; the full scenario passed.

## Owner checks

1. Start with `./start.sh --workspace /absolute/path/to/a/disposable-library` and
   register a harmless script that writes partial output and sleeps. Launch it
   from the portal, close/reopen the tab and refresh: the same run stays active.
2. Choose Quit SimShelf. Confirm the active count, Cancel focus and independent
   recorder explanation. Cancel and verify both server and run continue.
3. Open Quit again and choose Stop runs and quit. Confirm shutdown feedback and
   that the launcher exits. Restart on the same port; inspect interrupted status,
   stdout/stderr, source snapshot and retained partial files/capture status.
4. With no owned runs, Quit server and restart on the same port. While a server
   is running, launch another on that port: check actionable guidance and that
   the original server remains available.
5. Optionally record a harmless independent CLI/editor run into a distinct output
   folder. Quit the portal and verify the independent run continues; stop it
   explicitly from its original process when finished.
6. From two tabs, open confirmation then launch another run in the other tab.
   The old confirmation must request renewed review, without stopping that run.

## Limits

Linux and headless Chromium only; other OS/browser engines, GPU workloads and
long-duration/high-volume capture are untested. Slow capture timeout is simulated;
real kernel uninterruptible I/O and detached scientific processes are not exercised.
Shutdown acknowledgement is not proof all processes/capture completed. Existing
supervisors may continue capture after the server's 15-second shared wait. Custom
ASGI/service hosting requires shutdown through its owner. No release is published.

## Owner wording revision

2026-10-17: confirmation buttons now read **Cancel** and **Stop runs and quit**
for both active and idle servers. Cancel still dismisses the dialog without
stopping anything; confirmation retains the existing shutdown behavior. Version
remains 0.1.0.3. Earlier review-time wording above is preserved as history.
TypeScript and production build passed. The source Chromium workflow passed again
with the new labels, including Cancel focus and run preservation, active and idle
Quit, actual port reuse, tab reopening, interrupted records and partial output.
No backend changes; Python/package checks were not repeated for this wording-only
revision. Updated browser fixtures/screenshots are external under
`/tmp/simshelf12-wording`.
