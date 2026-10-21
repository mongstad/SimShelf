# SimShelf documentation

[Project overview](../README.md) · [Start here](GETTING_STARTED.md)

## User guides

| Task | Guide |
| --- | --- |
| Record a disposable first run; resolve interpreter/dependency problems | [Getting started](GETTING_STARTED.md) |
| Open the app, choose a library or appearance, try the demo | [Setup and workspaces](SETUP.md) |
| Launch, supply arguments, stop, or record from a terminal/editor | [Running simulations](RUNNING.md) |
| Understand versions, capture, comparison, screenshots, backups and restore | [Preserving data](DATA.md) |
| Expose parameters and understand discovery limits | [Simulation parameters](PARAMETER_DISCOVERY.md) |
| Enable optional progress and understand unknown reports | [Progress reporting](PROGRESS.md) |
| Connect an existing source repository without changing it | [Source Git history](GIT_PROVENANCE.md) |
| Understand retained legacy file-selection preferences | [Legacy Git file selection](GIT_FILE_SELECTION.md) |
| Review preservation settings, later annotations and historical files | [Shared Git archive](GIT_ARCHIVE.md) |
| Deliberately delete records or manually attached images | [Simulation removal](SIMULATION_REMOVAL.md), [Run removal](RUN_REMOVAL.md), [Screenshot deletion](SCREENSHOT_DELETION.md) |

## Technical references

- [Architecture](ARCHITECTURE.md): scientific provenance, storage and lifecycle contracts.
- [Development and packaging](DEVELOPMENT.md): external build/test paths and bundled licenses.
- [Application versioning](APPLICATION_VERSIONING.md): build policy, distinct from scientific versions.
- [Validation evidence](VALIDATION.md): dated checks and their limitations; historical reports
  retain their original review-time wording and are not current installation instructions.
- Design boundaries: [progress storage](PROGRESS_DESIGN.md),
  [Git archive](GIT_ARCHIVE_DESIGN.md), [master archive Stage A](MASTER_ARCHIVE_UX_DESIGN.md),
  [one-library preservation implementation](LIBRARY_PRESERVATION_DESIGN.md).
  Design documents can describe deferred work; use the user guides for available features.

For command syntax run `./start.sh --cli --help` from the checkout, then
`./start.sh --cli record --help` (or another subcommand). The [terminal/editor
examples](RUNNING.md#record-your-first-simulation) explain CLI and Python API usage.
The running local server also exposes API documentation at
`http://127.0.0.1:8740/docs` (use your selected port).

The [documentation walkthrough validation](validation/issue-39-documentation.md)
records the first-run and packaging checks for this documentation revision.
