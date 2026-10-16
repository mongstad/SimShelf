# SimShelf agent instructions

SimShelf is an independent, local-first Python simulation library and run journal. Its purpose is to help users preserve, find and compare simulations, versions, parameters, measurements, logs, screenshots and output references without forcing changes to their scientific scripts.

## Before work
- Read `README.md`, `docs/ARCHITECTURE.md`, `docs/VALIDATION.md`, and the entire assigned issue before editing. Inspect the current code and Git state; verify assumptions rather than inferring behavior from mockups.
- GitHub issues and the SimShelf Project board organize work. Implement only an owner-authorized issue (normally in Ready), one issue at a time. Ask or stop when requirements, dependencies or state are ambiguous.
- Use an assigned issue branch if present. Otherwise create a dedicated branch from current accepted `main` (prefer `issue-<number>-<slug>`). If an existing branch is stale or unsuitable, report it rather than silently replacing or rewriting it. Never commit to `main`.
- Check for existing issue PRs and avoid duplicate branches/PRs. Do not force-push without explicit owner authorization.

## Development boundaries
- Keep the application source checkout distinct from Python environments, SimShelf user workspaces, databases, source snapshots, simulation records, logs, checkpoints, large outputs, temporary evidence and test artifacts. The parent development directory may hold local-only files. Never delete valuable local/user data during repository cleanup.
- Default developer launch and test paths should remain outside the Git checkout once the migration is implemented. Until then, treat checkout-local `.simshelf/` as user data to preserve. Respect explicit workspace overrides and document path resolution.
- Never commit secrets, `.env` credentials, personal research data, virtual environments, interpreter caches or generated packaging metadata. Review `git status`, `git diff --cached`, file sizes and third-party notices before each commit. Note that `.gitignore` does not untrack already committed files.
- Built frontend assets under `src/simshelf/static/` are intentionally distributed so runtime users do not need Node.js; do not discard them as generic build litter. Rebuild them when frontend sources change and preserve their license notices.
- Keep SimShelf independent of Wavez and MLflow. External integrations must remain optional. Follow the existing package and dependency definitions, and do not vendor third-party tools or datasets without license review.
- Prioritize faithful scientific provenance: distinguish user-declared model version, exact source snapshot, Git revision, run parameters, measured values, and user annotations. Do not claim exact reproducibility when inputs, environments or source mutations make it uncertain.
- Preserve immutable completed execution records, annotation history, correct failure reporting, and non-destructive copy/reference/ignore behavior. Large external scientific results are references, not backups.
- Do not silently install dependencies, modify another project's interpreter, execute arbitrary user code, overwrite simulation outputs or migrate/delete workspaces. Require appropriate explicit user action and handle interruption safely.
- Keep changes scoped; avoid unrelated UI redesigns, broad refactoring and documentation churn.

## Validation and handoff
- Use focused, risk-based tests for the affected subsystem and direct integration boundaries. For storage, capture, migration, backup/restore, process execution, security, or packaging changes, expand coverage to relevant failure paths and fresh-install behavior. Do not run unrelated exhaustive suites just because they exist.
- Document exact checks, failures, skipped environments and limitations honestly. Validate that release/runtime assets still ship where applicable.
- Push only to the issue branch and open/update one PR into `main`, referencing the issue (use `Closes #N` for an implementation PR). Summarize changes, changed files, validation, risks and concrete owner-verification steps.
- Stop for owner review. Do not merge, enable auto-merge, close issues manually, move Project items to Done, tag releases, publish packages, change repository visibility/settings or start another issue without specific authorization.
- Owner-approved merges can be followed by safe local branch housekeeping; preserve historical reports and original review-time status language.

## Application version changes
- Follow `docs/APPLICATION_VERSIONING.md`. Keep the authoritative version only in
  `src/simshelf/_version.py`; scientific `SIMSHELF_VERSION` tags are independent.
- Each implementation PR proposes the next build from freshly verified accepted
  main. Run `python scripts/application_version.py --base-ref origin/main` before
  handoff; repeat after main changes. Review fixes do not increment again.
- Version-line changes and any tags/releases/publication require owner authority;
  normal issue implementation does not authorize publication. Preserve historical
  version evidence and build/test in external disposable directories.
