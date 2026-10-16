import React, { useState } from "react";
import {
  flattenArguments,
  groupArguments,
  parseArguments,
  type ArgumentRow,
} from "./arguments";

type Row = ArgumentRow & { id: number };
export function ArgumentEditor({
  initial,
  change,
  pasteEditing,
}: {
  initial: string[];
  change: (args: string[]) => void;
  pasteEditing: (pending: boolean) => void;
}) {
  const [nextId, setNextId] = useState(initial.length + 1);
  const [rows, setRows] = useState<Row[]>(() =>
    groupArguments(initial).map((row, id) => ({ ...row, id })),
  );
  const [paste, setPaste] = useState<string | null>(null);
  const count = flattenArguments(rows).length;
  let parsed: string[] = [],
    error = "";
  if (paste !== null) {
    try {
      parsed = parseArguments(paste);
    } catch (e) {
      error = (e as Error).message;
    }
  }
  function update(next: Row[]) {
    setRows(next);
    change(flattenArguments(next));
  }
  function edit(i: number, patch: Partial<ArgumentRow>) {
    update(rows.map((row, j) => (j === i ? { ...row, ...patch } : row)));
  }
  function add(paired: boolean) {
    update([...rows, { id: nextId, token: "", value: paired ? "" : null }]);
    setNextId(nextId + 1);
  }
  function move(i: number, offset: number) {
    const next = [...rows];
    [next[i], next[i + offset]] = [next[i + offset], next[i]];
    update(next);
  }
  return (
    <section className="argument-editor" aria-label="Runtime arguments">
      <h3>Runtime arguments</h3>
      <p className="muted">
        Pairs organize adjacent arguments without changing their order or text.
        Use Split or Pair with next for ambiguous options and positional
        arguments. Grouping is a view; only exact arguments are saved.
      </p>
      <p className="muted">
        Type values without shell quotes. Blank fields pass an empty argument;
        “No value” passes no extra argument.
      </p>
      {rows.map((row, i) => (
        <div className="argument-row" key={row.id}>
          <div className="argument-fields">
            <label>
              Parameter / argument {i + 1}
              <textarea
                rows={1}
                aria-label={`Parameter / argument ${i + 1}`}
                value={row.token}
                onChange={(e) => edit(i, { token: e.target.value })}
              />
              {row.token === "" && <small>Empty argument</small>}
            </label>
            <div className="argument-value">
              <span>Value</span>
              {row.value === null ? (
                <span className="argument-no-value">
                  No value{" "}
                  <button
                    type="button"
                    disabled={count >= 256}
                    onClick={() => edit(i, { value: "" })}
                  >
                    Add value
                  </button>
                </span>
              ) : (
                <>
                  <textarea
                    rows={1}
                    aria-label={`Value ${i + 1}`}
                    value={row.value}
                    onChange={(e) => edit(i, { value: e.target.value })}
                  />
                  {row.value === "" && <small>Empty argument</small>}
                </>
              )}
            </div>
          </div>
          <div className="argument-actions">
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
                    update([
                      ...rows.slice(0, i),
                      { ...row, value: null },
                      { id: nextId, token: row.value!, value: null },
                      ...rows.slice(i + 1),
                    ]);
                    setNextId(nextId + 1);
                  }}
                >
                  Split
                </button>
                <button type="button" onClick={() => edit(i, { value: null })}>
                  Remove value
                </button>
              </>
            ) : (
              <button
                type="button"
                disabled={i + 1 >= rows.length || rows[i + 1].value !== null}
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
              onClick={() => update(rows.filter((_, j) => j !== i))}
            >
              Remove row
            </button>
          </div>
        </div>
      ))}
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
                const next = groupArguments(parsed).map((row, i) => ({
                  ...row,
                  id: nextId + i,
                }));
                setNextId(nextId + next.length);
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
