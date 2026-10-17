import React, { useEffect, useRef, useState } from "react";
import { api } from "./api";
import type { Artifact, Run } from "./types";

export type ScreenshotDeletion = { deleted_id: string; already_deleted: boolean; cleanup_errors: string[] };

// Filter stale requests that were started before a successful deletion.
export function withoutScreenshots(run: Run, deleted: Set<string>): Run {
  const artifacts = (run.artifacts || []).filter(a => !deleted.has(a.id));
  const images = artifacts.filter(a => a.policy === "copy" && /^image\/(png|jpeg|webp|gif)$/.test(a.media_type));
  return { ...run, artifacts, image_count: images.length,
    cover_id: images.find(a => a.id === run.cover_id)?.id || images[0]?.id || null };
}

export function DeleteScreenshot({ image, run, close, deleted }: {
  image: Artifact; run: Run; close: () => void; deleted: (result: ScreenshotDeletion) => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const cancel = useRef<HTMLButtonElement>(null);
  const submitting = useRef(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => { dialog.current?.showModal(); cancel.current?.focus(); }, []);
  useEffect(() => { if (error && !busy) cancel.current?.focus(); }, [error, busy]);
  async function remove() {
    if (submitting.current) return;
    submitting.current = true;
    setBusy(true);
    setError("");
    try {
      const result = await api<ScreenshotDeletion>(`/runs/${run.id}/screenshots/${image.id}/delete`, {
        method: "POST", body: JSON.stringify({ confirmed: true }),
      });
      dialog.current?.close();
      deleted(result);
    } catch (e) {
      setError(`${(e as Error).message} If the response was lost, close this dialog and refresh to check the result. Retrying this same screenshot is safe.`);
    } finally {
      submitting.current = false;
      setBusy(false);
    }
  }
  return <dialog ref={dialog} className="modal" aria-labelledby="delete-screenshot-title"
    onCancel={e => { e.preventDefault(); if (!submitting.current) close(); }}>
    <h2 id="delete-screenshot-title">Delete screenshot?</h2>
    <p><strong>{image.name}</strong> from <strong>{run.name}</strong></p>
    <p className="muted small">Run <code>{run.id}</code><br />Screenshot <code>{image.id}</code></p>
    <p>This permanently removes this attachment from the library, not just this view. Its managed image copy is deleted only when no other attachment or source snapshot needs it.</p>
    <p>The run, captured outputs, source snapshots, logs and original files are preserved. A deletion audit remains. Existing backups keep their old contents; there is no undo here. Back up first if needed.</p>
    <p>This action enables schema 3 for this library. Stop older SimShelf servers and recorders first; older builds cannot reopen it.</p>
    {image.availability === "missing" && <p>The image file is already missing. Its attachment record will still be removed.</p>}
    {error && <p role="alert" className="error-banner">{error}</p>}
    <div className="modal-actions">
      <button ref={cancel} disabled={busy} onClick={close}>Cancel</button>
      <button disabled={busy} onClick={remove}>{busy ? "Deleting…" : "Delete screenshot"}</button>
    </div>
  </dialog>;
}
