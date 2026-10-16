import React, { useEffect, useRef, useState } from "react";
import { api } from "./api";
import { appendOverrides, present, type Discovery } from "./parameters";

export function DiscoveredParameters({
  simulationId,
  entry,
  args,
  blocked,
  apply,
  pending,
}: {
  simulationId: string;
  entry: string;
  args: string[];
  blocked: boolean;
  apply: (args: string[]) => void;
  pending: (value: boolean) => void;
}) {
  const [result, setResult] = useState<Discovery | null>(null);
  const [drafts, setDrafts] = useState<
    Record<string, { enabled: boolean; value: string }>
  >({});
  const [error, setError] = useState("");
  const [changed, setChanged] = useState(false);
  const [loading, setLoading] = useState(false);
  const previous = useRef<Discovery | null>(null);
  const request = useRef(0);
  const hasPending = Object.values(drafts).some((d) => d.enabled);
  useEffect(() => {
    pending(hasPending);
  }, [hasPending]);
  async function scan() {
    const id = ++request.current;
    setLoading(true);
    setError("");
    try {
      const next = await api<Discovery>(
        `/simulations/${simulationId}/parameters`,
      );
      if (id !== request.current) return;
      const differs =
        previous.current !== null &&
        previous.current.fingerprint !== next.fingerprint;
      setChanged(differs);
      setResult(next);
      previous.current = next;
      // Keep drafts for review, including options that disappeared. Never change argv.
    } catch (e) {
      if (id === request.current) setError((e as Error).message);
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
  return (
    <section
      className="discovered-parameters"
      aria-label="Discovered parameters"
    >
      <h3>Discovered parameters</h3>
      <p className="muted">
        Static declarations only; no script or --help command is executed.
        Declared defaults are informational, not resolved scientific values.
        Unselected options add nothing.
      </p>
      <button type="button" disabled={loading} onClick={() => void scan()}>
        {loading ? "Reading declarations…" : "Rescan parameters"}
      </button>
      {result && (
        <p>
          <small>
            Source: {result.source}. Existing runtime arguments remain
            authoritative; unknown, repeated and positional arguments are kept
            in the editor below.
          </small>
        </p>
      )}
      {result?.warnings.map((w, i) => (
        <p className="text-amber" key={i}>
          {w}
        </p>
      ))}
      {changed && (
        <p role="alert" className="text-amber">
          Declarations changed. Runtime arguments and drafts were preserved.
          Review saved options and defaults against the new declarations before
          applying.
        </p>
      )}
      {result?.parameters.length === 0 && (
        <p>
          No supported parameter list found. Use the manual argument editor or
          provide a project schema.
        </p>
      )}
      {result?.parameters.map((p, i) => {
        const draft = drafts[p.name] || { enabled: false, value: "" };
        const exists = present(args, p);
        const update = (patch: Partial<typeof draft>) =>
          setDrafts({ ...drafts, [p.name]: { ...draft, ...patch } });
        return (
          <div className="parameter-card" key={p.name + i}>
            <label className="check-label">
              <input
                type="checkbox"
                aria-label={`Override ${p.name}`}
                checked={draft.enabled}
                disabled={!p.supported || exists || blocked}
                onChange={(e) => update({ enabled: e.target.checked })}
              />
              <strong>{p.name}</strong>
              {p.required ? " · required" : " · optional"}
            </label>
            <p>{p.help || "No description declared."}</p>
            <small>
              {p.flags.join(", ")} · {p.action === "store" ? p.type : p.action}{" "}
              · Declared default:{" "}
              {p.default_known ? JSON.stringify(p.default) : "unknown"} ·{" "}
              {p.source}
            </small>
            {p.choices && (
              <p>
                <small>Choices: {p.choices.map(String).join(", ")}</small>
              </p>
            )}
            {!p.supported && <p className="text-amber">{p.reason}</p>}
            {exists && (
              <p>
                Already in runtime arguments. Edit or remove it in the manual
                editor below.
              </p>
            )}
            {p.supported && p.action === "store" && (
              <label>
                Override value for {p.name}
                <input
                  aria-label={`Value for ${p.name}`}
                  disabled={!draft.enabled || exists || blocked}
                  value={draft.value}
                  placeholder={
                    p.default_known
                      ? String(p.default ?? "")
                      : "Unknown default"
                  }
                  onChange={(e) => update({ value: e.target.value })}
                />
              </label>
            )}
          </div>
        );
      })}
      {Object.keys(drafts)
        .filter(
          (name) =>
            drafts[name].enabled &&
            !result?.parameters.some((p) => p.name === name),
        )
        .map((name) => (
          <p className="text-amber" key={name}>
            Pending {name} is no longer declared. Draft preserved:{" "}
            {JSON.stringify(drafts[name].value)}. Clear pending overrides and
            use the manual editor.
          </p>
        ))}
      {error && (
        <p role="alert" className="error-banner">
          {error}
        </p>
      )}
      <div className="argument-actions">
        <button
          type="button"
          disabled={!hasPending || blocked || loading || !result}
          onClick={() => {
            try {
              const names = Object.keys(drafts).filter(
                (n) => drafts[n].enabled,
              );
              if (
                names.some((n) => !result?.parameters.some((p) => p.name === n))
              )
                throw Error(
                  "A pending option disappeared; review or clear pending overrides.",
                );
              const selected = names.map((n) => ({
                parameter: result!.parameters.find((p) => p.name === n)!,
                value: drafts[n].value,
              }));
              apply(appendOverrides(args, selected));
              setDrafts({});
              setError("");
              setChanged(false);
            } catch (e) {
              setError((e as Error).message);
            }
          }}
        >
          Add selected overrides to arguments
        </button>
        <button
          type="button"
          disabled={!hasPending}
          onClick={() => {
            setDrafts({});
            setError("");
          }}
        >
          Clear pending overrides
        </button>
      </div>
      <small>
        Review Exact argv after adding. Added options belong to the manual
        editor and are saved with execution settings. Pending overrides must be
        added or cleared before saving or launching.
      </small>
    </section>
  );
}
