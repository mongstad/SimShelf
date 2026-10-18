# Issue #64 — First experimental pre-release preparation

Date: 2026-10-18 (Europe/Oslo). **Prepared, unpublished; readiness holds remain.**
No tag, release, asset upload, visibility change, merge or scientific-data change
was performed. Review this report before authorizing any publication.

## Identity and scope

- Issue: [#64](https://github.com/mongstad/SimShelf/issues/64), sole Ready item.
- Branch: `64-release-prepare-first-public-simshelf-experimental-pre-release-with-wheel-and-sdist`.
- Accepted main and candidate source: `aa4367951811ea171a9e3f0689978d292e6d341a`.
- Version: **0.1.0.17**; intended tag **v0.1.0.17**, not created.
- PRs #58 and #63 verified merged. Their branches are absent; no deletion needed.
  Existing issue branch was clean and equal to main/origin/main at start.
- Repository verified **PRIVATE**; no local/remote tags or GitHub releases found.
  No duplicate open PR existed at start.
- The issue explicitly says no version increment merely for issuing a release.
  `_version.py` remains byte-identical to accepted main. The ordinary implementation
  checker was run and rejected equality (expects 0.1.0.18); this is recorded, not
  disguised as a pass. That next-build gate is inapplicable to the explicitly
  authorized same-version release-preparation scope. No checker/policy was changed.

This PR adds only release notes, checksums and evidence. The candidate is built
from accepted main, **not** this preparation PR's later commit. The preparation
notes are therefore not inside its archives. Any different release target needs
fresh artifacts, digests and validation; do not relabel these bytes as another commit.

## Local artifacts

Kept outside the checkout under
`/home/Nozba/Codex/SimShelf/release-candidates/0.1.0.17-aa43679/`.
`dist/` holds the wheel, sdist and SHA256SUMS.txt; `source/` is the exact git archive;
`sdist/` and `rebuilt/` hold the extracted sdist and independently rebuilt wheel.
Fresh `build-env/`, `install-env/`, `sdist-env/` are disposable environments.
Artifacts have **not** been uploaded or committed to Git.

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| simshelf-0.1.0.17-py3-none-any.whl | 193808 | 1bea38d9eb05feb6f5ea59695f5246b2829288819e01b335451053f3f9ce663b |
| simshelf-0.1.0.17.tar.gz | 448940 | 0950c4a1834929bf69d4b7cfdb4d6777f5ed4506207c86220373366c6be8e27c |

[Checksums](../releases/v0.1.0.17-SHA256SUMS.txt) describe these exact local bytes;
build timestamps may change archive digests on later builds. `sha256sum -c`
passed for both. GitHub-generated source archives will be separate downloads
created after an approved tag; they have not been generated/verified here.

## Build and runtime evidence

Fedora 44, Python 3.14.8, Git 2.56.0; isolated PEP 517 builds. Exact source was
exported with `git archive aa4367951811ea171a9e3f0689978d292e6d341a`.
A new venv installed `build`, then `python -m build SOURCE --outdir DIST` produced
wheel/sdist. `python -m build --wheel EXTRACTED_SDIST --outdir REBUILT` passed.
Fresh separate venvs installed the candidate wheel (with dev extras for tests)
and the sdist. No editable/source-path installation was used for runtime checks.

- Wheel/sdist versions match 0.1.0.17. Rebuilt wheel has exactly the same member
  names and member bytes as the candidate wheel (not a claim about ZIP timestamps).
- Wheel MIT license and every bundled static file/license notice match accepted
  source bytes. Sdist contains LICENSE, THIRD_PARTY_NOTICES, installation guides,
  examples and executable launcher. No frontend rebuild was needed or performed.
- **FAILED packaging check:** all three `docs/images/01.png`, `02.png`, `03.png`
  are absent from the sdist. MANIFEST.in includes Markdown but not those PNGs.
  The accepted repository README's six gallery src/href references resolve to
  tracked PNGs, but the extracted-sdist gallery cannot resolve them. Wheel README
  metadata is also relative-link text, not a standalone documentation bundle.
- Wheel and sdist installed independently. Each passed Python `__version__`, CLI,
  `/api/workspace` and OpenAPI checks inside `unshare -Urn` with an empty PATH:
  no network, Git or Node. Imports came from each environment's site-packages.
- Installed-wheel CLI registered a disposable scalar example and recorded
  `--simulation release-example --steps 40 --size 16`: exit 0, completed, 3 managed
  copies, 3 references, source snapshot, measurements and logs retained.
- Actual Chromium browser on installed-wheel localhost port 8754 showed 0.1.0.17,
  run list, completed detail, full completion bar, captured image, source identity,
  measured value and capture counts. Portal assets and notices served byte-for-byte;
  all copied output downloads matched originals. Explicit Quit completed and
  the server exited. Temporary browser evidence is outside the checkout.
- **87 tests passed**, one existing Starlette/httpx deprecation warning:
  `test_application_version.py`, `test_api.py`, `test_recording.py`,
  `test_capture_backup.py`, `test_portal.py`, `test_git_archive.py` against the
  installed wheel. Covers real child failures, argv/API joining, portal cancellation,
  backup/restore and immutable archive/history behavior. No test failures.

Logs: setup.log, build.log, rebuilt.log, install.log, sdist-install.log and tests.log
in the candidate directory. Temporary runtime data is `/tmp/simshelf64-runtime`;
owner libraries, original source projects and external archives were not touched.

## Publication audit and unresolved decisions

Current tracked tree: 152 files. Targeted filename review found no tracked database,
private-key, environment, backup ZIP or large scientific-output file matches.
Read-only scan of **485 distinct reachable blobs** across fetched refs found no
matches for the selected private-key/GitHub-token/AWS-key patterns or SQLite file
signature. **63 blobs contain home-directory strings** (including documentation,
old bytecode and other historical content). This is a targeted check, not a
comprehensive secret certification; unreachable/remote-only data and arbitrary
secret formats were not covered. No history was rewritten or historical evidence edited.

The [original source audit](issue-1-source-audit.md#historical-exposure-assessment)
already records absolute developer paths in 11 reachable bytecode blobs. Removing
files from the current tree did not erase that exposure. The owner must explicitly
accept it or authorize separate remediation before making the repository public.

All three current README screenshots were visually inspected. They show scalar
example data, local run identifiers/times and version 0.1.0.16. Some paths/bookmarks
are blurred; **03.png retains a visible partial home/source path in the sidebar**.
Blur is not proof of anonymization. Owner approval of public screenshot content
and reachable history is still needed. Images were not altered or replaced here.

**Publication holds:**

1. Decide how to address the sdist gallery omission. A source packaging fix should
   be accepted before building a new candidate; do not patch the archived bytes
   while continuing to claim the original accepted commit. Alternatively the owner
   must explicitly accept and disclose the documentation limitation.
2. Review/approve historical developer-path exposure and screenshot content.
   Do not rewrite history under release-preparation authority.
3. Approve exact release target, artifacts, experimental notes, repository-publication
   timing, and Pre-release status. Recheck main, visibility and tag/release collisions
   immediately beforehand. No such approval is inferred from Ready status.

## Known limitations and owner verification

The [draft notes](../releases/v0.1.0.17-draft.md) explicitly retain open #59 output
path review UX, #60 absent source-relocation recovery, and #61 generated-output
inventory blocking archival consent. These were read and summarized, not fixed.
No Windows/macOS, additional browser-engine, old Python/Git matrix, GPU, scale or
long-session certification. No new theme matrix or exhaustive suite was run.
No PyPI upload, binary executable, remote sync or automatic install is provided.

Owner review:

1. Review the draft warning and known limits; keep independent source/result,
   library and external-archive backups. Reference-only files and the external
   archive are not included in library ZIPs.
2. Resolve the three publication holds above. This handoff is **not** release-ready
   approval merely because runtime tests pass.
3. Verify `sha256sum -c SHA256SUMS.txt` from local candidate `dist/`, install each
   package in a new environment and open a new disposable library. Confirm version,
   basic recording, copied/reference outputs and backup restoration.
4. Check the GitHub README thumbnails/full-size links and the extracted-sdist
   omission. Verify MIT and all third-party notices.
5. Only after explicit later approval, publish the approved exact commit/assets
   as a GitHub **Pre-release**. Never repoint a tag or replace published bytes.

Stop for owner review. No next issue was started.
