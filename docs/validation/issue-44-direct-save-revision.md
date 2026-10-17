# Issue #44 / PR #46 — direct selection saving

Review revision, 2026-10-17. Proposed version remains **0.1.0.13** against
accepted main `db1ad51018821d77df2bda7dd85887df96a2cdf6` / 0.1.0.12.
The original [implementation report](issue-44-git-file-selection.md) is preserved.

## Change and safety

**Select → Save selection** replaces the visible inclusion preview. Save is always
shown below the choices and enabled when rules differ from saved preferences.
Selected-file count and saved/unsaved status remain visible. Optional Selected
rules disclosures enumerate current matches, distinguish individual paths from
future folder/type matches, and allow removal. Stable rule keys keep disclosure
state attached to the correct rule when another is removed. Repetitive text is
reduced; tracked-file and scientific-input/large-file warnings remain.

The frontend submits the displayed revision/rules to the existing preview API
internally and then submits its exact returned payload to the existing save API.
Neither check is bypassed; stale or invalid requests stop the save. Backend,
limits, persistence binding, schema, scientific recording, Git state and ignore
preview/confirmation code are unchanged. Issue #45 still requires separate commit
review and explicit staging/commit consent.

## Checks

- **31 backend tests passed**: `tests/test_git_selection.py` and
  `tests/test_application_version.py`, using external pytest fixtures. Includes
  stale source/preferences/index/ignore state, invalid paths/rules, API consent,
  unchanged Git/source bytes, scientific provenance, schema and restore behavior.
- **9 frontend tests passed**: six file-selection tests and three existing Git
  observation/discovery tests. New checks cover optional match disclosures,
  count/status, order-independent saved-state comparison, exact two-request save
  payload, preview rejection without saving, and save-stage rejection propagation.
- TypeScript, frontend build, diff checks and accepted-main version gate passed.
  License notices and CSS remain unchanged.
- Wheel/sdist and wheel-from-sdist rebuilt externally; metadata 0.1.0.13 and all
  static asset bytes checked. Installed Python/CLI/API/OpenAPI/static checks
  passed with Git/Node absent and outbound Python socket connections denied.
  Test environment reuses existing development dependencies through its external
  `.pth`; no user interpreter was modified.
- Installed Chromium on a disposable library: directly saved an individual file;
  saved folder and extension choices with Enter; reloaded and verified saved
  choices/count; removed/edited existing rules; discarded unsaved edits; resaved.
  A metadata-only touch to a fixture source invalidated the displayed inventory:
  Save rejected it with “Files, rules or preferences changed. Refresh and review
  again.” Refresh restored saved choices and a subsequent edit/save succeeded.
- The separate ignore preview still showed the exact addition and explicit Apply
  and Cancel. Cancel left the entire fixture source/Git tree byte-identical to its
  before-state hash inventory; direct preferences saves also changed no bytes
  there. No Git staging or commit occurred.
- Light, Dark, Onyx, Slate and Linen checked at 1280×900 and 390×844; direct Save,
  count and unsaved status remain accessible without horizontal page overflow.
  Local screenshots: `/tmp/simshelf44-direct-{theme}-{width}.png`.

No test failures in this revision. The existing Starlette/httpx deprecation
warning remains. A temporary edit helper emitted a Python string-escape warning;
the generated JavaScript test regex was valid and tests passed. Browser inspection
found disclosure state following list indexes on removal; stable rule keys fix it.

## Limits and owner checks

Linux/Chromium only; no physical screen reader, other operating systems/browsers,
independent dependency installation or real scientific run. Backend code is
unchanged, so unrelated suites were not rerun. Original inventory/write limits
and external-editor concurrency caveats still apply.

Owner: open **Git history → Manage Git files**, edit an individual checkbox and
choose **Save selection** directly. Check count/status, reload, then try folder and
extension choices and optional rule matches. Edit and use **Refresh files /
discard edits**. Verify a stale inventory requires refresh, and `.gitignore`
changes still require their own preview/confirmation. Review in your preferred
palette and narrow window. Stop for owner review; no merge/release or issue #45.
