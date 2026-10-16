# Issue #16 parameter discovery

2026-10-17. Pending owner review; no merge/release claimed.
Accepted main: `90813fba005c14afaf83fa7f7b5c10fd6a056121` (PR #21).
Issue #16 was the sole Ready item. Its existing branch was clean/equal to main;
no open PR existed. Prerequisites #5/PR #8, #11/PR #13 and #10/PR #20 were verified
merged and ancestors of main. Previous issue branches were already removed.
Historical validation evidence is unchanged.

## Decisions

Read-only static AST discovery of a conservative single-parser argparse subset,
or optional `simshelf-arguments.json` in the registered project root. The schema
has explicit precedence and is never created/edited automatically. No imports,
subprocesses, `--help`, dependency installation, network or Git during discovery.
Bounds: 256 KB file, 20,000 AST nodes, 128 declarations, 100 choices, eight aliases
per declaration. Symlinks/outside-root/nonregular files are refused.

The portal shows names/aliases, help, type/choices, default knowledge, required
state and declaration source. Unsupported/conflicting definitions require manual
entry. Drafts start unselected/empty; placeholders never contribute tokens.
Explicit Add selected overrides appends values using option=value syntax or a
boolean flag to the existing argv editor. Existing matching options are left for
manual editing. Repeated/positional/unknown tokens and exact argv are preserved.
Pending drafts block save/launch; applying arguments invalidates validation.

Rescan compares declaration-content fingerprints, warns about changes, preserves
argv/drafts and blocks applying disappeared drafts. A new dialog has no previous
scan baseline. Saved argv is authoritative, not proof its options remain valid.
There is no new persisted parameter model, journal event, schema migration or
historical record mutation. CLI/editor recording and output mapping retain their
contracts. Build increments once from `0.1.0.1` to `0.1.0.2` under issue #18 policy.

## Validation

- Final focused Python run: **63 passed** across parameter discovery, portal,
  output paths, recording and application version tests. One existing
  Starlette/httpx deprecation warning. Earlier run had 62 passes; adding a real
  parameter-launch regression increased the final count. Five focused parameter
  tests also passed separately during development and again after final review
  made implicit defaults unknown for dynamic/custom actions.
- Backend coverage includes non-execution with missing GPU imports/throwing code,
  no subprocess discovery, literals and unknown defaults, bools, typed/negative
  defaults, choices, required/positional/repeatable/custom fallback, duplicate
  aliases, malformed/oversize/symlink schema, parser mutations/multiple parsers,
  same-origin protection, changed fingerprints and unchanged saved unknown argv.
- Actual subprocess launch preserved repeated flags, positional path with spaces,
  negative value, quoted string and boolean. The unselected steps default came
  from the script, not SimShelf-generated argv. Existing portal/output/recording
  tests passed, including cancellation, recovery and capture/backup boundaries.
- **15 frontend tests passed**: three new parameter argv cases plus existing
  argument/interpreter/output tests. Cases include omitted defaults, unknown and
  repeated manual tokens, exact values/empty strings, existing aliases/equals/
  attached short options, `--` positional delimiter, types/choices/boolean flags
  and unsupported constructs. TypeScript check and frontend build passed.
- Source and fresh installed-wheel Chromium flows passed: no initial override or
  source execution, pending-save block, typed overrides, changed declaration rescan
  preserving a draft, explicit append, repeated/positional manual argv, save/reopen,
  successful launch with exact values and untouched unselected default, no page
  errors. Desktop 1360×1000 and narrow 390×844 checked; dialog had no horizontal
  overflow and packaged narrow screenshot was inspected.
- Wheel and sdist built externally, wheel from sdist. Fresh wheel install passed.
  Metadata/Python/CLI/API/OpenAPI agree on `0.1.0.2`; discovery modules, frontend
  source, tests and documentation are packaged. Bundled assets match source bytes;
  third-party notices unchanged. Installed browser server PATH had neither Git
  nor Node. Application construction/OpenAPI also passed with socket connections
  blocked after dependencies were installed.
- Version check against freshly fetched origin/main passed. Scoped diff and
  whitespace checks passed. Temporary evidence and test environments live under
  `/tmp/simshelf16-*`; no user workspace, source snapshot or output was modified.

The first browser harness used an incorrect selector for the existing paste
textarea and timed out. Replacing it with the accessible label and using a fresh
fixture workspace resolved the harness error; both complete flows then passed.
No implementation test failures were observed. Temporary harnesses/captures are
local disposable evidence, not published artifacts.

## Limitations

Linux/headless Chromium, Python 3.14.8 and Node 24.19.0 only. No physical input,
other platforms/browsers, GPU/numerical workload or long-job validation. No help
execution fallback. Dynamic/custom parsers, imported declarations, groups,
subparsers, parser mutations and unsupported syntax require a schema/manual argv.
Static discovery does not prove branches execute, names are unshadowed, or declared
defaults equal runtime scientific values. Explicit schema is advisory and must be
maintained by the user. Short-option clusters and parser abbreviations may require
manual conflict review; discovery does not claim a full argparse interpreter.
Fresh dialogs cannot compare against an earlier scan; saved unknown options are
preserved with manual-review guidance. Broader unrelated suites were not rerun.

## Owner checks

1. Start an external disposable workspace and register a harmless argparse script.
   Open Start simulation. Check names/help/defaults and that no option is selected
   or passed until explicitly added. No script output should exist yet.
2. Choose trusted Python; paste manual repeated flags/positionals/unknown options
   appropriate to that script. Enable a typed/negative/string or boolean override,
   add it, and inspect Exact argv. Save/reopen; confirm the tokens are unchanged.
3. Edit only that disposable script's declaration, rescan and confirm the warning
   with preserved drafts/argv. Remove a pending declaration and confirm application
   requires review/clearing. Unsupported cases should remain manual, not invented.
4. Try the documented `simshelf-arguments.json` example in the disposable project.
   Confirm schema precedence/source, unknown omitted defaults, and conflicts or
   malformed declarations produce explicit fallback rather than rewritten argv.
5. Validate and launch the harmless script. Compare its actual parsed values with
   argv and defaults; inspect the completed record. Changing future arguments or
   discovery metadata must not rewrite it. Check desktop/narrow presentation.
6. Expect application version `0.1.0.2`. Review `docs/PARAMETER_DISCOVERY.md` limits.
   No release or next issue is authorized by this handoff.
