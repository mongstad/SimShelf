# Issue #74 — Stable run duration width

Prepared for owner review on 2026-10-18. Base: accepted `e95737e` (PR #77).
Application version: `0.1.0.25`; no release or schema change.

## Reproduction and correction

The header uses `display:flex; justify-content:space-between`. Its first child's
intrinsic width includes the duration, whose computed numeric style was `normal`.
With the date/title/status held constant at 1280×900, changing `9.0s` to `10m 0s`
increased the duration width from **22.1875 to 36.890625 px**. Favorite moved from
**x=790.53125 to x=797.875** (7.34375 px); Remove run stayed at x=1108.03125.
The earlier unconstrained-clock check also showed movement, but was not used to
isolate the cause because its timestamp text changed too.

Only the Run record duration span gains a class. Scoped CSS gives it tabular
numerals, a 12ch minimum width and no internal wrapping. At the tested font size
this reserves **83.265625 px**, preventing normal timer text growth from changing
the header's intrinsic width. Existing flex wrapping handles narrow screens.
No timing calculation, formatter, refresh interval, title, date, status, accessible
semantics, controls, execution or stored-data code changes.

## Validation

- Installed baseline and candidate measured in separate disposable Linux/Chromium
  portals. Test-only API responses and a controlled browser clock hold metadata
  constant and feed elapsed values through the unchanged three-second UI refresh.
  These are accelerated layout samples, not claims of multi-day real execution.
- Candidate samples `9.0s`, `10.0s`, `11.0s`, `18.0s`, `59.9s`, `1m 0s`,
  `10m 0s`, `59m 59s`, `60m 0s`, and `1000000m 0s` retained duration width
  83.265625 px and Favorite/Remove positions **821.0625 / 1108.03125 px**.
  Individually controlled boundary measurements are saved in
  `/tmp/simshelf-74-package/measurements.json`; additional samples are in the tool
  evidence. The formatter already expresses an hour as `60m 0s`; it is unchanged.
- 390×844: duration wraps as a whole metadata item when necessary; buttons remain
  usable. Long title and extended version metadata inspected without collisions.
  1024×800 long-header/finalized layout also inspected. Existing button text can
  wrap at this width; this change does not redesign the header.
- Finalized `59m 59s` remained exact. Keyboard Tab from Favorite skipped disabled
  Remove run and reached Overview as before. No browser warning/error logs on
  the corrected candidate fixture. System theme checked; no color changes.
- TypeScript and frontend build passed. **12 application-version tests passed**,
  with the existing Starlette/httpx deprecation warning. Version gate and
  whitespace checks passed. Focused browser geometry checks cover this CSS fix;
  no extra unit-test framework was introduced.
- External isolated sdist, wheel from sdist, direct wheel and fresh installation
  passed. Wheel contents match; JS/CSS/notices and Python/CLI/API/OpenAPI version
  `0.1.0.25` verified. Offline TestClient startup passed with socket connections
  denied and Git/Node absent. Optional `httpx2` was installed only in the disposable
  validation environment. Third-party notices remain unchanged.

## Failures and limits

A first fixture restart encountered an active output reservation left by the
terminated fixture; each later invocation used a fresh workspace, retaining the
old evidence. The test HTML wrapper initially failed to obtain the file-response
body, then its clock endpoint was hidden by the static mount, producing a temporary
NaN timer in the fixture. Directly reading the installed index and handling the
clock endpoint before the mount fixed the harness; these were not application
changes. The timed sample sequence also outran the tool's short selector waits;
missing boundary samples were measured individually. Only successful corrected
samples support the results above.

Other OS/browser/font combinations, physical screen readers, all-theme review,
real long-running scientific jobs and unrelated backend suites were not run.
A minimum width is not a maximum: exceptionally longer labels can still expand
rather than being clipped. The tested million-minute value is about 1.9 years.
The fixture changes only disposable response projections/clock, not user records.
Historical evidence and scientific sources/outputs are untouched.

## Owner verification

1. Open a running record and watch Favorite/Remove run as seconds change digits
   and cross into minutes. Their horizontal positions should remain stationary.
2. Inspect a run near one hour (`59m 59s` → `60m 0s`) and a finalized duration.
   Confirm the existing timing/format and status behavior remain intact.
3. Check a narrow window and a long custom title/version. Duration may wrap to
   another metadata line; controls and keyboard navigation should remain usable.

Stop for owner review; no merge, issue closure, Done transition or publication.
