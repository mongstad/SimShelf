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
  accepted,
}: {
  close: () => void;
  accepted: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const cancel = useRef<HTMLButtonElement>(null);
  const [state, setState] = useState<State | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(true);
  const [review, setReview] = useState(false);
  const started = useRef(false);

  function dismiss() {
    dialog.current?.close();
    close();
  }
  async function request(current: State, stopRuns: boolean) {
    try {
      await api("/server/quit", {
        method: "POST",
        body: JSON.stringify({
          confirmed: true,
          generation: current.generation,
          stop_runs: stopRuns,
        }),
      });
    } catch (e) {
      throw Error(
        `${(e as Error).message} If the connection closed, shutdown may already be underway. Check the original terminal before restarting.`,
      );
    }
    accepted();
  }
  async function check() {
    setBusy(true);
    setError("");
    try {
      const current = await api<State>("/server");
      setState(current);
      if (current.closing) {
        accepted();
        return;
      }
      if (!current.can_quit)
        throw Error(
          "This launch mode cannot quit from the portal. Stop its server in the original terminal or service manager.",
        );
      if (current.active_runs === 0) await request(current, false);
      else setReview(true);
    } catch (e) {
      setError((e as Error).message);
      // Never retry a rejected idle request with cancellation consent.
      setReview(true);
      await api<State>("/server")
        .then(setState)
        .catch(() => {});
    } finally {
      setBusy(false);
    }
  }
  useEffect(() => {
    if (!started.current) {
      started.current = true;
      void check();
    }
  }, []);
  useEffect(() => {
    if (review && !busy) {
      dialog.current?.showModal();
      cancel.current?.focus();
    }
  }, [review, busy]);
  async function confirm() {
    if (!state || busy) return;
    setBusy(true);
    setError("");
    try {
      await request(state, state.active_runs > 0);
    } catch (e) {
      setError((e as Error).message);
      await api<State>("/server")
        .then(setState)
        .catch(() => {});
      cancel.current?.focus();
    } finally {
      setBusy(false);
    }
  }
  if (!review) return <p role="status">Checking active runs…</p>;
  return (
    <dialog
      ref={dialog}
      className="modal"
      aria-labelledby="quit-title"
      onCancel={(e) => {
        e.preventDefault();
        if (!busy) dismiss();
      }}
    >
      <div className="modal-heading">
        <h2 id="quit-title">Quit SimShelf</h2>
      </div>
      {state && state.active_runs > 0 && (
        <p>
          Stop {state.active_runs} active{" "}
          {state.active_runs === 1 ? "run" : "runs"} and quit SimShelf?
        </p>
      )}
      {error && (
        <p role="alert" className="error-banner">
          {error}
        </p>
      )}
      <div className="modal-actions">
        <button ref={cancel} autoFocus onClick={dismiss} disabled={busy}>
          Cancel
        </button>
        <button
          disabled={busy || (state !== null && !state.can_quit)}
          onClick={state ? confirm : check}
        >
          {busy
            ? "Requesting shutdown…"
            : state && state.active_runs > 0
              ? "Stop runs and quit"
              : state
                ? "Quit SimShelf"
                : "Retry"}
        </button>
      </div>
    </dialog>
  );
}
