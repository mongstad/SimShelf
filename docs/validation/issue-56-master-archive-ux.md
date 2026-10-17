# Issue #56 — master archive Stage A

Validated on Linux, 2026-10-17, against accepted main
`cfd2b889cb41cb57444f58fe9fb4fa0035258ea8` (PR #50).
Owner explicitly approved Stage A after reviewing the architecture/design proposal.
Proposed application build: **0.1.0.15**, from accepted **0.1.0.14**.

## Scope and decisions

- Keep independent workspace storage, bare archive, source Git and scientific
  records. No migration, manifest-format change, notes export or remote operation.
- Master archive status has a green check/text and directly available Disconnect;
  initialization remains collapsed when connected. Per-simulation consent has its
  own Enabled / Disabled / Review required status.
- Source Git status and path appear immediately below its own heading, above its
  discovery/connection controls. Its observations remain inside that section.
- One Run files inventory matches workspace artifacts by ID, size and hash; it
  never deduplicates by filename or collapses separate archive events. Workspace
  download is primary; exact Git revision is available in row details when both
  stores hold it. Missing workspace copies can use explicitly labeled Git downloads.
- Existing archive-addition selection, review, confirmation, idempotency and retry
  remain. References/skips, filename/policy filters and capture summary remain.
- A matching source snapshot offers the existing Source preview; no source-export
  endpoint was added. Notes explain their workspace-only preservation.
- Read-only status projections reuse existing repository validation and start-time
  consent comparisons. Download-time ownership/hash checks remain authoritative.

Changed implementation: `frontend/GitArchive.tsx`, `GitHistory.tsx`, `main.tsx`,
`types.ts`, `style.css`; additive status responses in `git_archive.py` and `api.py`;
focused tests; packaged JS/CSS; authoritative application version. Updated the
archive guide and architecture; added the approved design and this evidence.
Third-party notices remain byte-for-byte unchanged.

## Automated checks

**74 distinct backend tests passed.** Initial focused invocation ran archive,
source provenance, file selection and application version tests: 73 passed. The
final archive invocation after adding the API availability case passed 23 tests,
including that one additional case. Existing tests cover A/B/A isolation, exact
historical downloads, immutable execution records, independent source Git index,
failed/interrupted recording, bounds, recovery/idempotency and backup/reconnection.

New backend checks cover:

- Connected/disconnected/unavailable projections and per-simulation consent.
- Changed selection, repository identity, moved-library binding and Git missing.
- New filenames matching existing intent do not invalidate consent solely because
  inventory revision changes.
- Projection calls do not change metadata, scientific records or repository files.
- API reload/reconnect, Git download refusal while disconnected and working
  workspace-copy download independently of source Git.

**18 frontend tests passed:** archive 9, source Git 3, file selection 6. These
exercise conservative row matching, preserved same-name revisions, removed/missing
workspace items, wrong/disconnected archive, explicit download routes, source
snapshot matching, selection eligibility, filters and connected-state labels.
TypeScript checking, frontend build and `git diff --check` passed.

Tests use disposable external paths. No owner library or research files were used.
The existing Starlette/httpx deprecation warning remains; it is not a test failure.
An initial combined Node test-runner invocation summarized bundled files rather
than individual cases; each bundle was then executed directly to obtain the exact
9/3/6 case totals. A few exploratory searches used nonexistent guessed filenames;
correct files were located with `rg --files`, without modifying data.

## Installed package and browser

Built wheel and sdist externally, then built another wheel from the extracted
sdist. Verified version metadata and exact bundled static bytes. Installed the
wheel into an external venv using existing development dependencies via a local
`.pth` entry (not a fresh dependency-resolution certification). Python version,
CLI, workspace API, OpenAPI and bundled asset/license routes passed with Git and
Node absent from PATH and socket connections denied. Runtime assets require no CDN.

Used the installed wheel with a disposable two-simulation library and real local
archive on localhost. Browser checks verified:

- Master connected with automatic Enabled and Disabled; master disconnected with
  Disabled or retained consent requiring review; source Git disconnected/connected
  independently. A newly initialized source repository without HEAD reports its
  limitation; after a test-only source commit, its history becomes available.
- A missing archive path never shows success. Explicit reconnection restores the
  original repository, and reload keeps associations. Creating source Git changes
  the location-bound selection binding and correctly requires consent review.
- Keyboard Enter for consent/addition review and Cancel; cancellation leaves event
  count unchanged. Explicit confirmation adds one event. Two separate manually
  attached same-name CSV revisions remain separate after archival and reload.
- Workspace CSV downloaded while both Git connections were disconnected. Exact
  Git CSV downloaded after later commits still contains `Alpha result 1`, not
  the later source-folder result. Download links remain scoped to event/entry.
- Source preview navigation resolves the matching original source bytes.
- No browser console warnings or errors were recorded in the final checked session.
- Light, Dark, Onyx, Slate and Linen: settings and final Files views at 1280×900
  and 390×900. Screenshot inspection and DOM widths showed no horizontal overflow;
  narrow rows stack, paths/hashes wrap and controls remain visible. Green master
  status uses text/check as well as color, with dark/light palette colors.
- Accessible section/row/action names inspected through browser accessibility
  snapshots; keyboard focus outline observed. Physical screen-reader behavior was
  not tested.

Temporary screenshots: `/tmp/simshelf56-settings-{theme}-{width}.png` and
`/tmp/simshelf56-files-{theme}-{width}.png`. These are local test evidence, not
research images or repository assets. Browser download waiting was slow once;
subsequent explicit historical-link download completed and bytes were checked.

## Limits and owner verification

Status is a point-in-time hint, not a scan of every historical object's integrity.
Repository checks retain existing bounded layout inspection; source consent checks
retain bounded inventory limits. Maximum-size archive performance, other operating
systems/browser engines, long-running simulations and physical assistive hardware
were not certified. No real VB_Phi_Field/Wavez workload was executed for this UX-only
change. Existing source text preview remains bounded to 1 MiB. Portable annotations
and manifests remain proposed only; #49 remote publishing is untouched.

Owner checks:

1. Open a simulation's Git history. Confirm green master connection/path and
   separate automatic status. Confirm Source Git status is immediately under its
   own heading, even if it is disconnected while the master is connected.
2. Open a run with a CSV present in both stores. Confirm one row with both labels;
   download the workspace copy, expand Revision details, and download its Git copy.
3. Compare separate same-name historical revisions. Advance the archive with a
   different run and confirm earlier downloads remain unchanged.
4. Disconnect only the master archive. Workspace downloads must still work;
   Git-only download actions become unavailable with an explanation. Reconnect the
   original archive explicitly, reload and confirm access returns.
5. Attach a small file. Select its row, review, cancel and verify no new event.
   Review again and explicitly confirm; check the new event and unchanged run status.
6. Review automatic consent after changes, and try narrow windows plus preferred
   themes. Confirm Notes clearly remains workspace-only and existing Screenshots,
   Source, file-selection and separately reviewed ignore actions remain available.

Stop at owner review: no merge, release, migration or other issue implementation.
