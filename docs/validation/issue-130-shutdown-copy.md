# Issue #130 — concise shutdown page

Validated 2026-10-23 against accepted main `17f9f1d` (merged PR #129,
0.1.0.47). Issue #130 was the top and only Ready item; its existing linked
branch matched main and the working tree was clean. No open PR existed, and
the previous issue branch was already absent. Proposed build: **0.1.0.48**.

## Change

The acknowledged shutdown page now contains only:

> SimShelf is shutting down. You can close this tab.

One paragraph with `role="status"` replaces the heading and three explanatory
paragraphs. Existing layout/theme styling and normal text wrapping are retained.
The confirmation dialog and failed/lost-response handling are unchanged, as are
all backend shutdown, cancellation, final-capture, process and logging behavior.
The wording makes no claim of completed capture or stopped detached processes.
The production JS bundle is rebuilt; third-party notices and CSS are unchanged.

## Validation

- **17 Python tests passed**, no skips: `tests/test_shutdown.py` and
  `tests/test_application_version.py`, with `PYTHONPATH=src`, bytecode/cache
  disabled and disposable `/tmp/simshelf-130-tests` fixtures. Includes real idle
  and active shutdown, listener release, independent recorder survival, partial
  result capture, consent/idempotence and launch-versus-shutdown races. One
  existing Starlette/httpx deprecation warning.
- TypeScript typecheck, production build, both theme tests, version gate and
  diff whitespace checks passed.
- Installed production assets with controlled API responses: five explicit
  themes (Light, Dark, Onyx, Slate, Linen) at 1366×900 and 390×900. All ten cases
  had exactly the requested text, one status element, no headings and no
  horizontal overflow. Keyboard Enter confirmed shutdown. A 280×700 check
  showed normal wrapping; representative screenshots were visually inspected.
- A simulated lost POST response retained the existing error and terminal-check
  guidance, without displaying the acknowledged shutdown message. This fixture
  tests browser response handling, not actual process termination.
- A separate real installed CLI server with a fresh disposable library and
  Git/Node absent from PATH was quit through the browser. It exited with code 0;
  the settled browser contained only the exact requested message. The installed
  upper-right label reported 0.1.0.48 before shutdown.
- External wheel and sdist builds passed. A wheel rebuilt from the sdist has
  identical members and bytes. Packaged JS/CSS/licenses match the checkout.
  Installed Python/CLI/API/OpenAPI/static serving agree on 0.1.0.48 without
  Git/Node on PATH, using existing environment dependencies without modifying
  the application or scientific interpreter.

Temporary fixtures, packages and screenshots are under `/tmp/simshelf-130` and
`/tmp/simshelf-130-ui`; no user library or scientific data was used or altered.
Historical validation reports remain unchanged.

## Limits and owner checks

No test failures occurred. The first real browser observation was still awaiting
acknowledgement; the settled state and successful process exit were checked
separately. Validation covers Linux/Python 3.14 and Chromium, not other platforms,
browser engines, screen-reader software or a fresh OS. Network-disabled startup
was not independently enforced. No exhaustive suite was run for this copy-only
change. Existing shutdown limitations, including detached processes and slow
capture, remain applicable.

1. Start the updated app with a disposable library; choose Quit SimShelf, then
   confirm with Enter. Expect only the exact message above, with no heading or
   secondary text, and verify normal server exit in the launch terminal.
2. Repeat in a preferred theme and a narrow window; text should wrap normally.
3. If checking active shutdown, use a harmless disposable simulation and review
   its interrupted/capture status after restart. The page does not certify
   completed capture or termination of independent/detached processes.
