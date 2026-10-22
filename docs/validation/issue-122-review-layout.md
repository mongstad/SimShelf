# Issue #122 — Owner visual-review revision

2026-10-22; follows the initial report without rewriting its evidence. The owner
requested more visible spacing and removal of routine prose across the entire
New run dialog in PR #126. Baseline commit: `8cd5cee`; accepted main remains
`fa9768d`. Review fixes retain application version 0.1.0.46.

## Revision

- Action rows have 16px horizontal and 12px wrapped gaps, 16px separation from
  nearby feedback, 28px between settings and 36px between major sections.
  Mapping cards, parameter rows, paste controls and progress consent follow the
  same scoped layout. Two-column alignment and narrow stacking remain intact.
- Remove duplicated entry context, unchecked-interpreter/metadata prose, routine
  progress explanations, manual-row boilerplate and output-mapping tutorials.
  Parameter-specific unsupported reasons and validation messages remain visible.
- **Check environment…** groups optional Python/dependency check buttons. Its
  trust warning is shown beside the execution actions when expanded. Errors,
  busy state and concise checked-version results stay outside the disclosure,
  so collapsing it never conceals feedback. The check payload and confirmation
  flag are unchanged; opening the disclosure performs no check.
- Validation and launch retain brief trust warnings immediately before their
  buttons. SWSS policy reasons, binding uncertainty, incompatible-policy guards,
  progress migration consent and outside-capture acknowledgement are retained.
  Backend, exact argv, saved settings, execution and scientific data are unchanged.

## Screenshots

The before images are unmodified captures from the initial installed-wheel
review; after images use the revised production bundle and the same disposable
registration, missing-interpreter input and error. Desktop is 1366×900; narrow
is 390×844. Scroll positions differ to show the relevant controls. These are
actual browser captures, not mockups. The new check disclosure is expanded in
the main after comparisons; a separate image shows its collapsed state.

| View | Before | After |
| --- | --- | --- |
| Desktop | [Before](../images/issue-122-review/before-desktop.png) | [After](../images/issue-122-review/after-desktop.png) |
| Narrow | [Before](../images/issue-122-review/before-narrow.png) | [After](../images/issue-122-review/after-narrow.png) |

Additional inspected states:
[collapsed checks with error](../images/issue-122-review/after-desktop-collapsed.png),
[output mapping](../images/issue-122-review/after-narrow-outputs.png),
[command review](../images/issue-122-review/after-narrow-command.png),
[progress consent](../images/issue-122-review/after-narrow-progress.png),
[paste controls](../images/issue-122-review/after-narrow-paste.png).

## Validation

- TypeScript and production build passed; distributed assets rebuilt, license
  bytes unchanged.
- 29 focused bundled frontend tests passed, no skips. Copy assertions were
  updated for removed idle prose and shorter mapping guidance.
- Six browser regression cases passed at desktop and narrow widths. Existing
  exact-argv/SWSS saved-policy/rescan guards remain covered. Added checks assert
  collapsed-by-default checks, trust disclosure at execution, 16px button gaps
  (12px when wrapped), unchanged confirmed check payload, visible specific errors
  after collapse, field/section spacing and incomplete-mapping blocking.
- Real production-bundle screenshots inspected desktop and narrow entry,
  interpreter, working directory, output settings/mapping, parameter controls,
  progress consent, expanded paste/Exact argv, validation and launch areas.
  No dialog horizontal overflow; keyboard focus and disabled/error states visible.
  Progress consent was canceled; no schema upgrade or simulation launch occurred.
- Wheel/sdist and sdist-rebuilt wheel were built from a disposable source copy.
  Python/static member bytes agree across source, sdist and both wheels; metadata
  remains 0.1.0.46. Version gate and diff checks passed.

One initial output test still expected removed prose; corrected the assertion
and reran successfully. The new interpreter-error browser assertion initially
hit an unimplemented fixture route; added the explicit failing response and
reran at both widths. These were harness corrections, not backend changes.

Limits: Linux/Chromium and disposable fixtures only; no scientific runs, other
OS/browser/screen-reader validation, all-theme audit or exhaustive parameter and
dependency combinations. Full backend/version suites were not repeated for this
review's presentation-only changes; the initial report retains their prior
results. User libraries, historical reports and scientific files were untouched.

## Owner checks

1. Compare the desktop/narrow before and after images, then inspect your own
   New run dialog at both widths. Check button gaps and separation from feedback.
2. Expand **Check environment…**; verify the trust warning and separated buttons.
   Check a missing interpreter, collapse the area and confirm its error remains.
3. Expand progress, declaration notes, paste and Exact argv. Check wrapping and
   keyboard focus; cancel progress consent rather than upgrading a real library.
4. Add an incomplete output mapping and review required parameters and the SWSS
   incompatible-policy state. Confirm their existing warnings/blocking remain.
