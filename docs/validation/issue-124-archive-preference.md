# Issue #124 — compact archive status and independent preference

Validated 2026-10-22 against accepted main
`5914a8e9d32f73cc4c2f4610a10de52401b1317a` (0.1.0.44, merged PR #123).
Proposed build: **0.1.0.45**. Issue #124 was the first and only Ready board item;
its existing linked branch matched main and the tree was clean. Previous issue
branches were already absent. Historical reports are unchanged.

## Cause and change

The simulation header disabled its switch whenever `global_enabled` was false.
Backend save/resume checks also rejected ON while the master was OFF, despite
already storing the two preferences independently. Three regressions against an
external copy of the unchanged backend reproduced those refusals: initial reviewed
save, format-2 resume and legacy resume.

The header now uses the same compact row for every state. A participating
simulation with master OFF has a filled amber ON switch and **Master Git Archive
disabled**, matching the owner-approved issue reference. Effective activity uses
the existing active treatment; OFF, unconfigured, unavailable, review-required,
loading and request-error states remain distinct and never falsely claim activity.
The switch describes its status through `aria-describedby`; native switch
semantics, ON/OFF text, warning/check glyphs and keyboard focus complement color.
Repeated explanatory paragraphs and the routine toggle-success sentence are
removed; detailed guidance remains in the user documentation.

Saving or resuming an explicitly reviewed preference no longer requires master
ON. Repository identity, source location, capture binding and scope validation
remain mandatory for ON. First-time participation still requires preview and
confirmation; unreviewed/stale/unavailable scope cannot bypass those checks. OFF
does not require Git. Legacy scope is resumed exactly, without conversion.

The effective-state gate in `git_archive.prepare` is unchanged: a run starting
while the master is OFF creates no automatic archive event, regardless of the
saved simulation preference. **Existing frozen plans and separately approved
pending operations retain their established behavior**; toggling is not
retroactive cancellation or historical rewriting. No storage schema, source,
scientific execution, capture rules or archive architecture changes are made.

## Automated evidence

- **79 source Python tests passed, no skips**, one existing Starlette/httpx
  deprecation warning, in 19.55 seconds: `test_archive_participation.py`,
  `test_preservation.py`, `test_git_archive.py`, `test_application_version.py`.
  Used `PYTHONPATH=src`, disabled bytecode/cache and external pytest roots.
  The pinned reference was explicitly supplied with
  `SIMSHELF_AUDIT_DECAY_REFERENCE`.
- **28 installed-wheel tests passed**, no skips, the same warning, in 4.45
  seconds: archive participation and application version suites. Installed into
  an external target using existing interpreter dependencies; fixtures were in a
  separate sibling directory outside the installed application's root.
- **30 frontend tests passed**: preservation, archive, Source Git and themes.
  TSX tests were bundled externally to CommonJS; the theme test ran as native
  ESM. TypeScript `--noEmit`, the production bundle, version gate and diff checks
  passed. Distributed JS/CSS were rebuilt; third-party notices are unchanged.
- **11 full-App browser regression scenarios passed**, including one control
  across tab/poll cycles, single writes, explicit consent/cancel, focus restoration,
  stale response ordering, loading, repeated navigation, all four master/preference
  combinations, and actual document reload. The existing harness was extended to
  toggle OFF/ON while master OFF and assert no extra explanatory paragraph.

Backend coverage launches real disposable simulations for the four-state matrix
and preference transitions. New runs while master OFF still capture locally and
have no Git events; repository HEAD does not move. Reopened stores retain the
preferences. Master ON restores a saved ON choice and leaves a saved OFF choice
off. Historical execution records, events and source bytes remain unchanged for
both format-2 and legacy policies. Missing-Git coverage confirms OFF succeeds,
ON remains refused until validation is possible, and preference writes create no
Git refs. Existing frozen-plan, backup/restore and location-invalidation tests pass.

## Installed UI and package checks

Used only `/tmp/simshelf-124-ui` fixtures: two simulations, one historical run,
one pre-existing archive event and a local disposable repository. In the actual
installed app:

- Space and Enter changed preferences with master OFF; reload retained OFF.
- Re-enabling the master preserved OFF independently and restored saved ON.
- First-time participation while master OFF opened the existing review and
  required explicit confirmation; no run or archive was created by the action.
- Light, Dark, Onyx, Slate and Linen were checked at 1366×900 and 390×900 for
  active/amber status, keyboard focus, wrapping and page overflow. At narrow
  widths the same row wraps naturally. Native table/tab scrolling is unchanged.
- Restart with Git and Node absent from PATH retained a saved ON preference and
  displayed **Git unavailable**. OFF remained usable. The production browser
  console had no errors during the checked interactions.
- The historical run, events, archive HEAD, simulation records and capture
  settings were compared with the initial fixture snapshot and were unchanged.

Wheel and sdist were built outside the checkout using isolated build dependencies.
A wheel rebuilt from the extracted sdist has the same members and identical member
bytes. Packaged assets match source. Python/CLI/API/OpenAPI and the installed UI
report 0.1.0.45. Runtime startup works without Git/Node on PATH; optional Git
functionality truthfully reports unavailable. No packages were published.

Screenshots and raw logs are temporary local evidence under `/tmp/simshelf-124`.
The shipped regression sources and this report are the durable review evidence.

## Failures and limits

The restricted sandbox stalled the initial TestClient run; it was interrupted and
the focused suite completed outside that sandbox. An initial run omitted the
reference path and skipped one integration; the final 79-test run supplied it.
The new missing-Git test initially assumed an empty repository had HEAD; checking
its refs instead corrected the fixture assumption, then all tests passed.

The first frontend invocation incorrectly bundled an `import.meta.url` theme
test as CommonJS; running that file as native ESM corrected the runner. Its old
selector-count assertion also rejected the already-existing color-only archive
status overrides. The test now checks that component theme overrides are actually
color-only instead of counting selectors. All 30 tests pass. The full-App harness
reported 11 passes but emitted React `act` warnings around its document-reload
tail; these are not presented as a clean harness-console result. The installed
production UI was checked separately and had no console errors.

Coverage is focused Linux/Python 3.14 and Chromium using existing environment
dependencies, not a fresh OS installation or exhaustive suite. Windows/macOS and
screen-reader software were not exercised. Repository loss, source mutation or
other external changes can still occur after a status response; the existing
backend checks remain authoritative. No user library or historical evidence was
migrated, relabeled or rewritten.

## Owner checks

1. In a disposable library, connect a local master archive and review participation
   for a test simulation. Turn the master OFF: confirm amber ON and the single
   concise disabled status, with the simulation switch still keyboard-accessible.
2. Turn the simulation OFF, reload/restart, then enable the master. Confirm it
   stays OFF. Repeat with a saved ON preference and confirm active status returns.
3. With master OFF, review first-time participation for another test simulation.
   Cancel once, then explicitly confirm. Confirm no archive commit occurs merely
   from changing preferences; a new run while master OFF captures only locally.
4. Temporarily remove Git from the test server's PATH and restart. Confirm truthful
   unavailable status and that ON can be turned OFF. Restore Git and review any
   invalid scope before enabling. Inspect earlier runs, outputs and Git history.
5. Check preferred theme, narrow layout and keyboard focus. Already-running runs
   retain their frozen plans; use a newly started run when checking master OFF.

One issue/PR only; stop for owner review without merge, release or publication.
