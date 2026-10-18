import React, { useEffect, useRef, useState } from "react";
import { api } from "./api";
import type { Simulation } from "./types";

type Review = { simulation_id: string; old_path: string; new_path: string; revision: string; warnings: string[] };

export function RelocationReview({ review }: { review: Review }) {
  return <>
    <dl><dt>Previous source folder</dt><dd><code>{review.old_path}</code></dd>
      <dt>New source folder</dt><dd><code>{review.new_path}</code></dd></dl>
    <p>This reconnects the existing simulation and its history. It does not move or delete files.</p>
    <p>Past commands, snapshots, captured copies and archive history stay unchanged.
      External reference-only files still refer to their original locations and may remain missing.</p>
    <p>Source Git mapping, file selections and automatic archival consent will be cleared for this simulation.
      Review and enable them again for the new location. The master archive connection stays unchanged.</p>
    <p>Saved capture rules and execution preferences are retained. Review the interpreter,
      working directory and output destinations before your next launch.</p>
    {review.warnings.map(w => <p className="error-banner" key={w}>{w}</p>)}
  </>;
}

export function RelocateSimulation({ simulation, close, relocated }: {
  simulation: Simulation; close: () => void; relocated: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const input = useRef<HTMLInputElement>(null);
  const submitting = useRef(false);
  const [path, setPath] = useState("");
  const [review, setReview] = useState<Review | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => { dialog.current?.showModal(); input.current?.focus(); }, []);
  async function submit() {
    if (submitting.current) return;
    submitting.current = true; setBusy(true); setError("");
    try {
      if (review) {
        await api(`/simulations/${simulation.id}/relocation`, {
          method: "POST", body: JSON.stringify({ review, confirmed: true }),
        });
        relocated();
      } else {
        setReview(await api<Review>(`/simulations/${simulation.id}/relocation/preview`, {
          method: "POST", body: JSON.stringify({ path }),
        }));
      }
    } catch (e) {
      setError((e as Error).message + (review ? " If a save response was lost, close and refresh to check the current location." : ""));
      setReview(null);
    } finally { submitting.current = false; setBusy(false); }
  }
  return <dialog ref={dialog} className="modal" aria-labelledby="relocate-title"
    onCancel={e => { e.preventDefault(); if (!submitting.current) close(); }}>
    <h2 id="relocate-title">Change source location</h2>
    <p><strong>{simulation.name}</strong> · Existing simulation ID: <code>{simulation.id}</code></p>
    <p>Current source folder: <code style={{ overflowWrap: "anywhere" }}>{simulation.root}</code></p>
    <p>Enter the absolute path on this computer. Your browser cannot browse arbitrary local folders.
      The new folder must contain the registered entry and version files. Stop active runs first.</p>
    <label>New source folder<input ref={input} value={path} disabled={busy || !!review}
      placeholder="/absolute/path/to/simulation" onChange={e => { setPath(e.target.value); setError(""); }} /></label>
    {review && <div style={{ overflowWrap: "anywhere" }}><RelocationReview review={review} /></div>}
    {error && <p role="alert" className="error-banner">{error}</p>}
    <div className="modal-actions">
      <button disabled={busy} onClick={close}>Cancel</button>
      {review && <button disabled={busy} onClick={() => { setReview(null); input.current?.focus(); }}>Edit path</button>}
      <button className="primary" disabled={busy || !path.trim()} onClick={submit}>
        {busy ? "Checking…" : review ? "Confirm source location" : "Review new location"}
      </button>
    </div>
  </dialog>;
}
