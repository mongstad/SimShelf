# Issue #18 application versioning validation

2026-10-17. Pending owner review; no merge, tag, release or publication claimed.
Accepted base: `eb9a5fc9155a76bbeaed38c4f0f808ffeb1f0b11` (PR #20).
Issue #18 was the sole Ready Project item. Its existing dedicated branch was
clean and equal to accepted main, with no open PR. Prior issue branches were
already removed; historical validation reports remain untouched.

## Implementation

Single source: `src/simshelf/_version.py`, first numbered build `0.1.0.1` after
historical `0.1.0`. Setuptools dynamic metadata, Python, CLI and existing API
agree. The existing upper-right label now reads the server value; its location
and styling remain unchanged. Unavailable connection never displays a guessed
version. Scientific example tags retain `0.1.0` deliberately.

`scripts/application_version.py` checks or explicitly writes the next version
from a supplied accepted Git ref. Repeated writes against the same accepted base
are idempotent; duplicate/skipped/conflicting versions fail checks. Default BUILD
increments once per implementation PR; explicit owner-directed version-line
changes reset lower components. Runtime never uses this developer Git tool.
Policy and release authorization boundaries are in `APPLICATION_VERSIONING.md`
and AGENTS.md. No tags/releases/publication or repository settings changed.

## Checks performed

- `tests/test_application_version.py tests/test_version_edge_cases.py
  tests/test_recording.py`: **26 passed**, Python 3.14.8. Existing Starlette/httpx
  deprecation warning only. Checks cover CLI/API/Python/source agreement,
  no CLI workspace creation, PEP 440 ordering, historical transition, repeatable
  explicit bumps, duplicate/conflicting proposals, version-line resets and
  scientific version/snapshot/recording regressions.
- `python scripts/application_version.py --base-ref origin/main`: passed,
  `0.1.0` → `0.1.0.1`. No implicit source mutation or increment at runtime.
- TypeScript check and frontend build passed with Node 24.19.0. Bundled JS updated;
  CSS and both third-party notice files are unchanged.
- Built sdist and then wheel from that sdist in an external disposable copy.
  Both metadata versions are `0.1.0.1`; source version, policy tool, tests,
  frontend source and policy documentation are included. Wheel assets/notices
  match the source copy byte-for-byte.
- Fresh wheel environment installed successfully. Package metadata, Python,
  installed `simshelf --version` and FastAPI/OpenAPI agree. Runtime PATH contains
  neither Git nor Node. Application construction and OpenAPI inspection passed
  with socket connections blocked; dependencies had been installed beforehand.
- Headless Chromium against both source and installed-wheel servers: one existing
  `.topbar .local-badge` shows `Local · 0.1.0.1`; API agrees. A controlled alternate
  API version is reflected in that same label, proving it is not baked into JS.
  A simulated API failure shows `Version unavailable`. Desktop 1360×900 and narrow
  390×844 labels stay visible, with no page horizontal overflow or page errors.
  Narrow screenshot inspected. Browser external requests were blocked; servers
  ran without Git/Node on PATH.
- Scoped diff/whitespace review passed. All build metadata, test libraries,
  screenshots and installations remained under `/tmp/simshelf18-*`, outside the
  checkout and user workspaces. No simulation source/data/output was modified.

No unexpected check failures. Expected rejection cases are automated assertions.
Temporary package/browser verification scripts and captures are local disposable
evidence, not published artifacts. The committed Python tests and documented
build procedure are reusable checks.

## Limits and owner verification

Linux/headless Chromium only; no other platforms/browsers, GPU workloads or long
scientific runs tested. Broader capture/backup/launcher suites were not rerun for
this version-only change. No claim of bit-for-bit identical archives, scientific
reproducibility or remote CI branch protection. Duplicate prevention is a required
accepted-main review check; parallel PRs must recheck after another merges.

1. Run `./start.sh --cli --version`; expect `SimShelf 0.1.0.1`. Restart the UI and
   reload: the established upper-right label should show `Local · 0.1.0.1`.
2. Compare `simshelf.__version__`, `/api/workspace` version and installed package
   metadata in a disposable wheel environment. Use the documented external build
   procedure; ensure Git/Node are absent from the runtime PATH.
3. Confirm existing scientific model tags and completed run details have not
   changed. This issue changes no database schema or scientific version logic.
4. Review the numbering/owner-release policy. Run the version check against fresh
   accepted main before merging. Do not create tags/releases from this PR unless
   separately authorized.
