# Issue #83 — Disable simulation settings during activity

Prepared for owner review on 2026-10-19 from accepted `8d64b00ac309ce71356ae67fc34a170e26af6cfb`
(PR #86). #83 was the sole Ready issue; its existing dedicated branch matched
main with a clean tree. Predecessor PR #81 and previous PR #86 were verified
merged. The completed #84 branch was already absent locally/remotely.
Application version `0.1.0.29`; no release or storage migration.

## Implementation and boundaries

`simulation_activity.py` extracts the existing removal activity predicate without
changing it: anything other than completed/failed/interrupted, or capture_status
pending, blocks administration. `Store.simulations()` projects that predicate over
all of each simulation's runs in a read transaction. This does not use the
filtered/paged run list, assume portal ownership, or persist new data. Iteration
short-circuits at the first active row; idle history is scanned fully, without a
new index or JSON-extension requirement.

The API combines this read-only field with live portal supervisors. `portal.py`
adds the simulation ID to its existing in-memory job record, so the projection
covers admitted startup before a run ID exists and finalization until process
exit. The union of supervisor observations before/after the database read covers
changes during that read conservatively, without holding the lifecycle lock over
database/source I/O. A job that finishes during the query can keep settings
disabled until the following poll.
No execution, stop, archive, relocation, removal authorization or schema behavior
changes. Schema-1 removal still refuses the action; an enabled cogwheel is not a
promise that every administrative operation is eligible.

The existing cogwheel markup is factored into a small testable component. Its
native disabled attribute retains its position/icon/accessible name, uses the
existing disabled styling and omits the hover title while disabled. The click
handler and settings dialog workflows are unchanged. Missing-source recovery
remains separate. Already-open dialogs still rely on their existing server checks.

The frontend requires an explicitly false activity field from a current query.
Missing data and failed refreshes disable the control. Query changes invalidate
in-flight refreshes before paint, including A → B → A navigation. Sequence/query
guards reject older responses and errors before changing simulation eligibility.
Normal polling retains known state without blinking every three seconds. This is
periodic guidance, not a reservation: external runs can start after a snapshot,
and pending network requests may delay fresh knowledge. Backend guards remain
the authority for any later operation.

Changed areas: activity helper, Store/API/portal read projection, unchanged-predicate
extraction in simulation removal, frontend settings/types/refresh integration,
bundled JS, focused tests, architecture/user guidance and application version.
Historical reports, source snapshots, original source/output folders and user
workspaces were not changed.

## Validation

- Focused backend selection: **100 unique tests passed** across activity, simulation
  removal, relocation, portal and application version suites. Initial run: 97 pass,
  one test-fixture failure. After correction, all 14 activity cases passed; the final 16-case activity
  rerun also passed after adding two supervisor observation-race cases.
  Command used `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src …/python -m pytest -q
  -p no:cacheprovider` with an external `/tmp/simshelf-83/` basetemp. Existing
  Starlette/httpx deprecation warning only. HTTP/process tests ran outside the sandbox.
- New cases cover terminal-but-pending capture, unknown/nonterminal status,
  completed/failed/interrupted outcomes, absent legacy capture status, concurrent
  independent runs, capture-in-progress, unrelated idle simulations, an active
  run behind 1,001 newer records, pending/finalizing supervisors, and no mutation
  of logical database contents or schema-1 libraries.
- Focused frontend suite bundled with esbuild to `/tmp/simshelf-83/settings-tests.cjs`:
  **3 passed**. Existing dialog/safe dismissal and removal confirmation checks plus
  missing/stale/active eligibility, native disabled markup, accessible name,
  unchanged class and no disabled tooltip. TypeScript and bundled build passed.
- External wheel/sdist, wheel rebuilt from sdist and disposable installation
  passed. Direct/sdist wheel members matched byte-for-byte. Installed assets and
  licenses matched source; Python/CLI/API/OpenAPI/portal reported `0.1.0.29`.
  Offline startup/assets passed with outbound sockets denied and no Git/Node on PATH.
  The new test environment read dependencies from the previous disposable test
  environment; its candidate installation is separate and the old package untouched.
- Installed Linux Chromium: two independent context recorders disabled their own
  simulation's cogwheel; another idle simulation stayed enabled. Finishing one
  kept it disabled. Holding the last run in actual capture kept it disabled;
  releasing capture re-enabled it automatically on refresh without page reload.
- Completed-only filtering hid active runs without enabling settings. A held idle
  response released after a search/query change did not enable the active simulation;
  navigation away/back stayed disabled. The held response test does not establish
  every possible network ordering or remove the ordinary polling window.
- A controlled 503 response disabled the idle cogwheel; successful polling restored
  it. Pointer force-click did not open a disabled control. Tab skipped it; after
  re-enable, Enter opened the same dialog, Cancel restored focus. Missing-source
  Locate source folder opened its existing relocation review and canceled safely.
- All five themes at 1280×900 and 390×844: disabled opacity 0.5, no document
  horizontal overflow, long-title/cogwheel alignment retained. No CSS changes.
  Native disabled semantics are visible to browser accessibility inspection.
- Accepted-main version gate and whitespace checks passed; third-party notices
  unchanged. Fixtures, build logs and screenshots remain outside the checkout at
  `/tmp/simshelf-83/`. No user simulation was executed or altered.

## Failures and limitations

The concurrent-run test initially selected nested output folders and correctly
hit the existing overlap rejection. Giving both recorders sibling output folders
fixed the fixture; no product behavior was relaxed. A browser handle from the
previous turn was unavailable, so a fresh fixture tab was created. Attempting
keyboard press directly on the disabled button was rejected by automation; Tab
skip and later enabled Enter activation were checked instead. Rapid viewport/theme
captures sometimes caught earlier paint states; settled captures and the final
full desktop screenshot supersede those transient images.

Other operating systems/browsers, actual screen readers, physical touch devices,
large production libraries and long scientific jobs were not tested. Pending
portal startup/finalization is covered with controlled supervisor state in API
checks; browser lifecycle checks use real context recorders with controlled capture,
not every launch/cancellation failure. Existing portal process regression tests
passed. No exhaustive unrelated scientific/Git/backup suite was run. The complete
idle-history activity scan is not a scale benchmark or new cache/index design.

## Owner checks

1. Select simulation A and start a disposable run, including from your usual
   terminal/editor workflow. Its title cogwheel should remain visible but disabled
   after refresh; pointer and keyboard must not open it. Hide the run with search
   or a status filter and confirm it stays disabled.
2. While A runs, select idle B. Its cogwheel should work normally. Return to A,
   start a second run with an independent output folder, and finish only one;
   A must remain disabled until the last run and capture/finalization complete.
3. After completion/stop, wait for normal refresh without reloading. Settings
   should enable. Open/Cancel with keyboard and check focus; verify the separate
   missing-source Locate source folder recovery remains available.
4. Check long titles at desktop/narrow widths in your preferred themes and browser.
   Existing schema-1 removal refusal and server-side active-run checks still apply.

Stop for owner review. No merge, issue closure, Done transition or publication.
