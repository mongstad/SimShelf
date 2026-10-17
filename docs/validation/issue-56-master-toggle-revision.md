# Issue #56 — master connection toggle revision

PR #57 Stage A, validated 2026-10-18 on Linux. Proposed version remains
**0.1.0.15** against accepted main `cfd2b889cb41cb57444f58fe9fb4fa0035258ea8`
(0.1.0.14). Earlier Stage A and automatic-toggle reports remain unchanged.

## Change and boundary

One master connection switch now sits beside the green connected status, above
the configured path and separately named per-simulation automatic switch. It
reuses the same styling, role, checked state, live status and focus restoration.
The normal view has no separate Connect/Disconnect buttons. Explicit initialization
and location confirmation remain under collapsed Archive location and setup.

OFF uses the unchanged disconnect endpoint; ON uses the existing connect operation.
The current panel remembers the prior connection only in memory. After leaving or
reloading a disconnected panel, ON opens setup if that identity is unavailable.
No new stored preference or startup reconnection was introduced. Initialization
always requires deliberate setup, never the switch alone.

The existing connect operation gained an optional expected-connection guard under
its existing workspace lock. Quick reconnection rejects changed path, repository
identity, library binding, conflicting current connection, unavailable Git and
initialization. Explicit advanced setup retains existing validation/consent.
This small backend guard is needed because ordinary setup intentionally permits
choosing a different archive; a quick switch must not silently do that.

Saved per-simulation consent is not changed by master connection actions. Exact
original reconnection can restore its availability; changed settings or another
archive still require review. Scientific records, frozen plans, managed copies,
repository format, publication/recovery, backup and storage schema are unchanged.

Runtime files: `frontend/GitArchive.tsx`, `src/simshelf/api.py`,
`src/simshelf/git_archive.py`, rebuilt `app.js`. Existing CSS is reused. Focused
tests and archive documentation were updated; third-party notices are unchanged.

## Automated and package checks

- **40 focused backend tests passed:** archive 28 and application version 12.
  Command: `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python -B -m pytest -q
  -p no:cacheprovider tests/test_git_archive.py tests/test_application_version.py`
  with external disposable `--basetemp` and the dedicated development interpreter.
- New regression checks cover disconnect/reconnect, persisted state after Store
  reopen, preserved consent for both simulations, frozen active-run plans,
  unavailable Git downloads versus available workspace copies, successful old
  Git downloads after reconnect, identity replacement, missing path, changed
  library binding, forbidden implicit initialization, conflicting connections,
  and failed connection writes retaining the previous state.
- **11 archive frontend tests passed**, bundled with esbuild for Node/CommonJS.
  Render checks verify named independent switches, authoritative checked state,
  green success only when connected, busy/unavailable behavior and absent old
  actions. Interaction checks were performed in the browser below.
- TypeScript, frontend build, diff check and accepted-main version gate passed.
- External wheel/sdist/sdist-derived-wheel builds verified metadata and packaged
  static bytes. External installed runtime checks passed Python/CLI/API/OpenAPI,
  assets and license routes with Git/Node absent from PATH and socket connections
  denied. Existing development dependencies were reused via `.pth`, not freshly
  resolved. No owner workspace or research data was used.

Initial test invocation mistakenly imported the older installed development
package (8 failures); explicitly selecting checkout `src` corrected that setup.
A new test initially read artifacts from the summary-only run view (1 failure);
it now reads artifacts from the detailed view and independently compares immutable
records. An initial ESM test bundle failed on React's dynamic `require`; CommonJS
resolved the harness issue. Final tests pass. The existing Starlette/httpx
deprecation warning remains.

## Actual installed-browser checks

Used a disposable two-simulation library with existing run/archive history.

- Space disconnects, Enter reconnects the remembered original. Pending requests
  retain prior checked state and disable controls; confirmed results restore focus
  to the master switch. Connected path remains directly below the master status.
- A temporarily missing fixture repository and a changed identity both reject
  ON, retain OFF, show an error and return keyboard focus. Original fixture bytes
  were restored after each check.
- Actual server restart and browser reload while disconnected retain OFF without
  reconnecting. ON opens setup and focuses the directory input when no remembered
  identity remains.
- Explicitly initialized a new empty disposable directory through setup. Master
  became connected while automatic consent remained review-required. Explicitly
  choosing the original repository restored only the existing matching consent.
- Dark, Light, Onyx, Slate and Linen checked at 1280×900 and 390×900 for connected
  and disconnected states. Width measurements show no horizontal overflow;
  switches wrap at narrow widths, paths wrap, keyboard focus remains visible.
  Theme-transition screenshots were followed by settled-color inspection.
- Accessible names, switch checked states and polite status region inspected;
  no warnings/errors in the checked console. Historical-download, managed-copy
  independence and connection-write failures are covered by actual API tests.

Temporary screenshots are `/tmp/simshelf56-master-{theme}-{width}.png` and
`/tmp/simshelf56-master-off-{theme}-{width}.png`; final desktop proof is
`/tmp/simshelf56-master-final.png`. They contain disposable fixture data only.

## Limits and owner checks

Linux/Chromium only. No physical screen-reader, real scientific workload, maximum
archive or long-running performance certification. Existing backend concurrency
and publication/recovery semantics remain; this switch is not cancellation of an
already executing publication. External repositories are still excluded from
workspace backups. No Stage B or remote work was undertaken.

1. Open Git history. Confirm two distinctly labeled switches and the green master
   connected status/path; setup should be collapsed.
2. Switch master OFF, then ON in the same panel. Check old files/history and
   unchanged simulation consent; Git downloads require reconnection while managed
   downloads do not.
3. Disconnect and restart/reload. Confirm OFF persists. ON should open setup;
   choose the original archive explicitly without initialization.
4. With a disposable archive, test missing/changed paths and identity failures:
   OFF must remain. Initializing an empty directory requires its explicit checkbox
   and setup confirmation; another archive must not grant automatic consent.
5. Use keyboard and preferred themes/narrow widths. Change connection during a
   disposable run and confirm its original frozen plan is preserved.

Stop for owner review. No merge, release, new PR or unrelated issue work.
