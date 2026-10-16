# Issue #11 argument editor validation

Date: 2026-10-16. Implementation is pending owner review; no merge or release is
claimed. This report covers paired runtime arguments and paste import only.

## Decisions and boundaries

The persisted `arguments: list[str]` and backend `shell=False` execution are
unchanged. Display rows hold one token and an optional second token: null means
absent, while `""` is an explicit empty argument. Initial display pairs common
options with adjacent non-option values (including negative numbers). This is
not a parser for a simulation's option grammar. Split/pair controls preserve the
array, and only that array is saved; display grouping is rederived on reopen.
Reorder moves the entire row; split first to move one token independently.

Paste handles single/double quotes, escaped characters, concatenated quoted text
and backslash-newline continuation. It does not evaluate expansions, comments,
operators, pipelines or commands. Inside double quotes a backslash only escapes
quote, backslash, dollar sign, backtick or newline. Blank paste intentionally
replaces the array with no arguments when applied. A malformed or unapplied
paste blocks validation and launch. Existing argument limits are checked locally
as well as by the unchanged server. The command display is quoted text, never an
execution mechanism; Exact argv shows unambiguous token boundaries.

No interpreter discovery, dependency installation, process ownership, source
capture, version identity, record storage or workspace migration code changed.
All test simulations, workspaces, environments and build products were external
temporary fixtures. Historical reports and personal workspaces were preserved.

## Checks

- TypeScript `tsc --noEmit`: passed with the existing locked dependencies.
- Four frontend tests: passed. Acceptance paste, flag-only rows, explicit empty
  values, quoting/escaping, literal metacharacters, malformed input and bounds.
  A 16-by-16 token corpus checks lossless display and quoted-preview round trips,
  including Unicode, newlines, repeated options, separators and equals forms.
- Focused Python integration: **11 passed, 11 deselected**. Exact argv survives
  save, real subprocess launch, reopen and backup/restore. Editing future launch
  settings leaves the entire completed run record unchanged. Invalid arguments
  and authorization/validation boundaries also pass. One existing
  Starlette/httpx deprecation warning was emitted.
- Headless Chromium: passed against a disposable simulation using the bundled
  UI. Verified the issue's eight-row paste example, exact five-token example,
  parse errors, blocked stale validation, current preview, split/pair, row
  reordering, absent versus empty value, add/remove, keyboard Tab from parameter
  to value, save/reload/reselect/reopen and real launch. Recorded command and
  Python API argv matched spaces, Unicode, quotes, repeated flags, equals,
  empty strings, literal metacharacters and `--` positionals. No page errors or
  shell-created sentinel files. Desktop 1360x1000 and narrow 390x844 screenshots
  were inspected; page and dialog had no horizontal overflow.
- Rebuilt bundled JS/CSS. Full third-party licenses and linked legal comments
  are byte-identical to the prior bundle's notices; no dependencies changed.
- Isolated wheel and sdist build: passed. Verified bundle and notice bytes in the
  wheel and new frontend source/tests in the sdist. Fresh wheel installation
  served HTML, JS, CSS and notices from a temporary runtime with Node absent
  from PATH.
- `git diff --check`: passed.

Reproduce the focused development checks from a checkout with its documented
frontend dependencies and Python development environment (use external build,
pytest and package directories as described in the repository guidance):

```sh
node node_modules/typescript/bin/tsc --noEmit
node_modules/esbuild/bin/esbuild frontend/arguments.test.mjs --bundle --platform=node --format=esm --outfile=/tmp/simshelf-arguments.test.mjs
node --test --test-isolation=none /tmp/simshelf-arguments.test.mjs
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/src" python -B -m pytest -q -p no:cacheprovider --basetemp=/tmp/simshelf-arguments-pytest tests/test_portal.py -k 'real_argv or invalid_launch or registration_validation'
node frontend/build.mjs
```

The frontend checks used Node 24.19.0. Python integration used Python 3.14.8.
Local temporary evidence lives under `/tmp/simshelf-issue-11-{build,ui,package}`;
these paths are disposable, not published artifacts or durable evidence links.

## Failures corrected during validation

An initial test bundling command incorrectly invoked the native esbuild binary
through Node; invoking esbuild directly fixed it. Chromium initially could not
start inside the execution sandbox and passed with host process permissions.
Browser testing found the Add value button inherited an enclosing label's
accessible name; removing that label nesting fixed it. Two subsequent fixture
failures were test navigation errors: reload requires selecting the simulation,
and its name also occurs in an overview card. A sidebar-specific selector fixed
those errors; the complete final run passed. An initial non-isolated package
build lacked setuptools in the reused development environment; an isolated build
passed without modifying that environment.

## Limitations and owner verification

Linux/headless Chromium only. Firefox, Safari, Windows/macOS, screen readers and
physical touch interaction were not tested. The broader unrelated test suite was
not rerun. Paste is a documented quoting subset, not a complete shell or Windows
command-line parser. Option grouping cannot infer a script's grammar; verify
Exact argv for ambiguous cases. No scientific reproducibility claim is made.

1. In a disposable workspace, register a small script that prints `sys.argv[1:]`
   and select its existing Python environment. Open Start simulation.
2. Paste `--particles 50000 --n 192 --steps 1000 --render-every 5 --wvz 'outputs/test-simshelf.wvz' --wvz-every 5 --compression none --headless`.
   Review and replace. Expect seven pairs and a final No value flag.
3. Split and pair a row; verify Exact argv is unchanged. Reorder it. Add a value
   to the flag and leave it blank: Exact argv should contain a final `""`.
   Remove value: that empty token should disappear.
4. Save settings, close/reopen, then validate. Change a value and confirm Start
   becomes unavailable until revalidated. Try an unclosed quote in Paste:
   Replace, Validate and Start must be unavailable until corrected or cancelled.
5. Try `--label 'path with spaces' --repeat α --repeat 雪 --key=value '' 'a"b' 'a'\''b' ';' '$(literal)' '*' -- -position`.
   Save/reopen and compare Exact argv. Validate and explicitly launch the test
   script; compare its printed argv with the preview and recorded command.
6. Check keyboard navigation and a narrow browser window. Edit future launch
   settings and confirm the earlier run's command and source snapshot stay intact.
