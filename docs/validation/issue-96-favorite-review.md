# Issue #96 — History indicator and silent favorite confirmation

Owner-requested PR #98 revision, 2026-10-19. Version remains 0.1.0.35 against
accepted main `85c9ceb` / 0.1.0.34. Original review evidence is unchanged.

## Changes

RunHistoryTitle groups the existing noninteractive favorite indicator immediately
after the run title, on its first line and before archive-commit metadata. It
remains inside the existing row button, with a 6px gap and the existing theme
color. Table scrolling, row selection and navigation are retained. The individual
RunTitle component and its clickable star placement are unchanged.

Only favorite toggles opt out of the existing save success notice. Other saves
retain the default confirmation. The server-confirmed response still drives the
star; errors, immediate duplicate-save guard and stale-response handling are
unchanged. No replacement message, backend/schema change or version increment.

## Validation

- Seven focused frontend tests passed, including history title/star grouping
  before archive metadata without a nested control, and the existing accessibility,
  disabled-state, duplicate/poll, failure/retry and navigation-order cases.
- TypeScript, bundled build, 12 version tests and the existing API annotation /
  access-protection integration test passed. Existing Starlette/httpx warning only.
- External wheel/sdist/rebuilt-wheel byte identity, disposable installation,
  source/installed assets/licenses and offline startup/assets passed. Version
  surfaces remain 0.1.0.35; notices/licenses unchanged. Dependencies reused read-only.
- Installed Linux Chromium: 1280x900 and 390x844. For both short and long favorite
  rows, measured title/star on the same line, star after title and above archive
  metadata in Dark, Light, Onyx, Slate and Linen. Dark desktop and Light desktop /
  narrow screenshots visually inspected. Table retains its internal horizontal
  scrolling for long rows/narrow windows. Favorite search returns two matching
  runs; unfavorited row excluded. Short-name search also retains the indicator.
- Keyboard Enter opens a table row and toggles its detail star. Successful
  favorites produce no Saved banner. Save notes still produces Saved. A rejected
  favorite PATCH clears old success and shows the error without changing state.
  Space retry with ten-second delay disables the control, retains confirmed state
  and permits navigation without leaking a notice to the next run. Returning /
  reloading observes the saved state; a subsequent successful toggle remains silent.
- No captured console errors; viewport override reset. Disposable evidence in
  `/tmp/simshelf-96-review/`, with independent library/source and installed package.
  Archive counts were injected by test-only server middleware to exercise layout;
  no real archive operation or scientific code was executed.

## Limits and owner checks

No validation failures. Linux/Chromium only; physical screen readers, other engines
and operating systems untested. All-theme checks measure geometry; screenshot
review covers Dark and Light. Actual Git archival, scientific execution and
unrelated backend suites were not rerun for this presentation-only revision.

1. In Run history, inspect a favorite run with archive commits: the star should
   follow its title on the same line, with archive metadata below.
2. Check desktop/narrow layout and your theme; open rows using the keyboard.
3. Toggle favorite on/off: only the confirmed star changes, with no success banner.
   Failed saves must still show an error. Save notes should still show Saved.
4. Reload, navigate Previous/Next/Back and search favorite; confirm persistence
   and independent per-run state.

Stop for owner review; no merge or release.
