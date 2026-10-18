# Issue #52 / PR #81 — owner-requested settings dialog

Follow-up evidence for the owner's PR comment 6255157100, on the existing issue
branch. Application version remains **0.1.0.27**: review fixes do not increment it.
Accepted main remains `e1a5730b538aa3ecf2a7e0a35ab9427d29f3191b`.
The original [removal evidence](issue-52-simulation-removal.md) is preserved.

## Changes

A labelled cogwheel sits at the simulation header's upper-right, with space
reserved when the header wraps. It opens a dedicated native settings dialog with
**Change source location…**, **Remove simulation…**, and default-focused **Cancel**.
Tab/Shift+Tab wrap inside the dialog; Escape, Cancel and backdrop dismissal return
to the cogwheel. Each administrative action opens its existing separate review.
Canceling that review returns to the cogwheel, or to **Locate source folder…**
when recovery was opened there. The missing-source warning and recovery button
remain visible; an available source shows only its path, without management buttons.

No backend, schema, removal/relocation semantics, source/archive retention or
historical records changed. **Start simulation** remains unchanged (issue #82 is
excluded). Bundled JS/CSS and current user instructions were updated.

## Validation

- TypeScript, frontend build and application version gate passed.
- Four bundled Node tests passed: new settings-dialog/removal-initial-state tests
  and existing relocation-review tests. The initial ESM bundle attempt failed on
  React's dynamic `require("util")`; using a CommonJS test bundle resolved the
  harness problem. No application dependency was changed.
- 62 focused Python tests passed: `test_simulation_removal.py`,
  `test_relocation.py`, `test_application_version.py`. One existing
  Starlette/httpx deprecation warning. Temporary test paths were outside checkout.
- External sdist/wheel and direct wheel checks use `/tmp/simshelf-52-cogwheel`;
  installed browser validation used the disposable package environment and a new
  fixture on port 8880. No owner workspace was used.
- Desktop 1280×900: normal overview has a cogwheel and source path, no relocation
  or removal button. Enter opens settings with Cancel focused. Both focus wrap
  directions and Escape return passed. Opening removal still showed exact-name
  review with disabled empty confirmation; opening relocation showed path entry.
- Missing-source fixture retained its warning and Locate action. Entering the
  moved fixture path produced the existing explicit old/new-path review. Cancel
  returned focus to Locate without committing relocation.
- Visually inspected settings in Light, Dark, Onyx, Slate and Linen, with System
  on initial overview. Narrow Linen 390×844 retained the upper-right cogwheel and
  readable dialog (356 px client width = scroll width), without dialog overflow.
- Initial native Tab behavior could leave button focus at the end; explicit
  wrapping was added and rechecked in both directions.

Screenshots are local temporary artifacts under `/tmp/simshelf-52-cogwheel`.
No Windows/macOS, physical touch or screen-reader validation. Only Linen received
narrow visual validation. No destructive operation or relocation commit was needed
for this UI-only revision; existing safety tests passed and backend files are
unchanged. The prior full removal/backup/archive evidence remains separate.

## Owner check

Select a simulation → upper-right cogwheel. Confirm the normal page has no
administrative buttons, while each settings action opens its separate review.
Check Cancel/Escape/Tab and focus return, desktop/narrow themes, and the visible
Locate recovery action for a missing source. Do not confirm removal on valuable
data merely to review this layout. Stop for owner review; do not merge.
