import React, { useEffect, useRef, useState } from "react";

export function RenameRun({ name, save, close }: {
  name: string;
  save: (name: string) => Promise<void>;
  close: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const input = useRef<HTMLInputElement>(null);
  const submitting = useRef(false);
  const live = useRef(false);
  const [draft, setDraft] = useState(name);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    live.current = true;
    dialog.current?.showModal();
    input.current?.focus();
    input.current?.select();
    return () => { live.current = false; };
  }, []);
  useEffect(() => { if (error && !busy) input.current?.focus(); }, [error, busy]);
  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (submitting.current) return;
    if (!draft.trim() || draft.length > 160) {
      setError("Enter a run name with 1–160 characters, including a non-space character.");
      input.current?.focus();
      return;
    }
    submitting.current = true;
    setBusy(true);
    setError("");
    try {
      await save(draft.trim());
      if (live.current) close();
    } catch (e) {
      if (live.current) {
        setError((e as Error).message);
        input.current?.focus();
      }
    } finally {
      submitting.current = false;
      if (live.current) setBusy(false);
    }
  }
  return <dialog ref={dialog} className="modal rename-run" aria-labelledby="rename-run-title"
    onCancel={event => { event.preventDefault(); if (!submitting.current) close(); }}>
    <h2 id="rename-run-title">Rename run</h2>
    <form noValidate onSubmit={submit}>
      <label>
        Run name
        <input ref={input} value={draft} maxLength={160} disabled={busy}
          aria-invalid={error ? true : undefined} aria-describedby={error ? "rename-run-error" : undefined}
          onChange={event => { setDraft(event.target.value); setError(""); }} />
      </label>
      {error && <p id="rename-run-error" role="alert" className="error-banner">{error}</p>}
      <div className="modal-actions">
        <button type="button" disabled={busy} onClick={close}>Cancel</button>
        <button type="submit" className="primary" disabled={busy}>{busy ? "Saving…" : "Save"}</button>
      </div>
    </form>
  </dialog>;
}
