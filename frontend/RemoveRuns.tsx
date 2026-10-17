import React, { useEffect, useRef, useState } from "react";
import { api } from "./api";
import type { Run } from "./types";

export type RemovalResult = { removed_ids: string[]; cleanup_errors: string[] };
export function RemoveRuns({ runs, close, removed }: {
  runs: Run[]; close: () => void; removed: (result: RemovalResult) => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const submitting = useRef(false);
  const cancel = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    const timer = setTimeout(() => cancel.current?.focus(), 0);
    return () => clearTimeout(timer);
  }, []);
  const eligible = runs.length > 0 && runs.every(r => ["completed", "failed", "interrupted"].includes(r.status) && r.capture_status !== "pending");
  async function remove() {
    if (!eligible || submitting.current) return;
    submitting.current = true;
    setBusy(true);
    setError("");
    try {
      const result = await api<RemovalResult>("/runs/remove", {
        method: "POST", body: JSON.stringify({ run_ids: runs.map(r => r.id), confirmed: true }),
      });
      removed(result);
    } catch (e) {
      setError(`${(e as Error).message} If the response was lost, refresh to check the result; retrying these same IDs is safe.`);
    } finally {
      submitting.current = false;
      setBusy(false);
    }
  }
  return <>
    <p>Remove {runs.length} run{runs.length === 1 ? "" : "s"} from this library?</p>
    <ul className="removal-list">{runs.map(r => <li key={r.id}><strong>{r.name}</strong><br />
      {r.simulation_id} · {r.version} · {r.status} · {new Date(r.started_at).toLocaleString()}<br /><code>{r.id}</code></li>)}</ul>
    <p>Removal is irreversible in this library: run records, notes, measurements, logs and unshared managed copies are removed. Back up first if you may need them.</p>
    <p>Original source folders, Git history and original output files (including external references) are never deleted. Existing backups keep their old data.</p>
    <p>The first removal upgrades this library to schema 2, which older SimShelf builds cannot open. Stop any older servers or recorders using it first.</p>
    <p className="muted">A minimal deletion audit remains. Shared files and baseline snapshots needed by surviving runs are retained. Existing source comparisons stay unchanged; future runs use the earliest surviving run as their baseline.</p>
    {!eligible && <p role="alert">Running or finalizing runs cannot be removed. Cancel, stop them and wait for finalization, then review the selection again.</p>}
    {error && <p role="alert" className="error-banner">{error}</p>}
    <div className="modal-actions">
      <button ref={cancel} autoFocus disabled={busy} onClick={close}>Cancel</button>
      <button disabled={busy || !eligible} onClick={remove}>{busy ? "Removing…" : `Remove ${runs.length} run${runs.length === 1 ? "" : "s"}`}</button>
    </div>
  </>;
}
