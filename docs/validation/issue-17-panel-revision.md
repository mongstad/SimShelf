# PR #34 compact progress panel

2026-10-17, frontend-only follow-up to issue #17. Existing branch
`17-ux-show-live-simulation-progress-when-reported-by-a-run`; proposed version
0.1.0.8 retained against accepted main `2fcfc900d99b59380b4822fc242bfb7389ed2478`
(0.1.0.7). Prior validation reports remain historical and unchanged.

## Presentation

The panel shows **Progress**, right-aligned percentage, an 8px solid teal bar,
comma-grouped current/total steps and an optional stage. Unknown values show
**Progress unavailable** without a bar, percentage or invented counts, including
finalized records without progress. Source/time are retained in the unchanged
payload but no longer displayed. Execution status stays in the existing run header;
the panel no longer duplicates status or routine explanatory prose. Existing
progress persistence-error alerts are preserved.

Scoped CSS uses Light fill/track `#147d70` / `#dde8e5`, Dark `#249e8b` / `#233b3a`.
Calculated sRGB relative-luminance contrast ratios: **3.99:1 Light**, **3.61:1 Dark**.
Percent/count text and native labeled progress semantics complement color. Native
WebKit/Gecko progress styling is explicit; forced-colors uses system colors.
No gradient, animation, glow, dependency, backend or schema change.

## Checks

- TypeScript `tsc --noEmit`: passed.
- `node frontend/build.mjs`: passed; rebuilt distributed JavaScript and CSS.
- Five frontend tests passed. Bundled `frontend/progress.test.mjs` with esbuild
  (`--platform=node --format=cjs`, external `node:test`, `node:assert/strict`),
  then ran `/tmp/simshelf17-panel-tests.cjs` with the runtime's Node executable.
  Checks cover known values, `3,000 / 50,000 steps`, unknown/malformed totals,
  stage absence/escaping, all four statuses retaining the same progress,
  99.9% rounding, error alerts, metadata immutability and existing settings examples.
- Wheel/sdist and wheel from extracted sdist built outside the checkout. Both
  wheels have version 0.1.0.8 and byte-identical current static assets. Installed
  the rebuilt wheel externally with `--force-reinstall --no-deps`; Python/CLI/API/
  OpenAPI/static checks passed without Git/Node in PATH and with API outbound
  startup connections denied after dependency installation. The disposable
  environment uses system-site-packages; not an isolated dependency audit.
- License notices and full third-party license file are unchanged. Backend Python
  sources, types, persistence, parsers, lifecycle and API contracts are unchanged.
  No backend suite was repeated for this presentation-only change; prior lifecycle
  evidence remains in the earlier reports.

## Actual installed-browser checks

Chromium, synthetic library `/tmp/simshelf17-panel-browser/library`, no user data:

- Desktop 1280px: completed fixture at 6%, `3,000 / 50,000 steps`, compact panel
  in Light and Dark, visible filled/remaining distinction.
- Narrow 390px: interrupted fixture at 2%, `1,000 / 50,000 steps`, optional Solve
  stage; visible low-percent fill in both themes. Document scroll width 375px
  within 390px viewport. Existing detail tabs retain their own horizontal scroll.
- Failed unknown fixture: only Progress unavailable inside the panel.
- Failed 100% fixture: Progress, 100%, `50,000 / 50,000 steps`; status remains in
  the header. These are synthetic finalized records, not new scientific runs or
  a repeat of the prior real-process lifecycle validation.
- No source/time/routine status explanations visible inside progress panels.
  Browser warning/error log empty. Restored theme/viewport and closed own tab.

Temporary screenshots: `/tmp/simshelf17-panel-light.png`,
`/tmp/simshelf17-panel-dark.png`, `/tmp/simshelf17-panel-narrow-light.png`,
`/tmp/simshelf17-panel-narrow-dark.png`.

No check failures. A temporary Python test-edit helper emitted an escape-sequence
warning; generated JavaScript tests and typecheck passed. Initial screenshot during
the existing theme transition was retaken after the theme settled. Firefox,
screen-reader behavior, forced-colors rendering and other platforms were not
manually tested. No new scientific execution/performance claim is made.

## Owner verification

1. Reopen the real 50,000-step run: check Progress / 6% and
   `3,000 / 50,000 steps`, with no source/time/status prose inside the panel.
2. Inspect 2–6% in both themes at desktop and narrow widths. Stage, if supplied,
   should remain concise. Unknown progress should show no fabricated values.
3. Compare final completed/failed/interrupted runs to their unchanged header
   status. Reporting 100% still has no control over execution or final status;
   this revision changes rendering only.
4. Re-fetch accepted main and run the version gate before merge. Stop for review;
   no merge, release or subsequent issue work is authorized by this handoff.
