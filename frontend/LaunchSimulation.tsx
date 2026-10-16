import React, { useState, useEffect } from "react";
import { ArgumentEditor } from "./ArgumentEditor";
import { argumentError, formatCommand } from "./arguments";
import { api } from "./api";
import { OutputPaths } from "./OutputPaths";
import type { Simulation, OutputMapping, OutputReview } from "./types";

type Plan = {
  output_review: OutputReview;
  command: string[];
  cwd: string;
  output_path: string;
  validation: { version: string; message: string };
};

export function LaunchSimulation({
  simulation,
  done,
  saved,
}: {
  simulation: Simulation;
  done: (id: string) => void;
  saved: () => void;
}) {
  const initial = simulation.execution;
  const [entry, setEntry] = useState(simulation.entrypoint || "");
  const [interpreter, setInterpreter] = useState(initial?.interpreter || "");
  const [cwd, setCwd] = useState(initial?.cwd || ".");
  const [args, setArgs] = useState<string[]>(initial?.arguments || []);
  const [pastePending, setPastePending] = useState(false);
  const argsError = argumentError(args);
  const preview = [
    interpreter || "(select Python)",
    `${simulation.root}/${entry || "(entry file)"}`,
    ...args,
  ];
  const [output, setOutput] = useState(
    initial?.output_dir || simulation.config.output_dir,
  );
  const [mappings, setMappings] = useState<OutputMapping[]>(
    initial?.output_mappings || [],
  );
  const [outputReview, setOutputReview] = useState<OutputReview | null>(null);
  const [outputError, setOutputError] = useState("");
  const [acknowledge, setAcknowledge] = useState(false);
  const [argumentRevision, setArgumentRevision] = useState(0);
  const outputRequest = JSON.stringify({
    cwd,
    arguments: args,
    output_dir: output,
    output_mappings: mappings,
  });
  useEffect(() => {
    let active = true;
    setOutputReview(null);
    setOutputError("");
    const timer = setTimeout(() => {
      api<OutputReview>(`/simulations/${simulation.id}/execution/outputs`, {
        method: "POST",
        body: outputRequest,
      })
        .then((result) => {
          if (active) setOutputReview(result);
        })
        .catch((e) => {
          if (active) setOutputError((e as Error).message);
        });
    }, 250);
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [outputRequest, simulation.id]);
  const [name, setName] = useState("");
  const [plan, setPlan] = useState<Plan | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const settings = {
    interpreter,
    cwd,
    arguments: args,
    output_dir: output,
    output_mappings: mappings,
  };
  function edited() {
    setPlan(null);
    setAcknowledge(false);
    setNotice("");
  }
  async function validate(save: boolean) {
    if (pastePending || argsError) return;
    setBusy(true);
    setError("");
    setNotice("");
    if (entry !== simulation.entrypoint) {
      setError("Update the registered entry before validating execution.");
      setBusy(false);
      return;
    }
    try {
      const result = await api<Plan>(
        `/simulations/${simulation.id}/execution/validate`,
        {
          method: "POST",
          body: JSON.stringify(settings),
        },
      );
      if (save) {
        await api(`/simulations/${simulation.id}/execution`, {
          method: "PUT",
          body: JSON.stringify(settings),
        });
        saved();
        setNotice("Execution settings saved for this simulation.");
      }
      setOutputReview(result.output_review);
      setPlan(result);
    } catch (e) {
      setPlan(null);
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function start(e: React.FormEvent) {
    e.preventDefault();
    if (
      !plan ||
      busy ||
      pastePending ||
      argsError ||
      !outputReview ||
      (outputReview.requires_acknowledgement && !acknowledge)
    )
      return;
    setBusy(true);
    setError("");
    try {
      await api(`/simulations/${simulation.id}/execution`, {
        method: "PUT",
        body: JSON.stringify(settings),
      });
      saved();
      const result = await api<{ run_id: string }>(
        `/simulations/${simulation.id}/launch`,
        {
          method: "POST",
          body: JSON.stringify({
            ...settings,
            name: name || null,
            acknowledge_outputs: acknowledge,
          }),
        },
      );
      done(result.run_id);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <form onSubmit={start} className="launch-form">
      <p>
        Launch <strong>{simulation.name}</strong> on this computer. Only run
        code and interpreters you trust.
      </p>
      <p className="muted">
        Source folder: <code>{simulation.root}</code>
        <br />
        Registered entry:{" "}
        <code>{simulation.entrypoint || "No entry file registered"}</code>
      </p>
      <fieldset disabled={busy}>
        <label>
          Registered entry file
          <input
            value={entry}
            placeholder="field.py"
            onChange={(e) => {
              setEntry(e.target.value);
              edited();
            }}
          />
          <small>
            Relative to the source folder. Updating this selection does not edit
            source or change the registered version file.
          </small>
        </label>
        <button
          type="button"
          disabled={!entry || entry === simulation.entrypoint}
          onClick={async () => {
            setBusy(true);
            setError("");
            setPlan(null);
            try {
              await api(`/simulations/${simulation.id}`, {
                method: "PATCH",
                body: JSON.stringify({ entrypoint: entry }),
              });
              saved();
              setNotice(
                "Registered entry updated. Validate execution settings before starting.",
              );
            } catch (e) {
              setError((e as Error).message);
            } finally {
              setBusy(false);
            }
          }}
        >
          Update registered entry
        </button>
        <label>
          Python interpreter
          <input
            required
            placeholder="/path/to/environment/bin/python"
            value={interpreter}
            onChange={(e) => {
              setInterpreter(e.target.value);
              edited();
            }}
          />
          <small>
            Choose the existing environment used by your simulation. Validation
            runs only its Python version check; no packages are installed.
          </small>
        </label>
        <div className="form-grid">
          <label>
            Working directory
            <input
              required
              value={cwd}
              onChange={(e) => {
                setCwd(e.target.value);
                edited();
              }}
            />
            <small>
              Relative to the source folder. A dot means the source folder
              itself.
            </small>
          </label>
          <label>
            Run name (optional)
            <input
              maxLength={160}
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Lower damping"
            />
          </label>
        </div>
        <label>
          Capture output folder
          <input
            required
            value={output}
            onChange={(e) => {
              setOutput(e.target.value);
              edited();
            }}
          />
          <small>
            Relative to the source folder. Point your script at the same folder
            using its arguments or SIMSHELF_OUTPUT_DIR. This does not redirect
            arbitrary file writes. Set copy/reference/ignore rules in File
            capture.
          </small>
        </label>
        <ArgumentEditor
          key={argumentRevision}
          initial={args}
          change={(next) => {
            setArgs(next);
            edited();
          }}
          pasteEditing={(pending) => {
            setPastePending(pending);
            edited();
          }}
        />
        <OutputPaths
          args={args}
          mappings={mappings}
          review={outputReview}
          error={outputError}
          change={(next) => {
            setMappings(next);
            edited();
          }}
          apply={(index, value) => {
            const mapping = mappings[index];
            if (mapping.argument_index === null) return;
            setArgs(
              args.map((arg, i) =>
                i === mapping.argument_index ? value : arg,
              ),
            );
            setMappings(
              mappings.map((item, i) =>
                i === index ? { ...item, value } : item,
              ),
            );
            setArgumentRevision(argumentRevision + 1);
            edited();
          }}
        />
        {argsError && (
          <p className="error-banner" role="alert">
            {argsError}
          </p>
        )}
        <h3>Command preview</h3>
        <pre className="log-block launch-preview" aria-label="Command preview">
          {formatCommand(preview)}
        </pre>
        <details>
          <summary>Exact argv</summary>
          <pre className="log-block launch-preview" aria-label="Exact argv">
            {JSON.stringify(preview, null, 2)}
          </pre>
        </details>
        <small>
          No shell is used: metacharacters and wildcards are passed literally to
          the script.
        </small>
        <div className="modal-actions">
          <button
            type="button"
            disabled={pastePending || !!argsError || !outputReview}
            onClick={() => validate(false)}
          >
            Validate interpreter & paths
          </button>
          <button
            type="button"
            disabled={pastePending || !!argsError || !outputReview}
            onClick={() => validate(true)}
          >
            Save settings
          </button>
        </div>
      </fieldset>
      {plan && (
        <div className="notice" role="status">
          Python {plan.validation.version} validated. {plan.validation.message}
          <p>
            Working directory: <code>{plan.cwd}</code>
            <br />
            Capture folder: <code>{plan.output_path}</code>
          </p>
        </div>
      )}
      {notice && <p role="status">{notice}</p>}
      {error && (
        <div className="error-banner" role="alert">
          {error}
        </div>
      )}
      <p className="muted">
        Start saves these settings and executes your script. Closing this tab
        leaves the run active. Stopping or restarting the SimShelf server
        requests cancellation. You can stop a portal run from its run details.
      </p>
      {outputReview?.requires_acknowledgement && (
        <label className="check-label">
          <input
            type="checkbox"
            checked={acknowledge}
            onChange={(e) => setAcknowledge(e.target.checked)}
          />
          Proceed with declared outputs outside capture coverage. I understand
          they may not be retained or backed up.
        </label>
      )}
      <div className="modal-actions">
        <button
          className="primary"
          disabled={
            busy ||
            !plan ||
            pastePending ||
            !!argsError ||
            !outputReview ||
            (outputReview.requires_acknowledgement && !acknowledge)
          }
        >
          {busy ? "Working…" : "Start simulation"}
        </button>
      </div>
    </form>
  );
}
