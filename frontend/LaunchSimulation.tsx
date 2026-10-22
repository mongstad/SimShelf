import { ProgressSettings } from "./ProgressSettings";
import React, { useState, useEffect } from "react";
import { ArgumentEditor } from "./ArgumentEditor";
import { argumentError, formatCommand } from "./arguments";
import { api } from "./api";
import { InterpreterPicker } from "./InterpreterPicker";
import { OutputPaths } from "./OutputPaths";
import { incompleteOutputMappings } from "./outputCandidates";
import type { Simulation, OutputMapping, OutputReview } from "./types";
import type { OutputPolicyStatus } from "./parameters";

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
  const [parameterReview, setParameterReview] = useState<{mode: string; fingerprint: string | null} | null>(null);
  const [validationAttempt, setValidationAttempt] = useState(0);
  const [parameterError, setParameterError] = useState("");
  const argsError = argumentError(args);
  const preview = [
    interpreter || "(select Python)",
    `${simulation.root}/${entry || "(entry file)"}`,
    ...args,
  ];
  const [output, setOutput] = useState(
    initial?.output_dir || simulation.config.output_dir,
  );
  const [outputPolicy, setOutputPolicy] = useState(initial?.output_policy || "fixed");
  const [policyStatus, setPolicyStatus] = useState<OutputPolicyStatus | null>(null);
  const policyBlocked = !policyStatus || (outputPolicy === "per_run" && !policyStatus.launcher_allowed);
  const [mappings, setMappings] = useState<OutputMapping[]>(
    initial?.output_mappings || [],
  );
  const [outputReview, setOutputReview] = useState<OutputReview | null>(null);
  const [outputError, setOutputError] = useState("");
  const [captureResult, setCaptureResult] = useState<{
    request: string; review: OutputReview | null; error: string;
  } | null>(null);
  // Resolve the capture folder independently: an unfinished declaration does
  // not invalidate it. Key results to current inputs, never display stale paths.
  const captureRequest = JSON.stringify({
    cwd, arguments: [], output_dir: output, output_policy: outputPolicy,
    output_mappings: [],
  });
  const captureKey = simulation.id + captureRequest;
  const capture = captureResult?.request === captureKey ? captureResult : null;
  useEffect(() => {
    let active = true;
    const timer = setTimeout(() => {
      api<OutputReview>(`/simulations/${simulation.id}/execution/outputs`, {
        method: "POST", body: captureRequest,
      }).then(review => {
        if (active) setCaptureResult({ request: captureKey, review, error: "" });
      }).catch((e: Error) => {
        if (active) setCaptureResult({ request: captureKey, review: null, error: e.message });
      });
    }, 250);
    return () => { active = false; clearTimeout(timer); };
  }, [captureRequest, simulation.id]);
  const [acknowledge, setAcknowledge] = useState(false);
  const [argumentRevision, setArgumentRevision] = useState(0);
  const outputRequest = JSON.stringify({
    cwd,
    arguments: args,
    output_dir: output,
    output_policy: outputPolicy,
    output_mappings: mappings,
  });
  useEffect(() => {
    let active = true;
    setOutputReview(null);
    setOutputError("");
    if (incompleteOutputMappings(mappings).length) return;
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
  const [progressMode, setProgressMode] = useState(initial?.progress_mode || "off");
  const [name, setName] = useState("");
  const [plan, setPlan] = useState<Plan | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const settings = {
    parameter_review: parameterReview,
    progress_mode: progressMode,
    interpreter,
    cwd,
    arguments: args,
    output_dir: output,
    output_policy: outputPolicy,
    output_mappings: mappings,
  };
  function edited() {
    setPlan(null);
    setAcknowledge(false);
    setNotice("");
  }
  async function validate(save: boolean) {
    setValidationAttempt(n => n + 1);
    if (policyBlocked || pastePending || !!parameterError || argsError) return;
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
    setValidationAttempt(n => n + 1);
    if (
      !plan ||
      policyBlocked ||
      busy ||
      pastePending ||
      !!parameterError ||
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
        <ProgressSettings value={progressMode} change={value => {setProgressMode(value);edited();}} />
        <div className="launch-setting">
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
            Relative to source folder.
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
        </div>
        <InterpreterPicker
          simulationId={simulation.id}
          value={interpreter}
          change={(next) => {
            setInterpreter(next);
            edited();
          }}
        />
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
              Relative to source folder (<code>.</code> = source folder).
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
        <section className="launch-output" aria-label="Capture settings">
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
            Relative to source folder. Your script must write here; capture does not redirect writes.
          </small>
        </label>
        <label>
          Output folder policy
          <select value={outputPolicy} disabled={!policyStatus} aria-describedby="output-policy-help" onChange={(e) => {
            setOutputPolicy(e.target.value as "fixed" | "per_run");
            edited();
          }}>
            <option value="fixed">{policyStatus?.state === "valid" ? "Fixed output parent — simulation creates its unique run directory" : "Fixed output parent"}</option>
            <option value="per_run" disabled={!policyStatus?.launcher_allowed}>Launcher-coordinated subfolder (requires support)</option>
          </select>
          <small id="output-policy-help">
            {policyStatus?.reason || "Checking SWSS metadata for output policy. If this fails, rescan the declarations below before continuing."}
            {policyStatus?.state === "valid" && " Recommended: fixed output parent. Shared-parent overlap safeguards still apply."}
            {" "}Arguments and script writes are never redirected automatically.
          </small>
        </label>
        {policyStatus && policyStatus.state !== "absent" && <div className="notice output-policy-notice" role="status">
          <strong>{policyStatus.state === "valid" ? "SWSS schema 2 · metadata valid" : "SWSS metadata unavailable for use"}</strong>
          <p>Source binding: {policyStatus.binding === "binding unverified" ? "unverified" : policyStatus.binding}.</p>
          <small>Metadata and listed-byte checks do not verify scientific behavior or full SWSS conformance.</small>
        </div>}
        {policyStatus && policyBlocked && <div className="notice output-policy-notice" role="alert">
          <p>The selected launcher-coordinated policy is unavailable. Saved settings have not changed. Review the capture parent and use fixed output before validating or launching.</p>
          <button type="button" onClick={() => {setOutputPolicy("fixed"); edited();}}>Use fixed output parent</button>
        </div>}
        </section>
        <ArgumentEditor
          discovered={discovery => {setPolicyStatus(discovery?.output_policy || null); setPlan(null);}}
          validationAttempt={validationAttempt}
          initialManual={initial?.parameter_review?.mode === "manual"}
          reviewed={review => {setParameterReview(review); setPlan(null);}}
          key={argumentRevision}
          initial={args}
          simulationId={simulation.id}
          entry={simulation.entrypoint || ""}
          validation={(error) => {
            setParameterError(error);
            if (error) edited();
          }}
          change={(next) => {
            setArgs(next);
            edited();
          }}
          pasteEditing={(pending) => {
            setPastePending(pending);
            edited();
          }}
        />
        {!policyBlocked && <OutputPaths
          args={args}
          mappings={mappings}
          review={outputReview}
          captureReview={capture?.review || null}
          captureError={capture?.error || ""}
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
        />}
        {argsError && (
          <p className="error-banner" role="alert">
            {argsError}
          </p>
        )}
        <section className="launch-command" aria-label="Command review">
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
          No shell: metacharacters and wildcards are literal.
        </small>
        <div className="modal-actions">
          <button
            type="button"
            disabled={
              policyBlocked || pastePending || !!argsError || !outputReview
            }
            onClick={() => validate(false)}
          >
            Validate interpreter & paths
          </button>
          <button
            type="button"
            disabled={
              policyBlocked || pastePending || !!argsError || !outputReview
            }
            onClick={() => validate(true)}
          >
            Save settings
          </button>
        </div>
        </section>
      </fieldset>
      {plan && (
        <div className="notice" role="status">
          Python {plan.validation.version} validated. {plan.validation.message}
          <p>
            Working directory: <code>{plan.cwd}</code>
            <br />
            {outputPolicy === "per_run" ? "Capture parent" : "Capture folder"}: <code>{plan.output_path}</code>
            {outputPolicy === "per_run" && <><br />A new run_&lt;unique ID&gt; subfolder is allocated when you start. The exact path appears in the run record.</>}
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
        Start saves settings and runs your script. Closing this tab leaves it running;
        stopping the server requests cancellation. Stop a run from its details.
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
            policyBlocked ||
            (!plan && !parameterError) ||
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
