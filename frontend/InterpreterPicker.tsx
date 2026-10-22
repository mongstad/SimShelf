import React, { useEffect, useRef, useState } from "react";
import { api } from "./api";

type Candidate = {
  path: string;
  sources: string[];
  kind: string;
  available: boolean;
  simshelf_runtime: boolean;
  state: string;
};
type Python = { version: string; prefix: string };
export function interpreterLabel(candidate: Candidate, version?: string) {
  const project = candidate.sources.find((source) =>
    source.startsWith("Project "),
  );
  const environment =
    candidate.kind === "Unclassified executable" || candidate.kind === "Unknown"
      ? "Python"
      : candidate.kind;
  const name = candidate.simshelf_runtime
    ? "SimShelf runtime"
    : project
      ? `${project} (${environment})`
      : environment;
  return [
    name,
    candidate.path,
    ...(candidate.sources.includes("Saved selection") ? ["Saved"] : []),
    version ? `Python ${version} · checked` : candidate.state,
  ].join(" · ");
}

type Dependencies = {
  python: Python;
  files: string[];
  requirements: {
    requirement: string;
    source: string;
    installed: string | null;
    status: string;
    note?: string;
  }[];
  warnings: string[];
  undeclared: boolean;
  message: string;
};
export function DependencyResults({ result }: { result: Dependencies }) {
  return (
    <div className="dependency-results" aria-label="Dependency check results">
      <p>
        <strong>Python {result.python.version}</strong> ·{" "}
        <code>{result.python.prefix}</code>
      </p>
      <p>{result.message}</p>
      {result.undeclared ? (
        <p>
          No supported declaration files found. Dependencies are undeclared; no
          package compatibility conclusion is possible.
        </p>
      ) : (
        <p>
          Declarations inspected: {result.files.join(", ")}. Optional extras and
          transitive dependencies are not resolved.
        </p>
      )}
      {!result.undeclared && result.requirements.length === 0 && (
        <p>
          No supported requirements could be assessed. This does not prove the
          script has no dependencies.
        </p>
      )}
      {result.requirements.map((row, i) => (
        <div className="dependency-row" key={i}>
          <strong>{row.requirement}</strong> — {row.status}
          <br />
          <small>
            {row.source} · Installed metadata:{" "}
            {row.installed || "not found / not assessed"}
            {row.note && ` · ${row.note}`}
          </small>
        </div>
      ))}
      {result.warnings.map((warning, i) => (
        <p key={i} className="text-amber">
          {warning}
        </p>
      ))}
    </div>
  );
}
export function InterpreterPicker({
  simulationId,
  value,
  change,
}: {
  simulationId: string;
  value: string;
  change: (value: string) => void;
}) {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [discoveryError, setDiscoveryError] = useState("");
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [python, setPython] = useState<Python | null>(null);
  const [dependencies, setDependencies] = useState<Dependencies | null>(null);
  const [checkedAt, setCheckedAt] = useState("");
  const sequence = useRef(0),
    input = useRef<HTMLInputElement>(null);
  async function rescan() {
    sequence.current++;
    setPython(null);
    setDependencies(null);
    setError("");
    setCheckedAt("");
    setBusy(false);
    change(value); // Preserve the selection, but invalidate prior launch validation.

    setLoading(true);
    setDiscoveryError("");
    try {
      const result = await api<{ candidates: Candidate[] }>(
        `/simulations/${simulationId}/interpreters`,
      );
      setCandidates(result.candidates);
    } catch (e) {
      setDiscoveryError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => {
    void rescan();
  }, [simulationId]);
  useEffect(() => {
    sequence.current++;
    setPython(null);
    setDependencies(null);
    setError("");
    setCheckedAt("");
    setBusy(false);
    return () => {
      sequence.current++;
    };
  }, [value]);
  async function check(deps: boolean) {
    const request = ++sequence.current;
    setBusy(true);
    setError("");
    setDependencies(null);
    setPython(null);
    setCheckedAt("");
    try {
      const result = await api<Python | Dependencies>(
        `/simulations/${simulationId}/${deps ? "dependencies" : "interpreter"}/check`,
        {
          method: "POST",
          body: JSON.stringify({ interpreter: value, confirmed: true }),
        },
      );
      if (request !== sequence.current) return;
      if (deps) {
        setDependencies(result as Dependencies);
        setPython((result as Dependencies).python);
      } else setPython(result as Python);
      setCheckedAt(new Date().toLocaleTimeString());
    } catch (e) {
      if (request === sequence.current) setError((e as Error).message);
    } finally {
      if (request === sequence.current) setBusy(false);
    }
  }
  const selected = candidates.find((c) => c.path === value);
  return (
    <section className="interpreter-picker" aria-label="Python environment">
      <h3>Python environment</h3>
      <div className="launch-setting">
      <label>
        Detected interpreters
        <select
          aria-label="Detected interpreters"
          value={selected ? value : value ? "custom" : ""}
          onChange={(e) => {
            if (e.target.value === "custom") {
              input.current?.focus();
            } else change(e.target.value);
          }}
        >
          <option value="">Choose an interpreter</option>
          {candidates.map((candidate) => (
            <option
              key={candidate.path}
              value={candidate.path}
              disabled={!candidate.available}
            >
              {interpreterLabel(
                candidate,
                candidate.path === value ? python?.version : undefined,
              )}
            </option>
          ))}
          <option value="custom">Enter custom path</option>
        </select>
      </label>
      <button type="button" onClick={() => void rescan()} disabled={loading}>
        {loading ? "Scanning paths…" : "Rescan interpreters"}
      </button>
      {discoveryError && (
        <p role="alert" className="error-banner">
          {discoveryError} Enter a custom path below.
        </p>
      )}
      {!loading && !candidates.length && (
        <p>
          No Python interpreters detected.
        </p>
      )}
      </div>
      <div className="launch-setting">
      <label>
        Python interpreter
        <input
          ref={input}
          required
          value={value}
          placeholder="/path/to/environment/bin/python"
          onChange={(e) => change(e.target.value)}
        />
      </label>
      {selected?.simshelf_runtime && (
        <p>
          {selected.simshelf_runtime && (
            <strong>
              This is SimShelf’s own runtime; it may not contain your
              simulation’s dependencies.
            </strong>
          )}
        </p>
      )}
      <details className="interpreter-checks">
        <summary>Check environment…</summary>
        <p className="execution-warning">These checks execute the selected Python. Only proceed if you trust it.</p>
      <div className="argument-actions">
        <button
          type="button"
          disabled={!value || busy}
          onClick={() => void check(false)}
        >
          Check selected Python
        </button>
        <button
          type="button"
          disabled={!value || busy}
          onClick={() => void check(true)}
        >
          Check dependencies
        </button>
      </div>
      </details>
      {busy && <p role="status">Checking Python…</p>}
      {error && (
        <p role="alert" className="error-banner">
          {error}
        </p>
      )}
      {python && (
        <p role="status">Python {python.version} · checked {checkedAt} (metadata only)</p>
      )}
      {dependencies && <DependencyResults result={dependencies} />}
      </div>
    </section>
  );
}
