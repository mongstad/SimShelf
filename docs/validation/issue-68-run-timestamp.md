# Issue #68 — Year in secondary run timestamp

Prepared for owner review on 2026-10-18. Accepted base: `4f77f75` (PR #76).
Application version: `0.1.0.24`; no publication or schema change.

## Change

The existing date formatter accepts an optional year flag, enabled only for the
smaller timestamp beneath the Run record title. It adds `year: "numeric"` to the
existing locale-based options. Default locale, time zone, month/day/hour/minute
formatting and other date call sites are unchanged. The heading still renders
`run.name` directly; no names, timestamps or stored records are rewritten.

Changed application files: `frontend/main.tsx`, rebuilt `static/assets/app.js`,
and the authoritative `_version.py`. CSS and third-party notices are unchanged.

## Checks

- TypeScript and frontend build passed; version gate against accepted main and
  `git diff --check` passed.
- Application-version tests: **12 passed**, with the existing Starlette/httpx
  deprecation warning. No additional unit-test machinery was introduced for this
  small presentation change; focused installed-browser checks cover the behavior.
- External isolated sdist, wheel from sdist, direct wheel and fresh installation
  passed. Wheel members/bytes match; metadata versions, bundled JS and notices
  verified. Python/CLI/API/OpenAPI report `0.1.0.24`. Offline TestClient startup
  passed with socket connections denied and Git/Node absent from PATH. The optional
  TestClient dependency `httpx2` was installed only in the disposable environment.
- Installed Linux/Chromium fixture: three finalized records and one live recorder.
  The running secondary timestamp included `2026`; finalized records displayed
  `Dec 31, 2025, 11:30 PM`, `Jan 1, 2026, 12:30 AM` and
  `Jan 1, 2025, 12:30 AM`. UTC inputs crossing the local midnight/year boundary
  retained the browser's existing local-time behavior.
- The default heading `Run Oct 18 · 21:54:40` and custom headings remained exact.
  List timestamps continued to omit the year, confirming the narrow scope.
- Inspected desktop 1280×900 and narrow 390×844 layouts, including running and
  finalized headers and a long custom title. Timestamp and neighboring controls
  remained usable; no CSS changes needed. No browser warning/error logs observed.
- All four raw database run rows matched their pre-browser snapshot exactly.
  Screenshots and disposable artifacts: `/tmp/simshelf-68-package/`.

No validation failures occurred. Other OS/browser engines, alternate browser
locales/calendars, physical screen readers and unrelated scientific/backend suites
were not tested. Existing Intl localization remains authoritative; no forced
locale or time-zone conversion was introduced. The fixture recorder is stopped
only after inspecting and comparing the stored rows.

## Owner verification

1. Open both a running and finalized run. Confirm the smaller timestamp includes
   the year and the large title is unchanged.
2. Open records from different years, including around local New Year. Confirm
   their date/time still follows your browser locale and time zone.
3. Check a custom-named run at narrow width; confirm title, metadata and controls
   remain usable. Existing list timestamps should retain their prior formatting.

Stop for owner review; no merge, issue closure or release performed.
