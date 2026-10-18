# Issue #69 — coordinated isolated output folders

Review-time evidence, 2026-10-18. Not a release or a claim about real scientific
workloads. Accepted base: `1aceecb3febf6e8e193fdc99d756ed345820d83c` (PR #65).
Proposed application version: **0.1.0.18**. Issue #69 was the first and only Ready
Project item; its existing linked branch matched accepted main, the working tree
was clean, and no dependency blockers or open PRs were present. Previous issue
#64's branch was already removed; historical evidence and release files remain
unchanged.

## Implementation and decisions

- `output_policy` defaults to `fixed`; `per_run` is explicitly selected in the
  portal, CLI (`--output-policy per_run`) or Python context API. Portal settings
  remain additive JSON and do not change independent CLI/editor defaults.
- A run UUID names an exclusively created child beneath the configured parent.
  No-follow directory opens reject symlinks. Collisions never reuse originals.
  Validation/save are passive; startup can leave an empty folder on later failure.
- The frozen capture configuration, environment and joined API share that exact
  folder. Preview explains allocation; run details show the actual path. Fixed
  declared destinations require acknowledgement; argv/cwd are never rewritten.
- Source snapshots exclude the configured parent, including sibling results.
  Archive consent still compares the configured base and all existing budgets;
  capture/fingerprinting/selected results operate relative to the allocated child.
- No schema migration, scientific source changes, output relocation/deletion or
  historical-record rewrite. Existing overlap, cancellation, capture, recovery,
  managed-copy/reference and backup contracts remain in force.

## Checks

Linux, Python 3.14.8, Node 24.19.0, installed Chromium-based in-app browser.
All fixtures, test workspaces, environments and artifacts were external to the
checkout. No owner library, external archive or scientific project was used.

- Focused pytest run: **109 passed**, then the added CLI/live-cancellation test:
  **1 passed**. One existing Starlette/httpx deprecation warning per invocation.
  Files: `test_isolated_outputs.py`, `test_output_paths.py`, `test_portal.py`,
  `test_git_archive.py`, `test_recording.py`, `test_capture_backup.py`, and
  `test_application_version.py`. Commands used `PYTHONDONTWRITEBYTECODE=1`,
  `PYTHONPATH=src`, `-p no:cacheprovider` and external `--basetemp` directories.
- Coverage includes successive and overlapping concurrent portal runs, both
  environment-only and joined-API scripts, exact downloaded result association,
  unchanged sibling originals/source snapshots, passive settings persistence,
  fixed-path omission, real solver failure, cancellation before/during execution,
  fixed-parent overlap rejection, traversal, symlinks, non-directories, collisions,
  replacement detection, per-file/run budgets, archive consent/results and backups.
- **5 frontend output presentation tests passed**, bundled with esbuild as CommonJS
  and executed with Node. `pnpm run typecheck` and `pnpm run build`: **passed**.
  Distributed `app.js` rebuilt; existing third-party notice files unchanged.
- Wheel and sdist built with isolated build dependencies in `/tmp`. Direct-source
  wheel and sdist-built wheel had identical member sets and bytes, including
  metadata. Verified 0.1.0.18, bundled UI/new label, licenses, docs and new tests.
- Fresh wheel installation: two independent isolated recordings and retained
  originals passed. With `PATH=/nonexistent`, Python/CLI/OpenAPI versions agreed;
  local API/UI startup and recordings worked without Git or Node on PATH.
- Installed browser: fixed default, opt-in selection, passive preview, validation,
  Start and successful completed-run capture summary verified. Exact allocated
  path and one copied output displayed. Normal narrow side-panel layout inspected;
  no browser console errors observed. The test server exited after explicit Quit.
- `application_version.py --base-ref origin/main` and `git diff --check`: passed.

## Failed attempts and limitations

The first restricted-sandbox pytest invocation stalled in the asynchronous test
client and was interrupted; the focused suite passed outside that sandbox. Initial
new tests used a nonexistent artifact URL (two failures, 107 passes); corrected
to the actual `/api/artifacts/{id}/file` endpoint before the passing run. Initial
frontend commands lacked Node on PATH; the existing bundled Node runtime resolved
that. An ESM test bundle failed on React's CommonJS dynamic require; the CommonJS
bundle passed all five checks. Both existing build environments lacked setuptools;
no-isolation attempts failed, then isolated builds succeeded without changing
those environments.

No Windows/macOS, other browser engines, all-theme/wide-layout sweep, GPU solver,
large scientific workload, sustained stress or hostile concurrent filesystem
mutation testing. The unique-folder policy requires cooperative simulation code;
unknown outside writes cannot be inventoried or inferred. Checking directory
identity does not sandbox a script or eliminate external path races during
capture. Original/reference files still need independent backup. Existing large
source-inventory/archive-consent limitations (#61) are unchanged. The complete
unrelated repository suite was not run.

## Owner verification

1. Use a disposable copy of a script that honors `SIMSHELF_OUTPUT_DIR` (see
   [Running](../RUNNING.md#unique-output-folders-for-cooperating-scripts)), or uses
   joined `run.output_dir`. Ensure its `mkdir` accepts an existing folder. Keep
   fixed arguments from overriding the environment contract.
2. Confirm existing saved configurations open with fixed behavior. Select
   **Unique subfolder for each run**, validate, and run twice with identical
   parameters. Verify different capture paths, both original results intact,
   matching downloads and unchanged source comparison.
3. Start two overlapping runs with a cooperating longer script. Verify separate
   originals and run associations; stop one and inspect its interrupted status
   and retained partial outputs.
4. Declare a fixed output outside the generated directory. Confirm the warning,
   acknowledge only in this disposable test, and verify omissions are explicit.
5. With optional archive consent for the configured parent and `result.csv`,
   check each run's archived bytes and commit. Reference-only originals and the
   external Git archive require separate backups.
6. Review this PR and version check before any owner-controlled merge. No release
   or next-issue work is authorized by this handoff.
