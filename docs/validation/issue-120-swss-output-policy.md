# Issue #120 — SWSS output ownership and launcher allocation

Validated 2026-10-22. Accepted SimShelf main:
`3399ac2023999fcd5bfb68a5c7d380b334950ca8` (0.1.0.43, merged PR #119).
Proposed application build: **0.1.0.44**. Issue #120 was the first and only Ready
item on the SimShelf Project board. Its existing linked branch began at accepted
main. Required output-policy work in PRs #70 and #113 was already merged. Previous
issue branches were absent; no historical evidence needed removal or rewriting.

Accepted SWSS main was checked at
`285ab0d6c06cc3b88e421a2c00577e72c650c750` (merged PR #37). Metadata/schema validity
and source-byte binding do not establish the optional coordinated-capture-root
agreement. This change introduces no portable contract or schema migration.

## Reproduction and implementation

Before editing, a disposable baseline launch of the standalone scalar-decay
reference with `per_run` completed with exit 0 but partial capture and zero copied
files. It left two siblings: the simulation-owned directory containing four files,
and SimShelf's empty `run_<run-id>` directory. The reference was version 0.1.3,
copied without modification from `Simulation-Standards/examples/decay`:

- `simulate.py`: SHA-256 `48a0b582d8bceb007a547dfc891333ad62d766114ffd17eb8284128e04780f41`
- `swss.toml`: SHA-256 `44f9bc668492b4f0957fe77a958e7f9b952da7379867c3bbdf9c16b34f9c6a98`

The launch form now recommends fixed-parent capture for valid associated schema-2
metadata and disables launcher allocation. Its compact indicator separates
metadata validity from listed-byte binding and explicitly disclaims scientific
or full SWSS conformance. Invalid, unsupported, stale or unassociated companions
leave ownership unknown; manual fixed-parent execution remains available after
review. Scripts without a companion retain both existing output policies.

Existing incompatible settings remain visible and blocked. **Use fixed output
parent** changes the draft only; validation/save is explicit. Rescans invalidate
previous validation even in manual mode, and failed scans cannot reuse stale
policy knowledge. Output previews remain hidden while correction is pending.

Save/validate, output preview, portal/supervisor launch and direct recorder entry
all enforce the policy. Recorder entry also rechecks adoption after source capture
and before allocation. Fixed-parent overlap guards remain. SWSS fixed-parent runs
now require a copied new/changed log for complete capture; old unchanged logs are
not attributed to a new run. Process status and capture/archive completeness remain
separate. Completed records, source bytes, original outputs and dated reports are
preserved.

Runtime changes are in `swss.py`, `parameters.py`, `output_paths.py`, `portal.py`,
`api.py`, `recording.py`, `capture.py`, the launch/argument components and their
types/styles. Distributed frontend assets are rebuilt; third-party notices are
unchanged. Current architecture, parameter-discovery and running documentation,
focused regressions and this new evidence report accompany the change.

## Automated validation

- **225 source Python tests passed, no skips**, one existing Starlette/httpx
  deprecation warning, in 55.03 seconds. Used `PYTHONPATH=src`, no bytecode/cache,
  and external disposable fixture directories. Files:
  `test_swss_output_policy.py`, `test_swss.py`, `test_swss_versions.py`,
  `test_isolated_outputs.py`, `test_portal.py`, `test_output_paths.py`,
  `test_recording.py`, `test_capture_backup.py`, `test_preservation.py`,
  `test_git_archive.py`, `test_library_preservation_audit.py`,
  `test_application_version.py`.
- **30 installed-wheel Python tests passed, no skips**, one same warning, in
  15.58 seconds: policy matrix, existing isolated-output suite and the pinned
  reference preservation integration. Dependencies came from the existing
  development interpreter; SimShelf itself was installed into an external target.
- **43 frontend unit tests passed**: outputs, arguments, parameters, parameter
  presentation and parameter hints, bundled to external CommonJS files and run
  with Node's `--test --test-isolation=none`.
- **Five live React DOM browser scenarios passed** with controlled API fixtures:
  policy/binding display and exact argv; saved-policy explicit correction;
  adoption on rescan; unavailable/unbound states; failed scan recovery.
  The harness is `frontend/swss-output.browser.test.mjs`, built with
  `node scripts/test_swss_output_browser.mjs /tmp/<disposable-directory>`.
- TypeScript `--noEmit`, production frontend build, application-version gate
  against freshly fetched `origin/main`, and `git diff --check` passed.

The policy matrix includes bound/unbound, malformed, unsupported, stale,
unassociated and symlink companions. It exercises API save/validate/launch/preview,
direct Python recording, saved settings after reopening, adoption during source
capture, exact aliases/empty/numeric/separator argv, and unchanged history. Existing
plain-script tests retain fixed/per-run allocation and overlap/failure behavior.
SWSS failure/cancellation and missing/ignored/referenced/oversized-log checks pass.

The pinned reference test uses real portal launches, preservation enabled in a
disposable library: two runs under `outputs`, then one under `custom-results`.
Each adds exactly one simulation-owned directory, captures four nonempty files,
and verifies copied blobs and archival Git content against original bytes. The
command and reference provenance retain exact argv, including `-k 1e-1`, `-n 0010`
and an empty label. Earlier originals and records are unchanged. A subsequent
argument failure exits 2, is failed/partial, and captures no historical artifacts.
An incompatible `per_run` request creates no directory.

## Packaging and installed browser

Wheel and sdist were built in an external source copy using isolated build
dependencies; a wheel was rebuilt from the extracted sdist. Both wheels have the
same member set and identical member bytes. Package metadata, Python, CLI,
workspace API, OpenAPI and UI report **0.1.0.44**. Installed assets and notices
match the reviewed source. Startup and the browser UI work with Git and Node
absent from PATH and no runtime network requirement. No package was published.

The installed application used a disposable library and copied reference sources.
A real browser launch completed successfully with four captured outputs. A
previously saved `per_run` selection stayed blocked after reopening; keyboard
activation of the explicit correction changed only the draft, and ArrowDown
could not select the disabled option. Plain-script controls retained both choices.
Light, Dark, Onyx, Slate and Linen were checked at 1366×900 and 390×900 for readable
policy/binding text, keyboard controls and overflow. Screenshots and raw logs are
local temporary evidence under `/tmp/simshelf-120`, not distribution artifacts.

## Failures, reruns and limits

The first combined backend run had two assertion failures: an overlap message
expectation and an old test expecting complete SWSS capture without a log. Both
were updated to the intended behavior. Two archive fixture setup errors reported
changed files/settings; all four affected tests passed in isolation and the final
225-test run passed without those errors. One reference check initially skipped
without the explicit reference path; final source and installed checks supplied
`SIMSHELF_AUDIT_DECAY_REFERENCE` and had no skips.

An initial installed test fixture was nested beneath the installed application
root and correctly refused archive activation; moving fixtures to a separate
external sibling directory produced the passing installed run. Local harness
server reconnection and a mistaken CLI `serve` invocation were validation setup
issues; the documented `ui` command worked. The harness initially emitted React
`act` warnings during its nested startup mount; startup now awaits its own mount
and prevents overlapping test runs. Final browser cases pass after that correction.

This is focused Linux/Python 3.14 and Chromium evidence, not an exhaustive suite,
fresh OS installation, Windows/macOS, GPU or arbitrary scientific workload test.
No scientific equivalence or full SWSS conformance is certified. Shared-parent
capture cannot prove ownership of writes from independent external processes;
overlap guards do not provide filesystem isolation. External source changes after
the final checks remain possible. Required-log checks establish copied evidence,
not log semantic correctness. No historical recapture or user-library migration
was performed.

## Owner verification

1. Install the PR build in a disposable environment/library. Register a copy of
   the pinned reference with its `swss.toml`. Open **New run…**: fixed parent is
   recommended, launcher allocation is disabled, and metadata/binding are distinct.
2. Use `-k 1e-1 -n 0010 --label ''` as explicit argv. Set capture parent `outputs`,
   validate, and run twice. Confirm one new populated reference directory per run,
   no empty SimShelf sibling, four copied outputs and unchanged first-run bytes.
3. Set both `--output-parent custom-results` and capture parent `custom-results`;
   review any archive selection change explicitly. Repeat and inspect the source,
   result blobs, Git archive event and exact argv/provenance.
4. On a disposable script saved with `per_run`, add the reference's valid
   companion, reopen/restart, and confirm blocking without a silent settings
   change. Use the explicit fixed correction, validate and save. Check keyboard
   behavior and narrow layouts in the preferred theme.
5. Check a plain cooperating script still offers both modes; check malformed or
   stale metadata reports uncertainty and allows reviewed manual fixed execution.
   Review process failure versus incomplete capture, and preserved earlier records.

Stop for owner review; no merge, auto-merge, issue closure, Done transition or
release/publication is part of this work.
