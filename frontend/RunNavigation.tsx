import React, { useEffect, useRef } from "react";
import type { Run } from "./types";

export type RunSequence = { simulationId: string; ids: string[]; fallback: boolean };
export function runSequence(runs: Pick<Run, "id" | "simulation_id">[], simulationId: string, fallback = false): RunSequence {
  return { simulationId, ids: [...new Set(runs.filter(r => r.simulation_id === simulationId).map(r => r.id))], fallback };
}
export function chronological(runs: Run[]): Run[] {
  return [...runs].sort((a, b) => Date.parse(b.started_at) - Date.parse(a.started_at) || (a.id < b.id ? -1 : a.id > b.id ? 1 : 0));
}
export function neighbors(sequence: RunSequence | null, id: string) {
  const index = sequence?.ids.indexOf(id) ?? -1;
  return { previous: index > 0 ? sequence!.ids[index - 1] : undefined,
    next: index >= 0 ? sequence!.ids[index + 1] : undefined };
}
export function RunNavigation({ id, sequence, navigate, close }: {
  id: string; sequence: RunSequence | null; navigate: (id: string) => void; close: () => void;
}) {
  const nav = useRef<HTMLElement>(null);
  useEffect(() => {
    const focused = document.activeElement;
    if (focused instanceof HTMLButtonElement && focused.disabled && nav.current?.contains(focused)) {
      nav.current.querySelector<HTMLButtonElement>("button")?.focus();
    }
  }, [id]);
  const { previous, next } = neighbors(sequence, id);
  return <nav ref={nav} className="run-navigation" aria-label="Run navigation">
    <button className="text-button" onClick={close}>← Back to runs</button>
    <div className="run-neighbors">
      <button className="text-button" disabled={!previous} onClick={() => previous && navigate(previous)}>← Previous run</button>
      <button className="text-button" disabled={!next} onClick={() => next && navigate(next)}>Next run →</button>
    </div>
    <small className="muted">{sequence ? sequence.fallback
      ? "Newest-first · up to 1,000 recent runs in this simulation. Previous is newer; Next is older."
      : "Following the opened list, within this simulation. Previous is before; Next is after."
      : "Open a run from its list to browse adjacent runs."}</small>
  </nav>;
}
