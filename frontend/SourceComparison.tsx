import React, { useEffect, useState } from "react";
import { api } from "./api";
import type { Run } from "./types";

type Entry = { blob: string; size: number; mode: number };
export type Comparison = {
  run_id: string;
  version: string;
  recorded_change: string;
  snapshot_id: string;
  baseline: { id: string; version: string; snapshot_id: string; started_at: string; deleted: boolean };
  counts: { added: number; removed: number; changed: number; unchanged: number };
  total: number;
  offset: number;
  limit: number;
  changes: { path: string; change: string; classification: string; detail?: string;
    permissions_changed: boolean; output_boundary: string | null; output_boundary_confirmed?: boolean; before: Entry | null; after: Entry | null }[];
  selection_changes: { field: string; before: unknown; after: unknown }[];
  notes: string[];
};

const classifications: Record<string, string> = {
  python: "Python file",
  "non-python": "Non-Python file",
  "python-text": "Python comments / formatting only",
  "python-structure": "Python structure changed",
  "python-unverified": "Python bytes differ; AST comparison unavailable",
  permissions: "Permissions changed; bytes unchanged",
  manifest: "Manifest metadata changed",
};
const selectionLabels: Record<string, string> = {
  source_include: "Source inclusion patterns", source_exclude: "Source exclusion patterns",
  output_dirs: "Output trees excluded from source", ignored_dirs: "Ignored directory names",
  workspace_dir: "Library directory excluded from source",
};
const mode = (value: number) => value.toString(8).padStart(4, "0");

export function RecordedVersionEvidence({ run }: { run: Run }) {
  const evidence = run.parameter_metadata;
  if (!evidence) return null;
  const reasons = evidence.provenance?.binding_reasons || [];
  if (run.version === "unversioned" && (reasons.length || evidence.warnings?.length)) {
    return <details className="recorded-version-evidence">
      <summary>{reasons.length ? "Why this run is unversioned" : "Recorded metadata diagnostics"}</summary>
      {(reasons.length ? reasons : evidence.warnings || []).map((reason, index) => <p key={index}>{reason}</p>)}
      <p>{reasons.length ? "Review root swss.toml and its source hashes for future runs. " : "Diagnostics were recorded at start. "}This recorded version stays unchanged.</p>
    </details>;
  }
  if (!evidence.provenance) return null;
  return <small>{run.version === evidence.provenance.simulation_version && !reasons.length
    ? "Version from captured swss.toml. Later metadata edits apply to new runs."
    : <>Captured SWSS declaration version: <code>{evidence.provenance.simulation_version}</code>. This run’s recorded version is retained.</>}</small>;
}

export function SourceComparison({ runId, selectPath }: { runId: string; selectPath: (path: string) => void }) {
  const [offset, setOffset] = useState(0), [retry, setRetry] = useState(0);
  const [result, setResult] = useState<{ key: string; data: Comparison | null; error: string } | null>(null);
  const key = `${runId}:${offset}:${retry}`;
  const current = result?.key === key ? result : null;
  useEffect(() => {
    let live = true;
    api<Comparison>(`/runs/${runId}/source-comparison?offset=${offset}&limit=100`)
      .then(data => { if (live) setResult({ key, data, error: "" }); })
      .catch((error: Error) => { if (live) setResult({ key, data: null, error: error.message }); });
    return () => { live = false; };
  }, [key, runId, offset]);
  const report = current?.data;
  return <section className="source-comparison" aria-label="Source changes against baseline">
    <h3>Changes against version baseline</h3>
    {!current && <p role="status">Loading recorded source comparison…</p>}
    {current?.error && <div role="alert" className="error-banner">
      <p>Source comparison unavailable: {current.error}</p>
      <button onClick={() => setRetry(value => value + 1)}>Retry source comparison</button>
    </div>}
    {report && <>
      <p>Version <code>{report.version}</code> · baseline run <code>{report.baseline.id}</code>
        {report.baseline.deleted ? " (run removed; snapshot retained)" : ""}</p>
      <details>
        <summary>Snapshot identities</summary>
        <p>Baseline: <code>{report.baseline.snapshot_id}</code></p>
        <p>This run: <code>{report.snapshot_id}</code></p>
      </details>
      <p role="status">{report.counts.added} added · {report.counts.removed} removed · {report.counts.changed} changed · {report.counts.unchanged} unchanged</p>
      {report.baseline.id === runId ? <p>This run established the version baseline.</p>
        : report.total === 0 && <p>No path, byte or permission differences.</p>}
      {report.notes.map(note => <p key={note} className="text-amber">{note}</p>)}
      {report.selection_changes.length > 0 && <details>
        <summary>Source selection changed</summary>
        {report.selection_changes.map(change => <div key={change.field}>
          <strong>{selectionLabels[change.field] || change.field}</strong>
          <p>Baseline: <code>{JSON.stringify(change.before)}</code></p>
          <p>This run: <code>{JSON.stringify(change.after)}</code></p>
        </div>)}
      </details>}
      {report.changes.length > 0 && <ul className="source-change-list">
        {report.changes.map(change => <li key={change.path}>
          <button className="text-button" onClick={() => selectPath(change.path)}>{change.path}</button>
          <span>{change.change} · {classifications[change.classification] || change.classification}</span>
          {change.permissions_changed && change.classification !== "permissions" && change.before && change.after && <small>Permissions also changed: <code>{mode(change.before.mode)} → {mode(change.after.mode)}</code>.</small>}
          {change.output_boundary && <small>Previously included; {change.output_boundary_confirmed
            ? "now inside recorded output exclusion" : "under this run’s recorded capture folder"} <code>{change.output_boundary}</code>.</small>}
          {change.detail && <small>{change.detail}</small>}
          <details>
            <summary>Recorded file evidence</summary>
            {(["before", "after"] as const).map(side => <p key={side}>{side === "before" ? "Baseline" : "This run"}: {change[side]
              ? <><code>{change[side]!.blob}</code> · {change[side]!.size} bytes · mode <code>{mode(change[side]!.mode)}</code></>
              : "Absent"}</p>)}
            {change.permissions_changed && <p>Permissions changed.</p>}
          </details>
        </li>)}
      </ul>}
      {report.total > 100 && <div className="argument-actions">
        <button disabled={offset === 0} onClick={() => setOffset(value => Math.max(0, value - 100))}>Previous changed paths</button>
        <span>{offset + 1}–{Math.min(offset + 100, report.total)} of {report.total}</span>
        <button disabled={offset + 100 >= report.total} onClick={() => setOffset(value => value + 100)}>Next changed paths</button>
      </div>}
    </>}
  </section>;
}
