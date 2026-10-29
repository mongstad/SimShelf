# SWSS schema-3 output-parent discovery

SimShelf consumes the accepted SWSS v3.0/schema-3 contract at
[Simulation-Standards `198f234`](https://github.com/mongstad/Simulation-Standards/blob/198f234693535c1f7bc7e78cd8e599a510c2d494/standards/SWSS/v3.0.md).
Schema 2 remains supported without acquiring these output defaults. No saved
settings, historical configurations, snapshots, runs or scientific files are
converted. Metadata validity and listed-byte binding do not certify simulation
behavior or full SWSS conformance.

For a newly configured schema-3 simulation, **New run** shows the discovered
capture parent. The script owns creation of one unique standalone child; SimShelf
watches the parent and never creates a redundant run directory. The optional
coordinated full-root capability remains unavailable for SWSS simulations.

```toml
[swss]
schema_version = 3
entrypoint = "solver/simulate.py"
simulation_version = "0.2.0"
output_parent = "results/standalone"
output_parent_parameter = "destination"

[[swss.parameters]]
id = "destination"
kind = "option"
options = ["--output-parent", "-o"]
required = false
type = "string"
action = "store"
help = "Parent for unique run directories, relative to the selected project root"
default = "results/standalone"
```

The author must implement this behavior in the simulation. With no override,
the parent is `results/standalone` beneath the registered root, independent of
CWD and the nested entrypoint. Omitting `output_parent` means `outputs`. A single
bound `--output-parent=other`, `--output-parent other` or `-o other` overrides it.
Relative overrides also use the registered root. No tokens are inserted or
normalized. Unsupported/repeated/unknown options, missing/empty values,
post-delimiter content, stale bindings and ambiguous ownership disable automatic
routing. Correct the arguments or explicitly choose **Change capture folder →
Review an explicit capture parent**. A known computed destination must agree with
that manual selection; conflicts cannot silently redirect capture.

Existing saved settings remain manual unless the owner explicitly selects
discovery and saves. Registration initializes a new schema-3 capture setting
from the declared/default parent. Existing registrations are unchanged. The local
capture extension cannot conflict with the portable parent. Source hashes,
entrypoint association and whole companion bytes are rechecked before execution.

## External parents and safety limits

An absolute bound override can select external storage. The parent must already
exist: explicitly mount and prepare it before review. SimShelf never creates an
absent external fallback path. Check that the intended volume is mounted before
validation. Review retains existing ancestor device/inode identities, rejects
symlinks and non-directories, and rechecks at supervisor/recorder startup, source
capture and final output access. Replaced or unavailable paths fail visibly.
The preview revision binds metadata, argv, source identity and destination checks;
changes require fresh review. A new parent created by the script also changes
that revision, so reopen/revalidate before the next launch.

This is Linux-local identity checking, not a portable required-mount protocol:
an already wrong filesystem at first review cannot be recognized from a path
alone. Removable/network-volume failure and hostile concurrent path replacement
are unverified; checks do not hold directory descriptors throughout solver
execution. The author must meet any stronger volume contract. External location
details remain in the local workspace's access-controlled records, not rewritten
into portable TOML. Backups retain copied artifacts and location evidence, not
reference-only external data or the Git archive.

Before source enumeration, the current internal parent and known prior generated
parents are excluded recursively. Location-bound additive metadata remembers
parents used by new schema-3 runs; it never rewrites earlier snapshots. Registered
and saved legacy boundaries remain. Explicit source manifests, the entrypoint and
companion cannot be swallowed by the parent or excluded from capture. Required
research inputs must be declared in the source manifest or kept outside output
trees: SimShelf cannot infer unknown input roles from names/content. Preserve a
separate layout and review source inclusion rules.

Capture still uses existing copy/reference/ignore rules, scan/file/run budgets,
overlap guards, and required-log checks. A successful process can have partial
capture. Parent capture does not identify arbitrary concurrent external writers
or prove which child the solver actually used; captured artifact paths are
observations, not a coordinated-root acknowledgment. Large binaries remain
references unless deliberately selected for copying.

Git consent is not widened. When the effective parent differs from the reviewed
capture configuration, automatic Git archival is unavailable until preservation
scope can be reviewed; local capture continues with a truthful archive diagnostic.
The existing preservation-settings UI supports internal parents only, so external
parent runs currently use local capture without automatic Git archival. This is
an explicit limitation, not a claim that external results reached Git.

The CLI recorder also discovers schema-3 parents when no explicit capture override
is given. It requires an explicit interpreter/registered-entrypoint command to
identify the simulation argv; wrappers and ambiguous Python invocations are
refused. Joined Python contexts use their wrapper's frozen capture configuration.
Standalone in-process contexts must have the same explicit entrypoint identity.

Use disposable copies of the accepted scalar-decay reference for owner checks;
see [validation and exact steps](validation/issue-154-swss-output-parent.md).
