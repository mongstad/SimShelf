# Issue #2: external development environment and workspace

Date: 2026-10-16. Prepared for owner review; this report does not indicate merge
or release approval. Historical prototype and issue #1 reports remain unchanged.

## Changes and decisions

- `start.sh` delegates to the standard-library `scripts/dev.py`. Normal launch
  uses current source with bytecode writing disabled and does not install anything.
- Explicit `--setup` creates/updates a dedicated external environment, identified
  by a marker tied to this checkout. Unowned environments are refused, including
  an active simulation environment. Package building happens in a temporary copy.
- Environment default: `<checkout-parent>/environments/<checkout-name>`.
  Workspace default: `<checkout-parent>/workspaces/<checkout-name>`.
  `SIMSHELF_DEV_ROOT` changes the parent; `SIMSHELF_DEV_ENV` overrides the
  environment. Resolved environment paths must be outside the source checkout.
- Launcher workspace precedence: `--workspace` before the mode selector,
  `SIMSHELF_HOME`, external default. Relative paths use the invoking directory.
  Explicit workspace choices may intentionally select a legacy checkout workspace.
  Installed CLI/API defaults remain compatible (`~/.local/share/simshelf` when
  neither workspace argument nor `SIMSHELF_HOME` is set).
- Default startup detects `.simshelf`, including a dangling symlink, and stops
  with explicit continuation/recovery guidance. No automatic move or deletion.
  README migration uses existing checked backup/restore into a new/empty location.
- `--cli` shares the launcher paths; the child simulation keeps the terminal PATH.
  `--demo` keeps its library, copied example sources and outputs external. Each
  batch registers a fresh source folder and retains prior reference targets.
- README covers setup, recording, editor workspace selection, overrides, migration,
  tests and builds outside the authoritative checkout. Conventional explicitly
  requested editable installs remain supported and can create packaging metadata.

No database schema, scientific capture/version semantics, bundled frontend assets,
package runtime source or historical evidence were changed.

## Validation

Validation products are temporary external files; no user workspace was migrated.
Linux only. Focused tests used Python 3.12; real setup used Python 3.14.8.
Setup resolves `pyproject.toml` ranges; its tested environment included FastAPI
0.143.3, Starlette 1.8.0, pytest 9.1.1 and HTTPX 0.28.1.

- Focused launcher, recording and backup tests: **25 passed**. Checks cover paths
  with spaces, precedence, empty/unsafe paths, legacy refusal and explicit use,
  unowned environment refusal, retained records after source updates, backup and
  restore with snapshot/parameter/note/log/copied-output preservation, refused
  nonempty restore destinations, and two demo batches without checkout products.
- Initial focused run: **1 failed, 24 passed**. Repeated demo batches exposed the
  example's hard-coded simulation ID after registering a new external source.
  Passing the actual registration ID fixed it; the regression check passes.
- After strengthening the source-update persistence assertion and clarifying demo
  output instructions, the six launcher checks passed again.
- API integration checks on the new setup environment: **3 passed**, with the
  existing Starlette HTTPX test-client deprecation warning.
- Explicit fresh setup completed in a disposable source checkout. Real loopback
  HTTP launch served HTML, JavaScript, CSS and license notices. Four demo runs
  retained three successes and the deliberate failure. Screenshot upload/download
  preserved exact bytes; backup/restore retained all four runs and the screenshot.
  A complete file/hash inventory stayed unchanged, including ignored files.

- Wheel and source-distribution builds passed in an external copy. Archive checks
  confirmed bundled assets/licenses match source exactly, no wheel bytecode, and
  the source archive includes the launcher helper, focused tests and this report.
- A fresh wheel-only environment (Node absent from PATH) passed real CLI/example
  recording: one success and one deliberate failure, parameters, measurements,
  copies, references, blob hashes, backup/restore and HTTP-served UI/licenses.
- An explicit editable install in a disposable external source copy passed editor
  context recording with retained parameters and a measurement.
- Shell syntax, Python parsing and `git diff --check` passed. Historical reports,
  architecture and all existing frontend assets compare unchanged to accepted main.

## Limits and owner checks

No visual browser interaction or non-Linux validation was performed. Network
access is needed for initial dependency installation; no offline provisioning or
universal interpreter management is claimed. Setup may leave its owned environment
partially installed after interruption; rerun `--setup`. It never adopts an
unrelated environment. Concurrent setup in the same environment is not supported.

Backup/restore does not relocate registered source folders or reference-only
outputs, and excludes unreferenced workspace files. Retain originals and backups
until checked. No legacy user data was modified for validation. Direct user
scripts can still write wherever they choose; the launcher does not rewrite their
output paths. Frontend Node dependencies are separate from these Python defaults.

Owner verification (use disposable data first):

1. In a fresh checkout run `./start.sh --setup`, then `./start.sh`. Confirm the
   printed workspace is external and the browser opens an empty library.
2. Run `./start.sh --demo`, then open the printed workspace using
   `./start.sh --workspace /absolute/demo/path`. Inspect three completed runs,
   one deliberate failure, parameters, screenshots, source and file references.
3. Set `SIMSHELF_HOME` to a custom external folder and use both normal launch and
   `./start.sh --cli list`. Confirm they select the same persistent library.
4. With a disposable legacy `.simshelf`, verify default launch stops. Follow the
   README backup/restore instructions, compare records and retained files, and
   confirm the original is still available. Never test on the only copy of data.
5. Check `git status --short` and inspect for ignored generated products. Review
   the external folder layout before using it with personal simulations.
