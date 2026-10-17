# Issue #24 screenshot deletion

2026-10-17. Pending owner review; no merge or release claimed.
Accepted main: `896832172a73c3fd10a3728454e0c95257cd8227` (merged PR #26).
The SimShelf Project board had #24 first and as its only Ready item. Its existing
`24-ux-delete-screenshots-from-previous-runs-in-the-portal` branch matched main with
a clean tree and no open PR. PR #26 and portal predecessor PR #8 were merged;
issue #15's branch was already removed. No historical report or user library was
changed. The owner explicitly authorized schema 3 on explicit screenshot deletion.

## Implementation and decisions

The Screenshots tab offers a modest per-image Delete screenshot action, a dialog
identifying image/run/full IDs, initial Cancel focus, Escape cancellation, deliberate
confirmation and success/error feedback. Successful deletion updates the image/count
and displayed cover; stale in-flight detail responses cannot resurrect removed
images. List refreshes discard older responses. Focus returns to the trigger on
cancel, Cancel after failure, or the screenshots heading after successful deletion.
Missing image bytes are shown explicitly and do not prevent reference removal.

Eligibility is deliberately conservative: manually attached managed raster copies
with explicit `automatic=false`, on completed/failed/interrupted runs after capture
finalization. Automatic scientific outputs and unknown legacy ownership are protected
with a reason. External references remain in Files and are not removed by this action.
Shared source/artifact blobs stay while any retained reference needs them.

One transaction writes a separate tombstone with original attachment metadata,
appends a chronologically ordered audit entry, removes the selected artifacts row,
queues its hash-derived blob path and activates schema 3. Run rows, measurements,
capture counts, source snapshots, logs, original files and earlier journal/caption
history remain intact. Replay excludes tombstoned attachments/captions. Historical
cover annotations remain evidence; the gallery/list derives a surviving cover.

The existing workspace lock and reference-aware, no-symlink cleanup protect concurrent
uploads, source capture, backups and deletion. Pre-commit failures roll back. After-
commit cleanup failures report that the entry is removed but bytes await retry.
Schema-1/2 startup/recording/backup remain supported without migration; only successful
explicit deletion selects schema 3. Schema-3 backup/restore is supported, older builds
reject it on opening, and subsequent whole-run removal never downgrades it. Stop
older already-open servers/recorders first. Existing backups remain untouched.
See [the deletion design](../SCREENSHOT_DELETION.md) for recovery and limitations.
Application version advances from 0.1.0.4 to 0.1.0.5.

Changed areas: new screenshots backend and confirmation/filter component; Store,
API, backup and run-removal compatibility; run-detail/list integration and types;
rebuilt bundled JavaScript; focused tests; current feature/architecture guidance
and this new evidence. Full third-party licenses and bundle notices are unchanged.

## Validation

- **64 Python tests passed** across `test_screenshots.py`, `test_removal.py`,
  `test_capture_backup.py`, `test_recording.py`, `test_api.py` and
  `test_application_version.py`. Coverage includes exact selected removal,
  immutable raw run rows and journal bytes, missing files, shared/source/captured
  content, external/unknown ownership, active/finalizing/failed/interrupted runs,
  duplicate and concurrent requests, wrong run/workspace, token/origin checks,
  unexpected path input, corrupt blob IDs, symlink file/directory refusal,
  read-only SQLite, pending-journal blocking, permission cleanup failure, crash
  after unlink, late captions/covers, upload/backup serialization, pre/post-deletion
  backup restore, schema-2 compatibility and no schema downgrade. The screenshot
  subset was rerun after a final audit-order assertion/adjustment and passed.
  One existing Starlette/httpx deprecation warning remains.
- **Two frontend tests passed**: exact confirmation/irreversibility/backup/missing
  wording and safe escaping; stale-response filtering with exact retained IDs,
  count, cover fallback and unchanged scientific parameters. TypeScript and the
  production build passed. These are static/pure tests; browser checks below
  exercise the actual interaction and failure paths.
- Source browser checks used a generated `/tmp` library: cancel and Escape kept
  the image; deletion of the selected cover changed count 4→3, preserved the other
  images and selected a remaining cover. Reload preserved deletion. Missing-file
  removal, shared-reference removal with another run's image still rendering,
  protected capture controls and explicit failure/retry feedback passed. A SQLite
  trigger injected a rollback failure; it was removed after the test. The dialog
  was inspected at the default desktop size and 390×844, with readable IDs/buttons
  and no horizontal overflow. Initial/success/error focus was inspected in the DOM.
- Fresh installed-wheel checks used a separate generated library and server PATH
  without Git or Node. Deletion and same-ID confirmation from a second stale tab
  succeeded once and then reported already deleted. Active run deletion stayed
  disabled while that recorder remained running. Captured outputs stayed disabled;
  missing-image removal, reload persistence and injected failure feedback were
  checked. The final focus fix was checked again after rebuilding/installing.
  Expected injected failures produced visible error feedback; no unexplained
  JavaScript errors were observed.
- A wheel and sdist were built in an external disposable source copy, with the
  wheel built from the sdist. The fresh installed package and checkout runtime/
  bundled asset bytes were compared. Archive checks covered the new module,
  component, test, design/evidence docs and unchanged licenses. Python, installed
  metadata, CLI, API, OpenAPI and portal label agree on 0.1.0.5. App creation passed
  with outbound socket connections denied. Accepted main's actual Store code
  rejected a disposable schema-3 database as intended.

Commands: dedicated development Python with `PYTHONPATH=src`,
`PYTHONDONTWRITEBYTECODE=1`, `-B -m pytest -q -p no:cacheprovider --basetemp=/tmp/...`
and the six test files above; `pnpm run typecheck`; `pnpm run build`;
`python scripts/application_version.py --base-ref origin/main`. Frontend tests were
bundled with esbuild (`platform: node`, `format: cjs`) to `/tmp` and executed directly
with Node. `node --test` reported only the bundled file as one suite; direct execution
reported both named tests passing. Packaging used `python -m build` in a disposable
source copy followed by pip installation into a new disposable virtual environment.
Fixtures, packages, logs and browser screenshots remain under `/tmp/simshelf24-*`.

## Failures and limits

Initial browser checks exposed lost focus after successful deletion and after an
injected failed request. Closing the native dialog before removal, and restoring
failure focus in a React effect after rendering, fixed both; the final behavior was
rechecked. Automated tests had no unexpected failures. TestClient checks used the
host execution environment because repository evidence already identifies restricted
sandbox stalls. Injected read-only/cleanup/crash/HTTP failures were expected tests.

Linux/local filesystem and in-app Chromium only. Other OS/browser engines,
assistive-technology tools, real power loss, corrupt disks, adversarial local writers,
network filesystems and large/long scientific workloads are not certified. Locking
can delay deletion during capture/backup. This is not secure erasure or arbitrary
retention management. Unknown ownership fails closed; external-reference removal
is intentionally unsupported. New backups retain audit metadata, and old backups
still contain deleted images. Missing source manifests or unsafe cleanup paths may
leave bytes pending until the owner resolves the problem.

## Owner verification

1. Back up a disposable library and stop older servers/recorders. Start this build
   with that explicit workspace and verify **Local · 0.1.0.5**.
2. Finish a disposable run; attach three distinct PNG/JPEG images through Add images.
   Add a caption, choose the first as cover, and note the run's parameters/measurements,
   source snapshot and logs. Optionally attach the same image to another run.
3. Open Delete screenshot with the keyboard. Check exact image/run/IDs, initial
   Cancel focus, Escape cancellation, desktop and narrow layouts. Cancel once.
4. Confirm deletion of the first image. Verify immediate count/cover change, success
   notice, keyboard focus, unchanged other images and preserved run evidence.
   Reload, inspect Files and Notes → annotation history, and verify persistence.
5. Verify original files and any second run's shared image remain. Compare the managed
   blob only: unshared image bytes should be gone; shared/source bytes should remain.
   Check captured outputs/active-run images are protected, and missing image removal
   removes only its selected reference. Try a stale second-tab confirmation.
6. Back up after deletion and restore into a separate empty directory. Confirm only
   surviving images display and the deletion audit remains. Restore the pre-deletion
   backup elsewhere to verify recovery. Do not open the schema-3 library with an
   already-running old process. Review the compatibility decision before merging.

## PR #30 review refinement — concise confirmation

2026-10-17. This review revision supersedes the initial dialog presentation and
UUID-display owner checks above; earlier evidence retains its original wording.
The existing issue branch and PR #30 remain in use. Accepted main is still
`896832172a73c3fd10a3728454e0c95257cd8227`; the gate accepts the unchanged proposed
application version **0.1.0.5**.

The dialog now uses only the real filename and run name, a short permanent-removal
warning, and reassurance about the run/results/original files and existing backups.
Full IDs remain internal request targets. Blob/audit/schema-number details are
absent from the ordinary confirmation. Cancel stays neutral and receives initial
focus; the restrained red Delete screenshot button has a decorative trash icon,
hover/focus/disabled states, and still requires an explicit click or keyboard action.
A small title icon, 480px maximum width and wrapping preserve the existing themes.

`GET /api/workspace` now reports the current schema number read-only. Each dialog
opening fetches it afresh: schema 1 or 2 shows a brief warning that older versions
will no longer open the library; schema 3 omits it. Deletion remains disabled until
the check succeeds, and failures leave Cancel/Escape available with an explanation.
This read does not migrate anything. Storage/deletion/replay/backup modules and
the version file are byte-for-byte unchanged from the original PR implementation.

Validation for this revision:

- **33 Python tests passed** in `test_screenshots.py`, `test_api.py`, and
  `test_application_version.py`, including a new live schema 1→2→3 API check and
  existing ownership/replay/shared-file/backup/concurrency safeguards. The existing
  Starlette/httpx deprecation warning remains. No unexpected test failures.
- **4 frontend tests passed**: dynamic escaped names, absent internal IDs/technical
  copy, decorative icons, disabled Delete while checking, warning only for schema
  1/2, short missing-file explanation, and exact selected-image filtering. TypeScript
  and production builds passed; final CSS only refines disabled-button specificity.
- Source browser checks: Dark and Light desktop plus 390×844 layouts, correct names,
  no UUIDs, initial Cancel focus, Escape and Cancel returning to the trigger, Tab to
  Delete and Enter confirmation, exact selected deletion, and immediate count change.
  Both narrow themes had no horizontal dialog overflow. The source schema-1 warning
  disappeared on the next opening after explicit deletion enabled schema 3.
- Fresh installed-wheel browser checks: the schema-2 fixture showed the warning,
  cancellation preserved all five references, explicit deletion removed exactly the
  selected ID and upgraded to schema 3, and the immediately reopened dialog omitted
  the warning. An injected compatibility-read HTTP 503 showed an error with Delete
  disabled and Cancel focused; Escape left all references/tombstones unchanged.
  Final database/API checks in both fixtures confirmed exactly one deletion, correct
  internal targeting, unchanged remaining IDs, original bytes and scientific run
  evidence. No unexplained browser errors were observed.
- Wheel and sdist rebuilt externally, with wheel built from sdist; installed into a
  fresh `/tmp` environment. Packaged JS/CSS/API and unchanged storage code match the
  checkout. Both bundled license files are byte-identical to the original PR.
  Python/metadata/CLI/API/OpenAPI/UI report 0.1.0.5. Installed startup works with
  outbound connections denied and Git/Node absent from PATH. All fixtures, injected
  flags and screenshots stayed in `/tmp/simshelf24-ux-*`; test servers/tabs were closed.

This remains Linux/in-app Chromium validation, not other browsers/OSs or an actual
screen-reader audit. The existing backend/storage limitations above still apply.
The dialog uses a fresh compatibility read per opening, not a persistent live
subscription while open; another client's upgrade during an already-open dialog
can leave its conservative warning visible until reopening. No additional consent
or storage behavior is introduced by that warning.

Updated owner checks: in a disposable schema-1/2 library, verify the real names,
short warning, red icon button, neutral focused Cancel, Escape and both themes at
narrow width. Confirm one image, then immediately open another: the compatibility
warning must be absent. Check the selected image alone disappeared and existing
run/shared/original-file protections remain. Repeat on an already-schema-3 library;
no compatibility warning should appear. Keep the backup/recovery checks above.
