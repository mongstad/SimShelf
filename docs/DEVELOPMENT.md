# Development and packaging

[Documentation](README.md) · [Getting started](GETTING_STARTED.md) · [Project overview](../README.md)

Commands using `./start.sh` assume your terminal is in the SimShelf source checkout.

## Share the source project

Recorded runs and simulation registrations are local data. The source project is
provided without a workspace database, captured source, retained results, or
browser screenshots. Launching the app creates a fresh empty workspace; the
example generator is optional.

The Git ignore rules exclude standard workspaces, generated outputs, local
environments, caches, database files, logs, and machine-local settings. Keep
custom workspace folders and backups outside the source checkout. Review any
screenshots before adding them to documentation: they can display personal paths
and run details. Source distributions exclude the generated capture folders.

## Develop and verify

```bash
./start.sh --setup
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$PWD/src"
DEV_PYTHON="$(dirname "$PWD")/environments/$(basename "$PWD")/bin/python"
pnpm install --frozen-lockfile
pnpm run typecheck
pnpm run build
"$DEV_PYTHON" -B -m pytest -q -p no:cacheprovider --basetemp="$(mktemp -d /tmp/simshelf-tests-XXXXXX)/pytest"
# Build in a disposable source copy, since setuptools writes build metadata.
BUILD_ROOT="$(mktemp -d /tmp/simshelf-build-XXXXXX)"
git archive HEAD | tar -x -C "$BUILD_ROOT"
"$DEV_PYTHON" -B -m build "$BUILD_ROOT" --outdir "$BUILD_ROOT/dist"
```

Adjust `DEV_PYTHON` if using `SIMSHELF_DEV_ROOT` or `SIMSHELF_DEV_ENV`. The launcher
loads current checkout source without an editable installation; setup builds its
installed package from a temporary copy, keeping packaging metadata external.
The archive build above tests committed code; use an external copy including your
changes to validate uncommitted work. Conventional `pip install -e` remains
supported when explicitly requested, but setuptools may write ignored `.egg-info`
metadata into that source tree. Use an external source copy if it must stay pristine.
Do not install into an unrelated simulation interpreter without choosing to do so.
`requirements-dev.lock` is the historical tested dependency set; setup resolves the
ranges in `pyproject.toml`. Frontend development installs `node_modules` locally;
this is separate from Python launch/record/test defaults.

React/TypeScript source lives in `frontend/`. The build emits bundled assets into
`src/simshelf/static/`, which are intentionally tracked and packaged with Python.
The build also regenerates complete bundled dependency licenses; keep those and
`app.js.LEGAL.txt` with the assets. See [third-party notices](../THIRD_PARTY_NOTICES.md).
Runtime UI resources are served locally; no CDN connection is required. Python
dependencies are declared
in `pyproject.toml`; `requirements-dev.lock` records the tested development
environment. `pnpm-lock.yaml` records the frontend dependencies.

This is a single-user local application, bound to loopback. Browser writes use a
same-origin token, and registered paths/source manifests constrain file access.
Remote hosting, user accounts, Git synchronization, environment provisioning, full
time-series plots, and 3D viewing remain outside the current feature set.

See [architecture](ARCHITECTURE.md) for storage and versioning contracts and
[validation](VALIDATION.md) for the checks performed on this build.

See [the issue #1 source audit](validation/issue-1-source-audit.md) for
repository cleanup, history exposure, and package validation evidence.

See [issue #2 validation](validation/issue-2-external-development.md) for
external launcher paths and legacy-workspace recovery checks.

See [issue #5 validation](validation/issue-5-portal-execution.md) for portal
execution, cancellation, recovery and browser checks.

## SimShelf application version

The upper-right **Local · version** label and `simshelf --version` identify the
application, independently of your simulation's `SIMSHELF_VERSION` tag. The label
uses the running server's version; restart and reload after updating. Application
updates do not renumber existing simulations or rewrite previous runs.

See [application versioning](APPLICATION_VERSIONING.md) for the single version
source, transition from the historical `0.1.0` baseline, deterministic PR build
increments and separately authorized immutable releases.
