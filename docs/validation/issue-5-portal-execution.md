# Issue #5: local portal execution

Date: 2026-10-16. Prepared for owner review; this report is not merge or release
approval. Issue #2 was accepted through PR #6 before implementation. Its launcher
and workspace migration logic and earlier issue evidence remain unchanged.

## Scope and contracts

The portal can register a source folder, select/update its registered Python entry,
validate/save an existing interpreter and execution settings, explicitly launch,
monitor, and stop a local recorded run. Separate argument fields and an exact argv
preview avoid shell parsing. CLI/editor recording remains supported.

Execution reuses `record_command`, `Run`, journal events, source snapshots and the
transactional output-root collision check. A dedicated supervisor owns each portal
record, with server control-pipe EOF triggering cancellation on stop/shutdown/crash.
Cancellation sends SIGTERM, then SIGKILL after three seconds if necessary. A script
that exits while descendants remain is interrupted and the remaining group is
stopped. Startup, capture and dead-recorder failures retain their own diagnostics.

Saved simulation execution settings use the existing JSON record, without a schema
migration. Completed runs retain original commands, versions, source and output
policies. Registration/entry selection does not execute source. Validation only
runs an explicitly selected interpreter's isolated version probe. Nothing installs
or provisions a simulation environment, rewrites source, migrates user data or
couples to Wavez. README and architecture document limits and path precedence.

## Focused validation

Linux, Python 3.14.8 and Node 24.19.0. All workspaces, interpreter installs, builds,
browser downloads and screenshots used synthetic data under temporary external
folders, not personal simulation workspaces.

- Initial API/portal/recording/backup checks: **40 passed**. After adding entry
  repair and cancellation edge cases: **44 passed**. These are focused checks from
  `tests/test_portal.py`, `test_recording.py`, `test_capture_backup.py`, and
  `test_api.py`, with bytecode/cache output disabled and pytest temp paths external.
- Coverage includes same-origin/token checks; rejected shell-command fields;
  missing/wrong/unresponsive interpreters; missing/escaping/excluded entry files;
  invalid cwd/argv/output roots; spaces, metacharacters and empty arguments;
  actual Python API joining one wrapper record; settings across app restart and
  backup/restore; logs, metrics, annotations, source and retained outputs;
  missing dependencies, invalid script arguments, nonzero exit; simultaneous
  launches and overlapping capture roots; explicit stop/escalation; cancellation
  before child creation; in-group descendant cleanup; graceful server shutdown;
  SIGKILL of the HTTP server and subsequent interrupted-state recovery. Entry
  changes preserve existing run history and the registered version file.
- Two additional source/version edge-case checks passed after the recorder changes.
- Existing Starlette HTTPX test-client deprecation warning remains. No failing
  Python check in these runs.
- TypeScript typecheck and frontend build passed using the existing locked
  dependency installation in an external build directory. Rebuilt JS/CSS assets
  are included; full dependency license notices compare byte-identical.
- Initial `pnpm run` in the sandbox attempted a dependency-status/store operation
  and failed to open its SQLite store. A subsequent direct invocation lacked Node
  on PATH. Using the known absolute Node executable with the locked TypeScript
  binary and `frontend/build.mjs` passed; no repository dependency change was made.
- Headless Chromium exercised actual browser registration, interpreter/path
  validation, saved settings, exact arguments, live logs, a successful run with
  parameters/artifacts, stderr from an intentional failure, and explicit stop.
  No page JavaScript errors. Desktop (1360×1000) and narrow (420×900) launch-form
  screenshots were inspected; no horizontal page overflow at the narrow size.

- Wheel and source-distribution builds passed in an external source copy. Archive
  checks found the new supervisor modules, portal UI source, tests and report;
  installed static assets and license notices matched the built source bytes.
- A fresh wheel runtime with Node absent from PATH and no checkout PYTHONPATH
  passed actual HTTP-served UI/assets, registration, portal recording with the
  Python API joining one record, literal arguments, measurements, copied and
  referenced outputs, explicit stop, and backup/restore with exact snapshot and
  parameter preservation. All servers used for these checks were stopped.

## Limits

Portal process control is Linux-only. The browser check uses headless Chromium;
other engines, operating systems and long-running/high-volume jobs are untested.
No automatic dependency check/install or environment recreation is claimed.
Inputs, packages, code edits during a run and external data can still affect results.

Process ownership covers ordinary foreground scripts and their process group, not
programs that daemonize or create separate sessions. Direct supervisor termination,
machine failure and uninterruptible OS I/O can prevent cleanup/final capture.
Interrupted/incomplete status never proves all external processes have stopped.
The browser cannot stop CLI/editor recorders or a recorder owned by another server.
A prior supervisor may still be completing cancellation/capture after restart.

The UI polls every three seconds. Logs retain the existing 10 MB/stream cap with a
200 KB browser tail. Startup acknowledgement is bounded at 30 seconds; timeout
requests cancellation and advises checking retained runs. Each server permits up
to 32 supervisors. Graceful shutdown waits up to 15 seconds after requesting all
cancellations; independent supervisors finish capture without being forcibly lost.

## Owner verification

Use disposable simulation folders and workspaces before personal experiments:

1. Start SimShelf normally. In **Add simulation**, enter an existing source folder
   and relative `.py` entry file. Verify registration does not execute it.
2. Select the simulation and **Start simulation**. Enter its existing absolute
   Python path. Check the visible source/entry/cwd, output folder and command array.
   Validate, add `--seed` and `42` as separate tokens if the script supports them,
   and use a value with spaces. Confirm editing any execution field invalidates
   the previous validation. Save settings, close/reopen and verify persistence.
3. Start explicitly. Verify a single run, live stdout/stderr, elapsed time, then
   final parameters/measurements and copied/reference artifacts. Scripts using the
   Python API must use this registered simulation ID and remain one run.
4. Try a missing interpreter, missing dependency and unsupported script argument.
   Expect validation errors or failed records with real exit status/stderr; no
   environment installation and no silent success.
5. Start a long foreground script, use **Stop run**, and inspect interrupted state
   and capture details. Repeat, close the browser tab (run continues), then stop
   the server (cancellation requested). Restart and inspect retained state/logs.
6. Try two starts watching the same capture folder: one must be rejected. For
   distinct folders, also point each script at the correct output folder.
7. Confirm terminal/editor recording still works and cannot be stopped from this
   server's portal controls. Back up and restore a disposable library; verify
   records and saved settings, then revalidate machine-specific interpreter paths.

No merge, release, manual issue closure or Project status change is authorized by
this evidence. Stop at the implementation PR for owner review.
