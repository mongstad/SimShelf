# Issue #101 — SWSS schema-2 adoption

Prepared for owner review on 2026-10-19. Accepted base: `fd603ff` / 0.1.0.36;
proposed application version: **0.1.0.37**. Standards prerequisite PR #21 was
verified merged at `8157653c58eb055102e587734e3898a43653eba0`. No standards repository,
workspace schema or historical report was changed.

## Implementation and decisions

- One bounded data-only `swss.toml` reader, strict schema-2 identity/row handling,
  descriptor-relative no-symlink access and identity rechecks, streaming optional
  source hashes, conservative literal source-version comparison without AST work.
- Typed declarations feed the existing three argument groups. No defaults inserted;
  original argv representations remain authoritative. Short attached forms remain
  manual; signed-64-bit choices use lossless decimal transport and BigInt checks.
- Visible unverified/stale/error diagnostics, explicit saved manual mode, rescan
  review and fingerprint checks through validation/supervisor/recording. Server-read
  previous typed provenance survives manual bypass. Run JSON retains exact declaration
  text/hash, binding evidence and argv; source snapshot must contain matching bytes.
- Documented optional `extensions.simshelf` version 1 initializes registration
  capture settings; saved settings remain deliberate user choices. Invalid portable
  metadata does not prevent manual registration with default settings, but does not
  import extension settings. Unsupported local extension configuration is refused.
- Legacy companion readers retired after initial new-flow end-to-end tests passed.
  Legacy files are refused for new runs; old runs and bytes remain readable.
  Defaults copy `.log`; SWSS-described isolated runs report incomplete capture if
  no matching log is copied, independently of solver exit status.
- Scalar-field example now uses the single companion and source version 0.1.1;
  timestamped logs and output-root conflict checks were added. Solver equations and
  RNG calls were not changed. This is not a numerical-equivalence claim.

## Automated validation

Linux, Python 3.14.8, Node 24.19.0. Source tests used `PYTHONPATH=src`, no bytecode,
no pytest cache and external disposable basetemps.

The focused integration command covered `test_swss`, `test_parameters`,
`test_portal`, `test_isolated_outputs`, `test_capture_backup`, `test_progress`,
`test_git_archive`, `test_git_selection`, `test_version_edge_cases`,
`test_git_provenance` and `test_application_version`: **278 passed**. After the
final integer-hint transport change, the SWSS suite was rerun: **50 passed**.
The existing Starlette/httpx deprecation warning remained; no dependency change.

Coverage includes minimal/empty/mixed-use metadata, ignored unknown extensions,
local extension import/conflict refusal, invalid TOML/schema/UTF-8/controls,
duplicate ownership, row-only failures, choices/defaults/types, stale hashes and
version labels, symlinks/missing/traversal paths, open-time substitution,
document/depth/entry/string/row/alias/choice/source bounds and several exact
permitted boundaries, source-size hashing limits and manual fallback. Discovery
is tested with AST parsing and subprocess launch forbidden. Existing progress,
metrics, archive, capture budgets, backup and source-version regressions passed.

A harmless conventional-parser fixture with **more than 20,000 AST nodes**
discovered parameters without AST inspection, saved and launched exact argv
including `--N 00192`, `--dt=1e-3`, `--label ''`, unknown tokens and `--`.
Successive and concurrent SWSS runs use distinct roots. Intentional exit-3 and
cancelled runs retain partial log evidence and truthful lifecycle status. Missing,
ignored, reference-only and oversized logs yield incomplete capture.

Frontend: **17 parameter-model tests**, **4 argument parser/formatter tests**,
TypeScript typecheck and production bundle build passed. Version-policy check,
changed-document relative links and `git diff --check` passed.

## Installed browser and historical evidence

The disposable wheel installation served localhost port 8799. The large-source
fixture showed four value controls and two valueless boolean controls. Checked
choices, unchanged lexical values, explicit empty strings, save/reopen, manual
bypass persistence, invalid-schema diagnostics, and rescan review. An extension-only
edit after preview refused launch. Rescan disabled typed editing until explicit
review, without changing argv. A subsequent UI launch completed with a copied log;
its stored command, provenance argv and actual child argv matched exactly. Both
`store_true` and `store_false` resolved correctly. Run:
`9f30e32566ab4d43a10c7daab84abd8b` in the disposable fixture library.

All five themes (Light, Dark, Onyx, Slate, Linen) were measured at 1280×1000 and
390×844. Editor/parameter-row scroll widths equaled client widths (927 and 301 px);
flags had no text value input. Desktop/narrow screenshots were visually inspected.
Native checkbox Space and Tab focus worked, with visible focus outline. Final
browser error log was empty. The final presentation bundle was rechecked in the
disposable installation and is byte-compared against the final packaged assets.
Two tiny runs of the converted scalar-field example (size 8, steps 2) also
completed from the final installed package with source version 0.1.1, distinct
output roots and complete copied-log capture. No numerical-equivalence claim was
made from those smoke runs.

Temporary evidence remains under `/tmp/simshelf-101/` (including `themes.json`,
`final-desktop.png` and `narrow.png`).

A real run was first recorded using the previous **0.1.0.36 installed wheel**,
including a `simshelf.toml` source snapshot. Opening it with 0.1.0.37 preserved the
entire returned record, exact argv, annotations and SHA-256 of all retained blobs,
snapshots, logs and journals. Historical fixture run:
`0d8f1f5ed47f49f1ade5e1c392215f66`. Owner libraries were not used.

## Packaging and limitations

Wheel and sdist are built outside the checkout, with a second wheel rebuilt from
the extracted sdist. Package smoke checks compare all wheel member bytes and all
installed static/license assets, and exercise Python/CLI/API/OpenAPI version
0.1.0.37 plus offline startup/assets with socket connections denied and Git/Node
absent from PATH. Final artifacts and build logs remain in the external evidence
directory; none are release assets or published packages.

Development checks caught and corrected a misplaced JSX closing tag. Harness
corrections included invoking esbuild directly rather than through Node, selecting
a choice by its label rather than assuming its internal value, and using a custom
local server instead of an unsupported CLI `--no-browser` option. A disposable
server exited with SIGTERM during testing and was restarted; its completed run
remained intact. These were not represented as successful checks before correction.

This is not exhaustive SWSS certification. No real vacuum-collapse solver, GPU,
scientific-export reader, numerical-equivalence experiment, screen reader,
Windows/macOS, other browser engine, hostile-filesystem stress campaign or long
scientific workload was tested. Hashes cover listed bytes only; edits after a
check remain possible. Log content/timestamp semantics and resolved scientific
parameters remain the simulation author's responsibility. Existing text-progress
and metric transports retain their documented limits. No automatic scientific
source migration or old-config compatibility is provided.

## Owner verification

1. Copy the scalar-field example into a new disposable source folder; register it
   using the installed candidate and an interpreter with SimShelf available.
2. Open New run. Confirm typed `--size`, `--steps`, `--dt` and other declarations,
   binding-unverified wording, no injected defaults, and exact argv preview. Select
   size 8, steps 2, unique output folders; review then launch twice. Inspect copied
   timestamped logs, summaries, distinct roots and unchanged first-run files.
3. On a disposable declaration fixture, test both boolean actions, aliases,
   `00192`, an explicit empty string and `--`; save/reopen and inspect child argv.
4. Edit only extension text after validation. Confirm stale launch refusal, rescan
   review and unchanged arguments. Try schema 1/3 or a mismatched source hash and
   confirm diagnostics plus deliberate manual mode, not automatic conversion.
5. Inspect an independently backed-up historical library read-only: old source
   snapshots/configuration, commands, annotations and artifacts must remain intact.
   Review desktop/narrow layouts and keyboard controls in your normal browser.

Owner review is pending. No merge, release, tag or publication is authorized here.
