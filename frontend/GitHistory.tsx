import React, { useEffect, useState } from "react";
import { GitFiles } from "./GitFiles";
import { api } from "./api";
import type { Simulation } from "./types";

type Connection = { root: string; identity: string; mappings: Record<string, string>; workspace: string; format: number };
export type Discovery = { status: string; reason: string | null; preview: Connection | null; eligible: {id: string; subdirectory: string}[]; partial: boolean };
export function DiscoverySummary({ discovery }: { discovery: Discovery }) {
  return <div role="status"><h3>{discovery.status === "found" ? "Repository found" : discovery.status === "not_found" ? "No Git repository found" : "Repository discovery unavailable"}</h3>
    {discovery.preview && <p><code>{discovery.preview.root}</code></p>}
    {discovery.reason && <p>{discovery.reason}</p>}
    {discovery.partial && <p>Some other simulations were not checked. Manual mapping remains available.</p>}
  </div>;
}
export type GitView = {
  availability: string; reason: string | null; commit: string | null; branch: string | null;
  dirty: boolean | null; simulation_dirty: boolean | null; subdirectory: string | null;
  conflicts?: boolean; incomplete?: boolean;
  history: { commit: string; timestamp: string; subject: string }[];
};
export function GitObservation({ value }: { value: GitView }) {
  if (value.availability !== "available") return <p role="status">{value.reason || (value.availability === "disabled" ? "Git is disconnected. Recording and source snapshots work without it." : "This simulation is not mapped to the connected repository.")}</p>;
  return <>
    <dl className="facts">
      <dt>Source folder</dt><dd>{value.subdirectory}</dd>
      <dt>Branch</dt><dd>{value.branch || "Detached HEAD"}</dd>
      <dt>Commit</dt><dd><code>{value.commit}</code></dd>
      <dt>Repository changes</dt><dd>{value.dirty === null ? "Unknown" : value.dirty ? "Local changes" : "No raw-byte changes detected"}</dd>
      <dt>Simulation changes</dt><dd>{value.simulation_dirty === null ? "Unknown" : value.simulation_dirty ? "Local changes" : "No raw-byte changes detected"}</dd>
    </dl>
    {value.conflicts && <p role="alert">Unresolved Git conflicts. Resolve them in your Git tools; SimShelf will not change files.</p>}
    {value.incomplete && <p>Some paths could not be inspected. This is not a clean-checkout guarantee.</p>}
    <p className="muted">Raw source bytes are compared without running Git filters. Line-ending conversion can appear as a change. Git commits are separate from scientific versions and exact run snapshots.</p>
    <h3>Recent source history</h3>
    {value.history.length ? <ul>{value.history.map(item => <li key={item.commit}><code>{item.commit.slice(0, 9)}</code> {item.subject} <span className="muted">{new Date(Number(item.timestamp) * 1000).toLocaleDateString()}</span></li>)}</ul> : <p>No commits affecting this simulation folder.</p>}
    <p className="muted">Up to 20 commits affecting this folder. History is read-only; no remote is contacted.</p>
  </>;
}

export function GitHistory({ simulation, simulations }: { simulation: Simulation; simulations: Simulation[] }) {
  const [discovery, setDiscovery] = useState<Discovery | null>(null);
  const [manual, setManual] = useState(false);
  const [saved, setSaved] = useState<Connection | null>(null);
  const [path, setPath] = useState("");
  const [selected, setSelected] = useState<string[]>([simulation.id]);
  const [preview, setPreview] = useState<Connection | null>(null);
  const [view, setView] = useState<GitView | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [ready, setReady] = useState(false);
  async function load() {
    const [c, v] = await Promise.all([
      api<{connection: Connection | null}>("/workspace/git"),
      api<GitView>(`/simulations/${simulation.id}/git`),
    ]);
    const d = c.connection ? null : await api<Discovery>(`/simulations/${simulation.id}/git/discovery`);
    return {c, v, d};
  }
  function apply({c, v, d}: Awaited<ReturnType<typeof load>>) {
    setSaved(c.connection); setView(v); setDiscovery(d); setManual(false);
    setPreview(d?.preview || null); setPath(d?.preview?.root || "");
    setSelected([simulation.id]); setReady(true);
  }
  async function refresh() { apply(await load()); }
  useEffect(() => { let active = true; setReady(false); setView(null);
    load().then(result => {if(active)apply(result);}).catch(e => {if(active)setError(e.message);});
    return () => {active = false;};
  }, [simulation.id]);
  async function action(work: () => Promise<void>) {
    setBusy(true); setError("");
    try { await work(); } catch (e) {setError((e as Error).message);} finally {setBusy(false);}
  }
  return <section className="surface run-facts git-history">
    <h2>Local Git history</h2>
    <p className="muted">Optionally connect one existing source repository. Files stay where they are. No Git account or remote is required.</p>
    {error && <p role="alert">{error}</p>}
    {!ready && !error && <p role="status">Loading Git connection…</p>}
    {ready && !saved && discovery && <DiscoverySummary discovery={discovery} />}
    {ready && !saved && !manual && <button disabled={busy} onClick={()=>{setManual(true);setPreview(null);}}>Enter repository path manually</button>}
    {ready && !saved && (manual || discovery?.status === "found") && <form onSubmit={e => {e.preventDefault();void action(async () => setPreview(await api<Connection>("/workspace/git/preview", {method:"POST",body:JSON.stringify({path,simulation_ids:selected})})));}}>
      {manual && <label>Repository folder<input value={path} disabled={busy} required onChange={e=>{setPath(e.target.value);setPreview(null);}} /></label>}
      <fieldset disabled={busy}><legend>Registered simulations to link</legend>
        {simulations.filter(s=>manual || discovery?.eligible.some(item=>item.id===s.id)).map(s=><label key={s.id}><input type="checkbox" checked={selected.includes(s.id)} onChange={e=>{setSelected(e.target.checked ? [...selected,s.id] : selected.filter(id=>id!==s.id));setPreview(null);}} /> {s.name}{!manual && <small> — {discovery?.eligible.find(item=>item.id===s.id)?.subdirectory}</small>}</label>)}
      </fieldset>
      {!preview && <button disabled={busy || !selected.length}>Preview connection</button>}
    </form>}
    {ready && !saved && preview && <section aria-label="Git connection preview">
      <h3>Review local connection</h3><p>{preview.root}</p>
      <ul>{Object.entries(preview.mappings).map(([id, folder])=><li key={id}>{simulations.find(s=>s.id===id)?.name}: <code>{folder}</code></li>)}</ul>
      <p>Only link these existing folders. No files will be moved, imported, committed or uploaded. Future runs may retain local Git provenance.</p>
      <button disabled={busy} onClick={()=>void action(async()=>{await api("/workspace/git/connect",{method:"POST",body:JSON.stringify({preview,confirmed:true})});setPreview(null);await refresh();})}>Connect locally</button>{" "}
      <button disabled={busy} onClick={()=>setPreview(null)}>Cancel</button>
    </section>}
    {saved && <><p>Connected repository: <code>{saved.root}</code></p><div className="git-actions">
      <button disabled={busy} onClick={()=>void action(refresh)}>Refresh history</button>
      <button disabled={busy} onClick={()=>void action(async()=>{await api("/workspace/git/disconnect",{method:"POST"});await refresh();})}>Disconnect Git</button>
    </div><p className="muted">Disconnecting preserves sources, Git history and recorded provenance. To change mappings, disconnect and preview a new connection.</p></>}
    <GitFiles key={simulation.id} simulationId={simulation.id} />
    {view && <GitObservation value={view} />}
  </section>;
}
