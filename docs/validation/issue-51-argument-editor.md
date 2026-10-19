# Issue #51 — Grouped and aligned argument editor

Prepared for owner review on 2026-10-19. Accepted base `880b77e` (merged PR #98),
application proposal 0.1.0.36. Sole Ready item; existing issue branch clean and
equal to accepted main. PR #98 cleanup already complete. Discovery #16 and archive
#47 are closed and their accepted implementation is in main. No historical report
or scientific record is changed.

## Changes and decisions

ArgumentEditor presents three groups over the existing ordered Row array:
Parameters requiring values, Boolean flags, and Manual / undiscovered arguments.
Original indices still drive edits, moves and pairing; display grouping never
sorts argv. Repeated/unsupported/ambiguous cases retain manual fallback. Existing
static discovery and validation are reused; no scanner or backend changes.

Value controls show integer/float/string metadata and literal choices use a select.
Existing noncanonical or invalid choice text remains visible as current until
deliberately changed. Text inputs with numeric input modes preserve exact spelling;
they do not normalize numbers. Defaults remain hints, and enablement semantics
are unchanged. Boolean controls emit flag tokens only.

Manual fields share equal-width, top-aligned columns and stack at narrow widths.
An open blank optional value is null (argument token only); Pass empty string sets
an explicit empty value. Parsing saved/pasted argv is unchanged, so old empty
values, aliases, equals/separate forms and order are retained. valueOpen is an
ephemeral presentation property, never part of persisted execution settings.
Explicit-empty placeholders and checkbox state distinguish the two blank states.

## Validation

- 13 parameter-model and four argument parsing/formatting tests passed. Coverage
  includes presentation-only grouping, mixed ordering, aliases, equals/separate
  values, repeated/positional fallbacks, flags, blank manual values, saved/pasted
  empties, explicit empty intent and rescans. Existing structured required/type/
  choice validation remains covered. TypeScript and bundled build passed.
- 17 Python checks passed: five discovery/API/launch tests plus 12 version tests.
  These cover nonexecuting discovery, saved unknown argv, declaration changes,
  access protection and exact real-process argv. Existing Starlette/httpx warning.
- External wheel/sdist/rebuilt-wheel byte identity, disposable installed assets /
  licenses and offline startup without Git/Node passed. Python/CLI/API/OpenAPI /
  portal report 0.1.0.36. Third-party notices unchanged. Final package evidence is
  `/tmp/simshelf-51/final2/`; dependencies reused read-only from an external env.
- Installed Linux Chromium at localhost:8798 with disposable standard-library
  fixtures. Discovered shape includes --N integer, --dt float, --precision choices,
  --label required string, --empty string and store_true/store_false flags.
  Choice changes, rescan, save and reopen preserve the original mixed command.
  Enabling --dt without a value shows guidance and blocks validation; disabled
  defaults remain absent. Keyboard navigation and visible focus inspected.
- Explicit browser launch of the safe discovered fixture completed. Stored command
  and stdout argv match exactly:
  `["--wavez","--N","192","--no-plots","--precision=double","--label","fixture","--empty","","--something"]`.
  Parser output confirms N=192, wavez=true, no_plots=false, precision=double and
  empty=""; dt remains the script's own default, not an inserted argument.
- In a second fixture without supported declarations, manual Add parameter/value
  with blank value passes --dt alone. Pass empty string on --empty and a nonempty
  --N pair survive rescan, save, reload and browser launch. Recorded command and
  stdout match `["--dt","--empty","","--N","192"]`. No UI No value text enters
  argv. Only these two safe fixture runs were launched; no user's code executed.
- Manual rows measured at 1280x1000 and 390x844 in all five themes: identical
  desktop column widths, one stacked narrow column, no row/editor overflow.
  Discovered narrow groups also have no overflow in all themes; boolean group
  has zero value inputs. Dark desktop and Light narrow screenshots inspected,
  including long manual text, aligned No value/Add value controls and explicit
  empty state. No captured browser console errors; viewport override reset.
- Fixture setup initially used incorrect API field names and then reused a
  TestClient-closed app instance, which correctly refused launch as shutting down.
  Corrected to existing cwd/output_dir fields and a fresh serving app. Both final
  launches passed; these were harness errors, not application changes.

## Limits and owner checks

Linux/Chromium and safe fixtures only; the actual VB_FreeCollapse_Wavez.py script,
GPU/scientific workloads, other browser engines/OS and physical screen readers
were not tested. Theme geometry checks cover all five palettes; visual screenshot
review covers Dark and Light. No unrelated exhaustive execution/storage suites.
Static discovery remains advisory, and manual missing-value errors are the script's
responsibility. No schema migration, source mutation, Git publication or release.

1. Open New run for your simulation; inspect value, boolean and manual groups.
   Check type/choice/required hints and that defaults are not silently passed.
2. Inspect multiple manual rows on desktop/narrow screens in your theme. Use
   Add value, remove, explicit empty, move/pair/split and keyboard navigation.
3. Review Exact argv for flags, --N 192, an unknown blank-value option and an
   explicit empty string. Rescan/save/reopen and confirm order and spellings.
4. With a disposable trusted script, validate and launch; compare recorded argv
   and parser output. Recognized invalid values should still block validation.

Stop for owner review; no merge, auto-merge, issue closure or Done transition.
