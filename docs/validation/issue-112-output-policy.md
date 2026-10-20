# Issue #112 — explicit output allocation policy

Validated 2026-10-20 on Linux, Python 3.14.8. Prepared for owner review;
no merge or publication performed.

## Change and boundaries

The shared `record_command` launch boundary now assigns
`SIMSHELF_OUTPUT_POLICY` from the validated recorder policy alongside the existing
absolute destination. Portal workers and CLI recording delegate to this boundary.
Inherited child-environment values cannot override either assignment. Independent
in-process `Run` contexts do not launch children or assign environment variables.

`fixed` identifies a shared capture parent, potentially absent or occupied;
`per_run` identifies the already exclusively allocated root. Allocation, argv,
cwd, snapshots, capture, schema and historical records are unchanged. Documentation
explains strict adapter fallback and distinguishes this local integration from
SWSS requirements. The accepted SWSS v2.0 capability contract permits documented
application adapters; no standard or reference simulation was edited.

Base: `c9589fb08d00cb49a70fcf16b437a48d73b1a58a` (accepted PR #111).
Issue #69 / PR #70 is merged and its merge is an ancestor of this base.
Application version: `0.1.0.40` → `0.1.0.41`.

## Validation

- Source tests: **123 passed**, one existing Starlette/httpx deprecation warning.
  `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1
  /home/Nozba/Codex/SimShelf/environments/SimShelf/bin/python -m pytest -q
  -p no:cacheprovider --basetemp /tmp/simshelf-112-tests-live
  tests/test_isolated_outputs.py tests/test_portal.py tests/test_recording.py
  tests/test_git_selection.py tests/test_git_archive.py
  tests/test_application_version.py`.
- New six-case matrix: portal/CLI/Python launch × fixed/per_run, twice each.
  Conflicting inherited environment, non-root cwd, exact argv (empty token,
  repeated options, numeric spelling, delimiter, literal variable), original
  destination semantics, preallocation, copied JSON bytes/run attribution,
  unchanged prior records and generated-output snapshot exclusions checked.
- Existing coverage passed for concurrent distinct per-run roots, joined API,
  scripts ignoring the discriminator/no SWSS companion, overlap rejection,
  cancellation, failures, replaced directories, capture budgets, archive and backup.
- Installed wheel: **19 passed**, same warning, running
  `tests/test_isolated_outputs.py` with `PYTHONPATH` pointing only to the disposable
  installation and a separate temporary test directory.
- External wheel and sdist built; extracted sdist rebuilt to wheel. All three
  metadata versions agree at `0.1.0.41`; both wheels contain the new assignment.
- Installed Python, CLI, `/api/workspace`, OpenAPI version and static HTML passed
  with Git/Node absent from PATH. Runtime smoke checks made no network requests.
- Application-version gate and `git diff --check` passed. Frontend sources and
  distributed assets are unchanged; no frontend rebuild required.

## Failures and limits

The first sandboxed test run stalled without output and was interrupted; the
reported complete run used unrestricted process execution and disposable fixtures.
The first no-isolation package build lacked setuptools; isolated temporary build
dependencies resolved it without modifying the application environment. The first
ad hoc smoke assertion used the wrong response key (`application_version`); corrected
to the existing `version` key and passed. No product fix was needed for these checks.

No GUI/browser label inspection, Windows/macOS validation, GPU/scientific solver
execution or full SWSS conformance claim. Existing dependencies were reused for
installed runtime checks; this is not a fresh operating-system installation.
Fixtures/builds remain under `/tmp/simshelf-112-*`; no owner research data was used.

## Owner checks

1. Use a disposable simulation that prints both environment values and writes a
   uniquely identified text result. Set cwd to a child folder and capture to a
   different root-relative folder.
2. Launch twice with Fixed folder: policy is `fixed`, destination is the shared
   parent, and a cooperating adapter exclusively creates its own child each time.
3. Launch twice (and concurrently) with Unique subfolder: policy is `per_run`,
   each destination exists before script startup, and results go directly there
   without an additional run-root directory.
4. Inspect captured bytes/run attribution, preserved earlier originals, exact argv
   and source snapshots. Confirm the restarted portal shows `0.1.0.41`.
5. Review the adapter documentation before separately updating Simulation-Standards
   PR #30 after this PR is accepted; that work is outside this change.
