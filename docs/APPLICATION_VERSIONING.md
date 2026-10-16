# Application versioning

`src/simshelf/_version.py` is the sole authoritative SimShelf application version.
Setuptools reads its literal for wheel/sdist metadata. Python, `simshelf --version`
and the server API use it; the existing upper-right **Local · version** label
reads the API value. Until connection succeeds it says **Version unavailable**,
never a hardcoded fallback. No Git, Node, network or installed-metadata lookup is
needed to obtain the runtime version. Restart the server and reload after updating.

This is independent of scientific `SIMSHELF_VERSION` tags, source snapshots, Git
revisions and the workspace schema. Updating the application does not rewrite
previous records or assign new scientific model versions.

## Numbering and transition

Use the PEP 440 numeric release form **MAJOR.MINOR.PATCH.BUILD**, with a positive
BUILD. Existing `0.1.0` remains the historical baseline; this issue introduces
`0.1.0.1`. No earlier commits, artifacts or tags are assigned invented build
numbers. Python packaging orders `0.1.0 < 0.1.0.1 < 0.1.0.2`; normal range
constraints still apply. An exact `==0.1.0` pin deliberately does not select the
new build; update such a pin explicitly. No database migration is involved.

- BUILD advances once per accepted implementation PR, derived from current
  accepted main. Review fixes in that PR retain its proposed number. It is never
  incremented by startup, simulation runs, installation or repeated packaging.
- PATCH advances for an owner-designated maintenance release line; MINOR for an
  owner-designated feature release line or breaking pre-1.0 application contract.
  Both reset lower components and start BUILD at 1.
- MAJOR advances for an owner-declared stable 1.0 contract, and later incompatible
  application contracts. It also resets lower components and starts BUILD at 1.
- Pre-1.0 is evolving software, not a promise of stable public APIs. Preserve
  scientific data compatibility; incompatible storage changes require separate
  migration design and authorization regardless of version number.

## Implementation PR workflow

After verifying a clean dedicated issue branch and fetching accepted main:

```sh
python scripts/application_version.py --base-ref origin/main --write
python scripts/application_version.py --base-ref origin/main
```

The explicit write is idempotent relative to that accepted base. Check mode writes
nothing and rejects duplicate/skipped build numbers. For an owner-approved release
line change add `--change patch`, `minor` or `major` to both commands. The tool reads
local Git history only: it never fetches, tags, commits, pushes or publishes.
It accepts the historical three-part baseline and reads versions without importing
old application code. Keep the base commit, chosen change and proposed version in
the PR. Before merge, fetch again and repeat the check against current main; stale
parallel proposals cannot both pass after one is accepted. Resolve branch/version
conflicts with the owner rather than replacing an existing branch. The check is a
required review gate, not an installed branch-protection setting.

Run version and affected subsystem tests. Build a wheel and sdist from a disposable
source copy outside the checkout (`python -m build --outdir /external/dist`), build
a wheel from the extracted sdist, and verify all metadata versions agree. Install
the wheel into an external disposable environment; with Git and Node absent from
PATH check Python `__version__`, CLI, `/api/workspace`, OpenAPI version and the
existing upper-right label. Test startup without network access after dependencies
are installed. Rebuild bundled frontend assets only if frontend source changed;
retain third-party notices. Never build into a user workspace or source project.

## Separately authorized releases

Merging a PR does not authorize a tag, GitHub release, package publication or
visibility change. Only on a separate explicit owner instruction, verify the
accepted main commit and version, build/test that exact source, review artifact
contents/checksums, and check that tag `v<application-version>` and corresponding
release do not already exist. Use that tag for the verified commit and publish
only the approved artifacts/destination. Tags, published artifacts and historical
validation reports are immutable: never replace/repoint them to correct a build.
Use a new version and separate authorization for a correction. Include the exact
commit, validation and limitations in release notes; do not claim reproducibility
of users' scientific runs from the application version alone.
