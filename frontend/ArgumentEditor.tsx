import React, { useState, useEffect, useRef, useId } from "react";
import { parseArguments } from "./arguments";
import { api } from "./api";
import type { Discovery } from "./parameters";
import { ParameterHint } from "./ParameterHint";
import { parameterPresentation } from "./parameterPresentation";
import {
  manualValue,
  parameterRows,
  rowArguments,
  parameterError,
  missingRequiredRows,
  type Row,
} from "./parameterRows";

export function ArgumentEditor({
  initial,
  change,
  pasteEditing,
  simulationId,
  entry,
  validation,
  reviewed,
  discovered,
  initialManual = false,
  validationAttempt = 0,
}: {
  initial: string[];
  validationAttempt?: number;
  initialManual?: boolean;
  change: (args: string[]) => void;
  pasteEditing: (pending: boolean) => void;
  simulationId: string;
  entry: string;
  validation: (error: string) => void;
  reviewed: (review: {mode: string; fingerprint: string | null}) => void;
  discovered?: (discovery: Discovery | null) => void;
}) {
  const [rows, setRows] = useState<Row[]>(() => parameterRows(initial, []));
  const [query, setQuery] = useState("");
  const searchInput = useRef<HTMLInputElement>(null);
  const editorId = useId();
  const presentation = parameterPresentation(rows, query);
  const editor = useRef<HTMLElement>(null);
  const focusMissing = useRef(false);
  const [attempted, setAttempted] = useState(false);
  const current = useRef(rows);
  current.current = rows;
  const [discovery, setDiscovery] = useState<Discovery | null>(null);
  const previous = useRef<Discovery | null>(null),
    request = useRef(0);
  const [loading, setLoading] = useState(false),
    [scanError, setScanError] = useState("");
  const [changed, setChanged] = useState(false),
    [paste, setPaste] = useState<string | null>(null);
  const [manual, setManual] = useState(initialManual);
  const missing = manual ? [] : missingRequiredRows(rows);
  useEffect(() => {
    if (!validationAttempt || !missing.length) return;
    focusMissing.current = true;
    setAttempted(true);
    // Reveal filtered omissions before moving focus; changing visibility never edits argv.
    setQuery("");
  }, [validationAttempt]);
  useEffect(() => {
    if (!focusMissing.current || !attempted || query) return;
    focusMissing.current = false;
    editor.current?.querySelector<HTMLElement>('[data-missing="true"] input, [data-missing="true"] select')?.focus();
  }, [validationAttempt, attempted, query]);
  const problem = manual ? "" : discovery && !discovery.provenance ? "Choose manual argv or provide valid SWSS declarations before continuing." : parameterError(rows, discovery?.parameters || []);
  useEffect(() => {
    validation(loading ? "Reading parameter declarations…" : changed && !manual ? "Review changed declarations before typed use." : problem);
    reviewed({mode: manual || !discovery?.provenance ? "manual" : "typed", fingerprint: discovery?.fingerprint || null});
  }, [problem, loading, changed, manual, discovery]);
  async function scan() {
    const id = ++request.current;
    setLoading(true);
    discovered?.(null);
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
      discovered?.(next);
      setRows(
        parameterRows(
          rowArguments(current.current),
          manual ? [] : next.parameters,
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
        manual ? [] : discovery?.parameters || [],
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
        value: null,
        valueOpen: paired,
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
    <section ref={editor} className="argument-editor" aria-label="Simulation parameters">
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
      <label className="check-label">Use manual argv (skip metadata validation)<input type="checkbox" checked={manual} onChange={e => {
        setManual(e.target.checked);
        setRows(parameterRows(rowArguments(current.current), e.target.checked ? [] : discovery?.parameters || [], current.current));
      }} /></label>
      {discovery && !discovery.provenance && <p role="status" className="text-amber">{discovery.warnings[0]}</p>}
      {discovery?.provenance && <p role="status">{discovery.provenance.binding_status}</p>}
      {changed && !manual && <button type="button" onClick={() => setChanged(false)}>I reviewed the changed declarations</button>}
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
            {discovery.source}. Data-only inspection; no script or --help
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
      {presentation.total > 0 && (
        <div className="parameter-search">
          <label htmlFor={`${editorId}-search`}>Search parameters and flags</label>
          <div className="parameter-search-controls">
            <input id={`${editorId}-search`} ref={searchInput} type="search"
              value={query} onChange={e => setQuery(e.target.value)}
              placeholder="Option, alias, help or type"
              aria-describedby={`${editorId}-search-status`} />
            <button type="button" disabled={!query} onClick={() => {
              setQuery(""); searchInput.current?.focus();
            }}>Clear search</button>
          </div>
          <p id={`${editorId}-search-status`} role="status" className="muted">
            {presentation.matches} of {presentation.total} declared controls shown.
            {" "}Search only changes visibility; arguments and edits are retained. Manual arguments remain below.
          </p>
          {presentation.matches === 0 && <p>No matching parameters or flags. Try another term or clear search.</p>}
        </div>
      )}
      <fieldset disabled={changed && !manual}>
      {presentation.sections.map(({name: group, rows: visibleRows}) => (
        <section className="parameter-group" aria-label={group} key={group}>
          <h4>{group} <small>({visibleRows.length})</small></h4>
          {!visibleRows.length && <p className="muted">No manual arguments added.</p>}
          {visibleRows.map(({row, index: i}) => {
            const p =
              row.parameter?.supported && !row.manual
                ? row.parameter
                : undefined;
            const flag = p && p.action !== "store";
            const invalid = attempted && missing.includes(row.id);
            const description = `${editorId}-hint-${row.id}${invalid ? ` ${editorId}-error-${row.id}` : ""}`;
            return (
              <div
                className={p ? "parameter-row" : "argument-row"}
                data-missing={invalid || undefined}
                data-value-kind={p ? flag ? "flag" : p.type === "str" && !p.choices ? "long" : "compact" : undefined}
                data-enabled={p ? row.enabled : undefined}
                role={p ? "group" : undefined}
                aria-label={p ? `${p.name} · ${p.required ? "required" : "optional"}` : undefined}
                key={row.id}
              >
                <div className="argument-fields">
                  <div>
                    {p ? (
                      <label className="check-label">
                        {(!p.required || flag) && (
                          <input
                            type="checkbox"
                            aria-label={`Enable ${p.name}`}
                            aria-describedby={description}
                            aria-invalid={invalid || undefined}
                            checked={row.enabled}
                            onChange={(e) =>
                              edit(i, { enabled: e.target.checked })
                            }
                          />
                        )}
                        <span className="parameter-name"><strong>{row.token}</strong>{" "}
                        {!flag && <span className="parameter-type">({p.type === "int" ? "integer" : p.type === "str" ? "string" : p.type})</span>}
                        {p.required && <span className="parameter-required" role="img" aria-label="Required" title="Required">*</span>}</span>
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
                      null
                    ) : p ? (
                      <label>
                        {p.choices ? (
                          <select
                            aria-label={`Value for ${p.name}`}
                            aria-describedby={description}
                            aria-invalid={invalid || undefined}
                            disabled={!p.required && !row.enabled}
                            value={
                              row.value === null
                                ? "unset"
                                : p.choices.findIndex(
                                      (c) => String(c) === row.value,
                                    ) < 0
                                  ? "current"
                                  : String(
                                      p.choices.findIndex(
                                        (c) => String(c) === row.value,
                                      ),
                                    )
                            }
                            onChange={(e) =>
                              edit(i, {
                                value: String(
                                  p.choices![Number(e.target.value)],
                                ),
                                enabled: true,
                              })
                            }
                          >
                            <option value="unset" disabled>
                              Choose a value
                            </option>
                            {row.value !== null &&
                              !p.choices.some(
                                (c) => String(c) === row.value,
                              ) && (
                                <option value="current">
                                  {row.value} (current)
                                </option>
                              )}
                            {p.choices.map((choice, index) => (
                              <option key={index} value={String(index)}>
                                {String(choice) || "Empty string"}
                              </option>
                            ))}
                          </select>
                        ) : (
                          <input
                            aria-label={`Value for ${p.name}`}
                            aria-describedby={description}
                            aria-invalid={invalid || undefined}
                            inputMode={
                              p.type === "int"
                                ? "numeric"
                                : p.type === "float"
                                  ? "decimal"
                                  : "text"
                            }
                            disabled={!p.required && !row.enabled}
                            value={row.value ?? ""}
                            placeholder={
                              p.default_known
                                ? String(p.default ?? "")
                                : "Enter value"
                            }
                            onChange={(e) =>
                              edit(i, { value: e.target.value, enabled: true })
                            }
                          />
                        )}
                      </label>
                    ) : (
                      <>
                        <label>
                          Optional value
                          {row.value === null && !row.valueOpen ? (
                            <span className="argument-no-value">
                              No value{" "}
                              <button
                                type="button"
                                aria-label={`Add value to argument ${i + 1}`}
                                onClick={() => edit(i, { valueOpen: true })}
                              >
                                Add value
                              </button>
                            </span>
                          ) : (
                            <textarea
                              rows={1}
                              aria-label={`Value ${i + 1}`}
                              value={row.value ?? ""}
                              placeholder={
                                row.value === ""
                                  ? "Explicit empty string"
                                  : "Blank: pass only the argument"
                              }
                              onChange={(e) =>
                                edit(i, manualValue(e.target.value))
                              }
                            />
                          )}
                        </label>
                        <label className="check-label argument-empty">
                          <input
                            type="checkbox"
                            checked={row.value === ""}
                            onChange={(e) =>
                              edit(i, {
                                value: e.target.checked ? "" : null,
                                valueOpen: true,
                              })
                            }
                          />
                          Pass empty string
                        </label>
                      </>
                    )}
                  </div>
                </div>
                {invalid && <small className="parameter-error" id={`${editorId}-error-${row.id}`} role="alert">
                  {flag ? "Enable required flag." : "Enter required value."}
                </small>}
                {p ? (
                  <ParameterHint parameter={p} token={row.token} value={row.value} enabled={row.enabled} id={`${editorId}-hint-${row.id}`} />
                ) : row.manual && row.manual !== "Manual argument; original tokens preserved." ? (
                  <small>{row.manual}</small>
                ) : row.parameter?.reason ? (
                  <small>{row.parameter.reason}</small>
                ) : null}
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
                    {row.value !== null || row.valueOpen ? (
                      <>
                        <button
                          type="button"
                          disabled={row.value === null}
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
                          onClick={() =>
                            edit(i, {
                              value: null,
                              equals: false,
                              valueOpen: false,
                            })
                          }
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
                            manual ? [] : discovery?.parameters || [],
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
        </section>
      ))}
      </fieldset>
      {problem && !(missing.length > 0) && (
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
            Paste arguments only. Quotes and backslashes group text; no shell expansion. Apply replaces all current arguments.
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
                const next = parameterRows(parsed, manual ? [] : discovery?.parameters || []);
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
