# Issue #9: local Git foundation validation

2026-10-17, proposed application **0.1.0.12**. Accepted main:
`492402c9843170b5243fe40ae0213722a06e92cf`, version **0.1.0.11**.

## Authorization and scope

Issue #9 was the sole Ready item on SimShelf project 2. Its existing dedicated
branch was clean, local/remote/main all at accepted main. No open PR existed.
Previous PR #41 was merged; its branch was already absent locally/remotely and
its historical reports remain unchanged. Portal/recording, external workspace,
versioning and progress predecessors are merged into accepted main.

The owner explicitly selected **Local foundation first** in response to the staged
scope question. This PR delivers connection preview/confirmation, existing-folder
mapping, read-only local history and the provider-neutral provenance interface
for #7. Local commits, import/copy and remote fetch/pull/push need separately
authorized follow-ups; no half-implemented synchronization controls are exposed.
No other issue or project settings were changed.

## Implementation decisions

- Git defaults to disconnected. All new-run Git observations go through one
  provider-independent module; removed the old unconditional automatic probe.
- A single connection maps existing registered folders without moving source.
  Settings are an additive, locked/transactional metadata key; no schema change.
  Preview is revalidated on confirmation. Moved/restored libraries and replaced
  repositories require reconnection, bound to host/path/inode identities.
- Recording preserves exact snapshots, scientific versions and actual statuses.
  Optional Git observations freeze with the snapshot ID; old runs are untouched.
  Captured-file comparison is explicitly limited to captured bytes/executable bits.
- Git commands are bounded, safe argv, local and read-only, with inherited Git
  overrides removed, optional writes disabled, and transport/lazy fetch disabled.
  No status refresh, filters, hooks, credentials, diff drivers or signatures run.
  Raw-byte comparison is conservative about CRLF/LFS/filter differences.
- Inspection failure or unsupported paths never become clean-state claims.
  Missing Git/unmapped/disabled/unavailable states do not block recording.
- Portal history uses existing surfaces, theme colors and responsive controls.
  Run details distinguish observed Git metadata from scientific version/snapshot.

## Automated checks

Dedicated Python 3.14 environment, external temporary fixtures, no user library:

```
PYTHONPATH=src python -B -m pytest -q -p no:cacheprovider \
  --basetemp=/tmp/simshelf9-final-tests \
  tests/test_git_provenance.py tests/test_application_version.py \
  tests/test_recording.py tests/test_capture_backup.py \
  tests/test_version_edge_cases.py tests/test_portal.py tests/test_api.py
```

**72 passed**. One existing Starlette/httpx deprecation warning. Additional SHA-256
repository regression: **1 passed, 14 deselected**. This establishes 73 distinct
passing focused backend cases, including 15 Git cases.

Coverage: disabled/no-Git recording, two folders sharing a repository, clean and
raw dirty bytes, staged/untracked/ignored files, source snapshot comparison,
changes outside the simulation, detached HEAD, branch changes, conflict index,
linked worktree, missing initial commit, malformed settings/preview, stale mapping,
repository replacement, path/symlink confinement, malicious filter/fsmonitor/hook
configuration, inherited Git overrides, result-size/time bounds, and backup/
restore/disconnect with immutable prior run provenance. Both ordinary local-path
and file-URL bare remotes were configured, then an unreachable HTTPS URL: local
inspection did not fetch or require credentials. No transport feature is tested
or shipped. Existing capture, recording, API and portal lifecycles passed.

Frontend Git display suite bundled with esbuild and run with Node: **2 passed**.
Nullable/error states, detached/conflict/incomplete state, separate repository and
simulation changes, escaped history subjects and immutable inputs covered.
TypeScript, frontend build, diff checks and accepted-main version gate passed.
Tracked JS/CSS rebuilt; bundled third-party license notices unchanged.

No failing product checks in this implementation. A repository-inspection command
looked for nonexistent `tests/test_core.py`; validation used the actual focused
files above. No dependencies were added or user environments modified.

## Actual browser validation

Disposable source repository `/tmp/simshelf9-browser/sources`, Alpha/Beta folders,
and separate disposable library. Source UI on port 8845; installed wheel on 8846.

- Preview both mappings; Cancel leaves disconnected. Re-preview and press Enter
  on Connect locally; connection persists after page reload.
- History shows main/commit and folder-scoped history. Modifying Beta marks the
  repository changed but Alpha unchanged. No automatic Git mutation/network.
- Light, Dark, Onyx, Slate, Linen at 1280x900 and 390x844: controls fit; narrow
  panel 343 px and document 375 px, within viewport. Labels and long paths wrap.
- Installed UI shows version 0.1.0.12 and same local history. Disconnect preserves
  sources and an existing completed fixture run with scientific version 1.0,
  energy=2, Git SHA/branch and captured-files-match observation.
- Browser warning/error logs empty. Browser settings restored; owned test servers
  stopped afterward. No real scientific script was executed.

Local screenshots: `/tmp/simshelf9-{light,dark,onyx,slate,linen}-{1280,390}.png`,
`/tmp/simshelf9-installed-history.png`, `/tmp/simshelf9-installed-run.png`.
DOM layout evidence: `/tmp/simshelf9-browser-layouts.json`.

## Packaging

Built wheel/sdist from external source copy `/tmp/simshelf9-package/source`, then
wheel from extracted sdist. Both wheel versions are 0.1.0.12 and every static byte
matches checkout, including license notices. Installed into a reused disposable
external environment. Python/CLI/API/OpenAPI/static checks passed with Git and
Node absent from PATH and outbound API socket connections denied. Installed
browser used normal PATH to exercise optional Git. Build log:
`/tmp/simshelf9-package.log`.

## Limits and owner checks

Linux Chromium and Git 2.56 only. No physical screen-reader, other OS/browser,
older Git versions, long/high-volume repository certification or unrelated full
suite. Package environment has system-site access; not an isolated dependency
audit. History is latest 20 folder commits, not a diff editor. Repository scans
are bounded observations, not atomic snapshots of a concurrently edited tree.
Raw comparisons may conservatively flag conversions; symlinks/submodules may
make status unknown. Detailed contract and limits: [Git provenance](../GIT_PROVENANCE.md).
Remote authentication/rejection/divergence workflows are intentionally deferred
with remote operations; no external hosting account was used.

1. In a disposable repository with two registered simulation folders, open Git
   history; preview selected mappings and cancel once. Then explicitly connect.
2. Inspect clean/dirty state, a change in the other folder, branch history and
   detached HEAD. Confirm scientific versions are independent.
3. Record a harmless run, inspect Git vs exact snapshot, then disconnect. Verify
   its old provenance stays unchanged and a new disconnected run still works.
4. Try absent Git or a moved repository; expect unavailable, never false clean.
   Restore a backup into a separate library and explicitly reconnect there.
5. Check preferred theme/narrow window and assistive technology. Review this PR;
   do not infer authorization for local commits, remote sync, merge or release.
