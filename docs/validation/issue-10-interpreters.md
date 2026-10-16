# Issue #10 interpreter discovery and dependency checks

Date: 2026-10-16. Pending owner review; no merge or release is claimed.
Base: accepted main `6e84142` (PR #19), including prerequisite portal PR #8.
The existing issue branch was clean and equal to main before implementation.
Previous issue branches were already removed; historical reports were preserved.

## Decisions and boundaries

Discovery is passive: inspect saved/project/PATH/environment-hint/Conda-registry
paths, preserve environment identity and saved spelling, deduplicate aliases,
label SimShelf's runtime, and select nothing automatically. Versions remain
unknown until the user explicitly checks a trusted selection. Missing saved
paths remain visible. A custom absolute path is always available.

Explicit same-origin checks run a fixed standard-library probe in the selected
interpreter with `-I -S -B`, argv and no shell, cwd `/`, time and output limits.
No simulation or installed package imports, startup hooks, activation scripts,
installs or environment modifications. A chosen executable can itself be
arbitrary code; isolated flags are not a security sandbox for an untrusted binary.
Existing explicit launch validation reuses the bounded version probe.

Dependency advice compares bounded static declarations with the selected
interpreter's installed distribution metadata. Server `packaging` parses PEP 508
requirements and version specifiers; marker context must come completely from
the selected interpreter. Missing target metadata never falls back to the
server's environment. `packaging>=24,<27` is now a declared runtime dependency;
the existing development lock already contains tested packaging 26.3. Nothing is
vendored and no frontend dependency changed.

Requirements/TOML, metadata, scan count and output limits are documented in the
architecture. Nested requirements, URLs/editable installs, optional extras,
transitive/dynamic dependencies and Conda solver syntax are unassessed; path hooks,
legacy or partial metadata produce conservative warnings. User-site/PYTHONPATH
packages are not inspected. Results are ephemeral advice, never a launch-success,
importability, environment-recreation or GPU/CUDA guarantee. Stored selection,
recording, snapshots, run lifecycle, output mapping and backups keep their contracts.

## Validation

- TypeScript typecheck and bundled frontend build passed.
- Three frontend tests passed: undeclared dependencies cannot imply readiness;
  missing/incompatible/unknown results remain distinct; custom saved paths and
  executable-trust guidance remain present.
- Targeted Python boundary run: **63 passed** across interpreter, portal, output
  paths, capture/backup and recording tests. After refining directory-alias
  deduplication and adding explicit environment-immutability/unavailable-metadata
  assertions, **11 interpreter tests passed again**. One existing
  Starlette/httpx test-client deprecation warning.
- Interpreter tests cover spaces, PATH variation, duplicate/symlink aliases,
  distinct virtual environments sharing a base executable, passive untrusted
  candidates, Conda registry discovery, stale paths and broken symlinks. Broken
  binaries, invalid JSON, nonzero exits, output floods and timeouts fail clearly.
- A disposable venv with synthetic NumPy distribution metadata, a throwing
  package module, hostile `.pth` hook and non-runnable simulation source proves
  checks do not execute those files. Environment file sizes/mtimes and project
  contents remain unchanged. Tests distinguish version mismatch, missing package,
  incomplete search, extras, invalid/nested declarations, platform markers,
  undeclared dependencies, unsafe declaration symlinks and size limits.
- API authorization, same-origin checks and explicit confirmation were tested.
  Discovery/checks neither create runs nor change saved execution settings.
  Existing portal/recording/backup tests passed, including launch failure,
  concurrency, cancellation, source retention and saved argv/output settings.
- Headless Chromium flow passed: no automatic selection or probe, project
  interpreter selection, explicit version/dependency checks, advisory outcomes,
  source not executed until explicit launch, custom-path failure, saved selection
  reload, rescan invalidation of stale checks, moved environment detection and rescan without replacement, restored
  environment and successful real launch. No page errors. Desktop 1360x1000 and
  narrow 390x844 screenshots were inspected with no page/dialog horizontal overflow.
- Wheel/sdist and fresh installation passed. New probe/check modules, frontend
  source/tests and bundled assets are packaged. With Node absent from PATH, the
  installed app served assets, discovered interpreters, enforced confirmation,
  checked its real installed packaging distribution, and completed a recorded
  launch while preserving output-mismatch acknowledgement/reference behavior.
- Third-party frontend notices remain unchanged. Runtime dependencies retain
  licenses in their installed distributions. Scoped diff/whitespace review passed.

Reproduce focused checks using the documented external development/build setup:

```sh
node node_modules/typescript/bin/tsc --noEmit
node_modules/esbuild/bin/esbuild frontend/interpreters.test.mjs --bundle --platform=node --format=cjs --outfile=/tmp/simshelf-interpreters.test.cjs
node --test --test-isolation=none /tmp/simshelf-interpreters.test.cjs
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/src" python -B -m pytest -q -p no:cacheprovider --basetemp=/tmp/simshelf-interpreter-tests tests/test_interpreters.py tests/test_portal.py tests/test_output_paths.py tests/test_capture_backup.py tests/test_recording.py
node frontend/build.mjs
```

Python 3.14.8, Node 24.19.0 and packaging 26.3 were used. Temporary evidence lives
under `/tmp/simshelf-issue-10-{build,ui,package}`; these are disposable local paths,
not durable published artifacts.

## Failures and limitations

The first boundary run had 43 passes and one failure in an existing output test:
its embedded script referenced `Path` without importing it. Inspection confirmed
the missing import was already in accepted main. This change restores that one
fixture import; runtime output behavior and historical issue #14 evidence are
unchanged. The corrected boundary run passed. The first browser run timed out on
a fixture selector waiting for a hidden option to become visible; checking the
selected-option state fixed the harness, and the full flow passed.

Linux and headless Chromium only. Other browsers/platforms, real Conda/PyPy
runtime behavior, network filesystems, physical keyboard/accessibility tooling,
large installations and long workloads were not validated. Discovery is bounded,
not exhaustive. Requirements depend on explicit declarations; imports may use
names unlike distribution names. Installed metadata may be stale or incomplete.
No real NumPy/CuPy imports, numerical execution or GPU/CUDA access were tested;
synthetic NumPy metadata tests exercise inspection without claiming package health.
The installed-package smoke check used a real packaging distribution. Unrelated
launcher/version suites were not rerun. No simulation environment was modified.

## Exact owner verification

1. Update SimShelf's own environment explicitly with `./start.sh --setup` if it
   lacks the newly declared packaging dependency. Start a disposable workspace.
2. Register a harmless script in a folder with an existing `.venv` or `venv`.
   Open Start simulation: expect a labeled project candidate and separate SimShelf
   runtime, with no automatic selection/probe. Select the trusted project Python;
   Check selected Python should show its version and environment path.
3. Select an existing trusted NumPy/CuPy-capable environment (custom path if not
   discovered). In a disposable project, declare `numpy` and its actual CuPy
   distribution name (for example `cupy-cuda12x` only if that is what is installed).
   Check dependencies. Compare reported versions with your known environment;
   confirm the UI explicitly does not certify imports or GPU/CUDA access. Verify
   real GPU use separately through your established trusted scientific workflow.
4. In that disposable declaration file, add an intentionally absent package and
   an incompatible NumPy version bound. Check again: missing/incompatible or
   incomplete-search warnings must be clear. With no declarations, expect unknown
   requirements, not a ready-to-run claim. No packages should be installed.
5. Save settings, close/reopen and rescan. The selected path must remain unchanged.
   Test a nonexistent custom path: expect an actionable error. If testing a moved
   environment, use only a disposable fixture; its saved path must remain flagged
   rather than silently selecting another interpreter.
6. Check narrow-window use and custom-path entry. Explicitly validate and launch
   the harmless script, inspect its recorded interpreter/argv, then change future
   selection and confirm the completed record/snapshot remains unchanged.
