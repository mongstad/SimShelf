# Issue #128 — effective Master Git Archive status

Validated 2026-10-23 against accepted main
`83dd35d03ada033fa4d91a7130eb32592b89d42b` (merged PR #126, build 0.1.0.46).
Proposed build: **0.1.0.47**. Issue #128 was the top and only Ready item;
its existing issue-linked branch matched main, with a clean tree and no open PRs.
Related #124 / PR #125 was merged. Previous completed branches were already
absent locally and remotely; fetching confirmed main was synchronized.

## Change and boundaries

The master switch now describes effective availability in one compact row:
neutral **Git archiving disabled** whenever OFF, green **Git active** only when
ON and the repository is connected, and warning **Git unavailable** when ON but
unusable. Loading, mutation/refresh pending, and failed status reads do not claim
confirmed activity or an OFF preference. The switch references the status text
through `aria-describedby`; existing responsive layout and semantic colors are
reused without CSS changes.

Repository health, reason, configured/remembered path, and refresh action are
inside **Repository location and setup**. Pending repository checks are distinct
from failed checks. Redundant top-level paragraphs are removed; setup safety and
backup guidance remain. Late departed status reads are ignored.

Only frontend presentation/request-state handling, regression tests, the bundled
JS and application version change. Git operations, backend endpoints, saved
simulation preferences, explicit consent, capture, scientific records, archive
history and storage schemas are unchanged. Status remains an observation, not a
reservation or proof that a particular run's evidence was archived.

## Validation

- **28 Python tests passed**, no skips: `test_archive_participation.py` and
  `test_application_version.py`, using `PYTHONPATH=src`, no bytecode/pytest cache,
  external `/tmp` fixtures. These include real disposable runs across the global
  and individual preference matrix, retained historical bytes/refs, restart,
  unavailable Git, frozen plans and backup behavior. One existing Starlette/httpx
  deprecation warning was emitted.
- **32 frontend tests passed**: archive (15), preservation (12), Source Git (3)
  and themes (2). TSX suites were bundled to external CommonJS and run directly
  with Node; themes ran as native ESM. New assertions cover OFF precedence across
  repository states, green only for ON/connected, pending/error states, status
  placement within setup, and initial unknown switch presentation.
- **12 full-App Chromium browser scenarios passed** using
  `node scripts/test_journal_browser.mjs /tmp/simshelf-128/journal`. The added
  scenario covers both preferences × connected/disconnected/invalid/unavailable,
  deferred refresh, failed refresh plus failed recovery, successful retry,
  path retention, collapsed setup, and switch/status accessibility association.
  Existing scenarios cover consent, focus, single writes, polling/navigation,
  stale responses and real document reload. The added matrix performs only reads;
  existing mutation-count assertions still pass.
- TypeScript `--noEmit`, production build, accepted-main version gate and
  `git diff --check` passed. Bundled JS was rebuilt; CSS and license notices did
  not change.
- Wheel and sdist built in an external disposable copy. A wheel rebuilt from the
  extracted sdist has identical member names and bytes. Packaged JS/CSS/license
  files match the checkout. Installed Python, CLI, `/api/workspace`, OpenAPI and
  static serving agree on 0.1.0.47 with Git/Node absent from PATH. Dependencies
  came from the existing development environment; no application/scientific
  environment was modified.

## Installed browser checks

A new library and empty dedicated archive under `/tmp/simshelf-128-ui` were used.
Space enabled the master; Enter disabled it; reload retained OFF. Setup opened
with Enter, kept its configured path, and exposed separate connected health.
Restart with Git/Node absent retained ON and displayed **Git unavailable**;
turning OFF then displayed **Git archiving disabled** despite unavailable Git.
The installed production browser reported no console errors during these checks.

Light, Dark, Onyx, Slate and Linen were checked at 1366×900 and 390×900 for OFF,
active and unavailable states: 30 theme/viewport/state combinations, with no
horizontal document overflow. Expanded connected setup was also checked across
the ten theme/viewport combinations. Representative screenshots were visually
inspected for compact layout, wrapping, readable text and keyboard focus.
Temporary screenshots and package evidence are under `/tmp/simshelf-128`.

## Failures and limitations

Initial frontend commands failed because Node was absent from shell PATH; using
the bundled runtime resolved this without installing dependencies. The sandbox
refused a localhost server socket; the same disposable server ran with approved
execution outside that sandbox. An initial browser tab opened before the server
was available; a new tab successfully loaded the running server.

The new toggle assertion initially checked before the asynchronous POST-followed-
by-GET settled; an additional React flush corrected the test timing. The final
12 scenarios pass. The first installed archive fixture was inside the application
boundary and was correctly refused; moving fixtures to a separate sibling `/tmp`
directory resolved setup without relaxing the boundary.

Coverage is focused Linux/Python 3.14 and Chromium. No Windows/macOS, other browser
engines, screen-reader software, fresh OS install or exhaustive suite was tested.
Network-disabled startup was not independently enforced; the runtime checks used
local requests with existing dependencies and no Git/Node on PATH. Repository
health can change after a response; existing backend checks remain authoritative.
No user library, scientific source/output or historical report was altered.

## Owner verification

1. In a disposable library with a connected archive, open Master Git Archive.
   With OFF, confirm neutral **Git archiving disabled**; expand setup to inspect
   **Repository — Connected**, the retained path and refresh control.
2. Use Space/Enter to turn ON/OFF. Confirm green **Git active** only when ON and
   connected, and confirm the chosen state survives reload/server restart.
3. Restart the test server without Git, retaining ON. Confirm **Git unavailable**;
   turn OFF and confirm **Git archiving disabled** while setup remains unavailable.
   Restore Git and refresh before enabling again.
4. Check preferred themes and a narrow window, keyboard focus and disclosure.
   Confirm individual simulation preferences and earlier runs/archive history
   remain unchanged. Use a newly started disposable run for an OFF behavior check;
   already-running runs retain their frozen plans.
