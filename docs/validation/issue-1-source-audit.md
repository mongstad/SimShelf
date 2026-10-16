# Issue #1 — initial source checkout audit

Date: 2026-10-16. Prepared for owner review; this report does not indicate merge
or release approval.

Issue: [#1](https://github.com/mongstad/SimShelf/issues/1). Accepted base:
`bce2e08da543c42f88d262511a3a0beae456e88b` (`main`, merged PR #3).
The SimShelf Project listed #1 as its only Ready item; #2 was Backlog.
The existing issue-linked branch was clean and equal to accepted `main` before
work: `1-repo-audit-and-clean-initial-simshelf-source-checkout`.
No prior issue implementation PR existed. PR #3's branch was already absent
locally and remotely; no additional branch deletion was needed.

## Inventory and changes

The accepted tree contained 59 tracked files:

| Classification | Count | Decision |
| --- | ---: | --- |
| Python bytecode under `src/simshelf/__pycache__/` | 11 | Remove from index only |
| Generated `src/simshelf.egg-info/` metadata | 6 | Remove from index only |
| Intentional source, tests, examples, docs, build inputs, license, and UI assets | 42 | Retain |

All 17 untracked local files were checked against their pre-work SHA-256 hashes
and remain unchanged on disk. No local database, source snapshot, journal,
simulation output, or research folder was deleted or migrated.

The four existing packaged UI files (`index.html`, `app.js`, `app.css`, and
`app.js.LEGAL.txt`) are necessary for the no-Node runtime. Their original bytes
are unchanged. The largest tracked file was `app.js` at 271,952 bytes; no large
research results, captures, databases, or vendored datasets were found in the
tracked inventory.

Additional changes within the cleanup scope:

- Ignore QA and alternate local workspaces, example outputs, backup/evidence
  folders, local screenshots, and machine-local agent/credential directories.
- Remove the source-manifest reference to `.npmrc`, which was absent from the
  accepted tracked tree. Include the project license and third-party notices.
- Make `start.sh` executable (mode `100755`), matching the README's `./start.sh`
  command. Its contents and workspace/environment path behavior are unchanged.
- Declare the existing MIT project license in Python package metadata.
- Generate complete bundled licenses from React 19.3.0, React DOM 19.3.0, and
  Scheduler 0.28.0 alongside the existing extracted license comments. These are
  upstream MIT license texts, not newly introduced runtime dependencies.
- Document frozen-lockfile rebuilding and license retention.

Fresh source distributions legitimately regenerate `.egg-info` metadata during
packaging; wheels contain `.dist-info` metadata. These build products must not be
confused with the stale generated files removed from Git's tracked tree.

## Historical exposure assessment

The audit inspected all 60 distinct blob objects reachable from the five
pre-work commits across fetched refs, including binary bytecode. Targeted checks
covered absolute home-directory paths, private-key headers, common GitHub/AWS/API
token formats, SQLite signatures, generated file paths, and large files. The
tracked source and asset inventory was also reviewed.

All 11 bytecode blobs contain absolute developer source paths (redacted form:
`/home/<user>/.../src/simshelf/<module>.py`). They were introduced by upload commit
`d769388` and remain reachable through existing Git history after this cleanup.
No matching credentials, tracked workspace database, simulation captures, or
research outputs were found in the inspected objects. Generic documentation
paths and the intentional copyright attribution in `LICENSE` were retained.

**Removing these files from the index does not erase historical path exposure.**
No history rewrite, force push, tag deletion, or historical report alteration was
performed. Before making the repository public, the owner should decide whether
the developer-path exposure is acceptable or authorize a separate coordinated
history-cleaning procedure. This targeted scan is not a guarantee that every
possible secret format or unreachable/remote-only object has been examined.

## Validation

Linux; Python 3.12.14; Node.js 24.19.0; pnpm 11.25.0; setuptools 84.0.0; wheel
0.48.0. Build/test environments, source exports, generated runs, package archives,
and server logs were placed in an isolated temporary audit directory outside the
authoritative checkout. Python test dependencies used `requirements-dev.lock`.

| Check | Result |
| --- | --- |
| `git ls-files` generated-bytecode/egg-info audit | No unwanted tracked files after index cleanup |
| Local copies of all 17 removed index entries | Byte-for-byte preserved |
| `pnpm install --frozen-lockfile` | Passed without lockfile edits |
| Original frontend rebuild | All four original assets byte-identical |
| Updated frontend rebuild and `tsc --noEmit` | Passed; original assets unchanged; full notices reproducible |
| Missing bundled license in disposable dependency copy | Build failed as expected; dependency restored and rebuild passed |
| Twelve representative ignore-path checks | All ignored; no local records created |
| `bash -n start.sh` and exported executable bit | Passed |
| Clean staged-source sdist and wheel build | Passed with `python -m build --no-isolation` using separately installed build requirements |
| Archive inspection | UI assets and both kinds of notices match source; MIT license/metadata included; examples, lockfile, and test fixtures retained; no bytecode or example outputs |
| Focused source tests below | 12 passed; one dependency deprecation warning |
| Wheel installed into a second fresh environment | Passed |
| Installed-wheel runtime with Node absent from PATH | Packaged HTML, CSS, JavaScript, and both notice files served correctly over loopback |
| Bundled scalar-wave example through installed CLI/API | One completed and one intentional failed run; version, resolved arguments, measurements, copied image, and raw-output references retained |
| Installed-wheel backup/restore | Both run IDs and records retained; copied artifact digests valid |

Focused test command, after installing the clean staged source as an editable
package in the isolated validation environment:

```bash
PYTHONDONTWRITEBYTECODE=1 python -B -m pytest -q -p no:cacheprovider \
  tests/test_api.py tests/test_capture_backup.py \
  tests/test_recording.py::test_wrapper_and_sdk_join_one_run_with_resolved_defaults \
  tests/test_recording.py::test_wrapper_preserves_exit_status_and_stderr
```

The first attempt used `PYTHONPATH=src` without installing the package. Eleven
tests passed and the wrapper/API test failed with `ModuleNotFoundError` after
its child changed working directory. The test setup was corrected by installing
the staged source in the isolated environment, matching the supported editable
workflow. The rerun passed all 12 tests; no runtime code was changed for this.

Observed warnings: Starlette's existing HTTPX test-client deprecation; harmless
setuptools messages for absent excluded generated folders and disabled bytecode
compilation; pip disabled its unwritable cache during the sandboxed editable
install. These did not prevent the checks above.

## Boundaries and owner verification

Launcher relocation, legacy workspace detection/migration, and changed default
storage/environment paths belong to #2 and are not implemented here. Existing
checkout-local `.simshelf` data must remain preserved. No application runtime or
scientific-recording behavior changed. Historical `docs/VALIDATION.md` and
`docs/ARCHITECTURE.md` remain unchanged.

Only Linux/Python 3.12 was exercised in this issue. Python 3.11/3.14, Windows,
macOS, long-running simulations, browser interaction/visual regression, and
exhaustive credential scanning were not repeated. The original UI assets are
byte-identical, and actual HTTP serving was checked; the earlier browser report
remains historical evidence, not a new browser test claim.

Owner checks before merging:

1. Review index deletions and confirm the existing UI assets are retained. Run
   `git ls-files ':(glob)**/__pycache__/**' ':(glob)**/*.pyc' ':(glob)**/*.egg-info/**'`;
   it should print nothing. `git ls-files --stage start.sh` should show `100755`.
2. In a disposable clone of the issue branch, run `pnpm install --frozen-lockfile`,
   `pnpm run typecheck`, and `pnpm run build`. `git diff -- src/simshelf/static`
   should show no asset or notice changes.
3. Create and activate a separate review Python environment outside that clone.
   Run `python -m pip install -e '/path/to/review-clone[dev]'`, run the focused pytest command above, and run
   `python -m build --outdir /path/to/review-packages` from the disposable clone.
   Inspect the resulting wheel for HTML/JS/CSS, both third-party notice files,
   and the project license before installing it into another fresh environment.
4. Launch the installed package with `simshelf --workspace /path/to/new-review-library ui --no-open`. Open the displayed loopback URL and confirm the empty library
   loads. Use only disposable copies of example scripts/results for review runs.
5. Review the historical developer-path exposure before any future public sharing.
   Merging this PR will not remove those paths from older commits.
