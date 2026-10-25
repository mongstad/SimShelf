import React from "react";
import { outputCandidates } from "./outputCandidates";
import type { OutputMapping, OutputReview } from "./types";

export function CapturePath({ review, error }: { review: OutputReview | null; error: string }) {
  return <div className="capture-path" aria-label="Effective capture destination">
    <p><strong>{review?.output_policy === "per_run" ? "Capture parent" : "Capture folder"}</strong></p>
    <code>{review?.output_path || (error ? "Capture path unavailable; check the capture settings." : "Checking capture path…")}</code>
    {error && <p className="error-banner" role="alert">{error}</p>}
    {review?.output_policy === "per_run" && <p className="notice">
      Capture uses a new run_&lt;unique ID&gt; subfolder allocated at launch. Your script must use
      SIMSHELF_OUTPUT_DIR or joined run.output_dir. Fixed paths do not follow it; arguments are unchanged.
    </p>}
  </div>;
}

export function OutputPaths({
  args,
  mappings,
  change,
  review,
  error,
  apply,
}: {
  args: string[];
  mappings: OutputMapping[];
  change: (next: OutputMapping[]) => void;
  review: OutputReview | null;
  error: string;
  apply: (index: number, value: string) => void;
}) {
  function edit(i: number, patch: Partial<OutputMapping>) {
    change(mappings.map((m, j) => (i === j ? { ...m, ...patch } : m)));
  }
  return (
    <section aria-label="Output coverage declarations" className="output-paths">
      <p className="muted">Declare paths only to check coverage. Declarations do not redirect writes or add capture folders. Relative paths use the working directory.</p>
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
                {m.value === "" ? `Output ${i + 1} is incomplete. Enter a ${m.kind} path or remove this mapping to continue.` :
                  "Relative to working directory; does not redirect writes."}
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
                      Changes this argument only. Your script must support the path and create directories; existing files stay in place.
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
          No paths declared; output coverage unknown.
        </p>
      )}
    </section>
  );
}
