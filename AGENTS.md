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
- Treat incompatible workspace/database schema changes as **separately owner-authorized**. Approval of a feature does not automatically authorize a storage migration. Never upgrade a user's library silently on startup, viewing, or an unrelated operation; for an explicitly approved action-triggered migration, disclose the trigger, older-version incompatibility, and recovery requirements beforehand.
- Before implementing a migration, define backup and restore verification, interruption/failure behavior, concurrency safeguards, old-version compatibility, and focused tests. Preserve unrelated scientific runs, snapshots, annotations, records and provenance. An explicitly authorized deletion may use narrowly scoped, auditable tombstones; do not rewrite surviving scientific history. Do not confuse managed copies with external reference-only files.
- Workspace migration authorization never permits Git history rewriting, historical report alteration, or deletion of original source/output folders. Follow `docs/APPLICATION_VERSIONING.md` for incompatible storage changes.
- Keep changes scoped; avoid unrelated UI redesigns, broad refactoring and documentation churn.

## SWSS contracts
- For portable simulation-facing contracts, consult the accepted SWSS specification
  in [Simulation-Standards](https://github.com/mongstad/Simulation-Standards).
  SimShelf consumes [SWSS v3.0 schema 3](https://github.com/mongstad/Simulation-Standards/blob/198f234693535c1f7bc7e78cd8e599a510c2d494/standards/SWSS/v3.0.md)
  and compatible [SWSS v2.0 schema 2](https://github.com/mongstad/Simulation-Standards/blob/8157653c58eb055102e587734e3898a43653eba0/standards/SWSS/v2.0.md)
  through one `swss.toml`; see `docs/PARAMETER_DISCOVERY.md` for tested boundaries
  and the local extension. Do not imply scientific baseline certification.
- Preserve exact argv and historical config/source bytes. Never convert scientific
  files automatically or reintroduce obsolete companion-file readers. Portable
  fields cannot be overridden by application extensions. Pure internal UI details
  remain local; changes to portable contracts need separately authorized standards
  work, not implicit semantics in a SimShelf extension.

### Missing or conflicting portable contracts
- Before changing a simulation-facing workflow contract, check the **accepted normative** [SWSS specification](https://github.com/mongstad/Simulation-Standards/blob/main/standards/SWSS/v3.0.md) and its applicable capability boundaries. A proposal, open issue or unmerged PR is **not** an accepted contract; check the repository's current authoritative revision before treating it as binding.
- If an authorized task requires a **new, changed or incompatible portable contract** (such as shared `swss.toml` semantics, portable arguments, lifecycle, capture or provenance rules) that SWSS does not define or support, **do not invent a competing SimShelf-specific standard** or silently extend `[swss]` or an application extension to replace normative rules. Identify the gap, the affected SimShelf work, the intended cross-tool behavior and relevant compatibility, safety, provenance and conformance consequences.
- **Propose** a dedicated issue in [Simulation-Standards](https://github.com/mongstad/Simulation-Standards) for owner consideration, cross-linking the dependent SimShelf issue/PR. Do **not** automatically create the issue, amend SWSS, or edit another repository without explicit owner authorization. Surface the proposal to the owner and request direction.
- **Pause only the SWSS-dependent implementation** until the owner authorizes a standards change and the needed contract is accepted. Independent, already-authorized work may continue without expanding scope. After acceptance, implement the contract in SimShelf only through the existing owner-authorized issue/PR workflow. **SWSS specifies; SimShelf conforms.**
- Ordinary SimShelf-only UI layout, visual grouping, local performance improvements, and implementation details that do **not** change portable meaning remain within SimShelf; they need no standards proposal. Application-specific extension fields may remain local only if they do not redefine SWSS portable fields, argv or guarantees.

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
