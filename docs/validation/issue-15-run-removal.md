# Issue #15 run removal

2026-10-17. Pending owner review; no merge or release claimed.
Accepted main: `97d28c4b5bc8660547b9b4165f4471784cc56961` (PR #25).
The SimShelf Project board had #15 first and as its only Ready item. The existing
`15-feature-safely-remove-obsolete-simulation-runs` branch, local main and remote
main matched with a clean tree. No open PR existed. PR #25 and portal predecessor
PR #8 were merged; the previous issue branch was already removed. No user
workspace or historical report was changed during housekeeping or testing.

## Implementation and decisions

Run details and list/gallery selections offer explicit removal confirmation with
identifying names, full IDs, versions, statuses and timestamps. Cancel receives
initial focus. Running/finalizing selections cannot proceed; the backend checks
all IDs transactionally. Success refreshes counts/selections; other tabs clear
unavailable details, and comparisons close when fewer than two selected runs
remain. Removed records are absent from searches, favorites and version counts.

The design was recorded in `docs/RUN_REMOVAL.md` before implementation: hard-delete
run relationships plus minimal audit tombstones, with a durable per-file cleanup
queue. Only unreferenced managed files are reclaimed, using descriptor-relative
no-symlink traversal. Shared content and baseline snapshots needed by surviving
records remain. Historical baseline IDs/classifications do not change, and source
comparison can still read a removed baseline's retained snapshot. Future runs use
the earliest surviving run, or establish a fresh baseline when none survive.

Thread/process locking covers source preparation through start, attachment
publication, event writes/replay, backup and removal. Live simulations do not hold
the lock for their full lifetime. Downloads keep an open inode and preserve range
responses across unlink. Async upload/caption paths offload blocking work. A
transaction commits before reclamation; recovery retries incomplete cleanup and
tombstones prevent resurrection. Original source/output/reference paths are never
cleanup targets. Earlier backup archives remain unchanged.

First confirmed deletion explicitly selects schema 2; startup still supports
schema 1 without migration. Older builds reject schema 2 when opening it. Stop
older servers/recorders before deletion. The confirmation explains this choice.
Audit entries remain in fresh backups, but removed payloads/cleanup tasks do not.
This is not secure erasure. Application version advances from 0.1.0.3 to 0.1.0.4.

Changed areas: removal/locking modules; Store, recording/capture, API and backup
integration; removal component, run selection/details/types/styles and rebuilt
bundled assets; focused tests; README/architecture/design/validation guidance.
Third-party notices and licenses remain unchanged.

## Validation

- **74 Python tests passed** in `test_removal.py`, `test_capture_backup.py`,
  `test_recording.py`, `test_api.py`, `test_portal.py`, `test_shutdown.py` and
  `test_application_version.py`. This covers single/bulk removal, atomic rejection,
  failed/active records, token/origin checks, unknown IDs/path injection, late
  uploads/annotations, shared source/artifact blobs, preserved baselines, old and
  fresh backups/restores, journal replay, transaction rollback, cleanup permission
  failure, crashes after commit and after unlink, duplicate concurrent removal,
  attachment/start/backup races, cross-process locking, symlink refusal, download
  ranges after removal, and event-loop responsiveness while waiting for a lock.
  Existing portal/recording lifecycle tests remain green. One existing
  Starlette/httpx deprecation warning remains.
- TypeScript check and production frontend build passed, including the final
  comparison-selection fix. Bundled JavaScript/CSS and full license notices ship.
- Source and installed-wheel browser checks used separate generated `/tmp`
  libraries. Cancel preserved the selected run; single completed/failed and bulk
  removals updated counts and cleared selection. Reload retained results. Shared
  screenshot availability and baseline source diffs survived removal. A second
  installed-app tab cleared the removed run's stale detail view. Mixed active and
  finalized selections were disabled, while the active installed recorder stayed
  running after other runs were removed. Version history reflected retained counts.
  The source confirmation was inspected at the default desktop viewport and
  390x844; controls and full IDs remained readable without horizontal overflow.
  No JavaScript errors appeared in the primary source/installed test tabs; the
  stale-detail tab received expected not-found responses.
- Wheel and source archive built in an external disposable source copy. Build
  produced the wheel from the sdist. A fresh disposable installation resolved its
  declared dependencies and passed browser checks with Git and Node absent from
  server PATH. Python, installed metadata, CLI, API, OpenAPI and portal label agree
  on 0.1.0.4. App creation passed with outbound socket connections denied. Package
  audits found the new modules, frontend source, design documentation, assets and
  notices. No Node runtime is required by the installed app.

Reproduce Python checks with the dedicated development Python, `PYTHONPATH=src`,
`PYTHONDONTWRITEBYTECODE=1`, `-m pytest -q -p no:cacheprovider` and the seven files
above, with `--basetemp` outside the checkout. Run `pnpm run typecheck`,
`pnpm run build`, and `python scripts/application_version.py --base-ref origin/main`.
Build from a disposable copy as documented in README. Browser fixtures, packages,
logs and screenshots remain outside Git under `/tmp/simshelf15-*`.

## Failures encountered and limits

The initial shell lacked Node on PATH; using the bundled runtime passed. Two
sandboxed TestClient runs stalled and were interrupted; host runs completed.
An initial download-stream implementation failed the SVG inert-content check;
it was replaced with an open-descriptor FileResponse that passes the original
safety checks plus byte-range-after-unlink coverage. An initial non-isolated build
could not find setuptools; the normal isolated build succeeded without changing
the existing developer environment.

An external backup helper in a different tool PID namespace marked a disposable
source-test recorder interrupted through existing dead-owner recovery. The final
installed fixture creates its backup/active recorder in the server's own process;
active protection was rechecked there. Cross-PID-namespace recording is not an
application guarantee. No user library was involved.

Linux/local filesystem and the in-app Chromium browser only. Other platforms,
browser engines, real power loss, filesystem corruption, adversarial local writers,
large/long scientific workloads and network-filesystem lock semantics are not
certified. Failure injection models interruption, not physical disk failure.
Long snapshots/backups can delay operations; full scale testing is deferred.
Missing retained manifests and unexpected symlinks fail closed. Empty managed
directories and event-ID deduplication entries may remain. SQLite/WAL free pages
and old backups mean removal is not privacy-grade erasure. No automatic garbage
sweep, retention policy, individual screenshot removal or release is included.

## Exact owner checks

1. Start `./start.sh --workspace /absolute/path/to/a/disposable-library`. Register
   a harmless Python source folder and create two completed runs plus one failed
   run. Attach the same image to two runs; keep an original output as reference.
   Add a comment between the first two runs so Source comparison has a visible diff.
2. Back up that library. In a completed run choose **Remove run…**. Check full ID,
   warnings and Cancel focus; cancel and verify unchanged data. Confirm removal
   on reopening. Check counts, favorites/search, shared image and original files.
3. Open the surviving run's **Source** tab and enable **Compare with version
   baseline (run removed; snapshot retained)**. Verify the original comment diff.
4. Select multiple finalized runs and choose **Remove selected…**. Confirm only
   those IDs disappear, selection clears and reload/history counts remain correct.
   Keep a second tab open on a removed run and verify unavailable-detail feedback.
5. Run a harmless sleeping script. Check disabled removal in its details and a
   mixed active/finalized selection. Cancel, stop it normally and wait for final
   capture before reviewing eligibility again. No original output should change.
6. Run `./start.sh --workspace /absolute/path/to/a/disposable-library --cli doctor`.
   Make a fresh backup and restore it to a new directory; check surviving records,
   images and baseline diffs. Restore the old backup separately and verify old
   records remain there. Keep originals/backups until satisfied. Do not use an
   older app build with the upgraded library.
7. Recheck desktop/narrow dialogs and comparison selection across two tabs. Review
   schema-2 compatibility, retained audit/baseline semantics and Linux-only limits
   before merging. No merge, tag or publication is authorized by this report.

Final handoff checks: refreshed main remained at the accepted commit, the issue
remained Ready, no open/duplicate PR existed, and the version gate passed. The
final rebuilt wheel's Python modules and runtime assets matched checkout bytes.
The final comparison-closure fix passed in both source and installed two-tab
checks. After a test-server restart, an old tab correctly rejected removal with
"Refresh SimShelf before saving"; refreshing renewed the token and the check
passed. Test servers were stopped. The source fixture's later finalizer was
correctly refused after the PID-namespace recovery/removal described above;
it did not resurrect the deleted record. The installed fixture shut down cleanly.
