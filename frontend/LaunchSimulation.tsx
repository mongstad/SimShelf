import React, { useState } from "react";
import { api } from "./api";
import type { Simulation } from "./types";

type Plan = {
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
  const [output, setOutput] = useState(
    initial?.output_dir || simulation.config.output_dir,
  );
  const [name, setName] = useState("");
  const [plan, setPlan] = useState<Plan | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const settings = { interpreter, cwd, arguments: args, output_dir: output };
  function edited() {
    setPlan(null);
    setNotice("");
  }
  async function validate(save: boolean) {
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
    if (!plan || busy) return;
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
          body: JSON.stringify({ ...settings, name: name || null }),
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
        <h3>Runtime arguments</h3>
        <p className="muted">
          One field is one argument. For example, add <code>--seed</code> and{" "}
          <code>42</code> as two fields. Spaces stay inside a field; do not add
          shell quotes. Empty fields pass an empty argument.
        </p>
        {args.map((arg, i) => (
          <div className="argument-row" key={i}>
            <input
              aria-label={`Argument ${i + 1}`}
              value={arg}
              onChange={(e) => {
                setArgs(args.map((a, j) => (j === i ? e.target.value : a)));
                edited();
              }}
            />
            <button
              type="button"
              aria-label={`Remove argument ${i + 1}`}
              onClick={() => {
                setArgs(args.filter((_, j) => j !== i));
                edited();
              }}
            >
              Remove
            </button>
          </div>
        ))}
        <button
          type="button"
          onClick={() => {
            setArgs([...args, ""]);
            edited();
          }}
          disabled={args.length >= 256}
        >
          Add argument
        </button>
        <h3>Command preview · separate arguments</h3>
        <pre className="log-block launch-preview">
          {JSON.stringify(
            plan?.command || [
              interpreter || "(select Python)",
              `${simulation.root}/${simulation.entrypoint || "(entry file)"}`,
              ...args,
            ],
            null,
            2,
          )}
        </pre>
        <small>
          No shell is used: metacharacters and wildcards are passed literally to
          the script.
        </small>
        <div className="modal-actions">
          <button type="button" onClick={() => validate(false)}>
            Validate interpreter & paths
          </button>
          <button type="button" onClick={() => validate(true)}>
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
      <div className="modal-actions">
        <button className="primary" disabled={busy || !plan}>
          {busy ? "Working…" : "Start simulation"}
        </button>
      </div>
    </form>
  );
}
