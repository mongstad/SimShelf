# Issue #127 — New run visual audit and refinements

October 24, 2026. Accepted base: `d34b2b56dc5eb8da19f36261b260aaa29af7bfd1`
(PR #139); version proposal: `0.1.0.54` from `0.1.0.53`.
The owner explicitly authorized implementing the audited refinements in this PR.
Issue #122 / PR #126 and all earlier reports/screenshots remain historical evidence.

## Audit and decisions

The audit used the accepted launch components in a real native dialog, with
controlled network responses and disposable source/environment paths. Before
captures were saved before changing production source. It covered initial and
expanded setup/environment, typed and manual arguments, required errors, output
policy/mappings, progress consent, paste, command/argv and validated feedback.

| Finding | Implemented refinement | Preserved boundary |
| --- | --- | --- |
| Optional progress preceded entry and Python selection; setup fields were scattered. | Group entry, working directory and optional name under Run setup; move optional progress near review. | Same state, defaults, consent and request handlers. |
| A tall field sequence lacked clear boundaries. | Headings and dividers separate setup, environment, parameters, outputs and review. | No wizard, extra steps or hidden mandatory settings. |
| Entry update/rescan buttons consumed separate desktop rows. | Align beside their inputs on desktop; stack with visible gaps at narrow widths. | Same disabled/busy and interpreter-trust checks. |
| Capture settings and output mappings were separated by all arguments. | Keep mappings and resolved capture feedback beside capture policy. | Same path review, exact argv, policy guards and outside-capture acknowledgement. |
| Search repeated routine interaction instructions; long fixed-policy option repeated the help below it. | Retain counts and concise selected-policy label; remove duplicated routine text. Place manual-mode checkbox before its label. | Source-binding/conformance uncertainty, specific errors and policy reasons remain visible. |
| Validated feedback inherited flex layout, splitting prose and paths into columns. | Render validation feedback as one readable block, including narrow widths. | Same backend result; no stronger claim about dependencies or readiness. |
| Dialog title differed from the New run entry point. | Name and explicitly label this dialog New run. | Other modal names and workflows are unchanged. |

This improves hierarchy and related-control placement; it does not attempt to
fit every expanded state in one viewport. Scrolling remains deliberate, with
existing bounded parameter collections and command previews.

## Before / after

Paired fixture desktop captures are 1280 × 720; narrow captures are 390 × 844. Fixture paths,
argv and metadata are the same for each paired scenario. Native scrolling/focus
positions vary to show the corresponding controls. These are browser captures,
not image mockups. The fixture supplies a dialog wrapper around the real launch
component; separate installed captures verify the production application.

| State | Before | After |
| --- | --- | --- |
| Initial desktop | [Before](../images/issue-127/before-desktop.jpg) | [After](../images/issue-127/after-desktop.jpg) |
| Initial narrow | [Before](../images/issue-127/before-narrow.jpg) | [After](../images/issue-127/after-narrow.jpg) |
| Expanded parameters | [Before](../images/issue-127/before-parameters-narrow.jpg) | [After](../images/issue-127/after-parameters-narrow.jpg) |
| Command review | [Before](../images/issue-127/before-review-desktop.jpg) | [After](../images/issue-127/after-review-desktop.jpg) |
| Validated feedback | [Before](../images/issue-127/before-validation-narrow.jpg) | [After](../images/issue-127/after-validation-narrow.jpg) |
| Incompatible saved policy | [Before](../images/issue-127/before-policy-narrow.jpg) | [After](../images/issue-127/after-policy-narrow.jpg) |

Additional evidence: [outside-capture review](../images/issue-127/after-review-narrow.jpg),
[busy environment check](../images/issue-127/after-busy-desktop.jpg),
[installed desktop](../images/issue-127/installed-desktop.jpg),
[installed narrow review](../images/issue-127/installed-review-narrow.jpg).

## Validation

- `node node_modules/typescript/bin/tsc --noEmit` and `node frontend/build.mjs`:
  passed. JS/CSS distribution assets rebuilt; third-party notices unchanged.
- Six esbuild-bundled frontend test files executed directly with Node:
  arguments, parameters, parameterPresentation, outputs, interpreters and
  ParameterHint: **50 tests passed**. Direct invocation reports their individual
  tests; this environment's `node --test` parent output only counted six files.
- `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 /home/Nozba/Codex/SimShelf/environments/SimShelf/bin/python -m pytest -q -p no:cacheprovider --basetemp /tmp/simshelf-127-python tests/test_application_version.py tests/test_output_paths.py tests/test_parameters.py`:
  **34 passed**, one existing Starlette TestClient deprecation warning.
- Existing SWSS/output DOM harness: **6 cases passed at desktop and narrow**,
  including exact saved argv, stale policy correction, rescan invalidation,
  uncertainty, failed refresh, error visibility and mapping blocking. Its setup
  grid selector was updated for the new containing section.
- New launch harness: **5 desktop scenarios passed** (ready, missing required
  value, incompatible saved policy, plain/manual source, schema-3 progress
  consent); ready interaction/consent checks also passed at narrow width.
  Checks cover no automatic code execution, unchanged exact saved argv including
  an empty string/leading zeros/exponent, validation unlocking Start, required
  error focus, non-executing disclosure, visible collapsed errors, pending paste,
  incomplete mappings and explicit outside-capture acknowledgement. A delayed dependency check also showed
  its busy status with both execution-check buttons disabled. No launch
  or migration endpoint is provided by the fixture.
- Existing parameter-validation DOM harness: **6 cases passed**, including
  omitted/invalid values, NaN/Infinity, aliases, repeated reveal/focus and required
  flags, with unchanged argv.
- System, Light, Dark, Onyx, Slate and Linen checked for layout at desktop and
  390-pixel width; no dialog horizontal overflow. System/Linen visual samples
  inspected; all theme palettes are unchanged. Keyboard disclosure activation,
  required-field focus, Exact argv, close/Escape and installed narrow navigation
  checked. No application console warning/error logs observed.
- Wheel and sdist built externally; wheel rebuilt from extracted sdist. Source
  Python/static and rebuilt-wheel package bytes match. Installed import/CLI,
  workspace/OpenAPI versions and static serving passed with empty PATH (no Git
  or Node). Installed Chromium showed 0.1.0.54 and the labeled New run dialog;
  manual-mode validation preserved exact argv, then the dialog was dismissed.
  The registered fixture raises if launched; it was never launched. No runs,
  source snapshots or output folders were created by the browser checks.

Reproduction: run `node scripts/test_launch_polish_browser.mjs /tmp/simshelf-127-check`,
serve that directory on loopback, and open `?state=ready&test=1`. Other states:
`required`, `blocked`, `manual`, `migration`; `theme` accepts the six theme values.
The page reports PASS/FAIL in `#results`. Existing harness builder:
`node scripts/test_swss_output_browser.mjs /tmp/simshelf-127-output-check`.

## Failures and limits

One initial new-fixture assertion expected the normally hidden output-destinations
section in the incompatible-policy state. That brittle expectation was removed;
the actual no-save/policy-consent checks passed. A summary-control selector was
corrected during manual browser work. The temporary fixture listener stopped;
it was restarted and a fresh tab restored the checks. These were validation
harness/transport issues, not application failures.

Linux/Python 3.14/Chromium only. Other OS/browser engines, screen readers,
scientific/GPU execution and an exhaustive state/theme cross-product were not
tested. Full unrelated backend suites were not repeated for presentation-only
changes. Network-isolated startup was not separately tested; package startup
checks used local-only operations after dependencies were installed. Browser
fixture results establish UI behavior, not runtime SWSS/scientific conformance.
Original user libraries, databases, source/config bytes, scientific outputs and
historical evidence were not changed. No package or release is published.

## Owner verification

1. Compare the paired captures; open New run for your usual simulation at desktop
   and narrow widths. Review setup grouping and input/action alignment.
2. Expand parameters/flags, search and clear, edit a value, paste/cancel and inspect
   Exact argv. Verify argument spelling/order, empty values and saved settings.
3. Open Check environment; ensure nothing executes until you choose a check.
   Confirm trust warnings and errors remain visible and actionable.
4. Inspect outputs, mappings and the incompatible saved-policy recovery. Validate
   an outside-capture draft: Start must require the existing acknowledgement.
5. Review progress settings; in an older disposable library, open and cancel
   upgrade consent. Do not migrate a scientific library just for visual review.
6. Validate a trusted disposable setup and inspect single-column feedback, keyboard
   focus, Escape and your preferred theme. Launch only if you deliberately want
   to run that trusted script; validation alone does not execute its source.
