# SWSS simulation version authority

Validated 2026-10-21 on Linux/CPython 3.14.8 and Node.js 24.19.0.
Accepted base: `8e9cea7230ffc9199519a6ffac5218161e4fbd00` (0.1.0.41).
Proposed application build: **0.1.0.42**; no storage migration.

## Behavior and contract

Valid, non-stale SWSS metadata supplies the run's version from
`[swss].simulation_version`, separately from schema version and source identity.
Discovery no longer reads or compares the application-local Python version tag.
The optional reader argument and `comparable_version` provenance key remain for
caller/record compatibility; new evidence sets that key to null.

The [accepted SWSS v2.0 §4.4](https://github.com/mongstad/Simulation-Standards/blob/285ab0d6c06cc3b88e421a2c00577e72c650c750/standards/SWSS/v2.0.md#44-consistency-and-provenance)
requires rejection of a mismatch against a separately available authoritative
simulation version. A SimShelf-specific constant is not an independent SWSS
version authority. No new portable version check, namespace or rule is invented.
Source hashes, entrypoint association and declaration fingerprints still apply;
valid metadata without hashes remains binding unverified and usable.

| Companion state | New run version |
| --- | --- |
| Valid, associated, no stale binding | Exact `swss.simulation_version` declaration; not a verification of scientific behavior |
| Invalid, unsupported, entrypoint mismatch or stale binding | `unversioned`, with existing metadata diagnostics/provenance and explicit manual fallback; never the Python tag |
| Absent | Existing captured `SIMSHELF_VERSION` literal, or `unversioned` if absent |

Recording compares reviewed companion bytes to the source snapshot before using
its version, and rejects a bound-source digest change observed in that snapshot.
A companion seen before review or in the snapshot cannot disappear into legacy
fallback. These checks do not isolate a running process from later edits or
prove capture of every external dependency.

Previous runs, source blobs and version groups are not relabeled. A newly declared
version starts its own existing comparison group; legacy history remains in its
original group. Old typed previews containing tag-comparison evidence can require
a rescan because their fingerprint changes; manual bypass retains previous
provenance. Application and simulation versions remain separate.

## Validation

Commands use the existing development interpreter, forced source imports and
disposable directories outside the checkout:

```bash
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider \
  tests/test_swss_versions.py tests/test_swss.py tests/test_recording.py \
  tests/test_version_edge_cases.py tests/test_capture_backup.py \
  tests/test_application_version.py --basetemp=/tmp/simshelf-version-check
python scripts/application_version.py --base-ref origin/main
```

- Initial focused run: 76 passed. Expanded source run: **96 passed** before adding
  the final legacy-to-SWSS adoption-history case. Installed-wheel run of the final
  new suite: **14 passed**, including that case. No backend failures; the existing
  Starlette/httpx deprecation warning remains.
- New tests cover absent/different/nonliteral legacy tags with SWSS, unbound and
  hash-bound declarations, legacy/no-tag behavior without a companion, malformed/
  schema-3/stale fallback, retained companion bytes, declaration changes, capture
  races, genuine portal launch with exact argv, version-list API results and
  unchanged earlier records after adopting or changing SWSS versions.
- TypeScript typecheck and frontend build passed; distributed JavaScript rebuilt.
  Thirty bundled argument/parameter/default tests passed. Add-simulation and
  Versions guidance now explains both version sources without a universal tag
  recommendation. No layout or editor behavior changed.
- First `build --no-isolation` failed because the existing development interpreter
  lacks setuptools. Isolated build succeeded, producing sdist and a wheel from
  that sdist. Build dependencies were installed only in disposable environments.
- Installed wheel imports were verified from the external install target. CLI,
  Python, workspace API and OpenAPI report 0.1.0.42; HTML and updated bundled UI
  serve successfully with Git/Node absent from PATH. Existing dependency packages
  were reused; this was not a fresh dependency-resolution or offline-install test.
- Version gate passed against the accepted base. No license notice changes,
  scientific source changes, external repository changes or user data operations.

## Limits and owner checks

No new browser visual/keyboard session, non-Linux testing or scientific
certification. Snapshot races after checks remain possible. The nested portable
row-value validation gap documented in [issue #114](issue-114-swss-audit.md) is
unchanged; this version correction does not claim to fix all metadata validation.
Historical reports retain their original evidence and review-time wording.

In a disposable library:

1. Register a reference-style script with schema 2 and `simulation_version="0.1.3"`,
   without a Python version tag. Check discovery binding status, launch it and
   inspect version **0.1.3** in the run and Versions list.
2. Add a differing optional legacy tag. Refresh any supplied source hash; confirm
   the tag itself creates no stale-binding reason and the version stays **0.1.3**.
3. Make the companion malformed, unsupported or hash-stale. Check diagnostics,
   select manual argv and confirm the run is **unversioned**, with exact arguments
   and failure/output status governed by the actual script.
4. Without a companion, check legacy tag and unversioned behavior. Add a valid
   companion and record again; verify earlier versions and source evidence remain.
5. Inspect Add a simulation and Versions guidance at desktop/narrow widths, and
   rescan an older saved typed preview if requested. Confirm the application label
   is **0.1.0.42**, distinct from the simulation version.
