import React, { useEffect, useRef, useState } from "react";
import { api } from "./api";

export function ProgressSettings({
  value,
  change,
}: {
  value: string;
  change: (value: string) => void;
}) {
  const [schema, setSchema] = useState<number | null>(null);
  const [review, setReview] = useState(false);
  const [consent, setConsent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const cancel = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    api<{ schema_version: number }>("/workspace")
      .then((w) => setSchema(w.schema_version))
      .catch((e) => setError(e.message));
  }, []);
  useEffect(() => {
    if (review) cancel.current?.focus();
  }, [review]);
  return (
    <details className="progress-settings">
      <summary>Progress reporting (optional)</summary>
      <p>
        Use the simulation’s progress API, or explicitly interpret a supported
        text format. Ordinary logs and parameters are never treated as progress
        automatically.
      </p>
      {schema !== null && schema < 4 && !review && (
        <button type="button" onClick={() => setReview(true)}>
          Enable progress reporting…
        </button>
      )}
      {review && schema !== 4 && (
        <div role="group" aria-label="Enable progress reporting confirmation">
          <p>
            <strong>Enable progress reporting for this library?</strong>
          </p>
          <p>
            This upgrades the library to schema 4. Older SimShelf versions will
            no longer open it. This cannot be undone in place.
          </p>
          <p>
            First back up the library and verify restoring it to a separate
            folder. External reference files are not included in backups. Stop
            all runs and older servers/recorders using this library.
          </p>
          <label>
            <input
              type="checkbox"
              checked={consent}
              onChange={(e) => setConsent(e.target.checked)}
            />
            I have verified a backup and stopped older servers/recorders.
          </label>
          <div className="modal-actions">
            <button
              ref={cancel}
              type="button"
              disabled={busy}
              onClick={() => {
                setReview(false);
                setConsent(false);
              }}
            >
              Cancel
            </button>
            <button
              type="button"
              disabled={!consent || busy}
              onClick={async () => {
                setBusy(true);
                setError("");
                try {
                  const result = await api<{ schema_version: number }>(
                    "/workspace/progress/enable",
                    {
                      method: "POST",
                      body: JSON.stringify({ confirmed: true }),
                    },
                  );
                  setSchema(result.schema_version);
                  setReview(false);
                  setConsent(false);
                } catch (e) {
                  setError((e as Error).message);
                } finally {
                  setBusy(false);
                }
              }}
            >
              {busy
                ? "Enabling…"
                : "Enable progress reporting for this library"}
            </button>
          </div>
        </div>
      )}
      {schema === 4 && (
        <p className="muted">
          Progress reporting is enabled for this library. Structured API reports
          take priority over interpreted text.
        </p>
      )}
      <label>
        Interpret terminal progress
        <select
          value={value}
          disabled={schema !== 4}
          onChange={(e) => change(e.target.value)}
        >
          <option value="off">Off</option>
          <option value="step">Step counts: step 10/100</option>
          <option value="percent">Percentage: 25%</option>
        </select>
        <small>
          Matches complete lines on stdout/stderr, including carriage-return
          updates. No custom regex or ETA. The selected format is saved for
          future launches.
        </small>
      </label>
      {error && (
        <p role="alert" className="error-banner">
          {error}
        </p>
      )}
    </details>
  );
}
