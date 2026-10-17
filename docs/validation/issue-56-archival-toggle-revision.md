# Issue #56 — automatic archival toggle revision

PR #57, Stage A owner review revision. Proposed version remains **0.1.0.15**
against accepted main `cfd2b889cb41cb57444f58fe9fb4fa0035258ea8` (0.1.0.14).
The original Stage A report is preserved unchanged.

## Implementation boundary

One named, keyboard-operable switch sits beside the selected simulation's status,
separately from master repository connection status. OFF uses the existing disable
endpoint; ON requests the existing preview and still requires explicit confirmation.
The switch reflects authoritative backend state, never an attempted activation.
Errors refresh state; invalid rule drafts remain editable. Cancel receives focus
when review opens, and closing review or finishing a toggle returns focus.

Future-output configuration is under collapsed Automatic archival settings.
Review appears only on request. Existing capture-relative guidance, limits and
backup warning remain. Disabling retains the existing backend semantics: saved
consent is cleared, so review/re-enter future-output rules when enabling again.
File-selection preferences are independent. Pending runs retain frozen consent.

Changed runtime files are only `frontend/GitArchive.tsx`, `frontend/style.css` and
rebuilt JS/CSS. Focused tests and the archive guide were updated. No backend
implementation, schema, scientific records, archive events, Git history, managed
copies, recovery, backup or source-file behavior changed. License notices are
byte-for-byte unchanged. No Stage B or remote functionality was added.

## Focused checks

- **37 backend tests passed:** archive 25 and application version 12. Added API
  coverage for disabling during a run, preserving frozen plans and old records/
  events, other-simulation isolation, canceled/unconfirmed previews, changing
  consent while running, historical downloads and reopening the store. Stale
  capture and file-selection reviews are rejected without enabling archival.
- **10 archive frontend tests passed**, including switch naming, checked/disabled
  states, unavailable-master behavior, removal of duplicate actions, collapsed
  settings and absent review until requested. These are render assertions;
  interactive behavior was checked in the actual browser below.
- TypeScript, frontend build and `git diff --check` passed. Application version
  gate retains 0.1.0.15; review fixes do not increment the version again.
- Built wheel and sdist externally and a second wheel from extracted sdist.
  Verified metadata and bundled static bytes; installed externally. Installed
  Python/CLI/API/OpenAPI/assets/license routes passed with Git/Node absent from
  PATH and socket connections denied. Existing development dependencies were
  reused through a local `.pth`; this is not fresh dependency-resolution coverage.

The existing Starlette/httpx deprecation warning remains. A sandboxed TestClient
smoke invocation stalled and was interrupted; the identical smoke passed outside
the sandbox with its explicit socket-network denial retained. One browser label
locator timed out; refreshing the observed DOM and using its textbox role worked.
Initial browser testing exposed focus loss after OFF; focus restoration was fixed
and rechecked in the installed package. No unresolved product failure was observed.

## Installed browser checks

Used an external disposable two-simulation library and real local archive with
the installed wheel on localhost. No owner library or scientific inputs were used.

- Enabled → OFF only after response; Space operates the switch and focus returns.
- OFF → review keeps the switch OFF. Cancel has initial focus; Enter cancels and
  restores switch focus. Explicit confirmation changes it to ON.
- Invalid future rule remains disabled with a visible error and editable draft.
  Changing capture settings after preview rejects confirmation; fresh review and
  confirmation succeed. The second simulation remains enabled independently.
- Disconnecting the master while OFF prevents activation and explains the needed
  connection. Reconnecting does not itself grant consent.
- Browser reload and an actual application restart retain enabled consent.
  Explicit settings review while already enabled can be canceled without turning
  it off. Existing runs remain listed; record/event/download preservation is
  additionally asserted by backend tests.
- Dark, Light, Onyx, Slate and Linen inspected at 1280×900 and 390×900, both normal
  enabled controls and activation review. Text, focus and ON/OFF are visible;
  measured document widths show no horizontal overflow. Final normal layouts
  were rechecked after keeping the backup warning outside collapsed settings.
- Switch role, accessible simulation name, checked state and polite status region
  verified. No warnings/errors in the final browser console.

Temporary screenshots: `/tmp/simshelf56-toggle-{theme}-{width}.png`,
`/tmp/simshelf56-toggle-review-{theme}-{width}.png` and final normal views at
`/tmp/simshelf56-toggle-final-{theme}-{width}.png`. These are disposable fixture
evidence, not repository assets or owner research.

## Limits and owner checks

Linux/Chromium only; no physical screen-reader, maximum-size archive, long-running
workload or real VB_Phi_Field certification. Existing backend safety tests were
rerun; unrelated suites were not. External Git archives remain outside workspace
backups. Status remains a point-in-time observation; server validation is decisive.

1. Open Git history: one Automatic archival status/switch beside the simulation
   name, distinct from green master connection. Settings starts collapsed.
2. Turn OFF; verify old files/history remain and another simulation is unaffected.
3. Turn ON, cancel, and confirm OFF remains. Review again and confirm; verify ON,
   then refresh/restart. Review future rules before re-enabling after disable.
4. Change capture or file selections after preview; confirmation must reject stale
   consent. Correct settings and review again. Try a disconnected master.
5. While a disposable run is active, change future consent and verify that run's
   original plan remains; later runs use the new consent. Download an old revision.
6. Use Tab/Space/Enter in preferred themes and a narrow window; check focus returns
   after OFF and Cancel, and explicit review remains required for ON.

Stop for owner review. No merge, release or subsequent issue work.
