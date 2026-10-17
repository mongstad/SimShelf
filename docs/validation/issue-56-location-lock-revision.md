# Issue #56 — connected location lock and remembered directory

PR #57 Stage A owner revision, 2026-10-18. Version remains **0.1.0.15** against
accepted main `cfd2b889cb41cb57444f58fe9fb4fa0035258ea8` / 0.1.0.14.
Earlier validation reports remain unchanged historical evidence.

## Implementation

- Connected setup shows the backend path read-only, with initialization and
  confirmation disabled. Active paths are labeled verified only after backend
  availability checks. Failed proposed paths never become active UI paths.
- The backend rejects any connection request while a connection record exists,
  before directory initialization or other repository changes. Explicit disconnect
  is also required for an unavailable configured archive; its switch remains
  operable and its status clearly says unavailable rather than connected.
- Existing metadata stores only the last successful path, repository identity
  and library binding. Active connection and remembered preference are committed
  atomically under the existing workspace lock. Disconnect preserves the preference;
  failed attempts preserve both prior values. No storage schema migration occurs.
- Disconnected setup distinguishes remembered from edited/proposed paths. Reload
  and restart retain the preference but never connect automatically. Both quick
  and manual reconnection at the remembered path verify original identity;
  initialization over that remembered repository is refused.
- Saved automatic consent, frozen run plans, scientific records, archive events,
  source files, managed copies and historical associations remain independent.
  Restored library bindings still require deliberate disconnect/remapping.

Changed runtime: `frontend/GitArchive.tsx`, `src/simshelf/git_archive.py`,
`src/simshelf/api.py`, rebuilt `app.js`. Existing theme CSS is reused. Tests and
archive/architecture guides were updated; third-party notices unchanged.

## Focused validation

**43 backend tests passed**: archive 31 and application version 12, using checkout
`PYTHONPATH=src`, `PYTHONDONTWRITEBYTECODE=1`, `python -B -m pytest -q
-p no:cacheprovider tests/test_git_archive.py tests/test_application_version.py`
and external disposable `--basetemp`. New tests cover direct API replacement and
initialization rejection, explicit disconnect before a new location, old-library
preference creation, unchanged schema, restart reads, replaced identity rejection
through manual and quick paths, and real SQLite rollback if the second metadata
write fails. Existing tests cover missing paths, failed writes, running-plan and
other-simulation isolation, historical Git downloads, independent managed downloads,
and backup/restore remapping. Restore tests now explicitly disconnect before remap.

**12 archive frontend tests passed**, bundled for Node/CommonJS. Added unavailable
configured-state/disconnectability coverage. Actual read-only input behavior and
disabled confirmation were checked in the browser. TypeScript, frontend build,
diff checks and accepted-main version gate passed.

External wheel, sdist and sdist-derived wheel builds verified metadata and exact
static assets. Installed Python/CLI/API/OpenAPI/assets/license smoke passed with
Git/Node absent from PATH and socket connections denied. Existing development
dependencies were reused via `.pth`; not a fresh dependency-resolution test.
The existing Starlette/httpx deprecation warning remains. No unresolved test failure.

## Installed browser

Disposable two-simulation library and bare archive; no owner research data used.

- Connected field exposes read-only semantics, remains unchanged after typing,
  and can receive keyboard focus for inspection. Initialize and Confirm are disabled.
- Master OFF preserves the path. Actual server restart plus browser reload leaves
  OFF and repopulates the remembered directory when setup is expanded.
- Editing to a missing directory and confirming fails; the UI labels it proposed,
  preserves the original remembered path, and never shows connected success.
- Replacing the fixture archive identity rejects quick reconnect after restart,
  retaining OFF and returning focus to the master switch. Restoring the original
  identity permits explicit reconnection and locks the verified field again.
- Dark, Light, Onyx, Slate and Linen at 1280×900 and 390×900: expanded connected
  settings inspected, read-only field and disabled confirmation verified in each,
  no document horizontal overflow, paths remain inspectable and focus visible.
- Historical Git and managed-copy download behavior is verified by the backend/API
  regression suite; no new download or publication implementation was introduced.

Temporary fixture screenshots: `/tmp/simshelf56-location-{theme}-{width}.png`;
final connected proof `/tmp/simshelf56-location-final.png`.

## Owner checks and limits

1. Expand Archive location and setup while connected. Verify read-only verified
   path, disabled initialization/confirmation and instruction to disconnect first.
2. Switch OFF, reload and restart. Verify OFF remains and the last successful path
   returns as remembered, editable, and not currently verified/connected.
3. Try a missing path or replaced disposable repository: connection must fail,
   remain OFF and preserve the remembered original. Restore the original and
   reconnect explicitly; verify historical downloads and unchanged consent.
4. To choose a different archive, disconnect first and explicitly confirm setup.
   Check a second simulation and a disposable running simulation remain intact.
5. Check keyboard navigation and preferred themes at narrow width.

Linux/Chromium only; no physical screen-reader, real scientific workload, maximum
archive or long-run performance certification. External Git repositories remain
outside workspace backups. Older builds ignore the additional metadata preference;
this revision does not change supported workspace schemas. Stage B is untouched.

Stop for owner review; no merge, release or unrelated issue work.
