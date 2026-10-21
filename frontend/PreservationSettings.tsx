import React, { useEffect, useRef, useState } from "react";
import { api } from "./api";
import { ArchiveSettings, archiveLimits } from "./GitArchive";
import type { Config, Simulation } from "./types";

type Review = Record<string, any>;
type Options = {
  enabled: boolean;
  all_sources: boolean;
  sources: string[];
  extensions: string[];
  process_logs: boolean;
};
const initialOptions: Options = {
  enabled: false,
  all_sources: true,
  sources: [],
  extensions: [".json", ".csv", ".log"],
  process_logs: false,
};
const lines = (s: string) =>
  s
    .split("\n")
    .map((v) => v.trim())
    .filter(Boolean);

export function PreservationReview({ review }: { review: Review }) {
  const sources = review.sources.filter((f: Review) => f.selected);
  return (
    <>
      <p>
        Future runs: capture inside <code>{review.config.output_dir}</code>. Git
        preservation is{" "}
        <strong>
          {review.options.enabled
            ? "enabled for the choices below"
            : "disabled"}
        </strong>
        .
      </p>
      <p>
        Source selection:{" "}
        {review.options.all_sources
          ? "all captured snapshot files, including future matching files"
          : "only the listed snapshot paths"}
        . Recursive output types:{" "}
        {review.options.extensions.join(", ") || "none"}. Process stdout/stderr:{" "}
        {review.options.process_logs ? "included" : "excluded"}.
      </p>
      <p>
        {archiveLimits} Records: 1 MiB each; notes/captions: 64 KiB each; 1,000
        annotation entries per run including revisions. These Git limits also
        apply when capture limits are larger.
      </p>
      {review.options.enabled && (
        <>
          <p>
            Git receives verified managed copies only. Reference-only and
            ignored bytes are excluded. Capture failures, missing copies and
            unknown coverage remain visible. Existing unchanged outputs are not
            attributed to a new run.
          </p>
          <p>
            Included record: {review.record_scope.join("; ")}. Records can
            contain local paths and parameters. They do not recreate the
            environment or restore a whole workspace.
          </p>
        </>
      )}
      <details open>
        <summary>
          Source review ({sources.length} selected of {review.sources.length}{" "}
          observed)
        </summary>
        <ul>
          {review.sources.map((f: Review) => (
            <li key={f.path}>
              <code>{f.path}</code> —{" "}
              {f.captured ? "snapshot" : "outside snapshot rules"};{" "}
              {review.options.enabled && f.selected
                ? "Git selected"
                : "Git excluded"}
            </li>
          ))}
        </ul>
        {!review.sources.length && <p>No source files observed.</p>}
      </details>
      <details open>
        <summary>
          Output review ({review.outputs.total_files} currently observed)
        </summary>
        <p>
          These are current matches, not evidence attributed to a future run.
          Recursive rules also cover new subdirectories.
        </p>
        <ul>
          {review.outputs.files.map((f: Review) => (
            <li key={f.path}>
              <code>{f.path}</code> — {f.size.toLocaleString()} bytes; capture:{" "}
              {f.action}; Git:{" "}
              {f.git_selected && !f.git_reason
                ? "selected"
                : f.git_reason || "excluded"}
            </li>
          ))}
        </ul>
        {review.outputs.truncated && (
          <p>
            Preview shows only the first 1,000 files; coverage is incomplete.
          </p>
        )}
        {[...review.warnings, ...review.outputs.errors].map(
          (w: string, i: number) => (
            <p role="alert" key={i}>
              {w}
            </p>
          ),
        )}
      </details>
      {(review.legacy || review.previous?.legacy_settings) && (
        <p>
          Confirming replaces legacy automatic consent for future runs.
          Historical policies and commits are retained unchanged.
        </p>
      )}
    </>
  );
}

export function SimulationPreservationControl({
  name,
  state,
  busy,
  onEnable,
  onDisable,
  onReview,
  actionRef,
  reviewRef,
  error = "",
}: {
  name: string;
  state: Review | null;
  busy: boolean;
  error?: string;
  reviewRef: React.RefObject<HTMLButtonElement | null>;
  onEnable: () => void;
  onDisable: () => void;
  onReview: () => void;
  actionRef: React.RefObject<HTMLButtonElement | null>;
}) {
  const connected = state?.connection?.state === "connected";
  const requested = !!(state?.policy?.options.enabled || state?.legacy);
  const enabled = connected && state?.status.state === "enabled";
  const unavailable =
    !!error ||
    (!!state &&
      (!connected || !["enabled", "disabled"].includes(state.status.state)));
  const label =
    !state && !error
      ? "Checking status…"
      : unavailable
        ? "Unavailable"
        : enabled
          ? "Enabled"
          : "Disabled";
  return (
    <section
      className="simulation-preservation"
      aria-label={`Git preservation — ${name}`}
    >
      <h3>Git preservation — {name}</h3>
      <div className="automatic-archive-line">
        <strong
          role="status"
          className={
            enabled
              ? "archive-connected"
              : unavailable
                ? "preservation-unavailable"
                : "muted"
          }
        >
          <span aria-hidden="true">
            {enabled ? "✓ " : unavailable ? "⚠ " : "○ "}
          </span>
          {label}
        </strong>
        {requested ? (
          <>
            <button
              ref={actionRef}
              disabled={busy || !state}
              onClick={onDisable}
            >
              Disable Git preservation
            </button>
            <button
              ref={reviewRef}
              disabled={busy || !connected}
              onClick={onReview}
            >
              Review Git preservation
            </button>
          </>
        ) : (
          <button
            ref={actionRef}
            className="primary"
            disabled={busy || !connected}
            onClick={onEnable}
          >
            Enable Git preservation
          </button>
        )}
      </div>
      <p>
        {unavailable
          ? error ||
            (!connected
              ? "Connect the shared Master Git Archive to enable preservation."
              : state?.status.reason ||
                "Review preservation choices before the next run.")
          : enabled
            ? "Future runs use this simulation’s confirmed choices."
            : "Connecting the archive does not enable this simulation."}
      </p>
      {state?.legacy && !state.policy && (
        <p>Legacy choices remain in effect until explicitly reviewed.</p>
      )}
      <small>Disabling keeps all existing Git history.</small>
    </section>
  );
}

export function PreservationSettings({
  simulation,
  onSaved,
}: {
  simulation: Simulation;
  onSaved: () => void;
}) {
  const [config, setConfig] = useState<Config>(
    structuredClone(simulation.config),
  );
  const [options, setOptions] = useState<Options>(initialOptions);
  const [state, setState] = useState<Review | null>(null),
    [review, setReview] = useState<Review | null>(null);
  const [loadError, setLoadError] = useState("");
  const [message, setMessage] = useState(""),
    [busy, setBusy] = useState(false);
  const [extensions, setExtensions] = useState(".json\n.csv\n.log"),
    [sources, setSources] = useState("");
  const reviewHeading = useRef<HTMLHeadingElement>(null),
    activation = useRef<HTMLButtonElement>(null),
    reviewTrigger = useRef<HTMLButtonElement>(null),
    trigger = useRef<HTMLButtonElement>(null);
  const returnTo = useRef<"activation" | "choices" | "review">("activation");
  const restore = useRef(false);
  const endpoint = `/simulations/${simulation.id}/preservation`;
  async function load(reset = false) {
    let result: Review;
    try {
      result = await api<Review>(endpoint);
      setLoadError("");
    } catch (e) {
      setState(null);
      setLoadError((e as Error).message);
      throw e;
    }
    setState(result);
    if (reset) {
      const o = result.policy?.options || {
        ...initialOptions,
        enabled: !!result.legacy,
      };
      setOptions(o);
      setConfig(result.config);
      setExtensions(o.extensions.join("\n"));
      setSources(o.sources.join("\n"));
    }
  }
  useEffect(() => {
    void load(true).catch((e) => setMessage(e.message));
  }, [simulation.id]);
  useEffect(() => {
    if (review) {
      reviewHeading.current?.focus();
      restore.current = true;
    } else if (!busy && restore.current) {
      (returnTo.current === "activation"
        ? activation
        : returnTo.current === "review"
          ? reviewTrigger
          : trigger
      ).current?.focus();
      restore.current = false;
    }
  }, [review, busy]);
  async function action(work: () => Promise<void>) {
    setBusy(true);
    setMessage("");
    try {
      await work();
    } catch (e) {
      setReview(null);
      setMessage((e as Error).message);
      await load().catch(() => setState(null));
    } finally {
      setBusy(false);
    }
  }
  function reviewChoices(
    from: "activation" | "choices" | "review",
    defaults = false,
  ) {
    if (!state) return;
    returnTo.current = from;
    restore.current = true;
    void action(async () =>
      setReview(
        await api<Review>(endpoint + "/preview", {
          method: "POST",
          body: JSON.stringify({
            config: defaults ? state.config : config,
            options: defaults
              ? { ...initialOptions, enabled: true }
              : {
                  ...options,
                  sources: options.all_sources ? [] : lines(sources),
                  extensions: lines(extensions),
                },
          }),
        }),
      ),
    );
  }
  function disable() {
    returnTo.current = "activation";
    restore.current = true;
    void action(async () => {
      await api(`/simulations/${simulation.id}/archive/disable`, {
        method: "POST",
      });
      setState(null);
      await load(true);
      onSaved();
      setMessage(
        "Git preservation disabled. Existing Git history is unchanged.",
      );
    });
  }
  return (
    <section className="surface preservation-settings">
      <h2>Preservation settings</h2>
      <ArchiveSettings
        simulation={simulation}
        disabled={busy || !!review}
        onChanged={() => {
          setReview(null);
          void load().catch((e) => setMessage(e.message));
        }}
      >
        <SimulationPreservationControl
          name={simulation.name}
          state={state}
          busy={busy || !!review}
          actionRef={activation}
          reviewRef={reviewTrigger}
          error={loadError}
          onEnable={() => reviewChoices("activation", true)}
          onDisable={disable}
          onReview={() => reviewChoices("review")}
        />
        {message && <p role="status">{message}</p>}
        {review && (
          <section
            className="preservation-review"
            aria-label="Preservation settings review"
          >
            <h3 ref={reviewHeading} tabIndex={-1}>
              Review future preservation
            </h3>
            <PreservationReview review={review} />
            <div className="settings-actions">
              <button
                disabled={busy}
                onClick={() => {
                  setReview(null);
                  setMessage("Review canceled. Saved settings are unchanged.");
                }}
              >
                Cancel
              </button>
              <button
                className="primary"
                disabled={busy}
                onClick={() =>
                  void action(async () => {
                    await api(endpoint + "/save", {
                      method: "POST",
                      body: JSON.stringify({ review, confirmed: true }),
                    });
                    setState(null);
                    setReview(null);
                    await load(true);
                    onSaved();
                    setMessage("Preservation settings saved for future runs.");
                  })
                }
              >
                Confirm preservation settings
              </button>
            </div>
          </section>
        )}
      </ArchiveSettings>
      <details className="preservation-options">
        <summary>Capture and Git options</summary>
        <fieldset disabled={busy || !!review || !state}>
          <legend>Capture and Git choices for future runs</legend>
          <label>
            Output parent folder
            <input
              value={config.output_dir}
              onChange={(e) =>
                setConfig({ ...config, output_dir: e.target.value })
              }
            />
            <small>
              Relative to the simulation folder. Use the fixed parent when your
              simulation creates its own unique subdirectories. Recording
              inspects nested files without changing the script or its
              arguments.
            </small>
          </label>
          <p>
            Capture rules run in order; the first matching rule wins. Keep a
            copy stores bytes in the library, Reference only stores a path, and
            Ignore leaves bytes out. Originals are never removed.
          </p>
          {config.rules.map((rule, i) => (
            <div className="rule-row" key={i}>
              <input
                aria-label={`Rule ${i + 1} pattern`}
                value={rule.pattern}
                onChange={(e) =>
                  setConfig({
                    ...config,
                    rules: config.rules.map((r, j) =>
                      i === j ? { ...r, pattern: e.target.value } : r,
                    ),
                  })
                }
              />
              <select
                aria-label={`Rule ${i + 1} policy`}
                value={rule.action}
                onChange={(e) =>
                  setConfig({
                    ...config,
                    rules: config.rules.map((r, j) =>
                      i === j ? { ...r, action: e.target.value as "copy" } : r,
                    ),
                  })
                }
              >
                <option value="copy">Keep a copy</option>
                <option value="reference">Reference only</option>
                <option value="ignore">Ignore</option>
              </select>
              <button
                aria-label={`Remove rule ${i + 1}`}
                onClick={() =>
                  setConfig({
                    ...config,
                    rules: config.rules.filter((_, j) => i !== j),
                  })
                }
              >
                Remove
              </button>
            </div>
          ))}
          <button
            onClick={() =>
              setConfig({
                ...config,
                rules: [...config.rules, { pattern: "", action: "copy" }],
              })
            }
          >
            Add capture rule
          </button>
          <div className="form-grid">
            <label>
              Maximum file size to copy (MB)
              <input
                type="number"
                min="0.001"
                step="any"
                value={config.max_file_mb}
                onChange={(e) =>
                  setConfig({ ...config, max_file_mb: Number(e.target.value) })
                }
              />
            </label>
            <label>
              Copy budget per run (MB)
              <input
                type="number"
                min="0.001"
                step="any"
                value={config.max_run_mb}
                onChange={(e) =>
                  setConfig({ ...config, max_run_mb: Number(e.target.value) })
                }
              />
            </label>
          </div>
          <details>
            <summary>Source snapshot patterns</summary>
            <label>
              Include patterns, one per line
              <textarea
                value={config.source_include.join("\n")}
                onChange={(e) =>
                  setConfig({
                    ...config,
                    source_include: e.target.value.split("\n"),
                  })
                }
              />
            </label>
            <label>
              Exclude patterns, one per line
              <textarea
                value={config.source_exclude.join("\n")}
                onChange={(e) =>
                  setConfig({
                    ...config,
                    source_exclude: e.target.value.split("\n"),
                  })
                }
              />
            </label>
          </details>
          <label className="archive-choice">
            <input
              type="checkbox"
              checked={options.all_sources}
              onChange={(e) =>
                setOptions({ ...options, all_sources: e.target.checked })
              }
            />{" "}
            Include all captured source snapshot files in Git
          </label>
          {!options.all_sources && (
            <label>
              Selected source paths, one per line
              <textarea
                value={sources}
                onChange={(e) => setSources(e.target.value)}
              />
            </label>
          )}
          <label>
            Recursive Git output extensions, one per line
            <textarea
              value={extensions}
              onChange={(e) => setExtensions(e.target.value)}
            />
            <small>
              For example .json, .csv and .log. Exact case; only new or changed
              outputs with Keep a copy coverage and verified managed bytes
              qualify, at any depth below the capture folder.
            </small>
          </label>
          <label className="archive-choice">
            <input
              type="checkbox"
              checked={options.process_logs}
              onChange={(e) =>
                setOptions({ ...options, process_logs: e.target.checked })
              }
            />{" "}
            Include recorded stdout and stderr in Git
          </label>
        </fieldset>
        {!review && (
          <button
            ref={trigger}
            className="primary"
            disabled={busy || !state}
            onClick={() => reviewChoices("choices")}
          >
            Review preservation settings
          </button>
        )}
      </details>
    </section>
  );
}
