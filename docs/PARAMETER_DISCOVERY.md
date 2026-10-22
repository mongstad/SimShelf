# Simulation parameters and SWSS 2

Open **New run… → Simulation parameters**. SimShelf reads the single root
`swss.toml` using the accepted [SWSS v2.0 schema 2](https://github.com/mongstad/Simulation-Standards/blob/8157653c58eb055102e587734e3898a43653eba0/standards/SWSS/v2.0.md).
The selected entry must match. No imports, `--help`, subprocesses, network,
dependency installation or scientific source writes occur during discovery.
A large Python AST does not affect TOML discovery.

Value parameters, boolean flags and manual arguments share the existing editor.
Declared defaults are hints only, shown separately from authored help and choices.
A known default is shown as `Default: …` only when an explicitly supplied draft value
differs. Unset inputs hide that footer; their placeholder can still show the hint.
Equivalent numeric spellings compare without rewriting argv; strings compare exactly, including explicit empty strings. Disabled drafts
use the same comparison but remain omitted. Unknown defaults have no footer label
and do not make an optional parameter required. An empty input does not prove
that the simulation has no internal default. Disabled optional arguments are omitted, and the simulation determines
their behavior, including any context-dependent values. SimShelf does not infer
those values. Enabling a flag emits its option, not its resulting
boolean value. Aliases retain their spelling. New long options use `--name=value`;
new short options use two tokens, immediately before `--` or at the end. Review
**Exact argv** before launch. Choice selections preview their generated token text.

Opening, rescanning and saving preserve ordered argv, numeric spelling, aliases,
equals forms, repeated options, delimiters and explicit empty strings. A blank
manual value omits a value; **Pass empty string** explicitly supplies one.
Unknown, positional, repeated and unsupported rows remain manual. Typed checks
validate supported integer/finite-float/string choices and required options.
**Use manual argv** is retained with saved settings and explicitly bypasses metadata validation; the script may still
reject those arguments, and independent runner safety checks remain active.

A valid partial or empty declaration is authoritative: no AST/JSON merging.
Missing/invalid metadata displays a diagnostic and requires an explicit manual choice in the portal. Registration can retain an invalid companion without importing its configuration; saved/default capture settings are shown for review. Optional
static discovery remains an explicit API choice (`parameters?source=static`),
limited to 256 KiB, 20,000 AST nodes and 128 rows; it is not SWSS discovery.
The portal uses SWSS/manual discovery only. Superseded `simshelf.toml`,
`simshelf-arguments.json` and `swss-parameters.toml` are rejected for new runs;
author-reviewed replacement/removal is required. There is no converter or fallback
reader. Existing records and their old configuration bytes remain readable.

## Companion example

```toml
[swss]
schema_version = 2
entrypoint = "simulate.py"
simulation_version = "0.1.1"

[[swss.parameters]]
id = "steps"
kind = "option"
options = ["--steps", "-n"]
required = false
type = "integer"
action = "store"
help = "Integration steps"
default = 100
```

Parameters may be omitted or `parameters = []` placed inside `[swss]`.
Use the standard for boolean flags, choices and optional SHA-256 source bindings;
the scalar-field example shows a complete mixed-use companion.

Without supplied hashes the UI says **binding unverified**. Listed matching
hashes verify only those bytes, not runtime behavior or unlisted dependencies.
The SWSS declaration's `simulation_version` supplies the run version. A separate
`SIMSHELF_VERSION` Python tag is neither required nor compared: it is a legacy
convention only for scripts without a companion. Changed source hashes disable
typed use. Invalid, unsupported or stale companions yield `unversioned` on a
manual run, with diagnostics retained; they never fall back to the legacy tag.
Rescan changes require
explicit review. Validation, the supervisor and recording recheck typed metadata;
a changed companion or binding refuses stale launch. Changes after checks remain
possible: snapshots do not isolate the running script.

Runs retain the exact companion text/hash, schema/scientific versions, selected
entry/source, binding reasons/hashes, review decision and final argv in
`parameter_metadata`, separately from resolved scientific parameters. Source
capture must include those same companion bytes. Saved typed settings retain
server-read provenance for a later explicit manual bypass. Historical runs are
never rewritten. CLI/editor invocations are manual unless configured through the
portal; they still retain available metadata and enforce legacy-file rejection.

## Bounds and filesystem safety

The reader applies the standard's 262,144-byte document, depth-8, 4,096-entry,
128-row, 8-alias, 100-choice, 32-source and string/path/alias limits, including
ignored extensions. Syntax nesting is checked before TOML parsing. Source hashes
stream with 16 MiB/file and 64 MiB/manifest bounds. Nonfinite values, invalid UTF-8,
unsafe paths, symlink components, special files and open-time identity changes
are refused. Safe descriptor-relative access is currently Linux-tested; platforms
without it decline metadata use rather than weaken containment. Discovery does
not certify complete schema coverage or scientific baseline conformance.

## Optional SimShelf extension

Only `[extensions.simshelf]` schema version **1** is interpreted by SimShelf.
It may contain `name`, `description`, `[extensions.simshelf.source]` with
`include`/`exclude`, and `[extensions.simshelf.capture]` with `output_dir`,
`max_file_mb`, `max_run_mb` and `[[extensions.simshelf.capture.rules]]` containing
`pattern` and `action` (`copy`, `reference`, `ignore`). Unknown/conflicting local
fields or an unsupported local extension version decline configuration import;
other extensions have no semantic effect on portable discovery.

The extension initializes registration settings; later portal settings are the
explicit saved configuration for future runs. Editing the companion does not
silently overwrite saved capture settings. No extension selects an interpreter,
working directory, portable identity or argv. Rules are first-match; file/run
copy budgets and source exclusions retain their existing behavior. `.log` files
are copied by default. For a SWSS-described launch, absence of an
automatically copied log is reported as incomplete capture independently of exit
status (including ignored, referenced or oversized logs). A log outside the
watched root or an unchanged historical log cannot satisfy that check. Authors
remain responsible for timestamped names, log content and diagnostics.

New run shows **SWSS schema 2 · metadata valid** separately from **Source binding**
(listed bytes verified, unverified, or stale/manual-only). These describe bounded
checks at scan time, not baseline conformance. Valid associated metadata recommends
**Fixed output parent — simulation creates its unique run directory** and disables
launcher-coordinated allocation. No coordinated-root agreement is inferred from
schema or source hashes. Existing incompatible settings require explicit fixed
selection and validation/save; history is untouched. Invalid/unsupported/stale or
unassociated metadata reports uncertainty, disables launcher allocation, and keeps
explicit manual fixed-parent execution available. Scripts without a companion
retain both policies. See [output policy](RUNNING.md#unique-output-folders-for-cooperating-scripts).

This is a portable-editor/configuration integration, not certification of a
simulation's SWSS baseline, scientific export, numerical equivalence, checkpoint
recovery or independent backup restoration. Existing progress/metric adapters and
their limits are unchanged.

## Finding controls in long parameter lists

In **New run → Simulation parameters**, search by option spelling, alias, help,
value type, or `required` / `optional`. Search is case-insensitive; multiple words
must all match the same control. The count reports visible supported controls.
**Clear search** restores the list and returns keyboard focus to search.

Each control groups its enable checkbox, value or flag, help and default hints
within one bordered row. Required declarations appear first when present, followed
by value parameters and boolean flags. Defaults remain hints, never inserted.
Search and grouping change only presentation: enabled arguments, disabled drafts,
token order and spelling remain intact. Manual/undiscovered arguments always stay
visible below the declared controls, including repeated or unsupported forms.
Search resets when the dialog closes; saved execution settings do not store it.
