# Issue #54 — Adjacent run navigation

Prepared for owner review on 2026-10-18. Base: accepted `522999b` (PR #75).
Application version: `0.1.0.23`; no release or storage migration.

## Implementation and decisions

- Previous/Next beside Back to runs; semantic buttons, visible existing focus
  styling, wrapping layout, disabled boundaries, no wrapping between runs.
- Capture the visible loaded list's IDs when opening a table/gallery item,
  retaining filters/search and restricting navigation to that simulation.
  Newest-first timestamp order uses ascending ID for ties. Previous is earlier
  in the displayed sequence (newer); Next is later (older).
- Polling and new runs cannot shift the captured sequence. External removal
  produces the existing unavailable message with navigation still available.
  Removal in this portal filters the sequence and returns to the simulation list.
- Back scopes the list to the opened simulation and preserves filters/view.
  Reload/direct-link/new-launch fallback is explicitly labelled: up to the
  newest 1,000 runs in that simulation, without filters. A direct-linked run
  outside that window is viewable with adjacent navigation disabled. Returning
  to the list/reopening refreshes the sequence.
- Key RunDetails by run ID to reset notes drafts, source/log selections, image
  state, archive filters/selections and nested async state. Late fallback-list
  responses are guarded on navigation. The navigation stays mounted for focus;
  reaching a disabled boundary transfers focus to Back.
- Backend, stored records, capture, Git, source/output data and schemas unchanged.
  Only frontend, rebuilt assets/notices, version and current documentation change.

## Validation

- Four focused frontend checks passed: mixed simulations/filtered sequence,
  immutable snapshot and deduplication, equal timestamps/year boundary ordering,
  empty/single/missing/removed IDs, semantic controls/boundaries/order guidance.
  Bundled with esbuild and executed directly with Node (the `node --test` wrapper
  reported one bundled file; direct execution reported all four named tests).
- TypeScript and frontend build passed. Generated React legal notices changed
  ordering only; full third-party licenses remain bundled.
- Application-version tests: **12 passed**, with the existing Starlette/httpx
  deprecation warning. Version gate and whitespace check passed.
- Fresh external isolated sdist, wheel from sdist, direct wheel and installation:
  matching wheel contents/metadata, packaged JS/CSS/licenses; Python/CLI/API/
  OpenAPI version `0.1.0.23`. Offline TestClient startup with socket connections
  denied and Git/Node absent from PATH passed. No scientific environment changed.
- Installed Chromium fixture: Alpha with three runs (two equal timestamps), Beta
  with two runs, and an empty simulation. Records have distinct source snapshots,
  notes, parameters, copied images/results and per-run archive commits.
- Open from All simulations: Alpha traverses 3 → 1 → 2 with disabled boundaries;
  Beta traverses only Beta. Search for one Alpha run disables both directions.
  Back selects Alpha; reload uses the labelled same-simulation fallback. Gallery
  navigation and Back retain gallery view; empty history remains usable.
- Keyboard Enter activates navigation; focus moves to Back when Next disables.
  An unsaved old note draft does not appear on the next run. Files filter resets;
  snapshot IDs, source text, notes, image IDs, archive commits and download URLs
  correspond to the newly selected run. Distinct historical source/CSV download
  bytes were verified through the installed API.
- Concurrent disposable Beta addition did not move the captured newest boundary.
  External removal of the viewed Beta run showed unavailable; Previous recovered
  to the surviving Beta run, and Back showed the new addition.
- All five themes (Dark, Light, Onyx, Slate, Linen): installed navigation and
  screenshots at **1280×900** and **390×844**, including keyboard activation.
  Navigation stays usable; the existing narrow detail-tab row scrolls horizontally.
  Screenshots are local evidence under `/tmp/simshelf-54-package/`.

## Failures and limitations

Initial no-isolation builds failed because the development environment lacks
setuptools; no wheel existed for the subsequent install attempt. Repeated with
isolated build dependencies and fresh wheel installation successfully. Initial
browser opening preceded server startup and got connection refused; reopened
after startup. The fresh runtime environment lacked the optional TestClient
HTTP dependency; installing `httpx2` only in that disposable environment allowed
the offline smoke check to pass. Browser harness selectors for Notes, heading level and Gallery
needed correction to the supported DOM role selectors; subsequent checks passed.

Linux/Chromium only; other operating systems/browsers, physical assistive
technology, very large histories and deliberately delayed network responses were
not exercised. Direct fallback is bounded to 1,000 runs; loaded-list navigation
is bounded to the list the user loaded. Equal timestamps are ordered within that
loaded set; API pagination itself is unchanged. Unsaved detail drafts are reset
on navigation, matching Back behavior; save before moving. Deleted frozen entries
are shown as unavailable rather than silently skipped. No unrelated exhaustive
backend/scientific suite was run for this presentation-only change.

## Owner verification

1. Open a simulation with three or more runs from All simulations. Use Previous
   and Next through both boundaries; confirm only that simulation appears.
2. Search/filter the list, open a result, browse and use Back. Check the expected
   filtered sequence, simulation destination and table/gallery choice.
3. Inspect Notes, Source, Screenshots, Parameters and Files on adjacent runs with
   different content. Download a workspace copy and a historical Git revision;
   verify they belong to the selected run. Save drafts before navigating.
4. Reload a detail URL and check the labelled newest-first fallback. Add a run
   elsewhere while browsing; Back/reopen should refresh the sequence.
5. Check keyboard focus, narrow layout and your preferred theme. If testing
   removal, use a disposable backed-up library; confirm unavailable-run recovery.

Stop for owner review; no merge, issue closure, Done transition or publication.
