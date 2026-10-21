# Issue #118 / PR #119 — two-level automatic Git participation

Date: 2026-10-21. Owner-requested revision after `e6f4f8b`, on the existing
issue branch and PR. Accepted base remains `40fa289509f99aad80d2d4dc3ac89663bb2b91e5`.
Application build remains **0.1.0.43**. Earlier dated reports are unchanged.

## Implemented model and decisions

The local SimShelf library remains always active. **Master Git Archive** is a
workspace navigation item outside simulations, with exactly one global ON/OFF
switch. Repository path and verified connection status are distinct information;
setup/disconnect are explicit actions, not additional activation switches.

Each simulation has one **Archive this simulation** switch above its tabs. It is
visible on the normal run-history page as well as Preservation settings. Advanced
settings configure scope only. First ON opens the existing review; cancellation
leaves OFF, and only backend confirmation persists ON. An unchanged, valid saved
policy resumes without another review. Disabled/stale/unavailable states are not
rendered as active Git preservation. Enter/Space and focus restoration work.

`preservation.status` is the effective gate for UI and recording start: global ON,
verified shared repository, individual participation and valid reviewed scope are
all required. Both legacy and format-2 paths use it. Toggle changes do not rewrite
frozen active-run plans or pending approved recovery operations. Ordinary capture
continues in all inactive/unavailable cases.

Global state is an additive metadata boolean, with absent/invalid state OFF.
Existing libraries therefore need explicit global ON once; individual consent
and history remain intact. Format-2 uses its existing policy enabled field. Legacy
OFF atomically retains the exact consent under a paused-settings key and clears
the old active key; ON revalidates and restores that same scope. Explicit adoption
alone can expand legacy consent. Paused current settings join existing relocation
and removal handling. Backups retain both preferences; restored/moved libraries
still require verified identity/location and policy review. No schema migration.
Older binaries do not implement this global gate; downgrade behavior is not a
promise of this UI. Explicit later additions/retries retain their existing review
semantics; global OFF governs new automatic run preservation.

## Automated checks

- Focused source coverage: archive state matrix, preservation, legacy archive,
  relocation, simulation removal, capture/backup and application-version tests.
  The final results are recorded below. Fixtures and pytest base directories are
  external to the checkout; source imports use `PYTHONPATH=src`.
- New state tests cover all four ON/OFF combinations, newly registered OFF,
  unavailable/disconnected/replaced identity, global OFF retaining connection and
  consent, OFF→ON exact resumption, cancel/rejected confirmation, strict API
  booleans and token enforcement, stale-policy refusal, nested actual Git bytes,
  legacy no-expansion, frozen plans, backup restore and paused-consent lifecycle.
- Focused frontend: **35 passed** (archive 13, preservation 8, source Git 3,
  outputs 7, screenshots 4). Assertions include exactly one switch at each scope,
  global-OFF saved participation, truthful unavailable states, no connection switch
  or duplicate enablement control, and retained legacy wording.
- TypeScript and frontend bundle build passed. Distributed JS/CSS were rebuilt;
  third-party notices are unchanged. Version gate and diff checks are below.

## Packaged application and real browser

Built an external sdist → wheel, installed into an isolated target, and launched
that installed package with a disposable library on localhost. Browser work did
not run a development server or mutate an owner library/archive. Installation
uses existing runtime dependencies; no fresh dependency-resolution claim.

Actual installed-browser checks:

- Global OFF + connected repository stays OFF. Global ON preserves a new
  simulation's OFF preference. Saved ON participation is disabled while global
  OFF and clearly says local library only; restoring global ON restores its scope.
- First participation ON opens one scope review with eligible captured sources,
  recursive JSON/CSV/log defaults, existing copy/reference/ignore rules, bounds
  and process-stream exclusion. The switch stays OFF while review/confirmation
  is pending. Cancel keeps OFF and returns focus. Confirmation becomes ON and
  survives reload. OFF is immediate; ON resumes unchanged policy without review.
- Disconnection retains global and individual preferences and displays Git
  unavailable. Global ON while disconnected opens setup, focuses the repository
  field, and requires explicit connection confirmation. Cancel setup retains OFF
  and returns focus to the global switch. Reconnection restores only saved scope.
- Legacy alpha pauses/resumes with no format-2 policy or expanded output scope.
  Advanced legacy review canceled at narrow width returns focus to its own review
  button and leaves the old consent unchanged.
- Exactly one participation switch exists in advanced settings. The only option
  checkboxes are captured-source inclusion and process-stream inclusion.
- Desktop 1280×900 and narrow 390×844 inspected in System (resolved dark), Light,
  Dark, Onyx, Slate and Linen. Global page inspected in all desktop themes;
  participation inspected in all narrow themes, plus desktop and narrow global
  OFF/unavailable states. No horizontal document overflow (375 px content inside
  390 px viewport). Narrow participation panel ends around y=630, above tabs.
- Space/Enter activation, review heading focus, Cancel/Confirm return focus,
  global setup focus and advanced-review return focus were inspected. No
  screen-reader or native-mobile certification is claimed.

Screenshots and executable fixture scripts are local temporary evidence under
`/tmp/simshelf119-twolevel/`, not repository or release assets.

## Actual installed archival evidence

The installed recorder used the policies confirmed through the browser:

1. With global OFF and beta participation saved ON, one run captured **4 nested
   outputs locally**, added no Git event, and left archive HEAD unchanged.
2. With global ON, B/A/B runs shared one repository with distinct simulation/run
   paths and three separate commits. Both beta events contained **2 source files
   and 4 nested outputs** (JSON, CSV, log); alpha retained **2 legacy sources**.
3. Independent `git ls-tree` / `git cat-file` inspection verified exact manifest
   paths, counts, byte sizes and SHA-256 hashes, alongside verified library/Git
   downloads. The browser showed **4 of 4 copied outputs**, 2 source files, and
   verified scope for beta. It did not attribute the earlier global-OFF run to Git.
4. Original legacy consent and the pre-existing committed record hash remained
   unchanged after toggles, review cancellation, new commits and retrieval.

Disposable commits: beta `295b6cf780acea32e990b4357f952c158c665ae4`, alpha
`c75bc8be3b9fa67267c56ead036101bab28cc5c6`, beta
`7a7e07f8eace7dd62f148fd338ca3faa7bd37306`. These are fixture commits, not release
or owner archive commits. No scientific sources or SWSS fixtures were modified.

## Failures, skips and limits

Initial checks exposed stale expected connection-status strings, fixtures that
had not explicitly enabled the new global gate, a new-test capture-count key
mistake, and a SQL placeholder mismatch when adding paused consent to relocation.
Those were corrected and checked again. A removal-specific fixture initially used
schema 1; it now explicitly prepares its disposable schema-2 prerequisite. No
runtime migration was added. One first test invocation referenced a nonexistent
backup test filename and ran no tests; the actual capture/backup module was used.

The existing Starlette/httpx deprecation warning remains. The standalone external
scalar-decay test is skipped because its pinned reference path was not supplied;
local disposable recursive-output fixtures provide the scope's real recording
checks. No external scientific workload, production library, cross-platform
locking, native mobile, Firefox/Safari, screen reader or scientific certification
is claimed. Unrelated exhaustive suites were not run.

## Owner checks

1. Open global Master Git Archive. Verify one switch, independent repository
   status/location, and clear always-active local-library wording.
2. Open a new simulation. Find its one participation switch immediately above
   tabs. Switch ON, cancel the review, then ON and confirm. Reload and verify ON.
3. Switch global OFF: connection and saved individual ON must remain, while its
   switch is disabled and new runs capture locally only. Global ON restores only
   saved participants; a new simulation remains OFF.
4. Toggle an existing participant OFF/ON without re-reviewing unchanged scope.
   Inspect legacy scope without adopting new defaults. Disconnect a disposable
   repository and verify truthful unavailable status and normal local capture.
5. Record nested JSON/CSV/log fixture outputs, inspect actual Git files/counts,
   and retrieve an earlier revision after another simulation commits. Check the
   preferred theme, keyboard navigation and a narrow window.

Stop at owner review of PR #119. No merge, release, remote push functionality,
issue closure or Project Done transition is authorized.

## Final results and package identity

- Final focused source command: `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider --basetemp /tmp/simshelf119-twolevel/accepted-source tests/test_archive_participation.py tests/test_preservation.py tests/test_git_archive.py tests/test_relocation.py tests/test_simulation_removal.py tests/test_capture_backup.py tests/test_application_version.py` — **132 passed, 1 skipped, 1 warning**, 19.43 s.
- Final installed-wheel state/preservation tests: **28 passed, 1 skipped, 1 warning**,
  8.66 s, from `/tmp` with `PYTHONPATH` pointing only at the isolated installed target.
- External sdist → wheel build/install passed. Changed backend modules and static
  index/JS/CSS match working-source bytes; metadata and installed imports report
  **0.1.0.43**. Final installed server restart retained global ON, beta ON and
  connected identity; reload and keyboard order passed. Browser console was clean.
- `python scripts/application_version.py --base-ref origin/main` passed after fresh
  fetch: candidate .43, accepted .42. TypeScript, bundle and `git diff --check` passed.
- Final wheel SHA-256: `9ccb47f377e880daebdd9d3785021965d26a344ee91a7968d729661f3694bf45`.
- Final sdist SHA-256: `e835d330319c4f6044bb6d2348dc02d3d789b440a9e566ff07a1445839b34e05`.

The validation packages precede this final results entry; they are test artifacts,
not a release. Final screenshots: `final-global.png`, `final-simulation.png`,
`narrow-global.png`, `narrow-global-off.png`, `narrow-unavailable.png` and the six
`desktop-{theme}.png` / `narrow-{theme}.png` pairs in the external evidence folder.
The disposable server was stopped after verification. No owner data was changed.
