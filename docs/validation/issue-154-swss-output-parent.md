# Issue #154: schema-3 output-parent discovery

Accepted SimShelf base: `23e23480eb13e37bd4f7bed979cec7fd407c633b`, build
`0.1.0.61`; proposed build `0.1.0.62`. Standards predecessor #41 / PR #42
merged at `198f234693535c1f7bc7e78cd8e599a510c2d494`. The adopted normative
v3.0 text and executable reference were inspected, not the earlier proposal alone.

Issue #154 was the first/only Ready item. Its existing linked branch matched
accepted main and was clean. No open PR existed. Previous PR #153 was merged and
its branch already absent locally/remotely; fetch/prune confirmed current main.
Predecessors #120, #146 and #148 were merged. Historical reports remain unchanged.

## Scope and decisions

See [the user/implementation contract](../SWSS_OUTPUT_PARENT.md). Both schemas
remain explicit. New schema-3 output routing preserves exact argv, validates
binding eligibility and conservative token ownership, refuses conflicting local
settings, and records read-only path/identity evidence. Source exclusion remembers
previous internal parents in additive location-bound metadata. No storage schema
migration, scientific-source edit, automatic output movement or historical rewrite.

External capture requires an explicitly prepared existing directory and preserves
local managed copies. It does not broaden Git consent; the current preservation
settings cannot review external roots, so automatic Git archival is unavailable
there. Stronger required-volume identity contracts, hostile-filesystem isolation,
coordinated full roots and automatic identification of arbitrary solver children
are not claimed. Unlisted input roles require author/owner layout review.

## Validation record

Validation uses Linux, Python 3.14.8, existing development dependencies and
disposable `/tmp` copies/workspaces. Source tests set `PYTHONPATH=src`; no owner
simulation or production library is executed or modified.

- First corrected focused batch: **171 passed, 1 skipped** (reference path absent).
- Expanded actual portal/reference/backup batch: **78 passed**, including pinned
  schema-2 and schema-3 scalar-decay reference copies. Four schema-3 runs cover
  default/repeat/internal/external parents with identical source snapshots,
  exact numeric/empty-string argv and complete four-file capture.
- TypeScript and production build passed; license notices retained.
- Broader source suite: **229 passed**, covering output review, both schemas,
  snapshots/comparison, portal/recorder lifecycle, preservation, backup and version.
- Final installed-wheel suite: **218 passed, no skips**, including both pinned
  standards references, real portal repeat runs, internal Git-byte verification,
  external local capture without widened consent, backup restoration, journaled
  start/boundary rollback and idempotent replay, and inaccessible-path refusal.
  The existing Starlette TestClient deprecation warning remains.
- Final browser fixture: **12 scenarios passed, no console errors**; includes
  schema-3 automatic previews using actual argv and explicit manual fallback after
  metadata becomes invalid. Responses are fixture-controlled, separate from real
  backend/reference tests. Installed desktop UI showed build `0.1.0.62`, two
  completed reference runs, declared-parent discovery and successful validation.
- Wheel, sdist and rebuilt wheel were generated in disposable external copies.
  Both wheels matched all **39 runtime Python/static files** and version metadata.
  An external venv reused existing dependencies read-only, then installed only the
  new SimShelf wheel. Import/CLI, workspace/OpenAPI and static assets worked with
  Git and Node absent from PATH. No dependency installation or release occurred.

[Installed capture preview](../images/issue-154/installed-capture.jpg) shows the
one effective destination and its separately stated declaration/binding limits.
Other OS/browser engines, narrow/all-theme layouts, actual external mount loss,
hostile filesystem races and owner scientific workloads remain untested.

Setup failures are not product passes: the first sandbox TestClient batch stalled
and was interrupted; its replacement initially imported the older installed
package because `PYTHONPATH` was missing. The new test module exposed that mistake.
A guessed backup test filename was corrected. Fixture setup initially used the
wrong Store registration method. The empty-bound-value regression exposed a
resolver diagnostic omission, corrected before rerunning. Browser schema-3 checks
needed a second settled effect cycle after asynchronous discovery.
The first packaging attempt lacked setuptools in the development venv; a
disposable build path reused the already bundled pure-Python setuptools/wheel
tools. No existing environment was modified. Pip reported its disabled cache and
correctly left the older package outside the disposable venv untouched.

## Owner verification

1. Use a disposable copy of the accepted `examples/decay` at standards commit
   `198f234`; register `simulate.py`, choose your Python interpreter, and use
   `-k 1e-1 -n 0010 --dt=0.25 --label ''`. Confirm the one capture summary is
   `<registered-root>/outputs` and exact argv is unchanged.
2. Run twice, reopening/revalidating between runs. Confirm distinct script-owned
   timestamped children, copied log/JSON/CSV/provenance, unchanged older bytes and
   identical source snapshots. No extra launcher-created child should appear.
3. Add `--output-parent custom-results`, then another internal parent. Confirm
   discovery changes, previous output trees stay out of new source snapshots,
   and real source/input edits still appear. If Git participation is enabled,
   review changed preservation scope before expecting automatic archival.
4. Prepare a directory on the intended mounted external volume and pass its
   absolute path through the bound option. Check actual mount identity yourself,
   then validate/run. Confirm local copied evidence and truthful unavailable Git
   archival. A nonexistent external parent must fail without creating it.
5. Try a repeated bound option, unknown token, empty value, conflicting manual
   parent and stale source hash. Verify actionable refusal/review and unchanged
   argv. Correct metadata deliberately, never regenerate historical snapshots.
6. Keep an existing schema-2 fixture and library backup: verify its saved capture
   path stays manual, run history remains identical, and backup restoration keeps
   copied bytes. Independently test preferred themes/narrow layout and your actual
   scientific environment. No cross-platform or full SWSS certification is claimed.
