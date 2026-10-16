# Discover simulation parameters

Open **Start simulation → Discovered parameters**. SimShelf reads declarations
without importing the simulation, probing its interpreter, running `--help`, or
installing dependencies. Missing GPU libraries do not prevent static discovery.

Each row shows aliases, help, type/choices, required state, source location and a
known declared default or **unknown**. These are declarations, not resolved
scientific values: scripts may compute different defaults during execution.
Nothing is selected automatically and placeholders never become arguments.

1. Select an optional override and type its value, or select a supported boolean
   flag. Required options also need deliberate entry; required positionals use
   the manual editor.
2. Choose **Add selected overrides to arguments**. Review **Exact argv**. Values
   are emitted as `--option=value` (including empty strings, negative values and
   spaces); no shell quoting/expansion occurs. Boolean flags contribute one token.
3. Use **Runtime arguments** to edit/remove added options, pass repeatable options
   or positionals, or paste a complete command's arguments. Existing aliases and
   values are never replaced by discovery. Options already present must be edited
   there; discovery conservatively detects short attached aliases as well.
4. Add or clear pending overrides before saving/validating/launching. Save settings
   stores only the existing exact argv representation, not a second parameter model.

**Rescan parameters** rereads declarations without altering argv or pending text.
A content change produces a review warning; disappeared pending options prevent
application until cleared. Removed/unknown saved options remain in the manual
editor: review them against the current declarations. A new dialog has no previous
scan baseline, so it cannot infer when a saved argument was last valid. Discovery
never rewrites historical commands or resolves every possible parser conflict.

If argv contains the `--` positional delimiter, use the manual editor; automatic
append cannot safely choose an insertion point. Repeated flags, positionals,
custom actions/types, multi-value arguments, groups/subparsers, multiple parser
instances, parser mutations and dynamic definitions use honest manual fallback.
Even ordinary static definitions are suggestions: conditional code, imports,
shadowed names and runtime changes can alter their meaning. Confirm the preview
and script behavior. No optional executable help fallback is implemented.

## Supported static argparse subset

The registered entry file may import `argparse` (with an alias) or import
`ArgumentParser` directly. One assignment to an ArgumentParser instance and calls
to that variable's `add_argument` are inspected, including definitions inside a
function. Literal aliases, help/default/choices/required, `str`/`int`/`float`, and
`store`/`store_true`/`store_false` are supported. Unsupported or dynamic arguments
are marked for manual use; dynamic names cannot generate a row. Other imported
files are not traversed. No default is inferred from an execution or log.

## Optional explicit project schema

For custom/dynamic parsers, deliberately create **simshelf-arguments.json** in the
registered source root. SimShelf never creates or edits this file for you. It takes
precedence over AST discovery; it is an advisory declaration for this registered
project, not proof that the current script accepts the options. Invalid schema
produces a warning rather than silently falling back to different declarations.

```json
{
  "schema_version": 1,
  "parameters": [
    {"flags": ["--steps", "-n"], "type": "int", "default": 100, "help": "Integration steps"},
    {"flags": ["--method"], "choices": ["euler", "rk4"], "default": "rk4"},
    {"flags": ["--quiet"], "action": "store_true", "default": false},
    {"flags": ["input"], "required": true, "help": "Set this positional path manually"}
  ]
}
```

`flags` is required; type defaults to `str`, action to `store`, required to false.
Omitting a schema default means unknown, not `null`. Literal explicit `null` is
shown as such. Optional help, choices, dest and metavar are accepted; unsupported
keys/actions/types/nargs disable automatic controls. Conflicting aliases disable
all conflicting rows. Keep schema declarations synchronized yourself; when a
schema exists, the fingerprint tracks that file rather than the script.

Discovery reads at most 256 KB, 20,000 AST nodes and 128 parameter declarations;
choices are capped at 100 and aliases at eight per row. Symbolic links and paths
outside the project are rejected. Errors leave existing arguments intact.
No network, Git, subprocess, source/config mutation or new database schema is
involved. Existing capture, scientific versions and CLI/editor recording remain
independent. Runtime is currently Linux-validated.
