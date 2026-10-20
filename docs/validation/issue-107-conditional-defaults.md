# Issue #107 / PR #111 — Conditional default labels

Owner-requested revision validated on 2026-10-20, Linux/Chromium. Version stays
**0.1.0.40** against accepted main `e3bb861` / 0.1.0.39. Earlier review evidence
remains historical; this report supersedes its unconditional default labels.

## Behavior

Known defaults appear as `Default: <value>` only when the actual draft differs.
Restoring the declared default hides the label. Unknown defaults produce no label;
`default_known` is unchanged. An absent input (`null`) remains distinct from an
explicit empty string: absence is not a supplied default, even if the placeholder
shows that hint. Strings compare exactly. Integer comparison uses BigInt, including
signed-64-bit decimal strings. Decimal floats compare normalized significand and
exponent strings, without Number rounding, exponent expansion or rewriting input.
The comparison uses the default supplied by existing discovery, not a saved value
or inferred scientific runtime behavior.

Disabled value drafts use the same display comparison but continue to emit nothing.
For a flag, only deliberate enabling supplies its declared action value; disabling
still emits nothing. Action/alias/choice metadata remains useful. Metadata segments
are joined without dangling separators. Authored help is passed through unchanged;
empty help creates no description placeholder. Manual rows retain their existing
renderer and bypass behavior. Grouping, #109 layout/errors/focus, backend, SWSS,
scientific scripts/TOML and schemas are unchanged.

## Validation

- **35 frontend tests passed**, including four new cases for edit/restore, saved
  custom values, disabled drafts, unknown/known-empty distinction, aliases,
  int64 precision, decimal precision, invalid/blank numerics, flags and exact argv.
  Existing argument/presentation tests also passed. TypeScript/build, version
  policy and whitespace checks passed; bundled third-party notices unchanged.
- External wheel/sdist and wheel rebuilt from sdist have identical member names
  and bytes. Installed assets match checkout; Python/CLI/API/OpenAPI version and
  offline API/assets checks passed with Git/Node absent from PATH. Existing
  dependencies were reused only through disposable environments.
- Installed browser: Light, Dark, Onyx, Slate and Linen at 1280×1000 and 390×844.
  `1e-2` hides default `0.01`; `0.0100000000000000001` shows it; restoring `0.01`
  hides it again. No row overflow. A disabled matching optional draft stayed
  absent from command preview. A supplied empty string hid a known empty default.
  Saved/reopened `2e-2` retained `Default: 0.01`, proving the saved argument is not
  treated as the default. Returning to `1e-2` hid it. Console error log empty.
- No application failures. Pip warned about an unavailable cache; installation
  completed. No dependency installation into application/scientific environments.

Local-only evidence/builds: `/tmp/simshelf-107-revision/`. No actual screen reader,
other OS/browser, real scientific solver/GPU, or fresh dependency resolution tested.
The earlier Python/backend and real-execution checks were not repeated for this
presentation-only revision. Unknown defaults and int64 edge cases were tested in
frontend rendering tests; no scientific TOML was edited to create browser cases.

## Owner checks

1. Edit a known default to a custom value, restore it, then save/reopen a custom
   value. Confirm the label follows the declared default rather than the saved one.
2. Disable an edited optional argument; confirm it stays absent from Exact argv
   regardless of hint visibility. Check empty strings and numeric spellings.
3. Inspect help/aliases/choices, unknown defaults, your theme and narrow layout.
   Groups and required feedback should remain unchanged. Review only; no merge or
   publication is authorized by this revision.
