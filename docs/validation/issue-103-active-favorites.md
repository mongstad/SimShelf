# Issue #103: active-run annotation investigation

2026-10-23, Linux, accepted main `c0ea81eb0b94393ff2c89d8457db7b0e0acd5b53`
(0.1.0.48), proposed application version 0.1.0.49.

## Diagnosis and scope

PATCH returned persisted run data without GET's `can_stop` and `stop_requested`.
The frontend replaces its confirmed run with that response, so a successful save
could temporarily hide Stop and show the non-owner warning even on an owned run.
The new integration test failed on the missing `can_stop` before the fix. PATCH
now includes current control metadata, queried after releasing the workspace
lock to avoid reversing launch's jobs/workspace lock order.

**The original owner's favorite rollback was not reproduced, and its historical
cause remains unconfirmed.** The response-shape defect explains a misleading
warning, not loss of tags. No speculative persistence, recorder, token, polling,
SWSS or scientific-data changes were made. Successful favorite saves remain silent.

A stale per-instance token was reproduced by restarting only a second, non-owner
server while the first server's disposable recording continued. PATCH returned
403, the visible alert said `Refresh SimShelf before saving.`, and the confirmed
star stayed unchanged. Reloading the page obtained the new token and saving then
worked. This proves that scenario, not that the owner's server had restarted.

## Validation

- `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 <venv>/bin/python -m pytest
  tests/test_active_annotations.py tests/test_portal.py
  tests/test_application_version.py -q -p no:cacheprovider
  --basetemp=/tmp/simshelf-103-tests`: 35 passed before the additional interrupted
  recovery test. Final `tests/test_active_annotations.py` run: 2 passed.
- `tests/test_api.py`,
  `tests/test_removal.py::test_annotation_wait_does_not_block_event_loop`, and
  `tests/test_preservation.py::test_annotations_captions_append_only_and_backup`:
  5 passed. Total: 41 distinct focused Python tests.
- Existing `frontend/favorite.test.mjs` plus new
  `frontend/activeAnnotations.test.mjs`, bundled with esbuild to external CommonJS
  and executed with Node: 10 tests passed. Covers delayed/out-of-order polls,
  save gating, navigation, failure/retry, active/completed state, stale token
  rejection and reconnect without automatic write retries. These helper/API
  tests are supplemented by browser checks, not claimed as mounted React tests.
- `tsc --noEmit`, `git diff --check`, and
  `scripts/application_version.py --base-ref origin/main`: passed.
- Python coverage includes real portal subprocess logging/percentage progress,
  both server ownership states, favorite/unfavorite, notes and annotation history,
  new Store reads, rejected validation/origin/token writes, finalization overlapping
  a save, reconciliation, and simulated dead-owner recovery preserving annotations.
  Existing lock-contention test verifies a waiting annotation does not block the
  event loop. No lock rejection or successful-write rollback was observed.
- Real browser run in `/tmp/simshelf-103-ui`, owner server on 8103, non-owner on
  8104: favorite while running, history star after polling/navigation, non-owner
  unfavorite, actual non-owner server restart, visible stale-token rejection,
  reload and successful favorite, then normal completion and unfavorite.
  Source and outputs belong only to this disposable fixture. Owner science was
  neither executed nor stopped. Servers were stopped after validation.
- External wheel/sdist build and wheel rebuilt from extracted sdist: all wheel
  member names and bytes identical. Bundled JS/CSS/legal notices match checkout.
  No production frontend source changed, so assets were not regenerated.
  Installed wheel into `/tmp/simshelf-103/installed` with existing dependencies;
  Python/CLI/workspace API/OpenAPI report 0.1.0.49. Installed browser label checked
  on port 8105 with Git/Node absent from PATH. In-process TestClient startup/API
  checks passed with socket `connect`/`connect_ex` denied; not an OS network namespace.

Screenshots retained outside Git: `/tmp/simshelf-103/stale-token.png` and
`/tmp/simshelf-103/non-owner-favorite.png`. They show the fixed API before the
version increment/server restart, hence the running browser still says 0.1.0.48.
The separate installed-wheel check verified 0.1.0.49.

Initial test failed as expected on missing PATCH control fields. Two attempted
fixture-launch commands used unsupported CLI flags (`serve`, then `--no-browser`);
corrected to `ui --no-open`. No application change resulted. Tests emit the existing
Starlette/httpx deprecation warning. No dependency changes were made.

## Limits and owner checks

No original Vacuum Collapse record, original network trace, owner database,
95.5%-progress scientific workload, large-output capture contention, other OS,
or full test suite was used. Dead-owner recovery was simulated; no process crash
was induced. This PR does not establish the cause of the original rollback.

1. Restart SimShelf from the branch and reload the page; confirm 0.1.0.49.
2. On an expendable active run, favorite/unfavorite. Wait at least two 3-second
   polls, navigate to history and back, then reload. Confirm the star and tags
   match, notes remain, and an owned run keeps its Stop control after saving.
3. View that run from a second server: annotation saves must still work while
   its non-owner warning remains truthful. Restart only that non-owner server;
   an old tab's write must show the refresh alert and keep confirmed state.
   Reload, retry, and confirm persistence through completion.
4. If the original rollback recurs, record PATCH status/response and subsequent
   GET tags (omit tokens), plus app version and server ownership/restart context.
   Review this evidence before treating the original symptom as resolved.
