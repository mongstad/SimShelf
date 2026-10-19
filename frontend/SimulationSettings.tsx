import React, { useEffect, useRef } from "react";
import { Icon } from "./Icon";
import type { Simulation } from "./types";

export function SimulationSettings({ close, relocate, remove }: {
  close: () => void; relocate: () => void; remove: () => void;
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
    <div className="simulation-settings-actions">
      <button onClick={relocate}><Icon name="folder" /><span>Change source location…</span></button>
      <button onClick={remove}><Icon name="trash" /><span>Remove simulation…</span></button>
    </div>
    <div className="modal-actions"><button ref={cancel} autoFocus onClick={close}>Cancel</button></div>
  </dialog>;
}

export function settingsDisabled(simulation: Pick<Simulation, "administration_active">, current: boolean) {
  return !current || simulation.administration_active !== false;
}

export function SimulationSettingsButton({ disabled, onClick, ref }: {
  disabled: boolean;
  onClick: React.MouseEventHandler<HTMLButtonElement>;
  ref?: React.Ref<HTMLButtonElement>;
}) {
  return <button ref={ref} className="icon-button simulation-settings-trigger"
    disabled={disabled} aria-label="Simulation settings"
    title={disabled ? undefined : "Simulation settings"} aria-haspopup="dialog" onClick={onClick}>
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden="true">
      <path d="m9 3-.6 2.4-2 .9-2.3-.7-2 3.4 1.7 1.8v2.4L2.1 15l2 3.4 2.3-.7 2 .9L9 21h4l.6-2.4 2-.9 2.3.7 2-3.4-1.7-1.8v-2.4L19.9 9l-2-3.4-2.3.7-2-.9L13 3Z" />
      <circle cx="11" cy="12" r="3" />
    </svg>
  </button>;
}
