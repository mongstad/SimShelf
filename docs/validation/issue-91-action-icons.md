# Issue #91 — Settings and New run action icons

Prepared for owner review on 2026-10-19. Accepted base `ff7a2a3` (PR #89),
application version `0.1.0.32`. Sole Ready issue; existing issue branch clean and
identical to accepted main. PR #89 merged; its branch was already cleaned up.
The Open source folder proposal (#90) remains separate Backlog work and is not
present or required here.

## Implementation

Moved the existing SVG icon map/renderer verbatim from main.tsx to shared Icon.tsx
and added one matching trash glyph. Settings uses the existing folder glyph and
new trash glyph, with unchanged exact labels and click handlers. Full-width
buttons align left, using the established 8px gap; nonshrinking icons and wrapping
text handle constrained widths. The trash glyph supplies a restrained destructive
cue without changing button colors or confirmation safeguards. New run… uses the
existing plus glyph rather than Play, preserving its primary color and dialog
semantics. All three SVGs are decorative aria-hidden; text supplies the names.
No icon dependencies, backend, storage, scientific data or positioning changes.

## Validation

- Three existing frontend settings/removal/activity tests passed, updated for
  span-wrapped labels and two decorative SVGs. Existing disabled-confirmation,
  labelled-dialog and fail-closed activity checks remain.
- TypeScript, frontend build and 12 application-version tests passed. Existing
  Starlette/httpx deprecation warning only. Version gate/whitespace checks passed.
  A direct comparison confirmed all existing icons and renderer moved verbatim;
  only the new trash glyph was added. Bundled React notice order changed only; full third-party licenses unchanged.
- Direct wheel, sdist, rebuilt-from-sdist wheel and disposable installation passed;
  wheel members byte-identical and installed assets/licenses equal source. Python,
  CLI, API, OpenAPI and portal label show 0.1.0.32. Offline startup/assets passed
  with outbound sockets denied and Git/Node absent from PATH. Existing dependency
  environment used read-only by the disposable environment.
- Installed Chromium fixture at localhost:8791, all source/data under
  `/tmp/simshelf-91/`. Disposable schema-2 fixture only; no real library migration.
  Settings Enter opens and focuses Cancel; Tab wraps to Change source location.
  Enter opens its separate review with blank path and disabled Review new location.
  Removal opens its separate exact-name confirmation, warnings and disabled
  Remove simulation button. Both canceled; no destructive action submitted.
  Cancel restores focus to the settings cogwheel.
- New run… retains its accessible name, opens configuration through Enter, and
  leaves final Start simulation disabled pending validation. All-simulations
  disabled state remains. Database still has one registration and zero runs;
  source bytes unchanged after all dialog checks.
- Desktop 1280x900 Dark settings/overview visually checked. Narrow 390x844 settings
  visually checked in Light, Onyx, Slate and Linen. New run… accessible name,
  decorative icon and nonoverflow geometry checked in all five themes at narrow
  width. Settings icons share x=373 on desktop; narrow Light shares x=43.5, icon
  width=18, gap=8, with no button overflow.
- At 240px width both labels wrap to 34px height while icons remain 18px and
  neither button overflows. This stresses wrapping without changing user labels;
  actual translated strings are not available. Existing page sections may scroll
  at that extreme width. Viewport override reset; no captured browser errors.
  Screenshots and package evidence remain in `/tmp/simshelf-91/`.

## Limitations and owner checks

No validation failures. Other browsers/OSes, physical screen readers/touch and
actual translations untested. No real relocation/removal or execution submitted,
and no unrelated backend/scientific suite rerun for decorative presentation.

1. Open Simulation settings; inspect aligned folder/trash icons and exact labels.
2. Use keyboard activation for each action, verify its existing separate review
   and cancel without submitting. Confirm focus returns to the cogwheel.
3. Check New run… plus icon; opening it must not execute a simulation.
4. Inspect your preferred theme and narrow width, including wrapped labels.

Stop for owner review; no merge, issue closure, Done transition or release.
