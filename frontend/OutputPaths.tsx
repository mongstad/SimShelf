import React from "react";
import { outputCandidates } from "./outputCandidates";
import type { OutputMapping, OutputReview } from "./types";
export function OutputPaths({
  args,
  mappings,
  change,
  review,
  captureReview = review,
  captureError = "",
  error,
  apply,
}: {
  args: string[];
  mappings: OutputMapping[];
  change: (next: OutputMapping[]) => void;
  review: OutputReview | null;
  captureReview?: OutputReview | null;
  captureError?: string;
  error: string;
  apply: (index: number, value: string) => void;
}) {
  function edit(i: number, patch: Partial<OutputMapping>) {
    change(mappings.map((m, j) => (i === j ? { ...m, ...patch } : m)));
  }
  return (
    <section aria-label="Output destinations" className="output-paths">
      <h3>Output destinations</h3>
      <p>
        <strong>{captureReview?.output_policy === "per_run" ? "Resolved capture parent:" : "Resolved capture folder:"}</strong>{" "}
        <code>
          {captureReview?.output_path ||
            (captureError
              ? "Capture path unavailable; check the capture settings."
              : "Checking capture path…")}
        </code>
      </p>
      {captureError && <p className="error-banner" role="alert">{captureError}</p>}
      {captureReview?.output_policy === "per_run" && <p className="notice">
        Capture will inspect only a new run_&lt;unique ID&gt; subfolder, allocated at
        launch. Your script must use SIMSHELF_OUTPUT_DIR or joined run.output_dir.
        Fixed paths below do not follow that folder; no arguments are rewritten.
      </p>}
      {captureReview?.output_policy !== "per_run" && <p className="muted">Simulation-owned unique output directories beneath this fixed parent are inspected recursively. No launcher coordination is required.</p>}
      <p className="muted">
        SimShelf inspects this folder only. It does not redirect script writes.
        Declare output paths below to check coverage; other writes cannot be
        detected. References are not backups.
      </p>
      <p className="muted">
        For options such as --wvz, --output or --output-dir, select the path
        token (or option=path token) and confirm whether your script treats it
        as a file or directory. No flag semantics are assumed. Paths resolve
        from the working directory without shell expansion.
      </p>
      {outputCandidates(args)
        .filter(
          (candidate) =>
            !mappings.some((m) => m.argument_index === candidate.index),
        )
        .map((candidate) => (
          <div className="output-candidate" key={candidate.index}>
            <p>
              Possible output option: <code>{candidate.flag}</code>. Confirm its
              meaning in your script:
            </p>
            <div className="argument-actions">
              {(["file", "directory"] as const).map((kind) => (
                <button
                  type="button"
                  key={kind}
                  disabled={mappings.length >= 32}
                  onClick={() =>
                    change([
                      ...mappings,
                      {
                        argument_index: candidate.index,
                        value: args[candidate.index],
                        kind,
                        format: candidate.format,
                      },
                    ])
                  }
                >
                  Map argument {candidate.index + 1} as {kind}
                </button>
              ))}
            </div>
          </div>
        ))}
      {mappings.map((m, i) => (
        <div className="output-mapping" key={i}>
          <div className="form-grid">
            <label>
              Output {i + 1} source
              <select
                aria-label={`Output ${i + 1} source`}
                value={m.argument_index ?? "fixed"}
                onChange={(e) => {
                  const index =
                    e.target.value === "fixed" ? null : Number(e.target.value);
                  edit(i, {
                    argument_index: index,
                    value: index === null ? "" : args[index],
                    format: "token",
                  });
                }}
              >
                <option value="fixed">Declared path (not an argument)</option>
                {args.map((arg, index) => (
                  <option key={index} value={index}>
                    Argument {index + 1}: {arg || "(empty)"}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Path kind
              <select
                aria-label={`Output ${i + 1} kind`}
                value={m.kind}
                onChange={(e) =>
                  edit(i, { kind: e.target.value as OutputMapping["kind"] })
                }
              >
                <option value="file">File</option>
                <option value="directory">Directory</option>
              </select>
            </label>
          </div>
          {m.argument_index === null ? (
            <label>
              Declared path
              <input
                aria-label={`Output ${i + 1} path`}
                value={m.value}
                onChange={(e) => edit(i, { value: e.target.value })}
                placeholder={m.kind === "directory" ? "Example: outputs" : "Example: outputs/data.csv"}
                aria-describedby={`output-${i}-help`}
              />
              <small id={`output-${i}-help`}>
                {m.value === "" ? `Output ${i + 1} is incomplete. Enter a ${m.kind} path or remove this mapping before validating, saving or starting. Example text is not an entered path.` :
                  "Paths resolve from the working directory. They may be prospective; an empty directory is allowed. This declaration does not create or redirect outputs."}
              </small>
            </label>
          ) : (
            <>
              <label>
                Token format
                <select
                  aria-label={`Output ${i + 1} format`}
                  value={m.format}
                  onChange={(e) =>
                    edit(i, {
                      format: e.target.value as OutputMapping["format"],
                    })
                  }
                >
                  <option value="token">Whole token is the path</option>
                  <option value="equals">
                    Option=path (use text after first =)
                  </option>
                </select>
              </label>
              <p>
                Mapped token: <code>{m.value}</code>
              </p>
              {args[m.argument_index] !== m.value && (
                <div role="alert" className="error-banner">
                  This argument changed. Confirm its current path token or
                  select another argument.
                  <button
                    type="button"
                    disabled={args[m.argument_index] === undefined}
                    onClick={() => edit(i, { value: args[m.argument_index!] })}
                  >
                    Confirm current token
                  </button>
                </div>
              )}
            </>
          )}
          {review?.targets[i] && (
            <div
              className={review.targets[i].covered ? "notice" : "error-banner"}
            >
              <code>{review.targets[i].resolved_path}</code>
              <p>{review.targets[i].reason}</p>
              {review.targets[i].suggested_argument !== null &&
                !review.targets[i].covered && (
                  <>
                    <p>
                      Suggested argument:{" "}
                      <code>{review.targets[i].suggested_argument}</code>
                    </p>
                    <button
                      type="button"
                      onClick={() =>
                        apply(i, review.targets[i].suggested_argument!)
                      }
                    >
                      Use suggested path
                    </button>
                    <small>
                      Changes only this argument. The script must support this
                      destination and create any required directories. Existing
                      files are not moved.
                    </small>
                  </>
                )}
            </div>
          )}
          <button
            type="button"
            aria-label={`Remove output ${i + 1}`}
            onClick={() => change(mappings.filter((_, j) => j !== i))}
          >
            Remove mapping
          </button>
        </div>
      ))}
      <button
        type="button"
        disabled={mappings.length >= 32}
        onClick={() =>
          change([
            ...mappings,
            { argument_index: null, value: "", kind: "file", format: "token" },
          ])
        }
      >
        Declare output path
      </button>
      {error && (
        <p className="error-banner" role="alert">
          {error}
        </p>
      )}
      {!mappings.length && (
        <p className="muted">
          No output paths declared. Coverage of your script’s actual outputs is
          unknown. You can still run it.
        </p>
      )}
    </section>
  );
}
