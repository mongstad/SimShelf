# Issue #47 — shared local Git archive

Review-time evidence, 2026-10-17. Accepted base:
`e29ff35a79cd111710adff8487c745b904adc8de` (0.1.0.13). Proposed build: **0.1.0.14**.
Existing issue branch retained. #43/#44 foundations are merged; #45 and #7 are not
implemented. Owner approved the revised design including future outputs, post-run
additions and cumulative limits before implementation. No schema migration.

## Implementation and decisions

See [design](../GIT_ARCHIVE_DESIGN.md) and [user guide](../GIT_ARCHIVE.md).
Dedicated bare shared archive, explicit initialization/connection and per-simulation
consent; source Git integration remains independent. Exact run-start snapshots and
verified managed output copies form initial commits. Post-run manual attachments
use separately confirmed additions, retaining all filename revisions. Future rules
are capture-directory-relative, with explicit per-run copy overrides. UI and docs
explain that source-adjacent CSVs outside capture require manual attachment.

Versioned metadata preserves immutable verified event associations and pending
operation recovery separately from scientific rows. Atomic ref publication uses a
private index and operation ref; retry verifies already published bytes before
association. Downloads use recorded commit/path with SHA-256/size verification.
Repository disconnect/remapping, run removal and backups preserve Git history.

## Automated validation

Final focused command (external Python environment, `PYTHONPATH=src`, `-B`, no
pytest cache, disposable `/tmp/simshelf47-tests-handoff`):

```text
pytest -q -p no:cacheprovider \
 tests/test_git_archive.py tests/test_git_selection.py \
 tests/test_git_provenance.py tests/test_recording.py \
 tests/test_capture_backup.py tests/test_removal.py \
 tests/test_portal.py tests/test_application_version.py
```

**124 passed**, one existing Starlette/httpx deprecation warning. Archive-specific
coverage: **20 tests**, including A/B/A distinct commits and isolation, overwritten
CSV retrieval, live source mutation, failed and cancelled real CLI commands,
unchanged exit status/logs/scientific records, same-name post-run revisions,
repeat confirmation idempotence, explicit API consent/token protection,
pre-first-run rules, missing/outside/unchanged outputs, nonrecursive wildcard
capture, stale settings, hardlinks/symlinks/traversal/unsafe config, missing Git,
missing objects, invalid payloads, cumulative limits, concurrent simulations,
archive-lock contention, crash after publication, pre-manifest crash without live
recapture, backup/remapping, preserved source Git index/history and run removal.

A final archive-only rerun after isolating malformed optional settings from run
startup passed **20/20**; this adds one distinct case (125 across the focused set).

**12 frontend tests passed** (archive 3, file selection 6, source Git 3), bundled
with esbuild to external CommonJS files and run with Node. These verify explicit
capture-relative guidance, revision-specific download routes, final-status review
availability, original selection validation and provenance rendering. TypeScript
`--noEmit`, frontend build and `git diff --check` passed. Third-party notice files
are unchanged.

## Package and offline runtime

Built wheel and sdist in `/tmp/simshelf47-package`, then built a wheel from the
extracted sdist. Both metadata versions are 0.1.0.14; all bundled static files match
checkout bytes. Installed wheel into an external disposable environment, reusing
already installed runtime dependencies through an external `.pth` file (not a fresh
dependency-resolution test). No development/simulation environment was modified.

Installed Python version, CLI, `/api/workspace`, OpenAPI and bundled HTML/JS/CSS/
license endpoints passed with Git/Node absent from PATH and socket connect denied.
Installed UI displayed 0.1.0.14. Initial no-isolation packaging failed because the
development environment lacked setuptools; isolated builds then passed. This was
a build-environment failure, not a passing first attempt.

## Actual browser checks

Linux Chromium/in-app browser, installed wheel, disposable Alpha/Beta sources,
library and archive under `/tmp/simshelf47-browser`; no owner research files used.

- Reviewed/cancelled and explicitly confirmed post-run analysis attachment archive.
  Original initial commit remained, and a distinct addition appeared for that run.
- Downloaded Alpha run 1's `result.csv` after Alpha run 2 and Beta had advanced HEAD;
  downloaded bytes were exactly `Alpha result 1`, not later output.
- Edited nonexistent future-output rule, cancelled preview, then explicitly enabled;
  refreshed page retained consent and rule lines.
- Disconnected/reconnected the archive without initialization; initial/addition
  history survived. Run lists and archive controls stayed simulation-scoped.
- Keyboard Enter opened an addition review and Cancel dismissed it; upload endpoint
  itself is covered by the actual multipart API regression. OS file-picker upload
  was not exercised manually.
- Settings and Files surfaces captured in Dark, Light, Onyx, Slate and Linen at
  1280×900 and 390×844. Document/client widths matched (1265/1265 and 375/375), no
  horizontal page overflow. Theme tokens, wrapping, controls and historical entries
  remained readable. Final browser console had no error/warning entries.

Browser review exposed duplicate sibling React keys causing repeated selection
controls and transient old-simulation rows during selection changes. Fixed with a
unique archive-component key and immediate simulation-ID display filtering;
rechecked one editor/panel and correct scoped rows through polling and navigation.
An initial TypeScript check caught an incorrect refresh callback name; corrected
before packaging. One temporary editing command used the wrong working directory
and made no edit; rerun correctly. A test server ended with signal 15 during the
session; restarted it and used a fresh localhost tab after the browser's unavailable
page blocked interaction. Final checks used the restarted server.

Screenshots and transient fixtures remain outside Git (`/tmp/simshelf47-*`). Earlier
validation documents retain their original wording and bytes.

## Limits and owner verification

Linux only; other OS/browser engines, physical assistive technology, real
VB_Phi_Field/ Wavez workflows, hostile-local-user races, sudden power loss, full
1,000-file performance and huge historical repositories were not certified.
Failure injection covers publication/association recovery, not every filesystem
failure. SimShelf locks cannot serialize arbitrary external editors. Automatic
capture outside the configured directory, detached writers, remotes, pruning and
arbitrary existing Git repositories are unsupported. Metadata manifests are bounded
at 16 MiB; omission details are capped at 1,000 plus a summary. Git storage is not
included in a library backup and is not purged by run/attachment removal.

Suggested owner checks on disposable data:

1. Initialize a new empty external archive and register simulations A and B. Select
   `sim.py`, declare `result.csv` before it exists, review copy overrides and enable
   each simulation. Keep outputs inside its configured capture directory.
2. Run A, B, then A again, overwriting A's CSV with distinguishable contents. Check
   separate commits and simulation-only inventories; download each old CSV.
3. Modify source during a run and deliberately fail another run. Check original
   snapshot bytes, true failed status and eligible partial results independently.
4. Attach a screenshot and analysis file to A's first run. Cancel the archive
   review once; then confirm. Attach another same-name revision and confirm again.
   Verify earlier revisions and the original initial commit remain downloadable.
5. Write a CSV beside the Python source outside capture. Confirm it is not silently
   archived; attach it manually. Check missing-pattern/unchanged-file explanations.
6. Disconnect and reconnect the archive; back up/restore the library to a new folder.
   Confirm explicit remapping is required and the external repository must be backed
   up separately. Check narrow layouts and your preferred theme.

Stop for owner review. No merge, release or other issue work is authorized here.
