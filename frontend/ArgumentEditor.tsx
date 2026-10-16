import React, { useState, useEffect, useRef } from "react";
import { parseArguments } from "./arguments";
import { api } from "./api";
import type { Discovery } from "./parameters";
import {
  parameterRows,
  rowArguments,
  parameterError,
  type Row,
} from "./parameterRows";

export function ArgumentEditor({
  initial,
  change,
  pasteEditing,
  simulationId,
  entry,
  validation,
}: {
  initial: string[];
  change: (args: string[]) => void;
  pasteEditing: (pending: boolean) => void;
  simulationId: string;
  entry: string;
  validation: (error: string) => void;
}) {
  const [rows, setRows] = useState<Row[]>(() => parameterRows(initial, []));
  const current = useRef(rows);
  current.current = rows;
  const [discovery, setDiscovery] = useState<Discovery | null>(null);
  const previous = useRef<Discovery | null>(null),
    request = useRef(0);
  const [loading, setLoading] = useState(false),
    [scanError, setScanError] = useState("");
  const [changed, setChanged] = useState(false),
    [paste, setPaste] = useState<string | null>(null);
  const problem = parameterError(rows, discovery?.parameters || []);
  useEffect(() => {
    validation(loading ? "Reading parameter declarations…" : problem);
  }, [problem, loading]);
  async function scan() {
    const id = ++request.current;
    setLoading(true);
    setScanError("");
    try {
      const next = await api<Discovery>(
        `/simulations/${simulationId}/parameters`,
      );
      if (id !== request.current) return;
      setChanged(
        previous.current !== null &&
          previous.current.fingerprint !== next.fingerprint,
      );
      previous.current = next;
      setDiscovery(next);
      setRows(
        parameterRows(
          rowArguments(current.current),
          next.parameters,
          current.current,
        ),
      );
    } catch (e) {
      if (id === request.current) setScanError((e as Error).message);
    } finally {
      if (id === request.current) setLoading(false);
    }
  }
  useEffect(() => {
    void scan();
    return () => {
      request.current++;
    };
  }, [simulationId, entry]);
  let parsed: string[] = [],
    error = "";
  if (paste !== null) {
    try {
      parsed = parseArguments(paste);
    } catch (e) {
      error = (e as Error).message;
    }
  }
  const count = rowArguments(rows).length;
  function update(next: Row[]) {
    setRows(next);
    change(rowArguments(next));
  }
  function edit(i: number, patch: Partial<Row>) {
    update(rows.map((r, j) => (j === i ? { ...r, ...patch } : r)));
  }
  function normalize() {
    setRows(
      parameterRows(
        rowArguments(current.current),
        discovery?.parameters || [],
        current.current,
      ),
    );
  }
  function add(paired: boolean) {
    update([
      ...rows,
      {
        id: Math.max(-1, ...rows.map((r) => r.id)) + 1,
        token: "",
        value: paired ? "" : null,
        enabled: true,
        equals: false,
        manual: "Manual argument",
      },
    ]);
  }
  function move(i: number, offset: number) {
    const next = [...rows];
    [next[i], next[i + offset]] = [next[i + offset], next[i]];
    update(next);
  }
  const unsupported =
    discovery?.parameters.filter(
      (p) => !p.supported && !rows.some((r) => r.parameter?.name === p.name),
    ) || [];
  return (
    <section className="argument-editor" aria-label="Simulation parameters">
      <div className="parameter-heading">
        <h3>Simulation parameters</h3>
        <button
          type="button"
          disabled={loading || paste !== null}
          onClick={() => void scan()}
        >
          {loading ? "Reading parameters…" : "Rescan parameters"}
        </button>
      </div>
      <p className="muted">
        Enable only the options you want to pass. Defaults are hints, never
        inserted. Manual rows retain exact argument order.
      </p>
      {scanError && (
        <p role="alert" className="error-banner">
          {scanError} Manual editing remains available.
        </p>
      )}
      {changed && (
        <p role="alert" className="text-amber">
          Declarations changed. Your arguments and disabled values were
          preserved; review them against the updated hints.
        </p>
      )}
      {discovery && (
        <details className="parameter-notes">
          <summary>Declaration source and limitations</summary>
          <p>
            {discovery.source}. Static inspection only; no script or --help
            execution.
          </p>
          {discovery.warnings.map((w, i) => (
            <p key={i}>{w}</p>
          ))}
          {unsupported.map((p, i) => (
            <p key={p.name + i}>
              {p.name}
              {p.required ? " (required)" : ""}: {p.reason}
            </p>
          ))}
        </details>
      )}
      {unsupported.length > 0 && (
        <p className="muted">
          Manual entry:{" "}
          {unsupported
            .map((p) => `${p.name}${p.required ? " (required)" : ""}`)
            .join(", ")}
          . See declaration notes for limitations.
        </p>
      )}
      {rows.map((row, i) => {
        const p =
          row.parameter?.supported && !row.manual ? row.parameter : undefined;
        const flag = p && p.action !== "store";
        return (
          <div className={p ? "parameter-row" : "argument-row"} key={row.id}>
            <div className="argument-fields">
              <div>
                {p ? (
                  <label className="check-label">
                    {(!p.required || flag) && (
                      <input
                        type="checkbox"
                        aria-label={`Enable ${p.name}`}
                        checked={row.enabled}
                        onChange={(e) => edit(i, { enabled: e.target.checked })}
                      />
                    )}
                    <strong>{row.token}</strong>
                    <small>{p.required ? "required" : "optional"}</small>
                  </label>
                ) : (
                  <label>
                    Parameter / argument {i + 1}
                    <textarea
                      rows={1}
                      aria-label={`Parameter / argument ${i + 1}`}
                      value={row.token}
                      onChange={(e) => edit(i, { token: e.target.value })}
                      onBlur={normalize}
                    />
                  </label>
                )}
              </div>
              <div className="argument-value">
                {flag ? (
                  <span className="muted">Flag · no value</span>
                ) : p ? (
                  <input
                    aria-label={`Value for ${p.name}`}
                    disabled={!p.required && !row.enabled}
                    value={row.value ?? ""}
                    placeholder={
                      p.default_known ? String(p.default ?? "") : "Enter value"
                    }
                    onChange={(e) =>
                      edit(i, { value: e.target.value, enabled: true })
                    }
                  />
                ) : row.value === null ? (
                  <span className="argument-no-value">
                    No value{" "}
                    <button
                      type="button"
                      onClick={() => edit(i, { value: "" })}
                    >
                      Add value
                    </button>
                  </span>
                ) : (
                  <textarea
                    rows={1}
                    aria-label={`Value ${i + 1}`}
                    value={row.value}
                    onChange={(e) => edit(i, { value: e.target.value })}
                  />
                )}
              </div>
            </div>
            {p ? (
              <small className="parameter-hint">
                {p.help}
                {p.help ? " · " : ""}
                {flag
                  ? p.action === "store_false"
                    ? "Sets false"
                    : "Sets true"
                  : p.type}{" "}
                · Default:{" "}
                {p.default_known ? JSON.stringify(p.default) : "unknown"}
                {p.choices
                  ? ` · Choices: ${p.choices.map(String).join(", ")}`
                  : ""}
              </small>
            ) : (
              <small>
                {row.manual || row.parameter?.reason || "Manual argument"}
              </small>
            )}
            {!p && (
              <div className="argument-actions">
                {!row.enabled && (
                  <label className="check-label">
                    <input
                      type="checkbox"
                      checked={false}
                      onChange={() => edit(i, { enabled: true })}
                    />
                    Enable preserved value
                  </label>
                )}
                <button
                  type="button"
                  aria-label={`Move row ${i + 1} up`}
                  disabled={i === 0}
                  onClick={() => move(i, -1)}
                >
                  ↑
                </button>
                <button
                  type="button"
                  aria-label={`Move row ${i + 1} down`}
                  disabled={i === rows.length - 1}
                  onClick={() => move(i, 1)}
                >
                  ↓
                </button>
                {row.value !== null ? (
                  <>
                    <button
                      type="button"
                      onClick={() => {
                        const tokens = rowArguments([row]);
                        if (tokens.length === 1) {
                          edit(i, {
                            token: tokens[0],
                            value: null,
                            equals: false,
                          });
                        } else
                          update([
                            ...rows.slice(0, i),
                            { ...row, value: null, equals: false },
                            {
                              ...row,
                              id: Math.max(...rows.map((r) => r.id)) + 1,
                              token: row.value!,
                              value: null,
                              equals: false,
                              parameter: undefined,
                            },
                            ...rows.slice(i + 1),
                          ]);
                      }}
                    >
                      Split
                    </button>
                    <button
                      type="button"
                      onClick={() => edit(i, { value: null, equals: false })}
                    >
                      Remove value
                    </button>
                  </>
                ) : (
                  <button
                    type="button"
                    disabled={
                      i + 1 >= rows.length ||
                      rows[i + 1].value !== null ||
                      !!rows[i + 1].parameter ||
                      !rows[i + 1].enabled
                    }
                    onClick={() =>
                      update([
                        ...rows.slice(0, i),
                        { ...row, value: rows[i + 1].token },
                        ...rows.slice(i + 2),
                      ])
                    }
                  >
                    Pair with next
                  </button>
                )}
                <button
                  type="button"
                  aria-label={`Remove row ${i + 1}`}
                  onClick={() =>
                    update(
                      parameterRows(
                        rowArguments(rows.filter((_, j) => j !== i)),
                        discovery?.parameters || [],
                        rows.filter((_, j) => j !== i),
                      ),
                    )
                  }
                >
                  Remove row
                </button>
              </div>
            )}
          </div>
        );
      })}
      {problem && (
        <p className="error-banner" role="alert">
          {problem}
        </p>
      )}
      <div className="argument-actions">
        <button type="button" disabled={count > 254} onClick={() => add(true)}>
          Add parameter + value
        </button>
        <button
          type="button"
          disabled={count >= 256}
          onClick={() => add(false)}
        >
          Add flag / positional
        </button>
        <button
          type="button"
          disabled={paste !== null}
          onClick={() => {
            setPaste("");
            pasteEditing(true);
          }}
        >
          Paste arguments
        </button>
      </div>
      {paste !== null && (
        <div className="argument-paste">
          <label>
            Arguments to paste
            <textarea
              rows={4}
              value={paste}
              onChange={(e) => setPaste(e.target.value)}
              placeholder="--particles 50000 --headless"
            />
          </label>
          <p className="muted">
            Arguments only, without Python or the script name. Single/double
            quotes and backslashes group text. No variable, wildcard or command
            expansion; metacharacters remain literal. Apply replaces all current
            arguments.
          </p>
          {error ? (
            <p className="error-banner" role="alert">
              {error}
            </p>
          ) : (
            <>
              <p>{parsed.length} arguments to import</p>
              <pre
                className="log-block launch-preview"
                aria-label="Paste token preview"
              >
                {JSON.stringify(parsed, null, 2)}
              </pre>
            </>
          )}
          <div className="argument-actions">
            <button
              type="button"
              disabled={!!error}
              onClick={() => {
                const next = parameterRows(parsed, discovery?.parameters || []);
                update(next);
                setPaste(null);
                pasteEditing(false);
              }}
            >
              Replace arguments
            </button>
            <button
              type="button"
              onClick={() => {
                setPaste(null);
                pasteEditing(false);
              }}
            >
              Cancel paste
            </button>
          </div>
          <p role="status">
            Apply or cancel the paste before validating or starting.
          </p>
        </div>
      )}
    </section>
  );
}
