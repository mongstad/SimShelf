# Issue #144 — Run display-name editing

October 25, 2026. Accepted base: `9d3154829a443cc7557fbe7057ebc222c43afafb`
(PR #143). Proposed application version: `0.1.0.57` from `0.1.0.56`.

## Result and boundaries

Run actions now include **Rename run…** during running, stopping, pending capture,
completed, failed and interrupted states, independently of recorder ownership.
The compact native dialog selects the current name, supports Enter/Save and
Escape/Cancel, restores focus to its action and retains drafts/errors on rejection.
There is no optimistic title update: confirmation updates the title and refreshes
the parent listings. Existing per-run request ordering rejects delayed pre-save
polls and responses after navigation. Ordinary polls leave the open draft alone.

The existing annotation PATCH retains its 1–160-character bound, rejects null or
whitespace-only names and trims surrounding whitespace. Names need not be unique.
The SQLite annotation transaction records `previous_name` alongside each newly
applied name revision. This preserves the original label and later revisions in
backups without relying on the original start journal. Previously applied history
and start-journal bytes stay unchanged. Notes no longer includes a second name
field or submits a stale name draft when saving notes/tags.

No schema migration, execution identity, command/argv, source snapshot, provenance,
filesystem path, output bytes, process-control or archive-publication change is
introduced. Existing explicit later-evidence review can include the name audit;
renaming alone cannot rewrite existing Git commits. Separate clients use the
existing last-applied-write convention. A storage operation can leave a durable
pending event even when its response fails: the error asks the user to refresh
and check the saved name before retrying, preserving existing recovery behavior.
Annotation history in the UI retains its existing latest-100-entry view; the
database and backups retain the full history.

## Validation

- Source progress-independent rename/API/version checks:
  `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 /home/Nozba/Codex/SimShelf/environments/SimShelf/bin/python -m pytest -q -p no:cacheprovider --basetemp /tmp/simshelf-144-python tests/test_run_rename.py tests/test_active_annotations.py tests/test_api.py tests/test_application_version.py`:
  **27 passed** initially, followed by **1 passed** for the added archive-integrity
  test. The final rename file (**11 passed**) was rechecked after clarifying the
  null-name error. `tests/test_capture_backup.py`: **7 passed**.
- Tests cover all stored lifecycle states; actual portal-owned and observer edits;
  concurrent finalization; dead-owner recovery; stale token/origin rejection;
  empty/whitespace/oversized/null input; permission failure; idempotent durable
  replay; restart/reopen; unchanged schema and start journal; name search; backup
  restoration of current and previous names; and unchanged execution/metrics,
  source/output bytes and capture paths. A temporary actual Git archive retained
  its exact HEAD, events, manifest and every historical download after rename;
  explicit later-evidence preview includes `previous_name` without publishing.
- Installed-wheel `test_run_rename.py`, `test_active_annotations.py` and
  `test_api.py`, run from `/tmp` with `PYTHONPATH` pointing to the isolated install:
  **16 passed**. Python API suites used unrestricted execution because the known
  sandbox/TestClient combination stalls. The existing Starlette deprecation
  warning remains; no scientific interpreter or installed dependency was changed.
- TypeScript check, production frontend build, accepted-main version gate and
  diff check passed. Intentional bundled JS/CSS were rebuilt; third-party notice
  and license bytes are unchanged. Esbuild-bundled active-annotation, favorite
  and navigation files executed directly with Node: **14 tests passed**.
- Full-App Chromium fixture: **6 lifecycle cases passed** (running, stopping,
  finalized process with capture pending, completed, failed, interrupted). Each
  checks cancellation, focused prefill, empty validation, rejected/stale writes,
  draft retention, delayed old polling responses, fresh polling, confirmed title,
  restored focus, Notes save isolation, list updates and navigation. No source,
  filesystem, launch or process-control route exists in the fixture. Final runs
  had no console warnings/errors.
- Native keyboard Enter opens/saves; Escape cancels without changing the title
  and returns focus. All six themes passed dialog bounds, no internal horizontal
  overflow and focused-input checks at **1280 × 720** and **390 × 844**. Narrow
  checks used a 160-character draft. Light desktop and Onyx narrow error views
  were visually inspected. Viewport overrides were reset afterward.
- Wheel/sdist builds and a wheel rebuilt from extracted sdist passed outside the
  checkout. Versions agree at `0.1.0.57`; all **36 Python/static files** match source
  across artifacts. Installed import/CLI, workspace/OpenAPI version, HTML/static
  serving and startup worked with Git/Node absent from PATH.
- Installed app: a real, controlled in-process recording context was renamed
  while active, completed with the same name and retained it through a real
  server restart and browser reload. Notes displayed the original and new labels.
  The controller verified unchanged source/output bytes, IDs, snapshot hashes,
  parameters, command/cwd, Git provenance, capture configuration/root and owner.
  No installed application console warnings/errors were observed.

Reproduce the full-App fixture from the checkout with
`node scripts/test_run_rename_browser.mjs /tmp/rename-check`, serve that directory
on loopback, and open `?state=running&test=1`. Other states: `stopping`, `finalizing`,
`completed`, `failed`, `interrupted`; optional `theme=light|dark|onyx|slate|linen|system`.
`#results` reports PASS/FAIL. Without `test=1`, the fixture supports manual keyboard
checks; its separate **Reject next save** control simulates a stale token.

Screenshots: [desktop dialog](../images/issue-144/rename-desktop.png),
[narrow retained draft/error](../images/issue-144/rename-narrow-error.png),
[installed completion after live rename](../images/issue-144/installed-renamed.png).
Native screenshots can omit scrollbar width from the configured viewport.

## Failures and limitations

The initial browser harness waited on the first history row instead of searching
all rows and lacked the simulation-preservation mock route. Both were corrected
before the six final passes. One repository diff check ran from `/tmp` and was
rerun from the checkout. These were validation-harness errors; the final checks
above passed. No real-user library, simulation, source folder or archive was opened.

Validation is Linux/Python 3.14/Chromium with small synthetic recordings, not
scientific performance or Windows/macOS/browser-engine/screen-reader certification.
Simultaneous editors can overwrite each other's display-name choice under the
existing last-applied-write rule; each applied revision remains auditable. A lost
response cannot prove whether a durable annotation was applied. No new automatic
retry, compatibility migration, release or archive publication is introduced.

## Owner verification

1. In a disposable library, register a plain Python fixture that prints a counter
   and sleeps one second in each of 30 iterations. Select a trusted existing
   interpreter and manual argv, then start with an explicit initial run name.
2. While it runs, choose **Rename run…**. Check selected prefill, Tab focus,
   Escape/Cancel without a write, whitespace rejection, then Enter to save a
   descriptive name. Wait through polling and completion; the title must retain
   it. Back to runs, table/gallery, reopening and browser reload must show it.
3. Rename completed, failed (fixture exits with code 3) and interrupted (Stop run)
   examples. Rename must not depend on Stop ownership. Check the same behavior
   while Stop is pending or capture is finalizing when observable.
4. Open **Notes → Annotation history** and verify both `name` and `previous_name`.
   Save unrelated notes; the title must not revert. Restart the server normally
   and reload a finalized run; names/history must persist. Back up and restore
   only this disposable library into a separate new folder and check them again.
5. On a finalized run, open Rename, restart its server without refreshing the
   browser, then try Save. The stale-token error must retain the draft and the
   confirmed title. Refresh to reconnect before retrying. Check narrow layout and
   your preferred theme; no name edit should rename files or change recorded
   IDs, argv, source, provenance, outputs or existing archive downloads.
