# Issue #9 / PR #43: repository discovery revision

2026-10-17. Existing issue branch, proposed version **0.1.0.12** retained against
accepted main **0.1.0.11**, `492402c9843170b5243fe40ae0213722a06e92cf`.
[Original foundation evidence](issue-9-local-git.md) remains unchanged.

## Revision

Opening Git history while disconnected now discovers the repository from the
registered source folder. It shows Repository found/root, preselects only the
current simulation, and offers other registered folders belonging to that same
repository. Independent nested repositories and linked worktrees resolve to their
actual repository. The current mapping is previewed automatically; selection
changes invalidate it and require another preview. Connect locally remains an
explicit, revalidated write. Cancel never connects. Manual path entry is a
secondary fallback. No marker yields No Git repository found; missing Git,
missing source and invalid/unsafe configuration yield an unavailable state.

Discovery is a separate read-only endpoint and does not change the format-1
provenance contract, recording, snapshots, Git/source files, remote behavior,
connection ownership, disconnect or backup/restore. No initialization is exposed.
Other-registration eligibility checks are bounded to 100 registrations/10 seconds
between candidates, plus completion of an in-flight bounded Git inspection.
Partial results are disclosed; manual mapping remains available.

## Validation

- **51 focused backend tests passed** across `test_git_provenance.py`,
  `test_application_version.py`, `test_recording.py`, `test_capture_backup.py`.
  Includes direct/parent repositories, shared mapping, independent nested repo,
  linked worktree, no repo, missing Git/source, invalid config, path boundaries,
  explicit confirmation, read-only discovery/preview, manual fallback, disconnect,
  unchanged recorded provenance and existing restore safeguards. Repository file
  bytes remain identical before/after discovery. One existing Starlette/httpx
  deprecation warning.
- Initial run: 49 passed, one fixture failure. A pre-existing `/tmp/.git` marker
  meant the supposed no-repository fixture had an invalid repository ancestor.
  The test now isolates ancestry checks above its temporary root; host files were
  not modified. Final run passes; unavailable was the correct product response
  for the original unsafe ancestor.
- **3 frontend tests passed**: prior observation tests plus found/not-found/
  unavailable discovery rendering, escaping and no implied connection.
  TypeScript, frontend build and diff checks passed. Packaged JS rebuilt; CSS
  and license notices unchanged.
- External source-copy wheel/sdist/wheel-from-sdist metadata and static-byte
  checks passed at 0.1.0.12. Installed Python/CLI/API/OpenAPI/static startup passed
  without Git/Node on PATH and with outbound API sockets denied.
- Installed Chromium UI (disposable library, port 8847): automatic parent root,
  Alpha selected/Beta unchecked, Cancel stays disconnected, optional Beta selection
  and refreshed preview, Enter on Connect locally, connected reload, disconnect
  returning to unconnected discovery, manual-path preview/cancel. No browser
  warnings/errors. Five themes at 1280x900 and 390x844 fit; narrow document/panel
  widths 375/343. Settings restored and owned temporary server stopped.

Evidence: `/tmp/simshelf9-discovery-desktop.png`,
`/tmp/simshelf9-discovery-{light,dark,onyx,slate,linen}-{1280,390}.png`,
`/tmp/simshelf9-discovery-layouts.json`, `/tmp/simshelf9-discovery-package.log`.

Limits: Linux Chromium/Git 2.56 only; no physical screen reader, other OS/engines,
large-registration performance certification or unrelated full-suite rerun.
No-repository state uses isolated ancestry in backend tests; browser exercised
successful discovery and manual fallback. Existing disposable install has
system-site access. No user source/library or real scientific script was used.

## Owner checks

1. Open Git history for a registered simulation in a parent repository: expect
   Repository found with the resolved root, no required path input, and only the
   current simulation selected. Select another eligible project if desired.
2. Cancel once; verify no connection. Review and explicitly Connect locally.
3. Reload, disconnect and reopen: discovery must not reconnect automatically.
4. Try a directly initialized repository, nested independent repo, worktree and
   no-repository folder. Check manual fallback and graceful missing-Git behavior.
5. Confirm old run provenance remains unchanged and inspect preferred theme,
   narrow layout and keyboard/screen-reader behavior. Review PR #43 only.
