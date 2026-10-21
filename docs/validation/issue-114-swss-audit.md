# SWSS metadata audit and static CLI investigation

Audited 2026-10-21 on Linux, CPython 3.14.8 and Node.js 24.19.0, against
SimShelf `73b634059557d9d88199589b4ae3faffbef763bc` (0.1.0.41).
This is a bounded audit, not full SWSS or scientific conformance certification.
No runtime behavior, stored records, application version or portable contract changes.

## Authority and evidence

The authoritative [SWSS v2.0](https://github.com/mongstad/Simulation-Standards/blob/285ab0d6c06cc3b88e421a2c00577e72c650c750/standards/SWSS/v2.0.md)
§§4.1–4.5 and §5.2 distinguish document validation, source binding and exact argv.
Issue #101's implementation is in accepted main. Related standards issue #23 is
closed; its research brief is not a new accepted verifier contract. The scalar-decay
reference at that same standards revision is **0.1.3**, superseding the adapter
revision mentioned in #114. It was read only; no reference/consumer adapter was
installed or executed for the AST investigation.

Implementation references:

- [SWSS reader](../../src/simshelf/swss.py): `parse`, `parameters`, `safe_read`,
  `read`, `review`.
- [Discovery](../../src/simshelf/parameters.py): `discover_parameters`,
  `static_parameters`; SWSS is the default, static is an explicit separate source.
- [Launch plan](../../src/simshelf/portal.py): `execution_settings`; its supervisor
  repeats validation. [Recorder](../../src/simshelf/recording.py) `__enter__` rechecks
  metadata and compares captured companion bytes with the reviewed hash.
- [Saved settings](../../src/simshelf/store.py): `update_simulation` retains typed
  provenance for later manual bypass. [Editor](../../frontend/ArgumentEditor.tsx)
  shows diagnostics/binding state and preserves an explicit manual path.
- Existing [SWSS tests](../../tests/test_swss.py), [static discovery tests](../../tests/test_parameters.py)
  and added [audit probes](../../tests/test_swss_audit.py).

## Part A: coverage matrix

“Already covered” means existing focused tests passed. “Partial” identifies a
bounded evidence gap, including one filled by this audit; it is not a conformance claim.

| Scenario | Coverage and observed result |
| --- | --- |
| No companion | Already covered by ordinary portal fixtures; added `test_audit_manual_launch_matrix` proves registration, save and actual manual launch preserve unknown tokens, numeric spelling, empty string and delimiter. No typed rows; diagnostic returned. |
| Valid schema 2, parameters/flags | Already covered by `test_choices_flags_and_bad_scalar_types`, minimal/empty/partial declarations and real launch tests. Supported rows remain typed; no implicit AST merge. |
| Valid metadata without hashes | Already covered: `binding unverified` with typed rows allowed, as §4.4 requires. Added matrix and unbound-edit probe confirm unknown binding is not parser mismatch. |
| Malformed TOML / unsupported schema | Partial existing integration: invalid registration and manual plan were tested, plus document fallback tests. Added matrix executes both malformed and schema-3 cases manually with exact argv and retained source bytes. Neither becomes typed or gets reinterpreted. |
| Stale supplied hashes | Already covered: matching listed bytes, stale reasons, typed refusal and manual review. Added matrix confirms actual manual launch with stale hashes. Matching hashes do not establish CLI compatibility. |
| Runtime parser rejection | Partial existing evidence: nonzero solver exits were covered. Added `test_audit_verified_bytes_do_not_prove_parser_compatibility` launches an intentionally mismatched, hash-bound fixture: exit 2, failed run, original `--N 00192`, genuine argparse stderr. No repair/coercion. This is expected behavior, not a metadata-schema defect. |
| Changes after registration | Already covered: companion or bound-source edits invalidate typed review; previous provenance and historical runs survive. Added unbound-edit case verifies saved argv remains exact. Without hashes/comparable version, source-only edits need not change the metadata fingerprint: binding remains unverified, never CLI-verified. |
| Document versus row failure | Already covered for duplicate/invalid IDs, alias ownership and safety limits (whole document), and unsupported actions/types/defaults/repeatable/nargs (manual row). Added mixed-row probe retains the other valid row and unknown optional default. **Confirmed gap below:** nested portable row structures are incorrectly reduced to row failure. |
| Required/default/alias semantics | Existing parser/row tests and bundled frontend suites cover required presence, optional omission, numeric grammar, known empty defaults, flags, exact alias/order spelling, repeats and manual tokens. Unknown defaults do not imply requiredness; defaults are not inserted. No new browser interaction performed. |
| Filesystem/resource safety | Already covered for symlink refusal, entrypoint association, open-time substitution, UTF-8, nonfinite/control values, document/string/depth/row/alias/choice/source bounds and 16 MiB hashing. **Partial:** not an exhaustive key/shape/fuzz audit, all-platform filesystem proof or hard CPU/memory benchmark; aggregate 64 MiB boundary and every race variant were not newly exercised. |

### Confirmed gap and smallest correction

SWSS §4.5 says nested portable values outside specified structures invalidate
portable metadata. A row containing `default = { unexpected = 1 }` currently
gets `supported=False`, while a sibling valid row remains typed and provenance
is still returned. `parse.visit` checks bounds but not permitted structural
locations; `parameters` subsequently applies its scalar-type fallback.
`test_audit_nested_portable_value_is_document_failure` records this as one
**strict expected failure**, not a pass. The existing `type = {}` test likewise
expects row fallback; that expectation needs reconsideration in a correction.

Recommended correction: reject arrays/tables in portable scalar fields and other
unspecified portable locations before row normalization. Retain the allowed
parameter/source arrays and choice/alias arrays, extension semantics, scalar
row-error fallback and whole-file limits. Test nested default/type/help/required
and nested choice values alongside valid siblings, scalar wrong types, valid
structures and explicit manual launch. No schema change or migration is needed.
This audit reports the defect; it does not bundle an unapproved runtime fix.

## Part B: optional AST evidence

Keep three independent questions:

1. **Metadata validity:** schema/document accepted, with individual unsupported
   rows identified. This does not mean the parser accepts the declared options.
2. **Source binding:** listed bytes verified, unverified, or stale/invalid.
   Matching bytes neither prove completeness nor verify behavior.
3. **CLI compatibility:** optional method-scoped evidence, field by field:
   match, confirmed mismatch, or indeterminate/unsupported. No current SimShelf
   discovery result supplies this third guarantee.

The pinned reference's twelve literal declarations agree on aliases, actions,
types, requiredness, choices and declared defaults in a read-only syntax probe.
Omitted defaults are not asserted to match runtime defaults. Seven in-memory
source mutations expose spelling, alias, type, action, requiredness, choices and
default disagreements; a multi-value `nargs` mutation becomes unsupported.
These tests inspect syntax, never import or run the reference.

| Field | Evidence a narrow future checker could report | Indeterminate cases |
| --- | --- | --- |
| Spelling/aliases | Exact literal aliases on an identified, proven parser binding | No recognized declaration, dynamic names, factories/imported additions, conditional construction or ambiguous ownership; absence alone is not mismatch |
| Arity/action | Literal supported action and effective single-value/no-value arity | Custom action, dynamic nargs, groups/subcommands, mutation or unknown parser configuration |
| Type | Literal built-in binding whose identity is established | Shadowed names, custom converters, imported/rebound constructors |
| Requiredness | Literal presence requirement on that parser | Mutually exclusive groups, branching or later mutation |
| Choices | Bounded literal scalar sequence with exact typed comparison | Computed choices, custom containers or unknown conversion |
| Declared default | Bounded literal effective default under known action/parser precedence | Missing SWSS hint, context-dependent defaults, string conversion, `set_defaults`, parser-level defaults or later mutation |

A literal inequality is only a **confirmed mismatch** after establishing the
relevant parser identity, control-flow path, effective configuration and field
semantics. Otherwise it is an apparent difference requiring review. Overall
mismatch requires at least one confirmed mismatch; overall match requires every
applicable declared field to match within a stated supported scope. Any unresolved
field makes the overall result indeterminate. Extra undeclared CLI arguments are
allowed by partial metadata, not automatically a mismatch.

Current `static_parameters` uses `ast.literal_eval` for candidate literal data,
without general `eval` or execution of the inspected module. It walks the entire AST and compares variable spellings,
not lexical bindings/control flow. The added probes demonstrate supported-looking
`--x` rows inside `if False`, an unrelated function taking `p`, and after `int = str`.
Its explicit “suggestions, not proof” warning is therefore necessary. Do not
promote that API's `supported` flag into CLI verification, silently combine it
with SWSS discovery, or use it to block registration/manual/valid typed metadata.
The reference positive case proves local literal agreement only, not that every
runtime path reaches those declarations.

### Recommendation and proposed separate scope

Additional optional evidence is worthwhile, but reuse of the current suggestions
walker as a verifier is not. A separately authorized first implementation should:

- Inspect one explicitly selected Python file using safe descriptor-relative reads;
  no imports of inspected code, eval/literal evaluation, `--help`, subprocesses,
  network, plugins or installation. Decode only a small AST constant/container
  whitelist; reject expressions, expansion, calls and shadowed bindings.
- Initially support an explicitly identified straight-line parser block with
  recognized constructor/built-in bindings and no escaping parser, mutation,
  conditional additions or unknown calls. A simple factory can provide local
  declaration evidence, but cannot by itself certify entrypoint execution.
- Bound input bytes (proposed 256 KiB), tokens/nodes (20,000), nesting (64),
  declarations (128), literal strings (4,096 bytes) and literal collections (100).
  These are proposed inspector limits, not SWSS validity rules. Limit exhaustion
  yields indeterminate and leaves existing use paths available.
- Resolve parser-time resource control before shipping. Current `ast.parse` runs
  before `list(ast.walk(...))` enforces node count; there is no hard parse timeout
  or memory budget. A deadline checked after parsing cannot bound the parse itself,
  and a thread cannot enforce a process memory cap. With subprocess inspection
  forbidden, demonstrate bounded parser allocation/work under admission limits
  or keep this feature deferred; do not claim isolation or add a worker silently.
- Return per-field evidence, source and companion digests, inspector version,
  scope/assumptions and limits. Invalidate evidence when either byte sequence
  changes. Keep the first scope read-only and advisory, without new storage,
  automatic source/TOML edits or launch requirements.

No new SWSS fields or portable capability are proposed by this local audit.
Any future shared verification contract requires separately authorized standards
work. No implementation issue was created and no general verifier was implemented.

## Reproduction and validation results

Use the existing development interpreter and force source imports. All libraries,
outputs and compiled test bundles belong in disposable directories outside the checkout.
The optional reference probe requires an existing read-only checkout of standards
commit `285ab0d6c06cc3b88e421a2c00577e72c650c750`; it checks the source digest and
skips explicitly if `SWSS_AUDIT_REFERENCE` is absent. It never fetches fixtures.

```bash
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider \
  tests/test_swss.py tests/test_parameters.py --basetemp=/tmp/swss-existing-audit
SWSS_AUDIT_REFERENCE=/path/to/pinned/standards/examples/decay \
  PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider \
  tests/test_swss_audit.py --basetemp=/tmp/swss-new-audit
node_modules/.bin/esbuild frontend/parameters.test.mjs frontend/arguments.test.mjs \
  frontend/ParameterHint.test.mjs --bundle --platform=node --format=cjs \
  --outdir=/tmp/swss-audit-js --out-extension:.js=.cjs
node --test /tmp/swss-audit-js/*.cjs
```

- Existing backend suite: **54 passed**. Added audit suite with pinned reference:
  **11 passed, 1 xfailed** (the confirmed nested-value defect). The combined
  final run from repository paths reports **65 passed, 1 xfailed**.
- Three bundled frontend test files passed. The first direct Node attempt failed
  on TSX and extensionless TypeScript imports; rerunning through the documented
  esbuild bundling workflow passed. No frontend source/assets changed.
- Backend tests emit the existing Starlette/httpx deprecation warning; no packages
  were installed or changed. Tests use actual local fixture processes only for
  explicit launch/error checks, never as a discovery mechanism.
- No runtime implementation changes: application build remains 0.1.0.41. The
  implementation version-increment gate, package build and installed-browser
  validation are not applicable to this report/test-only PR and were not run.
- Browser rendering/accessibility, installed packages, other platforms, exhaustive
  conformance/fuzzing and hard parser resource enforcement are not established.
  Diagnostic visibility is supported by API results and editor source inspection,
  not a fresh browser check.

Owner checks: reproduce both backend commands and confirm the single strict
expected failure; review the proposed nested-value correction and the optional
inspector's limited scope/resource gate separately. On a disposable portal library,
try malformed metadata with manual argv, valid unbound metadata, and an intentional
parser mismatch; verify diagnostics, exact argv and the failed run's stderr.
