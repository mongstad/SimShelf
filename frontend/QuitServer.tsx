import React, { useEffect, useRef, useState } from "react";
import { api } from "./api";

type State = {
  generation: number;
  active_runs: number;
  closing: boolean;
  can_quit: boolean;
};
export function QuitServer({
  close,
  accepted: onAccepted,
}: {
  close: () => void;
  accepted: () => void;
}) {
  const cancel = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    const timer = setTimeout(() => cancel.current?.focus(), 0);
    return () => clearTimeout(timer);
  }, []);
  const [state, setState] = useState<State | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [accepted, setAccepted] = useState(false);
  const load = () => api<State>("/server").then(setState);
  useEffect(() => {
    load().catch((e) => setError(e.message));
  }, []);
  async function quit() {
    if (!state || busy) return;
    setBusy(true);
    setError("");
    try {
      await api("/server/quit", {
        method: "POST",
        body: JSON.stringify({
          confirmed: true,
          generation: state.generation,
          stop_runs: state.active_runs > 0,
        }),
      });
      setAccepted(true);
      onAccepted();
    } catch (e) {
      setError(
        `${(e as Error).message} If the connection closed, shutdown may already be underway. Check the original terminal before restarting.`,
      );
      await load().catch(() => {});
    } finally {
      setBusy(false);
    }
  }
  if (accepted || state?.closing)
    return (
      <div role="status">
        <p>Shutdown requested. This portal is closing.</p>
        <p className="muted">
          Portal runs receive cancellation and final capture is attempted. Slow
          capture may continue after the server exits; interruption does not
          guarantee detached processes stopped.
        </p>
        <p>
          You can close this tab. Restart SimShelf from its launcher when
          needed. Terminal/editor recorders remain independent.
        </p>
      </div>
    );
  return (
    <>
      <p>
        Quit this local SimShelf server? The browser portal will become
        unavailable.
      </p>
      {!state && !error && <p>Checking active portal runs…</p>}
      {state && (
        <p role="status">
          {state.active_runs} active portal recorder
          {state.active_runs === 1 ? "" : "s"} (including startup or final
          capture).
          {state.active_runs > 0 &&
            " Quitting requests cancellation and attempts to preserve partial outputs and logs."}
        </p>
      )}
      <p className="muted">
        Closing a tab leaves the server and simulations running. Terminal/editor
        recorders are independent and will continue outside this portal.
      </p>
      {state && !state.can_quit && (
        <p role="alert">
          This launch mode cannot quit from the portal. Stop its server in the
          original terminal or service manager.
        </p>
      )}
      {error && (
        <p role="alert" className="error-banner">
          {error}
        </p>
      )}
      <div className="modal-actions">
        <button ref={cancel} autoFocus onClick={close} disabled={busy}>
          Cancel / Keep running
        </button>
        <button disabled={!state?.can_quit || busy} onClick={quit}>
          {busy
            ? "Requesting shutdown…"
            : state?.active_runs
              ? "Stop runs and quit"
              : "Quit server"}
        </button>
      </div>
    </>
  );
}
