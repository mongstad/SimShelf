# Issue #39 — Project overview and first-run documentation

Validated 2026-10-18 on Fedora 44, Python 3.14.8, Git 2.56.0 and the Chromium-based
Codex browser. Review-time evidence; not a release or production certification.

## Scope and decisions

The sole Ready item was #39. Existing dedicated branch
`39-docs-refocus-readme-on-project-vision-and-add-getting-started-guide` was clean
and matched accepted main `61f9cff2c8cae2e2ed0ebbbf58ba1c97e79f6047`.
PR #57 was merged; its branch had already been removed. #47 and source Git work
were accepted. There were no open PRs or issue comments requiring reconciliation.
Proposed application version is 0.1.0.16, from accepted 0.1.0.15.

README now gives the agreed tagline, experimental disclosure, practical purpose,
requirements, archive-size warning, licensing and concise navigation. Detailed
README material moves to SETUP, RUNNING, DATA and DEVELOPMENT guides; existing
specialist guides remain linked. GETTING_STARTED provides a disposable first run
and separates application setup from simulation dependencies. docs/README is the
user/technical index. Existing historical reports and VALIDATION.md are unchanged.
Only the required version literal changes outside documentation. No frontend,
recording, schema, Git, storage or simulation behavior changes. The proposed
experimental portal badge and assisted dependency installation remain out of scope.

## Checks and results

- Read launcher, package requirements, CLI, example, parameter discovery behavior,
  Git commands and existing guides against accepted source. Python >=3.11 is the
  declared requirement; no unsupported older-Git minimum is invented. Linked
  upstream Fedora/Python and Git installation guidance was checked. No system
  package installation was performed.
- Explicit `start.sh --setup` from a disposable checkout and external development
  root passed with a newly created environment. No real library or simulation
  environment was used. Runtime setup and all evidence are outside the checkout.
- Actual browser: empty workspace, Add simulation, custom interpreter, Python
  check, undeclared-dependency result, argument paste/review, validation and start.
  Corrected example completed with exit 0, 3 copies (PNG/CSV/JSON), 3 binary
  references, no capture skips, and a full completion bar. Note save survived reload.
  File view distinguished references, managed copies and manual attachment history.
  Explicit Quit with no active jobs shut down the disposable server.
- Initial draft exposed two documentation mistakes: the bundled parser falls back
  to manual entry, and its `--simulation` must match the registered ID. The first
  attempt failed honestly with unknown `scalar-field-example` and exit 1. The
  guide now specifies the registration name/ID and six exact argv tokens; corrected
  browser execution passed. Failed-run evidence was retained, not overwritten.
- Browser file-chooser automation timed out before upload; it is not claimed as
  passed. A separate API request uploaded the generated PNG; its downloaded bytes
  matched exactly, and the browser showed it after reload. CSV download bytes
  matched the original. Manual picker/caption interaction remains an owner check.
- `tests/test_application_version.py`: 12 passed. Focused API tests plus Git archive
  history, source history and absent-Git recording checks: 6 passed. The existing
  Starlette/httpx deprecation warning remains. The initial relative interpreter
  invocation also printed prefix-path warnings; subsequent absolute invocation did not.
- Fresh wheel and sdist builds passed; wheel rebuilt from extracted sdist passed.
  Both wheel metadata versions are 0.1.0.16. All bundled static files and notices
  match checkout bytes; frontend rebuilding is unnecessary because no assets changed.
  The sdist includes the new guides and short README. Installed wheel Python,
  CLI, `/api/workspace` and OpenAPI versions passed in a network-isolated Linux
  namespace with Git and Node absent from PATH. Actual portal label showed 0.1.0.16.
- Documented launcher backup/restore into a new disposable destination passed;
  restored simulations, runs and artifact rows matched the source. No external
  Git archive or reference files are implied to be inside that backup.
- Relative-link/heading checks across README and current docs pages passed;
  `git diff --check` passed. Historical validation reports are byte-for-byte unchanged.

## Limitations and owner checks

No Windows/macOS, additional browser-engine, Python-version/Git-version matrix,
GPU, long-session or scale testing. System dnf commands were reviewed, not executed.
No theme matrix or frontend suite was rerun for this documentation-only change.
The full historical suite was not run; focused checks cover the documented path.
No repository publication, remote synchronization, migration or release occurred.

1. Read the shortened README in GitHub; confirm tone, experimental disclosure,
   licensing and archive/backup caveats before making the repository public.
2. Follow GETTING_STARTED in a new disposable library. Keep the specified name
   and `--simulation first-scalar-run`; confirm manual parameter fallback, exit 0,
   CSV/JSON/PNG copies, binary references and note persistence.
3. Manually upload the generated PNG in Screenshots, add a caption, reload and
   verify it. Download the CSV and compare its bytes with the original.
4. Review SETUP/RUNNING/DATA/DEVELOPMENT navigation and restore instructions.
   Restore only into a new directory; back up the external archive separately.
5. Recheck the version gate if accepted main changes; merge only after owner review.
