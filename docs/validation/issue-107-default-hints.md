# Issue #107 — Declared default hints

Validated 2026-10-20 on Linux, Python 3.14.8 and Chromium. Accepted main
`e3bb861` (0.1.0.39); proposed version **0.1.0.40**. This is the narrowed
follow-up to merged #109/PR #110; group headings and accordions belong to #108.

## Change and boundaries

`ParameterHint.tsx` separates untouched authored help from generated metadata.
Known defaults are labeled `Declared default (hint)`; absent defaults remain
`Declared default: unknown`. Zero, false, explicit empty strings and signed-64-bit
integers remain visible without guessing effective scientific values. Choices
quote strings so an empty choice is not invisible. Alternate aliases remain
available without repeating the option spelling already in the row title.
Generated footer type text is removed; flag action information remains useful.

The editor's shared guidance explains that disabled optional arguments are omitted
and simulation code determines their behavior. The existing description ID still
associates help and metadata with each control. Two CSS rules separate the text
blocks by 4px. No changes to groups, search, argv conversion, validation, manual
rows, backend contracts, SWSS, scientific sources, storage or historical evidence.
Built assets, the application version and current user guidance were updated.

## Automated and package checks

- **31 frontend tests passed**: existing argument/parameter/presentation cases plus
  three rendering/regression cases for authored help, unknown versus known
  defaults, empty/zero/false/int64 values, aliases/choices and immutable exact argv.
- **16 Python parameter/version tests passed**, using `PYTHONPATH=src`. Existing
  Starlette/httpx deprecation warning only.
- TypeScript, bundled frontend build, version policy and whitespace checks passed.
  Third-party notices unchanged.
- External wheel/sdist builds and a wheel rebuilt from extracted sdist have
  identical member names/bytes. Installed assets match source. Python, CLI,
  API, OpenAPI and portal report 0.1.0.40. Installed API/assets work with outbound
  sockets denied and Git/Node absent from PATH. Existing dependencies were reused
  through disposable environment `.pth` files; no environment installation into
  the application or a scientific interpreter was performed.

Frontend tests were bundled with esbuild `--platform=node --format=cjs` into
`/tmp/simshelf-107/tests` and executed with `node --test`. Tests included
`ParameterHint.test.mjs`, `parameters.test.mjs`, `parameterPresentation.test.mjs`
and `arguments.test.mjs`. Python checks targeted `tests/test_parameters.py` and
`tests/test_application_version.py`. Node used the bundled CUA runtime.

## Installed browser and harmless execution

Generated a new external workspace with `tests/fixtures/parameter_list.py`; only
those disposable generated companions had the first two defaults removed to
exercise known/unknown cases. No tracked or scientific TOML files were changed.

- The 77-declaration optional fixture showed unknown hints without mandatory
  markers. Editing then disabling a `2e-3` draft and filtering away/back retained
  the draft while omitting its token. Empty-string defaults and choices stayed
  explicit; authored help and aliases remained available.
- Save/reopen retained an alias, repeated same-value option, numeric spelling,
  equals syntax, explicit empty strings, manual token and `--` delimiter. Repeated
  options remained manual with the existing count semantics, not metadata rows.
- Harmless run `31b2244d336540c9ba5c3501b69b4b2a` received exactly:

```json
["--alias-0", "00192", "--queue-zmin=00192", "--diag-dt=1e-3", "--snapshot-times", "", "--unknown", "", "--", "--no-plots"]
```

No disabled optional/default token was added.

- Mixed-required fixture: Light, Dark, Onyx, Slate and Linen at 1280×1000 and
  390×844 retained two required markers, unchanged groups/counts and no row
  overflow. Help/default blocks wrapped and remained readable. Clearing all argv
  and attempting Start while filtered marked only the two required controls and
  focused the first; optional unknown-default rows were not marked. Explicit
  manual bypass removed typed hints/errors. Accessible names/descriptions and
  focus were inspected; no actual screen reader used. Browser error log empty.

## Limits and owner checks

No failing application check occurred. Pip warned that its cache was unavailable;
installation completed. Focused tests ran outside the sandbox because prior
verified sandbox restrictions prevent reliable Node/TestClient execution.
No real solver/GPU, Windows/macOS, other browser engine, actual screen reader,
clean dependency-resolution environment or exhaustive backend suite was tested.
Local-only builds/screenshots/fixtures are under `/tmp/simshelf-107/`.

1. Inspect known, unknown and empty-string defaults in New run. Confirm authored
   help is intact and separate, with types only beside names.
2. Leave optional unknown-default controls disabled; confirm they are absent from
   Exact argv and do not acquire required markers/errors. Check a genuinely
   required omission still receives the existing border/focus behavior.
3. Edit/filter/back, save/reopen and compare aliases, repeats, numeric strings,
   explicit empties and manual tokens. Check narrow layout and your theme.
4. Verify group headings and behavior remain unchanged for the separate #108 work.
   Review only; this change does not authorize merge or publication.
