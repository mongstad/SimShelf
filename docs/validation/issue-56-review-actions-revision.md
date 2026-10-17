# Issue #56 — mutually exclusive review actions

PR #57 Stage A, 2026-10-18. Proposed **0.1.0.15** remains valid against accepted
main `cfd2b889cb41cb57444f58fe9fb4fa0035258ea8` / 0.1.0.14.
Earlier review evidence is preserved unchanged.

## Focused change

Normal settings show Review archival settings. Once the server returns a review,
that button is removed and only Confirm changes and Cancel appear with the reviewed
configuration. Future-output editing is disabled while review is active. Existing
server preview and confirmation payloads are unchanged; toggle activation uses the
same review. Successful confirmation or Cancel restores the normal action with
concise feedback. Errors retain existing authoritative-state refresh behavior.

Cancel starts focused. If the removed Review button initiated the review, focus
returns to its newly rendered replacement; its settings disclosure reopens if
necessary. Toggle-initiated reviews return focus to that toggle. No backend,
master connection/preference, consent, storage, capture, scientific-record,
historical-download, recovery or backup code changed. CSS and notices are unchanged.

## Validation

- **12 frontend archive tests passed**, esbuild CommonJS bundle executed directly
  with Node. Normal-state rendering asserts one Review action and no confirmation
  or Cancel. Actual active-review interaction is checked in the browser below.
- **43 backend tests passed:** `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python -B
  -m pytest -q -p no:cacheprovider tests/test_git_archive.py
  tests/test_application_version.py` with disposable external basetemp. Existing
  stale/invalid consent, failure-state, isolation, frozen-run, connection and
  historical-download regressions remain passing.
- TypeScript, frontend build, diff check and accepted-main version gate passed.
- Wheel, sdist and sdist-derived wheel built externally; version/static bytes
  verified. Installed Python/CLI/API/OpenAPI/assets/license smoke passed without
  Git/Node in PATH and with socket connections denied. Dependencies reused from the
  dedicated environment through `.pth`, not freshly resolved.
- Existing Starlette/httpx deprecation warning; no failed checks in this revision.

Installed Linux/Chromium browser with a disposable two-simulation archive verified:

1. Normal settings have one Review action. Open review has zero Review buttons,
   exactly one Confirm changes plus Cancel, visible rules and disabled editing.
2. Keyboard Cancel returns focus to the recreated Review button, including after
   collapsing the settings disclosure while review was open. Confirm succeeds,
   closes review, shows success and restores normal controls/focus.
3. OFF → ON opens the same review while the toggle remains OFF. Cancel returns
   focus to that toggle without granting consent. Changing fixture capture settings
   after preview causes confirmation rejection and authoritative OFF remains.
4. Invalid `../unsafe.csv` rejects preview, preserves editable input, restores
   normal actions and displays the server error. Refresh archive status clears
   an unconfirmed review; navigation to another simulation starts with no review
   and preserves its independent Enabled state.
5. Dark, Light, Onyx, Slate and Linen inspected at 1280×900 and 390×900. Review
   action counts remain correct, controls wrap, focus is visible, and measured
   document widths show no horizontal overflow. Final console checked for errors.

Temporary screenshots: `/tmp/simshelf56-actions-{theme}-{width}.png`;
final desktop proof `/tmp/simshelf56-actions-final.png`.

## Owner verification and limits

Open Automatic archival settings and review: the initiating button should vanish.
Cancel and confirm separately; check normal action/focus return. Repeat activation
from OFF through the toggle. Try changing settings from another view after preview
and confirm stale consent is rejected. Check refresh/navigation and preferred
themes/narrow width. Master connection and remembered path should behave as before.

Linux/Chromium only; no physical screen-reader or real scientific workload/scale
certification. No Stage B or other issue work. Stop for owner review; no merge or
release.
