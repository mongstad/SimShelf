# Issue #118 — implemented local preservation workflow

Validated on 2026-10-21 on Linux with Python 3.14.8, Node.js 24.19.0 and
application **0.1.0.43**, against accepted `main`
`40fa289509f99aad80d2d4dc3ac89663bb2b91e5` (0.1.0.42).
This report covers the owner-approved implementation on the existing issue
branch and PR #119. The [Phase 1 audit](issue-118-library-preservation-audit.md)
and its original tests remain unchanged historical evidence.

## Scope and data protection

One reviewed Preservation settings workflow now combines capture and optional
local Git inclusion. Recursive selection uses verified run-specific managed
copies, preserves copy/reference/ignore choices and requires explicit adoption.
Format-2 records and later reviewed additions use additive metadata and the
existing durable, append-only Git publisher. Execution, capture and initial Git
completeness have separate status and counts. Files joins exact evidence identities
and revisions across library and Git retrieval; source development Git is separate.

All implementation runs, failure injection, archives, backups, restored libraries,
package builds and browser edits used disposable locations outside the checkout.
No owner library, source snapshot, database, output, scientific source, SWSS file,
original archive commit or Phase 1 report was edited. No schema migration, remote
archive synchronization, publication or output-allocation protocol was introduced.

## Automated source checks

Final result: **227 passed, 1 dependency warning, 52.66 seconds; no skips**.
The warning is the existing Starlette/httpx TestClient deprecation. Imports were
forced to the source checkout with `PYTHONPATH=src`; bytecode/cache output was
disabled or directed outside the checkout.

```sh
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 \
SIMSHELF_AUDIT_DECAY_REFERENCE=/path/to/accepted/examples/decay \
python -m pytest -q -p no:cacheprovider --basetemp /tmp/simshelf118-validation \
  tests/test_preservation.py tests/test_git_archive.py \
  tests/test_library_preservation_audit.py tests/test_git_selection.py \
  tests/test_capture_backup.py tests/test_api.py tests/test_screenshots.py \
  tests/test_recording.py tests/test_portal.py tests/test_isolated_outputs.py \
  tests/test_relocation.py tests/test_simulation_removal.py \
  tests/test_application_version.py
```

The new preservation suite has **16 cases**, including parametrized publication
interruption. It checks:

- First/repeated nested JSON/CSV/log results, source snapshots and process streams;
  A/B/A commits, exact argv, byte/hash/size retrieval and reopen after Git advances.
- Explicit, atomic adoption; stale review rejection; unchanged legacy manifests;
  deliberate source/extension omissions, reference/ignore and size exclusions.
- Disabled/disconnected/missing/replaced archive states, original-identity
  reconnection, absent Git, source-root replacement, symlinks and corrupt copies.
- Failure/cancellation/interruption status independent of capture and preservation;
  injected pre-publication and post-publication failure, restart and idempotent
  retry using frozen evidence despite changed live originals.
- Concurrent simulations, conflicting pending intent, exact operation identity,
  notes/captions/screenshots/manual attachments as append-only events, and earlier
  record/commit/download preservation.
- Record, text, annotation, file and cumulative byte limits, including repeated
  revisions; visible rejection without silent truncation.
- Backup/restore with a separately retained Git repository; approved pending
  attachment bytes survive gallery removal, backup and restart before publication.
- API confirmation, verified source/artifact retrieval and tamper rejection.
- Browser-number round trips: nanosecond timestamps and a scientific integer
  `2**60 + 1` retain exact server values and exact archived JSON after confirmation
  and retry.

The existing archive, capture, process, API, screenshot, relocation/removal and
version suites exercise their direct integration boundaries. The Phase 1 suite
still reproduces legacy manifest-only behavior without changing that history.

The optional standalone scalar-decay tests were enabled using accepted
Simulation-Standards revision `285ab0d6c06cc3b88e421a2c00577e72c650c750`.
They verify both pinned source hashes before copying only `simulate.py` and
`swss.toml` to disposable simulation roots. Across the historical and new-policy
tests, five real launches validate successful first/repeated fixed-parent capture
and the uncoordinated `per_run` mismatch. No original reference source was changed.
Without this environment variable, the three optional integration cases skip;
they did not skip in the final recorded source run.

## Frontend and browser checks

TypeScript `tsc --noEmit` and `node frontend/build.mjs` passed. The intentional
bundled JS/CSS assets were rebuilt; third-party notices are retained unchanged.
Five focused frontend suites (`archive`, `preservation`, `git`, `outputs`,
`screenshots`) were bundled with the installed esbuild and run through Node's
test runner: **29 passed**. They cover evidence identity/revision joins,
manifest-only status, reviewed controls, source Git separation and existing
output/screenshot integration.

The existing theme test's contrast case passed. Its selector-count case failed
with `3 !== 2` for archive selectors; the identical failure was reproduced from
unchanged `origin/main` CSS and test bytes. This pre-existing assertion was not
changed as part of #118. Visual checks covered System, Light, Dark, Onyx, Slate
and Linen; this is not a claim of full automated accessibility certification.

The in-app browser used only a disposable two-simulation library and local archive.
Checks covered desktop (up to 1280×900) and narrow (390×844) layouts:

- Combined capture/Git review, recursive nested matches, explicit consent, saved
  state, original-archive disconnection/reconnection and independent Source Git.
- Cancel initially focused; keyboard activation cancels and returns focus to the
  review trigger. Confirmation saves unchanged reviewed settings successfully.
- Legacy manifest-only run displays execution completed, three workspace copies,
  Git partial, zero scientific Git payloads and 0 of 3 outputs preserved.
- Shared run summary across tabs; source preview and exact source identities;
  Files keeps one attachment row with multiple historical Git revisions.
- Saved note revision and screenshot caption revision, explicit attachment/note
  review and append, then an annotation-only append. The initial preservation
  remains separate; confirming an addition returns focus to the evidence heading
  when resetting the selection disables the original trigger.
- Narrow settings/review controls and evidence rows wrap without document-level
  horizontal overflow. Long hashes and paths remain inspectable. Theme rendering
  was visually checked. No console warnings/errors were observed in the completed
  final UI flow.

The browser found an actual initial confirmation defect: JSON numbers rounded
nanosecond timestamps and could round large scientific integers. Confirmation now
binds a digest of the exact server review, revalidates authoritative server values
and supplies exact record JSON as text. A regression test and real browser
confirmation pass. A post-confirmation focus loss was also corrected and rechecked.

API tests verify download bytes. A browser download-event wait timed out; native
browser download completion was not independently captured, so it is not claimed.
Screen-reader use and non-Chromium engines were not tested.

## Packaging and version checks

The source distribution and wheel were built in an external disposable source
copy; a wheel was built from the extracted sdist. A separate nested target
installation imports `simshelf` from the wheel, not the checkout. Installed
preservation tests passed: **16 passed, 1 existing dependency warning, 6.41 seconds;
no skips**. Runtime version surfaces, packaged HTML/JS/CSS and metadata were checked. Python, CLI, `/api/workspace` and OpenAPI agree on 0.1.0.43 with
Git and Node absent from PATH; the browser also displayed 0.1.0.43. Runtime startup
does not require a network service. Dependencies came from the existing test
environment; a completely fresh dependency resolution is not claimed.

The application-version gate against freshly fetched accepted `origin/main`
passes: 0.1.0.42 → 0.1.0.43. No tag, release or package was published.

## Failures and limits

- An intermediate combined run had one legacy stale-selection setup rejection;
  later focused and final expanded runs passed. No unverified root cause is
  asserted for that transient failure.
- The first flat `/tmp` package target caused archive safety checks to treat the
  shared `/tmp` parent as an application boundary (14 setup errors and one failure).
  A correctly nested installation passed; no safety check was relaxed.
- Early harness attempts used an unavailable npm command, a misspelled test path,
  and a bundled theme test with the wrong relative CSS location. Correct absolute
  Node invocation, test path and native theme-test location were used afterward.
- One disposable UI server exited with SIGTERM during overlapping fault tests.
  The cause was not established. UI checks were resumed on a fresh server after
  the fault suite completed, and passed. The normal sandbox also prevented binding
  the test server; the authorized external execution path was used.
- Linux only. No malicious same-user writer, filesystem-wide atomicity,
  cross-platform lock behavior, high-volume performance or scientific/SWSS
  certification is claimed. Legacy unknown coverage stays partial.
- Records export selected local evidence; Git alone does not restore a workspace,
  missing references, unexported annotations or an interpreter environment.
- Simulation-owned output directories work beneath a fixed parent. An unsupported
  launcher-coordinated `per_run` selection still creates an unused child. This
  independent output-allocation defect is documented, not disguised as repaired.

## Owner verification

1. Use a disposable library and separately located local archive. Register two
   small simulations that create unique subdirectories beneath `outputs`. Choose
   the fixed-parent output policy. In Preservation settings, review copy/reference/
   ignore rules, source selection, recursive `.json`/`.csv`/`.log` and optional
   stdout/stderr. Cancel once, then confirm explicitly.
2. Run A, B, A with distinct values. In each run compare execution, capture and
   initial Git status/counts. In Files download retained bytes and an exact Git
   revision under Identity and revisions. Inspect the verified record for original
   argv, version, snapshot, outcome, hashes and omissions after later commits.
3. View the historical manifest-only run read-only. Expect partial/unknown scope
   and no scientific payload claim; its original commit/manifest must be unchanged.
   Do not adopt new policy or retry publication as part of this historical check.
4. In the disposable library attach an image/file, save a note and caption, then
   explicitly review additions. Change the note/caption and review again. Confirm
   one evidence row, separate event revisions and retrievable earlier records.
5. Disable Git and run; disconnect and run; reconnect the original repository.
   Ordinary recording must continue, statuses must explain availability, and old
   downloads must use the original repository identity. Replaced identities must
   be rejected. Use only disposable paths for unavailable-repository tests.
6. Back up the disposable library and separately preserve its Git archive. Restore
   to a new empty destination, reconnect the original archive explicitly and review
   future automatic consent again. Verify historical source, files and annotations.
7. Check Preservation settings, Files, Source, Screenshots and Notes at desktop and
   narrow widths using keyboard and preferred theme. Re-run the version gate after
   any accepted-main change before merge.

Recommended independent follow-up: require explicit confirmation of simulation
support when choosing launcher-coordinated `per_run`, and review the actual capture
target. Any portable acknowledgement protocol needs separate owner-approved
standards work. No follow-up issue was created automatically.
