# Issue #96 — Favorite star beside run title

Prepared for owner review on 2026-10-19. Accepted base `85c9ceb` (PR #97),
version proposal `0.1.0.35`. Sole Ready item; existing dedicated branch matched
clean accepted main. PR #97 is merged and its completed branch already removed.
No outstanding prerequisite is specified; existing run navigation and annotation
work is included in main. Historical evidence remains unchanged.

## Implementation and decisions

RunTitle renders the unchanged heading beside a 36px native button with a 22px
decorative star, 10px gap, Favorite run / Unfavorite run name and aria-pressed.
Neutral outline and filled theme-amber distinguish confirmed states. The title
can wrap, including unbroken names, while the button retains its dimensions.
Remove run, Stop, metadata and navigation remain in their existing workflows.

The star uses the existing tags PATCH/save path, retaining all non-favorite tags.
No optimistic favorite state is displayed. The run-local request gate immediately
blocks duplicate saves, skips polling during a save and rejects superseded reads
or completions after navigation. Pending saves disable the star; errors preserve
confirmed state and clear old success notices. Each keyed detail owns its gate.
No backend contract, schema, scientific data or run-history change is introduced.

## Validation

- Six frontend tests passed: accessible native toggle/decorative icon, disabled
  confirmed state, duplicate-save/poll exclusion, retry after failure, navigation
  isolation and out-of-order reads. Bundled favorite.test.mjs with esbuild and
  ran the result directly with Node. TypeScript and production build passed.
- 13 Python checks passed: 12 version tests and the existing API annotation,
  registration/upload/access-protection integration case. Existing Starlette/httpx
  deprecation warning only. Fresh-main version and whitespace checks passed.
- External direct wheel/sdist and wheel rebuilt from sdist passed; wheel members
  byte-identical. Disposable installation assets/licenses match source; no license
  notice changes. Python/CLI/API/OpenAPI/portal show 0.1.0.35. Offline startup/assets
  passed with sockets denied and Git/Node absent from PATH. Existing dependencies
  were reused read-only by the disposable environment.
- Installed Linux Chromium, localhost:8796: desktop 1280x900 short/long Dark
  titles; narrow 390x844 wrapping and unbroken Light titles, outline Onyx and
  filled Slate/Linen states visually inspected. Title and star do not collide
  with Remove run. Narrow geometry: 36x36 button, 10px heading gap, no document
  overflow; existing detail-tab scrolling stays within its container.
- Tab from navigation reaches the star with visible focus. Enter favorites;
  Space activates the same save workflow. Reload retains state. Previous/Next
  display each run's own state; Back shows matching list stars. Search for
  favorite returns precisely the two tagged runs and excludes the unfavorited run.
- Disposable server-only middleware injected a rejected PATCH: visible error,
  no changed favorite and no stale Saved notice. A ten-second delayed retry
  leaves the confirmed star disabled. Navigating before completion shows the next
  run's independent favorite and no leaked notice; returning to the list shows
  the original run's confirmed update. Three attempts produced three PATCHes.
- Fixture contains three completed no-op recordings, with unrelated baseline
  tag and source bytes preserved. No scientific simulation was executed or user
  library touched. No captured browser console errors. Viewport reset. Evidence
  and screenshots remain in `/tmp/simshelf-96/`.

## Limitations and owner checks

No validation failures. Linux/Chromium only; other OS/browser engines, physical
screen readers/touch and long scientific sessions untested. Request ordering and
loading isolation have focused gate tests; browser latency injection covered a
pending save, not every network failure permutation. Existing concurrent-client
tag-write semantics remain unchanged. Unrelated execution, removal and backend
suites were not rerun; Remove run was inspected, not executed.

1. Open a run, Tab to the star and toggle with Enter/Space. Check outline/filled
   state, accessible label, visible focus and persistence after reload.
2. Check a long title at desktop/narrow width and in your preferred theme.
3. Navigate Previous/Next/Back; confirm each run and list/filter shows its own
   favorite state and Remove run remains available under its existing rules.
4. With a failed or slow connection, confirm no premature success or repeated
   submission; retry after recovery and verify server-confirmed state.

Stop for owner review; no merge, auto-merge, issue closure, Done or release.
