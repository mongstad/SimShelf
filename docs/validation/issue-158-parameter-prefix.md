# Issue #158 — declared long-option prefix ownership

Validated 2026-10-30 against accepted main
`e5d8397d47f98a4c97144c18c4002576aa7f7a69` (0.1.0.63); proposed build 0.1.0.64.
Issue #158 was the only Ready item. PRs #155/#156 were merged, main was current
and clean, and no issue branch or open PR existed. Prior branch cleanup was
already complete. Historical evidence and user workspaces were not modified.

## Change and boundaries

`possible()` previously considered an exact `--volume` token a possible occurrence
of `--volume-interval`. Complete declared names (including aliases and unsupported
exact declarations) now take precedence over prefix guesses. The same rule is
used by omission validation. Per-row error projections retain other rows'
declarations for ownership checks, without changing their validation target.

Undeclared long abbreviations and short clusters retain the existing conservative
manual handling: exact tokens survive, no abbreviation is expanded, and potentially
represented declarations are not duplicated as typed controls. This is not a new
abbreviation parser or a promise that a solver accepts those spellings. Repeated
options, delimiters and invalid flag values retain their existing diagnostics.
No defaults are inserted. No portable SWSS semantics, solver, recorder, output
capture, schema, source snapshot or historical run data changes are involved.

## Validation

- 40 focused frontend assertions/tests passed across `parameters.test.mjs` (20),
  `parameterPresentation.test.mjs` (7), `ParameterHint.test.mjs` (8), and new
  `parameterPrefix.test.mjs` (5). Tests were bundled with esbuild as Node CommonJS
  into `/tmp/simshelf-158/tests-cjs`, then run with Node 24.22.1.
- Coverage includes both input orders, boolean/value and value/value pairs,
  enabled/disabled shorter options, aliases, equals/separate values, exact numeric
  spelling, repeats, delimiter and empty tokens, draft/rescan preservation,
  required-field projections, unsupported exact names and actual abbreviations.
- TypeScript `--noEmit`, production asset build, version gate and `git diff --check`
  passed. Distributed JavaScript rebuilt; CSS and license notices unchanged.
- 66 Python tests passed: `tests/test_application_version.py`,
  `tests/test_parameters.py`, `tests/test_swss.py`, using the development Python
  3.14 environment, `PYTHONPATH=src`, `-p no:cacheprovider`. Existing
  Starlette/httpx deprecation warning remains.
- Four React/browser scenarios passed in the in-app Chromium browser. Actual
  schema-3 discovery supplied 22 supported declarations from a disposable TOML:
  saved shorter flag, search/count, explicit interval editing, rescan/reopen,
  reverse order and disabled defaults. The fixture does not execute a simulation.
- Installed production portal independently showed version 0.1.0.64, 22 controls,
  both volume search matches after enabling the flag and rescanning, and exact
  launch preview `--volume --volume-interval=0.1`.
- Wheel, sdist and wheel rebuilt from sdist built externally. Both wheels matched
  all 39 runtime files and the current source, with expected metadata version and
  retained third-party licenses. Fresh external venv installed the wheel with
  `--no-index --no-deps`; existing development dependencies were reused read-only.
  Import location confirmed the new wheel. Import/CLI worked in the network-blocked
  sandbox with Git/Node absent from PATH. Installed workspace API, OpenAPI and
  static asset smoke checks passed with Git/Node absent from PATH.

To reproduce the browser fixture from repository root, using an available Node:

```sh
PYTHONPATH=src python scripts/test_parameter_prefix_browser.py /tmp/prefix-browser --node /path/to/node
python -m http.server 8158 --bind 127.0.0.1 --directory /tmp/prefix-browser
```

Open localhost:8158 and select **Run tests**. The destination must not exist.

## Failures, retries and limitations

Node was absent from PATH; checks used the bundled runtime. Initial ESM test
bundling failed on React's dynamic require; CommonJS bundling fixed the harness.
An intermediate implementation duplicated declarations during normalization;
seven existing tests caught the regression, and the corrected implementation
passed all 40 checks. Initial browser harness reopen assertions raced discovery;
settling the fixture's async React mount fixed the harness, with all four passing.

Sandbox restrictions blocked localhost listening and stalled TestClient; the
stalled test run was interrupted and focused tests/API checks rerun with approved
sandbox escalation. Standalone Playwright lacked a downloaded browser, so the
existing in-app browser was used. Initial package build lacked setuptools; bundled
build dependencies supplied it without modifying the development environment.
An attempted `serve --help` command was rejected (the actual CLI command is `ui`);
the installed portal check used Uvicorn's supported app factory instead.

No fresh dependency download, cross-platform/browser matrix, all-theme/narrow
layout sweep, real Cosmos launch, numerical validation or scientific-output check
is claimed. Production browser verification stopped at the exact launch preview.
The full backend suite was not rerun for this frontend-only fix.

## Owner verification

1. In a disposable library, register a copy of the schema-3 simulation that declares
   `--volume` and `--volume-interval`. Open New run with saved `--volume` argv.
2. Search `volume`, then `interval`: confirm both declarations remain discoverable
   and the expected declared-control count remains 22 for the reported metadata.
3. Enable the interval, enter `0.1`, rescan, and inspect Exact argv. Confirm the
   original flag plus `--volume-interval=0.1`, with no inserted default arguments.
4. Save settings, close/reopen New run, and verify both choices persist. Repeat
   with the interval before the boolean and with the boolean disabled.
5. If desired, launch a trusted disposable simulation after normal interpreter/path
   review; verify its recorded argv and behavior independently.

Owner review only; no merge, release, issue closure or Done transition.
