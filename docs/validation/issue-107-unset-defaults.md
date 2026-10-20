# Issue #107 / PR #111 — Hide unset default footers

Owner-requested final correction, 2026-10-20. Version remains **0.1.0.40**
against accepted main `e3bb861` / 0.1.0.39. Earlier reports remain historical.
This supersedes the prior conditional-default report's footer for absent values.

`ParameterHint.tsx` now requires a non-null current value before showing a known,
differing default. Unset values hide the footer even when the default is visible
as a placeholder. Explicit empty strings remain supplied values: they hide the
footer for a known empty default and show it for a differing known default.
Unknown defaults never produce a footer. Disabled optional drafts follow the same
visibility rule while remaining absent from argv. Disabled flags have no supplied
action value; action metadata remains visible without a default footer.

Validation: **36 frontend tests passed**, including a state sequence of null,
equal, custom, explicit empty, restored equal and restored null for enabled and
disabled optional arguments. Each step checks footer visibility, immutable row
state and exact argv; unknown defaults are also checked throughout. Existing
precision, flag, manual, alias and presentation regressions passed. TypeScript,
frontend build, version policy and whitespace checks passed. Bundled licenses
remain unchanged. External wheel/sdist, rebuilt-sdist wheel byte equality and
installed asset/API/CLI/version checks passed using disposable environments.

No application failures. This one-condition correction does not change CSS,
validation, saved arguments, grouping, SWSS, scientific sources or backend logic.
The previous five-theme desktop/narrow browser checks were not repeated; this
revision is verified through rendered-component regressions and package checks.
No actual screen reader, other OS/browser or scientific execution tested anew.

Owner check: open an unset optional input and confirm only its placeholder shows
the known default; enter a differing value, restore the default, and disable the
argument. Verify label visibility and unchanged omission from Exact argv. Check
explicit empty strings separately from unset values. Stop for review; no merge
or publication.
