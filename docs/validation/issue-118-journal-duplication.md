# Issue #118 — journal duplication regression

Validated 2026-10-21 for the existing PR #119, after owner testing of `ad60e8b`.
Build remains **0.1.0.43**; accepted main is
`40fa289509f99aad80d2d4dc3ac89663bb2b91e5` (0.1.0.42).
Earlier validation reports remain unchanged historical evidence.

## Confirmed cause and before evidence

The actual installed `ad60e8b` wheel reproduced the owner's defect with an
external disposable library containing alpha and beta. Open alpha → **Source
Git**, then allow the normal three-second journal refresh to continue. The page
grew from one participation control/navigation bar to **5**, then **27** of each,
without further interaction. The new development-mode full-App harness also
reproduced the conflicting ON/active and OFF/loading copies immediately.

`PreservationSettings` and `GitHistory` were siblings in the same journal fragment
with the identical `${simulation.id}:${simulation.root}` React key. Reconciliation
could not preserve their distinct identities across refreshes. The development
build reported “Encountered two children with the same key”; the production build
showed no console warning. This was a sibling-identity defect, not recursion,
duplicated source markup, CSS, or a backend participation disagreement.

An audited replay recorded **622 HTTP requests, all GET**. Preservation GETs in
successive 15-second buckets grew from 61 to 75, 125 and 175 (the last partial
bucket contained 129). Repeated mounts/pollers amplified read traffic. During a
separate unchanged-state observation of the multiplying page, the complete
logical SQLite dump, all 16 existing retained evidence-file hashes and Git refs
were unchanged. No archival commit, policy mutation or scientific run was caused
by merely rendering or polling the defective page.

## Focused correction

- Give the two sibling keys distinct `preservation:` and `source-git:` prefixes,
  retaining the existing simulation/root reset boundary.
- Show a disabled dash with **Checking archive status…** before status is known,
  instead of presenting OFF/Local library only as a confirmed result. Request
  failure displays unavailable, never green active. Confirmed participation and
  effective activity continue to come from the existing backend response.
- Invalidate outstanding preservation status reads when the component unmounts;
  the existing sequence guard and interval cleanup remain in place.
- Add full-App live-DOM browser regressions, one focused static loading assertion,
  an external harness build helper, this report, and the rebuilt distributed JS.

Runtime edits are limited to `frontend/main.tsx`, `PreservationSettings.tsx` and
`GitArchive.tsx`. No CSS masking, reload workaround, rendering limit, backend
change, consent expansion, archive/data-structure change, version bump or new
activation control is introduced. Shared toggle styling and the global/individual
hierarchy are unchanged. CSS and third-party notices are byte-identical.

## Automated checks

- **11 full-App browser scenarios passed**, in real Chromium with controlled
  API responses and timers. The first test failed against the original app with
  duplicated controls and React's duplicate-key diagnostic. The corrected tests
  mount the real `main.tsx`, not a reconstructed component tree. They cover:
  one control/nav under repeated polling; all four tabs retaining the same DOM
  node; exactly one mutation per OFF/ON; first review cancellation and focus;
  explicit save acknowledgement; delayed success and failure after newer status;
  loading/departed-simulation responses; 20 A/B switches without accumulated
  intervals/window listeners; global OFF/unavailable hierarchy; unexpected
  writes/requests; and a real document reload with saved participation.
- **36 existing/focused frontend tests passed**: archive 13, preservation 9,
  Source Git 3, outputs 7 and screenshots 4.
- **40 Python tests passed, 1 skipped, 1 warning** in 8.55 seconds:
  `tests/test_archive_participation.py`, `tests/test_preservation.py`,
  `tests/test_application_version.py`, using `PYTHONPATH=src`, no pytest cache and
  `/tmp/simshelf119-regression/source-tests` for all fixtures.
- TypeScript `--noEmit`, `frontend/build.mjs`, `git diff --check` and the
  `scripts/application_version.py --base-ref origin/main` gate passed.
- External sdist → wheel build/install passed. Packaged JS, CSS, HTML and backend
  modules matched checkout bytes; the installed module and metadata reported
  0.1.0.43. Real-backend browser checks below used that installed wheel.

To rerun the full-App harness from the checkout (installed Node/dependencies):

```sh
node scripts/test_journal_browser.mjs /tmp/simshelf-journal-tests
python -m http.server 8762 --bind 127.0.0.1 --directory /tmp/simshelf-journal-tests
```

Open `http://127.0.0.1:8762/` in a real browser and click **Run journal regression
tests**. It performs a deliberate document reload for the final scenario and
prints **11 passed; 0 failed**. The harness controls fetch/timers only on this
separate test page and is not an application entry point. It cannot contact a
real archive API. Its synthetic state persists only in browser storage for this
test origin. Real Git/history safety is verified separately below.

## Installed-app browser and data checks

All work used `/tmp/simshelf119-regression/browser`, not an owner library. Alpha
had a legacy-consented archived run; beta had a completed locally captured run
before its first preservation review. The original reproduction used alpha's
existing archived history. The corrected page was checked with both histories.

- **48 combinations**: Runs, Version history, Source Git and Preservation settings
  × System, Light, Dark, Onyx, Slate, Linen × desktop 1280px and narrow 390×844.
  Each had exactly one participation control and one navigation bar, with no
  document-level horizontal overflow. Narrow tabs keep the established internal
  horizontal scrolling. Screenshots of all twelve theme/width combinations were
  visually inspected. Additional final desktop evidence is 1280×900.
- Legacy OFF via Space and ON via Enter retained scope and returned focus to the
  same toggle. First beta ON opened review with all eligible sources, recursive
  CSV/JSON/log defaults and existing copy rules. Cancel returned focus to the
  toggle and left the **complete logical database dump unchanged**. Tab moved to
  Runs. Explicit confirmation alone enabled participation; reload and reselection
  showed the saved ON/active state with one control/nav.
- Global OFF kept repository Connected and the individual ON preference disabled,
  showing Local library only plus its reason across all four tabs. Global ON
  restored activity. Explicitly disconnecting only the disposable binding showed
  ON/preference plus **Git unavailable**, without green active. Reconnecting the
  same repository restored activity without new consent or history changes.
- Twenty additional real-backend A/B navigations through Source Git retained one
  control/nav. A final idle minute made exactly 20 preservation GETs for only the
  selected simulation (median interval 3.0 seconds), with no accumulated controls.
  Browser console had no warnings/errors and audited HTTP responses had no errors.
- Exactly **9 deliberate POSTs** were observed: alpha participation OFF/ON (2),
  beta preview/cancel and preview/confirm (2 previews, 1 save), global OFF/ON (2),
  disconnect (1), reconnect (1). No duplicate POST or archive publication occurred.
  All original Git refs and retained evidence hashes matched; every non-metadata
  SQLite table was unchanged. The archive still contained the original one
  commit. Only the reviewed metadata preferences/binding changed as requested.

Before/after screenshots, the 48-row matrix, original/final harness output,
request audits, data comparison and build/test logs are retained externally at
`/tmp/simshelf119-regression/`. Principal screenshots: `before.png`, `after.png`,
`narrow-unavailable.png`, `narrow-disabled.png`, `narrow-global-off.png` and
`desktop-{theme}.png`/`narrow-{theme}.png`. They show disposable paths only and are
local review artifacts, not distributed application data.

Candidate wheel SHA-256:
`230c2bc9e22851dfda19403bd0645a1ac2c231700e234821e0a272a16b3b6335`.
Candidate sdist SHA-256:
`0f3b4ec572ce7bfdf7f3405016d6a91fc60f4497629055a14374d930d7c567f9`.
These are validation artifacts, not releases; they were built before this report
was added. Runtime assets are the verified final bytes.

## Failures, limits and owner checks

The original-build browser failure is intentional red-test evidence. During
harness development its reload check initially raced controlled timer startup;
an explicit timer tick made initialization deterministic. The final harness ran
all scenarios from a fresh page. The first narrow-viewport attempt applied the
override to another test tab; width assertions caught it, and all 24 narrow
combinations were rerun at verified 390px. Neither is hidden as a successful check.
The separate static harness server also logged an incidental missing favicon
(404); the installed application API audit had no HTTP errors.

The external pinned scalar-decay test was skipped because no reference path was
supplied. The existing Starlette/httpx deprecation warning remains. Validation is
Linux/Chromium only; no Firefox, Safari, native mobile, screen-reader certification
or production-library testing is claimed. This frontend-only correction does not
repeat all earlier backend/packaging/scientific checks; those historical results
remain in their original reports.

Owner verification before merge:

1. Open a simulation with history → Source Git. Leave it open for at least 30
   seconds, then alternate all four tabs and two simulations repeatedly. Confirm
   one Archive this simulation switch and one simulation navigation bar throughout.
2. In a disposable library, cancel first participation review; verify it stays
   OFF. Confirm a reviewed scope, reload/reselect, then disable/resume it. Confirm
   one control, accurate status, keyboard focus and unchanged historical commits.
3. Turn global OFF/ON and disconnect/reconnect the disposable repository. Check
   retained individual preferences and distinct connected versus effective state.
4. Check the preferred theme and narrow layout. Run the full-App harness above.

Return PR #119 for owner review. No merge, release, publication, new issue/PR,
Done transition, SWSS change or scientific-simulation modification is authorized.
