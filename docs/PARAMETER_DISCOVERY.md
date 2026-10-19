# Simulation parameters

Open **New run… → Simulation parameters**. One editor combines discovered
options with saved and manual arguments. SimShelf reads declarations without
importing the simulation, probing its interpreter, running `--help`, or installing
dependencies. Missing GPU libraries do not prevent static discovery.

Supported parameters have their name on the left and value on the right, with
concise help, required/optional status, type/choices and a declared default hint.
The hint is not the resolved scientific value. No default is inserted into argv.

- Enable an optional parameter's checkbox, then enter the value you want. Disable
  it to omit all its tokens; its edited value stays in this open dialog. Disabled
  values are not saved as execution arguments and do not survive closing/reopening.
- Required supported options are identified and must be supplied. Missing values,
  invalid simple types/choices, values on boolean flags and conflicting known scalar
  values block validation/save/launch. Explicit empty string arguments remain
  distinct from missing values and are allowed for string options.
- Boolean flags use a checkbox without an artificial value. A required boolean
  flag also needs deliberate enablement.
- Saved `--name=value` and `--name value` forms appear in separate name/value
  fields while retaining their exact original tokens, alias and order. A discovered
  option already present is not added again. Newly enabled options use equals
  syntax; use Exact argv to review every change.
- Unknown/repeated/positional/ambiguous tokens stay as clearly labeled manual rows
  in this same editor, with the original add, remove, pair, split, move and paste
  controls. Repeated options remain intact for manual review. Conflicting scalar values
  are not silently resolved by last-wins; identical values and repeated boolean
  flags remain valid. Unsupported repeatable actions can repeat normally.

There is no separate discovered-parameter list, pending-override stage or Apply
button. Edits immediately update the exact command preview and invalidate launch
validation. Paste still requires explicit Replace or Cancel. Only the existing
ordered argv array is saved; historical run commands are never rewritten.

**Rescan parameters** updates metadata without rewriting argv or disabled edited
values. Changed declaration bytes produce a review warning. Removed definitions
fall back to manual rows; disabled edited values remain disabled. A new dialog has
no previous scan baseline and cannot infer when a saved argument was last valid.
The optional schema retains precedence, with source/warnings in expandable inline
notes. Unsupported required definitions are identified for manual review, not
claimed to be automatically validated.

Newly enabled options are placed before an existing `--` positional delimiter;
existing tokens keep their relative order. Attached short flags, abbreviations,
custom actions/types, multi-value arguments, groups/subparsers, multiple parser
instances, parser mutations and dynamic definitions use manual fallback. Required
positionals are identified but not automatically assigned or counted: unknown
options may consume tokens, so guessing could corrupt the intended command.
Static definitions are advisory; conditional code, imports, shadowed names and
runtime changes can alter their meaning. No executable help fallback is offered.

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
