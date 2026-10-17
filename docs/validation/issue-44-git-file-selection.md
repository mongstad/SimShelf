# Issue #44 — include-first Git file selection

Validated 2026-10-17 on Linux, Python 3.14.8, Git 2.56 and Chromium in-app browser.
Review-time evidence, not a release or cross-platform certification.

## Scope and accepted base

Issue #44 was the sole Ready item. PR #43 was confirmed merged; accepted main
was `db1ad51018821d77df2bda7dd85887df96a2cdf6` (0.1.0.12). No open PR existed.
The obsolete local issue branch was already removed after owner clarification.
Work continued on the clean existing branch
`44-ux-include-first-git-fileselection-and-reviewed-ignore-rules` at that base.
The version gate proposes **0.1.0.13**, with no schema migration.

Implemented metadata-only inventories, typed inclusion preferences, exact-match
previews, separate literal-path ignore previews/append consent, and the portal
editor. Git tracking/index/history, connection/provenance interfaces, scientific
recording and prior validation evidence are unchanged. Issue #45 is not started.

## Automated validation

- **68 passed** in the focused run:
  `tests/test_git_selection.py`, `tests/test_git_provenance.py`,
  `tests/test_recording.py`, `tests/test_capture_backup.py`,
  `tests/test_application_version.py`.
- Two additional targeted cases were then added for standard linked worktrees,
  large-file warnings, inert hooks/fsmonitor and target replacement during write.
  The selection suite passed **19/19**. Total distinct backend cases: **70**.
- **6 frontend tests passed**: three in `frontend/git-files.test.mjs` and three
  existing Git observation/discovery tests. Bundled with esbuild and executed
  with Node, including typed rule matching, exact preview/consent wording,
  tracked-vs-ignored presentation and escaped filenames.
- TypeScript `--noEmit`, bundled frontend rebuild, `git diff --check`, and
  `scripts/application_version.py --base-ref origin/main`: passed.
- Existing bundled license notices are byte-for-byte unchanged.

Backend coverage includes default-empty selections; file/folder/extension exact
matches; saved/reopened rules; unchecked tracked files staying tracked; direct,
parent/shared and linked-worktree repositories; nested repository exclusion;
parent/nested ignore precedence; literal metacharacter filenames; CRLF-preserving
append; read-only cancel/preview; no index/history/source-result writes;
missing Git/no repository; inventory limits; missing permissions; oversized
ignore files; symlinks/hardlinks/FIFOs/unsupported names; stale source, index,
ignore, preferences and source-root changes; path traversal; API token and
explicit confirmation; frozen run provenance/measurements and unchanged schema;
backup/restored library preference invalidation.

Tests used disposable repositories/libraries under `/tmp/simshelf44-*`.
The command used `PYTHONPATH=src`, the dedicated development Python, `-B`,
`pytest -q -p no:cacheprovider` and external `--basetemp` directories.
One existing Starlette/httpx deprecation warning remains.

### Failures and corrections

The initial 17-case selection run had 16 passes and one failed assertion: its
"preferences changed" fixture saved an empty list over an effective empty list.
That did not change the review state. The fixture now makes a real selection
change and the stale-preview rejection passes. No runtime workaround was added.

The first installed smoke attempt lacked FastAPI in its new disposable venv;
the first server launch also used unsupported `--host`/`--no-browser` flags.
The test venv now references the existing development dependency site-packages
through a disposable `.pth`, and the verified CLI uses `ui --port 8848 --no-open`.
No dependency installation or modification of a user/simulation environment
occurred. These setup failures are not application test failures.

## Packaging and installed runtime

Built wheel + sdist from an external copy, then a wheel from the extracted sdist.
Both wheel metadata versions are 0.1.0.13; every packaged static asset matches
checkout bytes. Installed the wheel with `--no-deps` into
`/tmp/simshelf44-package/env`. Python/CLI/workspace API/OpenAPI versions and HTML,
JS/CSS/legal assets passed with Git/Node absent from PATH and outbound Python
socket connections denied. This reuses existing dependencies and is not an
independent clean dependency-resolution test. Build/check helpers and logs remain
in `/tmp/simshelf44-package.py`, `/tmp/simshelf44-installed-check.py` and
`/tmp/simshelf44-package.log`.

## Actual installed-browser checks

Disposable Alpha/Beta simulation folders shared a local repository, with Python,
JSON, NPZ, CSV and output fixtures. No owner's scientific script/library was used.

- Opened Git history without connecting; Manage Git files starts unchecked and
  distinguishes tracked source from untracked possible scientific inputs/results.
- Selected `.py` plus `config.json`, inspected exact preview, canceled and
  refreshed: choices remained unsaved. Explicit save then page reload preserved
  both choices. Group-selected paths explain how to change the group rule.
- Canceled the optional `metrics.csv` ignore preview: no ignore file was created.
  Explicit keyboard Enter confirmation subsequently created only `/metrics.csv`
  in Alpha's `.gitignore`; the file became visibly ignored, not deleted.
- Git's staged diff remained empty and the fixture's only commit remained the
  original `0963c02`. Beta and the scientific fixture files were untouched.
- Tab navigation reached Cancel at the ignore confirmation, and focus remained
  visibly outlined. Controls have named checkboxes, bounded scroll regions and
  distinct preview/save/apply actions; no auto-confirm behavior.
- Light, Dark, Onyx, Slate and Linen at 1280×900 and 390×844: document width equaled
  viewport content width (1265 / 375); the file panel was 911 / 303 pixels. No
  horizontal overflow or theme-specific layout changes. Browser warning/error
  log was empty.
- Initial visual inspection exposed inherited column layout on file labels;
  explicit scoped row direction fixed it, assets/packages were rebuilt, and
  installed browser layout was rechecked. Early rapid theme screenshots caught
  existing CSS color transitions; settled Dark was rechecked (button background
  RGB 23/30/38, text 229/237/241), and its screenshot replaced.

Local screenshots: `/tmp/simshelf44-{theme}-{width}.png`; layout measurements:
`/tmp/simshelf44-layouts.json`. Browser/server are stopped after validation.

## Limits and owner verification

Only Linux/Chromium tested; no physical screen reader, other OS/browser,
independent dependency resolution, real scientific run, hostile network filesystem,
or unrelated full-suite testing. Inventory refuses more than 1,000 entries,
20 levels or scan-time limits. Nested ignore-rule edits require Git tools;
only exact literal paths can be appended. Advisory locks do not make external
editors transactional. Partial creation/append or fsync failures require inspecting
`.gitignore` before retrying; existing bytes are never overwritten as rollback.
See [the user guide](../GIT_FILE_SELECTION.md) for full bounds and #45 handoff.

Owner checks with a disposable source repository:

1. Register a folder containing `sim.py`, `config.json`, `checkpoint.npz`,
   `metrics.csv`, and `output/result.csv`; optionally map a sibling simulation.
2. Open **Git history → Manage Git files**. Verify unchecked defaults, sizes,
   warnings and correct tracked/untracked/ignored labels.
3. Select a file, folder and extension. Preview exact matches; cancel/refresh.
   Repeat and save; reload and confirm saved choices. Uncheck tracked source and
   verify `git ls-files` still contains it.
4. Preview an exact untracked ignore addition. Cancel and compare `.gitignore`
   bytes; repeat and apply. Check only the displayed target gains displayed rules,
   original source/results remain intact, and `git diff --cached` stays unchanged.
5. Change an ignore/source file after preview: confirmation should require a new
   review. Check nested rules are visible and conflicting nested writes refused.
6. Check your preferred theme and narrow window. Inspect existing run snapshots,
   scientific values/provenance and backup restore. No initialization/staging or
   commit action should be offered.

Stop for owner review; no merge, release or subsequent issue is authorized here.
