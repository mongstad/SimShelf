# Issue #104 — Searchable parameter lists

Validated on 2026-10-19 on Linux with Python 3.14.8, Node 24 and the Chromium
in-app browser. Accepted base `7c8600d` (0.1.0.37); proposed version **0.1.0.38**.
This is focused local validation, not scientific or cross-platform certification.

## Scope and decisions

The editor now renders bounded rows using the existing theme tokens (the previous
separator used undefined `--border`). Native checked/disabled state, an enabled
accent edge and focus outline distinguish controls. Help/aliases/defaults have
explicit description associations. Required controls appear first only if present;
value parameters, flags and manual arguments remain distinct.

A pure presentation projection retains original row references and indexes for
editing. Search matches case-insensitive words across option/aliases/help/type
and required/optional status. It changes no argv, drafts, validation, requests or
saved settings. Manual rows are never filtered. Search is dialog-local and Clear
restores focus to it. No backend, SWSS, storage/schema, source, capture or scientific
execution logic changes; the authoritative application version advances once.

## Automated validation

- 26 frontend tests: existing argument parsing/parameter rows plus five focused
  presentation cases. Search/counts/empty state, required-first/entirely optional,
  required flags, unsupported/repeated manual rows, original indexes, 77 controls,
  enabled/disabled draft retention, aliases, repeats, numeric spelling, equals,
  empty strings and delimiters passed.
- 12 application-version tests passed. Existing Starlette/httpx deprecation warning.
- TypeScript check, frontend rebuild, version policy check and diff whitespace check
  passed. Bundled third-party licenses unchanged.
- External wheel and sdist built; wheel rebuilt from extracted sdist. Wheel member
  names and bytes agree. Installed assets/licenses match checkout; Python/CLI/API/
  OpenAPI report 0.1.0.38. Installed startup/assets work with outbound socket calls
  denied and Git/Node absent from PATH. Existing development dependencies were
  reused through a disposable environment `.pth`; no dependency installation or
  changes to a scientific interpreter.

Frontend commands (use the available Node executable):

```sh
node_modules/.bin/esbuild frontend/parameterPresentation.test.mjs frontend/parameters.test.mjs frontend/arguments.test.mjs --bundle --platform=node --format=esm --out-extension:.js=.mjs --outdir=/tmp/simshelf-104/tests
node --test /tmp/simshelf-104/tests/*.mjs
node node_modules/typescript/bin/tsc --noEmit
node frontend/build.mjs
python scripts/application_version.py --base-ref origin/main
```

## Installed browser and real process

Reusable fixture: `tests/fixtures/parameter_list.py`. Run it with an installed
SimShelf Python and a **new external directory**; point a disposable portal at its
`workspace` subdirectory. It creates an entirely optional 77-declaration SWSS
schema-2 fixture and a six-declaration required/optional mixture. The harmless
script writes its received argv to stdout and a run log; it performs no science.

- Option, alias and help searches matched expected controls; no-match message and
  Clear worked. All 77 returned after Clear, with no empty Required section.
- Enabled `--queue-zmax`, entered `2e-3`, filtered it away/back, saved while filtered,
  closed/reopened and retained the value. Choice `double` and a boolean flag worked;
  flags had no value input. Manual rows stayed editable under filtering.
- The mixture displayed Required first; editing required `00192` to `00032`, then
  filtering and editing a manual token, retained each value at its original argv
  position. Search alone left command preview unchanged.
- Native Space toggled enable; Tab moved from search to Clear and then the next
  enabled control; Enter cleared search and restored focus. Group names, control
  labels and referenced hint elements were inspected. No actual screen reader used.
- Light, Dark, Onyx, Slate and Linen checked at 1280×1000 and 390×844. Search/rows
  had matching scroll/client widths (927/923 desktop; 301/297 narrow), long names
  and hints wrapped, narrow inputs stacked, and focus remained visible.
- Run `6d51243be0984fd6873c0c0a080c76c2` completed with exit 0 and complete copied-log
  capture. Its stdout contained exactly:

```json
["--queue-zmin","00192","--diag-dt=1e-3","--snapshot-times","","--unknown","--queue-zmax=2e-3","--precision=double","--no-plots","--","--no-plots"]
```

This matched the saved settings and recorded command. No owner simulation, source,
database, output or prior report was used or modified. Browser error log was empty.
Disposable evidence/builds/screenshots are under `/tmp/simshelf-104/` (local only).

## Harness failures and limits

An initial frontend glob selected no tests; sandboxed Node then reported only
file-level checks. The corrected `.mjs` run outside the sandbox executed the
individual cases above. Sandboxed TestClient stalled; the disposable external
run passed. First installed-server startup lacked FastAPI; an attempted dependency
`.pth` used a nonexistent site directory and wrote nothing. The correct disposable
site directory with existing dependencies resolved startup. Pip reported its cache
was unavailable. A read-only verification script initially used the wrong Store
accessor; corrected to `simulation`, it confirmed saved/recorded/received argv
equality. These were harness issues, not claimed passing application tests.

No actual Vacuum Collapse Recirculator, numerical results, GPU workload, Windows,
macOS, other browser engine or screen reader tested. No unrelated exhaustive
backend suite, dependency refresh, release or publication performed. Search does
not filter unsupported declaration notes; ambiguous argv stays in manual rows.

## Owner verification

1. Open a trusted simulation's New run dialog with many SWSS declarations. Check
   adjacent rows and long help in your preferred theme and a narrow window.
2. Search an option, alias and help phrase; try no match, then Clear. Enable/edit
   a value, filter it away/back, and confirm the command preview remains exact.
3. Check required-first ordering with a required declaration; optional defaults
   should not become required or be inserted. Check a flag has no value field.
4. Edit a manual argument while filtered. Save/reopen and compare Exact argv,
   including aliases, repeated options, empty strings and `--` where applicable.
5. Use a disposable harmless simulation to validate/start, then compare its received
   arguments and retained record. Review only; merging does not publish a release.
