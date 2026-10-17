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

function TrashIcon() {
  return <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor"
    strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">
    <path d="M3 6h18M9 6V3h6v3M5 6l1 15h12l1-15M10 10v7m4-7v7" />
  </svg>;
}

export function ScreenshotDeletionCopy({ imageName, runName, schemaVersion, missing }: {
  imageName: string; runName: string; schemaVersion: number | null; missing: boolean;
}) {
  return <>
    <p>Are you sure you want to delete <strong>{imageName}</strong> from <strong>{runName}</strong>?</p>
    <p className="screenshot-deletion-warning"><span aria-hidden="true">⚠</span><strong>This screenshot will be permanently removed from SimShelf. This action cannot be undone.</strong></p>
    <p className="muted">The simulation run, its results, and original files will not be affected. Existing backups remain unchanged.</p>
    {(schemaVersion === 1 || schemaVersion === 2) && <p className="screenshot-compatibility">
      This also updates this library. Older SimShelf versions will no longer open it. Stop older servers and recorders first.
    </p>}
    {missing && <p className="muted">The image file is already missing. It will be removed from this run’s gallery.</p>}
  </>;
}

export function DeleteScreenshot({ image, run, close, deleted }: {
  image: Artifact; run: Run; close: () => void; deleted: (result: ScreenshotDeletion) => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const cancel = useRef<HTMLButtonElement>(null);
  const submitting = useRef(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [schemaVersion, setSchemaVersion] = useState<number | null>(null);
  useEffect(() => {
    dialog.current?.showModal();
    cancel.current?.focus();
    let live = true;
    // Read on each opening; a previous deletion may just have upgraded the library.
    api<{ schema_version: number }>("/workspace").then(info => {
      if (![1, 2, 3].includes(info.schema_version)) throw new Error("Unknown library format");
      if (live) setSchemaVersion(info.schema_version);
    }).catch(() => {
      if (live) setError("Could not check library compatibility. Close this dialog and try again.");
    });
    return () => { live = false; };
  }, []);
  useEffect(() => { if (error && !busy) cancel.current?.focus(); }, [error, busy]);
  async function remove() {
    if (submitting.current || schemaVersion === null) return;
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
  return <dialog ref={dialog} className="modal screenshot-deletion" aria-labelledby="delete-screenshot-title"
    onCancel={e => { e.preventDefault(); if (!submitting.current) close(); }}>
    <h2 id="delete-screenshot-title"><TrashIcon />Delete screenshot?</h2>
    <ScreenshotDeletionCopy imageName={image.name} runName={run.name} schemaVersion={schemaVersion} missing={image.availability === "missing"} />
    {schemaVersion === null && !error && <p className="muted" role="status">Checking library compatibility…</p>}
    {error && <p role="alert" className="error-banner">{error}</p>}
    <div className="modal-actions">
      <button ref={cancel} disabled={busy} onClick={close}>Cancel</button>
      <button className="screenshot-delete-button" disabled={busy || schemaVersion === null} onClick={remove}>
        <TrashIcon />{busy ? "Deleting…" : "Delete screenshot"}
      </button>
    </div>
  </dialog>;
}
