import React, { useEffect, useRef, useState } from "react";
import { api } from "./api";

type Review = {
  simulation_id: string;
  name: string;
  revision: string;
  active: boolean;
  counts: Record<string, number>;
};
export type SimulationRemovalResult = {
  simulation_id: string;
  already_removed: boolean;
  cleanup_errors: string[];
};
export function RemoveSimulation({
  id,
  close,
  removed,
}: {
  id: string;
  close: () => void;
  removed: (result: SimulationRemovalResult) => void;
}) {
  const [review, setReview] = useState<Review | null>(null);
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const submitting = useRef(false);
  const cancel = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    let live = true;
    const timer = setTimeout(() => cancel.current?.focus(), 0);
    api<Review>(`/simulations/${encodeURIComponent(id)}/removal-preview`)
      .then((r) => {
        if (live) setReview(r);
      })
      .catch((e) => {
        if (live) setError(e.message);
      });
    return () => {
      live = false;
      clearTimeout(timer);
    };
  }, [id]);
  const eligible = !!review && !review.active && name === review.name;
  async function remove() {
    if (!eligible || !review || submitting.current) return;
    submitting.current = true;
    setBusy(true);
    setError("");
    try {
      const result = await api<SimulationRemovalResult>(
        `/simulations/${encodeURIComponent(id)}/remove`,
        {
          method: "POST",
          body: JSON.stringify({
            typed_name: name,
            revision: review.revision,
            confirmed: true,
          }),
        },
      );
      removed(result);
    } catch (e) {
      setError(
        `${(e as Error).message} If the response was lost, refresh to check the library; retrying this exact confirmation is safe.`,
      );
    } finally {
      submitting.current = false;
      setBusy(false);
    }
  }
  return (
    <>
      {!review && !error && <p role="status">Reviewing this simulation…</p>}
      {review && (
        <>
          <p>
            <strong>
              Remove “{review.name}” and its {review.counts.runs} runs from this
              workspace?
            </strong>
            <br />
            Simulation ID: <code>{review.simulation_id}</code>
          </p>
          <dl className="simulation-removal-counts">
            {Object.entries({
              runs: "Runs",
              snapshots: "Source snapshots referenced",
              screenshots: "Images / screenshots",
              annotations: "Note and annotation history entries",
              measurements: "Measurements",
              copies: "Managed file copies",
              references: "External file references",
              archive_events: "Git archive associations",
              archive_pending: "Pending archive operations",
            }).map(([key, label]) => (
              <React.Fragment key={key}>
                <dt>{label}</dt>
                <dd>{review.counts[key]}</dd>
              </React.Fragment>
            ))}
          </dl>
          <p>
            This permanently removes these library records, notes, logs and
            unshared managed files. Shared snapshots and copies needed by
            surviving runs remain. Back up first if you may need this history;
            restore a backup into a separate workspace to recover it.
          </p>
          <p>
            Original Python files, source folders, local source Git repositories
            and output folders—including reference-only files—are not deleted or
            modified.
          </p>
          <p>
            Existing commits and bytes in the shared Git archive remain and may
            still consume disk space. This action does not purge Git history or
            securely erase data. Existing backups retain their old contents.
          </p>
          {review.active && (
            <p role="alert">
              Running or finalizing runs prevent removal. Cancel, stop them and
              wait, then review again.
            </p>
          )}
          <label>
            Type the exact simulation name to confirm
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              disabled={busy || review.active}
              autoComplete="off"
              spellCheck={false}
              autoCapitalize="none"
            />
          </label>
          <p className="muted">
            Match case, spaces and punctuation exactly. No library schema
            upgrade is performed.
          </p>
        </>
      )}
      {error && (
        <p role="alert" className="error-banner">
          {error}
        </p>
      )}
      <div className="modal-actions">
        <button ref={cancel} autoFocus onClick={close}>
          Cancel
        </button>
        <button disabled={busy || !eligible} onClick={remove}>
          {busy ? "Removing…" : "Remove simulation"}
        </button>
      </div>
      {busy && (
        <p role="status">
          Removal requested. Closing this dialog cannot cancel a request already
          sent.
        </p>
      )}
    </>
  );
}
