# Issue #61 — Source inventory and generated output boundaries

Validated 2026-10-18 on Linux, Python 3.14.8 and the Codex in-app browser.
Accepted base: `e276edd` (merged PR #70, application 0.1.0.18).
Proposed application version: **0.1.0.19**. Owner review is required; no merge,
release or storage migration is part of this work.

## Implementation and decisions

`git_selection.inventory` previously enumerated the entire source tree before
inclusion rules were applied. Both file-selection/ignore reviews and archive
settings preview, automatic status and recorder preparation consume that inventory.
Generated results could therefore block archival even when none were selected.

The configured base capture directory is now a traversal boundary. Its entry is
counted and fingerprinted, but descendants are never enumerated by source inventory.
This covers default `outputs/`, nested output histories, custom nested capture
folders and #69's per-run children. The declared path also enters the revision,
so changing it invalidates an outstanding review. Existing location bindings and
saved rules remain intact. Symlinks are classified as blocked, never followed.
Git classification uses inventoried literal file paths in batches of at most 100,
so the classification request does not select generated descendants either.
Tracked/ignored indicators and index signatures remain scoped to visible files.

No filename heuristic, source-extension allowlist, `.gitignore` filtering or
snapshot-exclusion filtering was added. Those could hide explicitly useful source
or configuration files and couple independent selection contracts. Unrelated
folders named `outputs` remain visible and count toward the limit. The UI names
the capture boundary and directs users to separate future-output rules.

The 1,000-entry, depth-20 and five-second-between-directory-scans bounds remain.
The capture boundary itself and its source-side ancestors count toward the bound.
Git retains its three-second/4-MiB bound per command. Automatic output selection,
capture rules, per-run archive limits (1,000 files / 25 MiB each / 100 MiB total,
including additions), scientific records and archive history are unchanged.

Archive action feedback is displayed beside the toggle and within the settings
panel beside Review. Failures are announced as alerts, refresh authoritative
state and cannot imply consent. Successful/canceled action messages use the same
nearby feedback locations. The bundled UI was rebuilt; license notices unchanged.

## Validation

- **70 Python tests passed**, one existing Starlette/httpx deprecation warning:
  `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 /home/Nozba/Codex/SimShelf/environments/SimShelf/bin/python -m pytest -q -p no:cacheprovider --basetemp /tmp/simshelf-61-source-tests tests/test_git_selection.py tests/test_git_archive.py tests/test_application_version.py`.
- New cases cover 3,301 nested generated outputs, default/custom capture roots,
  proof that source traversal never enters the capture tree, literal Git path
  selection, useful JSON/source files outside that tree, genuine oversized source
  inventory, changed capture boundaries, symlinks and stale review rejection.
- Integration cases verify selected source plus new CSV/JSON archives with 3,301
  pre-existing outputs in both fixed and per-run modes, exact historical download
  bytes, intact original outputs and unchanged archive constants. API refusal
  leaves consent disabled. Existing tests cover source/index/preference races,
  ignore writes, repository identity, restored bindings, capture changes,
  cumulative archive budgets, recovery and immutable run records.
- **18 frontend tests passed**: archive (12), Git file selection (6), bundled with
  esbuild as CommonJS into `/tmp/simshelf-61-ui-tests` and executed directly with
  Node. `pnpm run typecheck` and `pnpm run build` passed.
- Wheel and sdist built outside the checkout. The default build generated a wheel
  from the sdist; a separate direct-source wheel had identical members and bytes.
  Verified 0.1.0.19 metadata, bundled UI, license notices, guide and regression tests.
  A fresh disposable environment installed the wheel and its dependencies.
  Python/CLI/API/OpenAPI versions agreed; API/UI startup passed with
  `PATH=/nonexistent` (Git and Node unavailable), with no runtime dependency fetch.
- Installed browser checks passed at **479 px** and **1,534 px** widths. Selected
  source/configuration and capture exclusion appeared despite 3,301 generated
  files. `*.csv`/`*.json` review required confirmation; enabled state and rules
  persisted on revisiting. Desktop cancel retained consent and restored focus.
  Genuine source-limit refusals appeared beside both the toggle and Review;
  consent stayed OFF. Text wrapped without obscuring the controls. No browser
  console errors were reported during these checks. Explicit Quit completed and
  the disposable server exited.
- Version-policy check against accepted `origin/main` and `git diff --check`
  passed. All fixtures, environments and package artifacts stayed outside the
  checkout; original user workspaces and historical evidence were untouched.

Local disposable artifacts and browser screenshots are under
`/tmp/simshelf-61-package/`; they are not shipped as user data.

## Failed attempts and limitations

The first Python invocation omitted `PYTHONPATH=src` and tested installed 0.1.0.18:
63 passed / 7 failed, including the new regressions and source-version mismatch.
The corrected invocation above tested the changed source and passed. The initial
server command used unsupported `--no-browser`; corrected to `--no-open` before
browser validation. No application change was made for either invocation error.

No Windows/macOS, other browser engines, all-theme sweep, large scientific solver,
sustained stress, or hostile concurrent filesystem-mutation validation. Metadata
revisions do not sandbox external editors. This change does not increase capture
or Git budgets, scan arbitrary outside output trees, or guarantee archival of
files excluded by source snapshots. Source inventory still refuses genuine bound
violations instead of presenting a partial inventory. The unrelated complete
repository suite was not run.

## Owner verification

1. Use a disposable simulation with a few Python/JSON source files and over 3,300
   files beneath its configured File capture directory. Confirm that both default
   `outputs` and a custom nested capture folder allow Manage Git files to open.
   Verify source/configuration selections and the visible capture exclusion.
2. Connect a disposable master archive, select source files, enter `*.csv` and
   `*.json` under Future outputs, and review/confirm. Verify the switch changes
   only after confirmation. Cancel another review and check that consent remains.
3. Run a cooperating disposable script producing new CSV/JSON outputs in the
   capture directory, in fixed and unique-per-run modes. Compare downloaded archive
   bytes with those outputs and ensure older original output files remain intact.
4. In a separate fixture with over 1,000 actual source entries outside capture,
   try the toggle and Review at desktop and narrow widths. Verify the visible
   reason and recovery guidance, no consent dialog, and unchanged OFF state.
5. Change source selection or capture settings between review and confirmation;
   require a fresh review. Review the PR/version gate before any owner merge.
