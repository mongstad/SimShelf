# Issue #152: primary Python within-version warning

Validated 2026-10-25 on Linux, Python 3.14.8 and the Chromium in-app browser.
Accepted main: `f43670f852cb2458ff2a61c7a9643f337d26c691` (`0.1.0.60`).
Proposed application build: `0.1.0.61`.

## Selection and boundaries

#152 was the first and only Ready item on the SimShelf Project board. Its existing
issue-linked branch matched accepted main and the working tree was clean. No open
PR existed. Predecessor #146 / PR #147 and #150 / PR #151 were merged and their
merge commits were ancestors of main. The preceding #150 branch was already absent
locally and remotely; fetch/prune confirmed main was synchronized (`0 0`). No
historical validation report, user library, source folder or output was changed.

## Implementation

The old warning used stored whole-snapshot `source_change == "changed"`, which
could include helpers, generated copies, JSON, permissions or changed selection.
The new `entrypoint_warning` API projection compares the verified retained primary
Python file against the run's original baseline. Exact bytes, including comments,
must differ, while captured Python declarations and the associated root SWSS
version remain unchanged. Either declaration changing suppresses this warning;
Python declarations do not override SWSS's authority over the recorded run version.

- `entrypoint_warning.py`: read-only manifest/blob verification, recorded baseline
  lookup, static declaration checks and bounded request-local caches. It reads no
  live scientific source and executes/imports no scientific code.
- `api.py`, `store.py`: the same predicate supplies list/detail/annotation-response
  projections and version-history counts. Snapshot counts and stored whole-source
  classifications retain their existing meanings.
- `recording.py`: new start JSON retains the registered `source_entrypoint`.
  Historical SWSS records use their retained companion/association. No schema
  migration, retrospective row/journal change, rebaseline or fingerprint rebuild.
- Frontend warning component, detail and version history use the projection;
  separate full-snapshot evidence and metadata/stale-binding diagnostics remain.
  Existing neutral comments/formatting hints remain. Bundled JS rebuilt; third-party
  license files unchanged. Architecture/data guidance describes the narrowed rule.

## Validation

Python checks used `PYTHONDONTWRITEBYTECODE=1`, `pytest -q -p no:cacheprovider`,
disposable `/tmp` basetemps, and `PYTHONPATH=src` only for source testing. API tests
ran outside the known sandbox TestClient boundary.

- Initial focused source batch: **53 passed**.
- Expanded source batch: **109 passed**, covering `test_entrypoint_warning.py`,
  `test_source_comparison.py`, `test_swss_versions.py`, `test_version_edge_cases.py`,
  `test_source_output_boundaries.py`, `test_recording.py`, `test_api.py`,
  `test_capture_backup.py`, and `test_application_version.py`.
- After adding bound-source hash-refresh/revert/live-registration and stronger
  immutable-row assertions, the final warning suite passed **27 tests**.
- The installed wheel passed the complete final expanded batch: **110 passed**.
  Tests ran from `/tmp` without checkout imports. A fresh disposable venv reused
  the existing development dependencies read-only through a `.pth`; the installed
  package took precedence. No dependencies were added to a scientific interpreter.
- **5 frontend assertions passed** (3 warning, 2 recorded-version evidence), bundled
  with esbuild and run directly with Node. TypeScript, production build, version
  gate and `git diff --check` passed.
- **5 full-App browser scenarios passed**: primary edit, primary comment, unrelated
  output change, version change and unavailable evidence. Each checked detail,
  access to full-source evidence, run-history warning and version-history count.

Backend coverage includes helper/JSON/TOML-only changes, outputs and copied Python,
permissions, capture paths, arguments, absent/known literal declarations, comment
and structural edits, Python/TOML/both version changes, contaminated old records,
retained deleted SWSS baselines, backup/restore, missing/corrupt/oversized evidence,
dynamic declarations, stale hashes, wrong association, new legacy primary identity,
hash updates without version bumps, source reversion and later registration edits.
Read-only API/count checks preserve exact stored run JSON and managed
snapshot/blob/journal bytes. Existing source comparison, version attribution,
portal execution, exact argv and backup tests also pass.

Validation setup retries: the sandbox API batch was interrupted after stalling;
the shell initially lacked Node on PATH; a new venv initially lacked pytest until
its existing dependency location was linked correctly; a guessed `serve` command
was rejected and corrected to the documented `ui` command. The browser harness
initially missed the arrow in “Back to runs” and a preservation-status mock. These
fixture/setup issues were corrected before the reported final passes.

## Package and real UI evidence

Wheel/sdist and a wheel rebuilt from the extracted sdist were built in external
disposable copies using existing build tools. Both wheels' **38 Python/static
files** matched checkout bytes and reported `0.1.0.61`. Installed import, CLI,
workspace/OpenAPI versions and served UI passed with Git/Node absent from PATH.
The server used only `/tmp/simshelf-152-runtime/library`; no release was published.

Four actual installed `Run` context recordings used a tiny passive Python source
fixture and generated logs (no solver execution): A baseline with an old copied
Python output, A with that tree explicitly excluded, A with a primary comment,
and B with both declarations changed. Only the primary-comment record warned.
The output-only record's source view showed **1 removed, 0 changed, 2 unchanged**,
and the primary preview said **No changes in this file**. The original baseline
remained available. Installed desktop captures:

- [History warning selection](../images/issue-152/installed-history.png)
- [Retained output-only comparison](../images/issue-152/installed-output-evidence.png)

## Limits and owner verification

Python declaration recognition is intentionally static: module literal strings
named `VERSION`, `__version__` or `SIMSHELF_VERSION`, where present. It does not
infer arbitrary application-specific naming or execute dynamic declarations.
The existing 1 MB/file preview bound applies. Missing/corrupt/oversized evidence,
unparseable/dynamic declarations, stale bindings, changed primary association or
unknown historical legacy primary identity yield an unavailable comparison and
no named warning. Removed legacy baselines without recorded identity also remain
unknown; retained SWSS baselines can use their captured companion. Details disclose
unavailability; counts include only positively established warnings.

No owner library or FreeCollapse solver was inspected/executed. Large-history
performance, GPU behavior, other operating systems/browser engines, every theme
and narrow/mobile layout were not tested. No scientific-conformance claim is made.

1. Open an affected historical FreeCollapse run. If the retained primary is
   byte-identical to its baseline, confirm no named warning in history or detail,
   and no contribution to the version's warning count. Source comparison must
   still expose the generated added/removed paths and original baseline.
2. On a disposable copy, record twice with changed argv/output folders but identical
   primary bytes. Expect no warning. Change only a helper, JSON, TOML comment or
   permission and repeat; still no named warning.
3. Add a primary Python comment without changing its version declarations. If SWSS
   lists source hashes, deliberately refresh the changed hash before running.
   Expect the warning in history/detail and one corresponding counted run.
4. Bump the corresponding Python and TOML declarations, refresh applicable hashes,
   and record again. Expect no spurious warning; old runs/versions remain unchanged.
5. Deliberately make a stale-hash case only in the disposable copy. Confirm existing
   SWSS diagnostics and typed/manual safeguards remain visible and operative.
   Restore the fixture deliberately; SimShelf must not rewrite its source.
6. Review the PR and independently check the owner's environment and preferred
   layouts before acceptance. This handoff does not merge or authorize a release.
