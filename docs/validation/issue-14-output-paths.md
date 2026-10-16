# Issue #14 output destination validation

Date: 2026-10-16. Pending owner review; no merge or release is claimed.
Base: accepted main `67da4b3` (PR #13), which includes portal PR #8.
The existing dedicated issue #14 branch was clean and equal to main before work.
Previous issue branches were already absent locally and remotely.

## Design and scope

Output declarations are optional per-simulation execution settings, stored in the
existing JSON record. Each declares a file or directory, using an exact argv token
and index (whole-token or option=path form), or a fixed path. Common output flag
names offer explicit mapping buttons, not automatic semantic assumptions. Custom
flags and multiple locations use the same editor. Changed token bindings must be
confirmed again; argv is never silently rewritten. An explicit suggestion button
changes only the selected token. Relative declarations resolve from cwd; capture
remains relative to the registered root. Paths are literal, without expansion.

The token-protected path-review endpoint reads only declared path metadata and
ancestry. It does not execute Python or scan extra locations. Outside targets and
symlink exclusions require per-launch acknowledgement, checked by server and
supervisor. The launch-time review is frozen with the existing run metadata.
Undeclared outputs remain unknown and do not prevent normal execution.

Overview and Files distinguish capture inspection from retention, show the frozen
capture folder and all existing automatic counts, and explicitly identify zero
observed files or unavailable historical counts. References remain external;
only copies are included in backups. No changes to capture traversal, rules,
limits, overlap ownership, source snapshots, completed records, or process cleanup.

Additional post-run external-reference registration was considered and deferred:
it would need explicit ownership/provenance/backup rules beyond this single-root
capture contract. Declarations do not add capture roots or register artifacts.
No data was moved or deleted; all validation fixtures are outside the checkout.

## Validation performed

- TypeScript typecheck and production frontend build passed using locked
  dependencies. No dependency changes.
- Four frontend tests passed: zero-observation/complete wording, partial and
  historical count handling, unknown/stale mapping guidance, and candidate token
  indices including repeated flags, equals form and `--` boundaries.
- Python boundary suite: **53 passed**, covering output review, portal execution,
  capture/backup and recording. After refining symlink/parent resolution, the
  **12 output tests passed again**. One existing Starlette/httpx deprecation warning.
- Output tests cover custom equals arguments, paths with spaces, cwd resolution,
  fixed/multiple declarations, literal `$HOME`/tilde, stale/invalid/oversized
  mappings, authorization, forbidden capture roots, symlinks and loops. A real
  script writes a WVZ fixture plus three CSV files beside source: capture counts
  are zero, and an unacknowledged launch is rejected without creating a run.
  An aligned failed run records three copies, one reference, one ignored file,
  one skipped oversized file and partial capture. Reference availability,
  immutable earlier run metadata, saved mapping backup/restore and unchanged
  snapshots are checked. Existing portal tests cover overlapping concurrent
  capture roots and distinct-root execution, interruption and server shutdown.
- Final headless Chromium flow passed: explicit common-option mapping,
  mismatch acknowledgement, stale mapping confirmation, zero-observation run,
  explicit alignment suggestion, spaces, settings reload, and actual launches.
  The aligned run displays three copied CSVs and one available WVZ reference.
  Desktop 1360x1000 and narrow 390x844 screenshots were inspected; no page/dialog
  horizontal overflow and no page errors. All files were synthetic fixtures.
- Wheel/sdist build and fresh wheel installation passed. Checked packaged new
  modules/frontend/tests and bundled asset bytes. With Node absent from PATH,
  the installed package served the UI, reviewed mappings, rejected an
  unacknowledged mismatch, and completed an aligned run with one reference.
- Full bundled third-party licenses are unchanged. Generated linked legal
  comments retain the same notices, reordered by the bundler's import traversal.
- Whitespace and scoped file review passed. Historical reports are untouched.

Developer commands (use an external build/test environment as documented in README):

```sh
node node_modules/typescript/bin/tsc --noEmit
node_modules/esbuild/bin/esbuild frontend/outputs.test.mjs --bundle --platform=node --format=cjs --outfile=/tmp/simshelf-outputs.test.cjs
node --test --test-isolation=none /tmp/simshelf-outputs.test.cjs
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/src" python -B -m pytest -q -p no:cacheprovider --basetemp=/tmp/simshelf-output-tests tests/test_output_paths.py tests/test_portal.py tests/test_capture_backup.py tests/test_recording.py
node frontend/build.mjs
```

Python 3.14.8 and Node 24.19.0 were used. Disposable artifacts are under
`/tmp/simshelf-issue-14-{build,ui,package}`; these are not durable published links.

## Corrected failures and limitations

The first output test run found that non-strict `Path.resolve` on Python 3.14
can leave a symlink loop unresolved. An explicit metadata check now reports it
as a path-review error. Review also caught normalization before symlink resolution;
that was corrected and a symlink-plus-parent traversal regression was added.
One test invocation named nonexistent separate capture/backup modules; no tests
ran, then the actual combined module was used. Frontend server-render tests
initially bundled React as ESM, which failed on its dynamic require; CommonJS
bundling passed. An initial frontend staging command used a directory before
creating it; no files changed in that failed invocation. A license-block comparison
initially included the last block’s trailing newline; normalizing block whitespace
confirmed that only block order changed. The final package check passed.

Only Linux and headless Chromium were validated. Other browsers/platforms,
screen readers, physical touch, remote/network filesystems and long runs were
not tested. Unrelated launcher/version suites were not rerun. Declarations cannot
prove where arbitrary code writes or that an expected file exists; scripts that
change cwd internally or interpret paths specially need suitable declarations.
Filesystem changes after review remain possible. Suggestions do not create
folders or prevent a script from overwriting its own results. Extra locations
are neither scanned nor automatically backed up. No scientific reproducibility
claim is made.

## Owner verification

1. Use a disposable simulation with `--wvz PATH` that writes a small WVZ fixture
   and three CSVs to that path's parent. Set capture to `outputs`, and arguments
   to `--wvz test-simshelf.wvz`.
2. In Start simulation, select **Map argument 2 as file**. Confirm the resolved
   capture folder, outside warning and suggested argument. Validate: Start must
   require the explicit outside-coverage checkbox. Proceed intentionally.
3. Inspect the run's Overview and Files: execution may complete, but capture
   shows zero eligible observed files and makes no claim that the external WVZ
   or CSVs were preserved. Check the source folder still contains them.
4. Reopen Start simulation, set capture to `outputs with spaces`, and choose
   **Use suggested path**. Confirm the exact argv change, save/reopen and validate.
   Launch: under default rules expect three copied CSVs and a WVZ reference.
5. Change a mapped token: validation/launch must wait for confirmation or removal
   of the stale mapping. Try a custom argument, an option=path token (choose its
   format), and a fixed directory declaration using **Declare output path**.
6. Verify narrow-window and keyboard use. Check partial/failed-run counts and
   verify editing future settings leaves earlier commands, reviews and snapshots
   unchanged. Back up a disposable workspace: copied data should restore while
   reference-only data still requires the original files.
