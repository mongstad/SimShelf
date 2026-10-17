# Issue #47 implementation design

Owner approved the revised boundary on 2026-10-17: initial per-run commits, optional
post-run additions, capture-relative future rules, managed-copy-only automatic
outputs and cumulative 1,000/25 MiB/100 MiB limits. See [user guide](GIT_ARCHIVE.md).

- Separate dedicated bare repository, identity marker, exact allowlisted config,
  rejected links/alternates/shallow layouts, local Git argv with isolated config,
  disabled hooks/transports/signing/replacement/lazy fetching. Initialization is
  explicit and restricted to an empty directory. Source Git remains read-only.
- `archive_v1:` metadata holds location-bound connection and per-simulation
  consent, run-start capture plan, pending operation, immutable event, and separate
  error. Existing schema and journal event vocabulary remain unchanged. SQLite
  backup naturally includes these associations; payload references remain ordinary
  snapshots/artifacts covered by existing backup/removal behavior.
- Future rules are a bounded grammar with filename-only `*`. Existing #44
  preferences and location binding are reused. Copy overrides are recorded at run
  start and supplied only to that run's capture invocation. No global capture
  rewrite. Bounded before/after hashes plus verified artifact hashes gate output
  attribution; external paths are excluded. Normal capture may conservatively
  miss same-size/same-mtime mutations; they never get silently archived.
- Finalization prepares a durable manifest of managed-byte references and omissions
  after genuine scientific finalization. Generic dead-owner reconciliation does
  not collect live files or issue Git writes. Explicit retry resumes prepared work;
  a pre-manifest crash is visibly incomplete and requires manual attachment.
- Lock order is workspace managed-data lock then nonblocking archive flock. A
  pinned directory FD anchors Git invocations. Temporary isolated index starts
  from archive main. Raw `hash-object`, explicit `update-index --cacheinfo`,
  `write-tree` and `commit-tree` bypass worktree/filter/hook execution. A Git ref
  transaction compare-and-swaps main and creates a unique operation ref together.
  Manifest and every blob are verified before atomic event insert/pending removal.
- Paths are `simulations/<simulation-id>/runs/<run-id>/<operation-id>/<entry>/<name>`.
  The operation manifest is also committed. Commit SHA lives in the independent
  immutable event (not self-referentially inside the committed manifest). Additional
  commits never modify previous paths. Aggregate inventory is the ordered union
  of verified event entries, retaining all filename revisions. Downloads resolve
  event ownership, archive identity, commit/path, bounded bytes and hash.
- Requests have stable operation IDs. Same request retry returns the same event;
  another request cannot steal that ID or bypass a pending operation. Missing bytes,
  space, Git, conflicts or corruption leave scientific records valid. Publication
  failures may leave unreachable objects or a published-but-unassociated commit;
  recovery verifies exact intent instead of creating an extra commit.

Dependencies #43/#44 are accepted. #45 source-repository initialization and #7
scientific version semantics are independent and unimplemented here. Remote
operations, arbitrary existing repositories, external automatic capture, archival
history deletion and incompatible migrations are outside this approved stage.
