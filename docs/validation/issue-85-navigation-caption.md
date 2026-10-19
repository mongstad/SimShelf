# Issue #85 — Run navigation caption removal

Prepared for owner review on 2026-10-19. Accepted base `7f93f13` (PR #87);
application version `0.1.0.30`. Issue #85 was the sole Ready item when selected.
Existing dedicated branch matched accepted main. Navigation predecessor #54 / PR
#76 is merged. Previous issue branch #83 was already absent locally/remotely.

## Change

Removed the common caption element for opened-list, fallback and unavailable
navigation, plus its full-width CSS rule. Existing button labels, native disabled
states, focus effect, ordering, simulation scoping and 1,000-run fallback remain
unchanged. No replacement tooltip or hidden paragraph is needed: the navigation
landmark and three buttons retain their accessible names. The ordinary 22px
section margin remains; the caption row and its flex gap no longer exist.
Rebuilt JS/CSS and advanced the application version. Historical reports retain
their original descriptions; no backend or scientific data changes.

## Validation

- Four existing frontend navigation tests passed after updating caption assertions;
  coverage includes list snapshot/deduplication, simulation isolation, chronological
  ties/year boundaries, absent entries, disabled boundaries and all caption modes.
  Bundled `frontend/navigation.test.mjs` with esbuild and ran it with Node.
- TypeScript `tsc --noEmit`, frontend build and 12 application-version tests passed.
  Existing Starlette/httpx deprecation warning only. Version gate and whitespace
  check passed. Third-party notices/licenses unchanged.
- Built direct wheel and sdist externally; rebuilt wheel from extracted sdist.
  Wheel members matched byte-for-byte. Installed in a new disposable environment
  using existing read-only test dependencies; no existing environment modified.
  Installed static assets/licenses match source. Python/CLI/API/OpenAPI report
  0.1.0.30. Offline startup/assets passed with socket connections denied and Git/
  Node absent from PATH. The portal version label also shows 0.1.0.30.
- Installed Chromium fixture at localhost:8785: two simulations, three completed
  context recordings each, all under `/tmp/simshelf-85/`. From the mixed list,
  Alpha traversed all three runs without crossing into Beta. Enter activated Next;
  reaching the oldest boundary disabled Next and moved focus to Back. Reloading
  the direct run URL retained the correct fallback boundary; Previous worked.
  Back selected Alpha. Search by a single run ID disabled both neighbor controls;
  keyboard Back retained the search and one-result list.
- Desktop 1280x900 Dark and narrow 390x844 Dark/Light screenshots inspected.
  No caption or reserved row; narrow navigation height 30px with two children,
  no small element, and document scroll/client widths both 375px. Existing detail
  tabs still scroll independently. No captured browser console errors.
  Local evidence: `/tmp/simshelf-85/{desktop,narrow,narrow-light}.png`.

## Limitations

No validation failures. A lookup for an older disposable fixture found it absent;
a fresh fixture was created. Other browsers/OSes, physical screen readers/touch,
other palettes, histories beyond 1,000 runs and delayed responses were not tested.
No unrelated backend/scientific suite was run for this presentation-only removal.
Existing navigation algorithms and fallback request code were not changed.

## Owner checks

1. Open a run from a filtered list; verify the clean navigation row, Previous/Next
   boundaries and Back retaining the filter and simulation.
2. Open a direct run URL and reload; verify Previous/Next remain simulation-scoped.
3. Use keyboard Enter through the oldest boundary; verify focus moves to Back.
4. Check desktop and narrow layouts in your preferred theme for comfortable spacing.

Stop for owner review; no merge, issue closure, Done transition or release.
