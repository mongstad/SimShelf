# Issue #95 — New run document-plus icon

Prepared for owner review on 2026-10-19. Accepted base `6a19c1a` (merged PR #94),
application version `0.1.0.34`. Issue #95 was the sole Ready item; its existing
dedicated branch was clean and equal to accepted main. Issue #93 is merged;
its completed branch was already cleaned up. Historical evidence is unchanged.

## Change

Added a hand-authored file-plus path to the existing Icon map and selected it
only for New run…. The folded sheet and internal plus use the existing 18px size,
1.6 stroke, round joins/caps, currentColor and decorative aria-hidden semantics.
The existing 8px button gap, exact caption/ellipsis, tooltip, eligibility and
callback remain. No dependency, CSS, other icon, launch or scientific-data change.
Rebuilt the distributed JavaScript and advanced the required application build.

## Validation

- Existing overview-action checks: three passed (empty/populated All simulations,
  available selection and missing-source disabled state). Bundled with esbuild
  and executed directly with Node; Node's --test wrapper initially summarized
  the bundle as one file, while direct execution reported the three cases.
- TypeScript typecheck, frontend build and 12 application-version tests passed.
  Existing Starlette/httpx deprecation warning only. Fresh accepted-main version
  check and git diff --check passed. CSS and third-party notices/licenses unchanged.
- External wheel and sdist built; wheel rebuilt from extracted sdist has identical
  members/bytes. Disposable installed assets/licenses match the checkout.
  Python/CLI/API/OpenAPI and portal report 0.1.0.34. Offline startup/assets passed
  with socket connections denied and Git/Node absent from PATH. Disposable
  installation reused existing dependency files read-only.
- Installed Chromium UI on localhost:8795, disposable fixture only: visually
  inspected 1280x900 Dark and Light and 390x844 Light, Onyx, Slate and Linen.
  Glyph remains recognizable and aligned with adjacent Terminal / editor.
  Narrow Linen DOM check confirms no document overflow, 18px decorative SVG,
  currentColor, 1.6 stroke, 8px gap and exact New run… accessible text.
- Tab from Terminal / editor reaches New run… with visible focus. Enter opens
  the selected simulation's configuration with separate Start simulation disabled
  pending validation. Closed without launch. No captured browser console errors;
  viewport override reset. Fixture has one registered simulation, zero runs and
  unchanged source bytes. Evidence remains under `/tmp/simshelf-95/`.

## Limitations and owner verification

No validation failures. Linux/Chromium only; other browser engines, operating
systems, physical screen readers/touch and scientific workloads untested.
Missing-source eligibility covered by existing frontend assertions, not a live
moved-folder scenario. Final execution and unrelated backend suites were not
rerun because this change only selects a decorative glyph. No release published.

1. Select a simulation and inspect the document-plus beside New run… in your theme.
2. Narrow the window; confirm icon/text spacing and recognizable sheet/plus.
3. Tab to New run… and press Enter: configuration should open without execution;
   the separate final Start simulation action remains. Close without starting.
4. Confirm Add simulation/sidebar + retain their original plus icon.

Stop for owner review; no merge, issue closure or Done transition.
