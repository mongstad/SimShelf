import React, { useEffect, useRef } from "react";

export function SimulationSettings({ name, close, relocate, remove }: {
  name: string; close: () => void; relocate: () => void; remove: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const cancel = useRef<HTMLButtonElement>(null);
  useEffect(() => { dialog.current?.showModal(); cancel.current?.focus(); }, []);
  return <dialog ref={dialog} className="modal simulation-settings" aria-labelledby="simulation-settings-title"
    onKeyDown={e => {
      if (e.key !== "Tab") return;
      const buttons = e.currentTarget.querySelectorAll<HTMLButtonElement>("button");
      const first = buttons[0], last = buttons[buttons.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }}
    onCancel={e => { e.preventDefault(); close(); }}
    onClick={e => { if (e.target === e.currentTarget) close(); }}>
    <h2 id="simulation-settings-title">Simulation settings</h2>
    <p className="muted">{name}</p>
    <div className="simulation-settings-actions">
      <button onClick={relocate}>Change source location…</button>
      <button onClick={remove}>Remove simulation…</button>
    </div>
    <div className="modal-actions"><button ref={cancel} autoFocus onClick={close}>Cancel</button></div>
  </dialog>;
}
