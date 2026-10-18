import { SimulationSettings } from "./SimulationSettings";
import { RemoveSimulation, type SimulationRemovalResult } from "./RemoveSimulation";
import { useSidebar } from "./useSidebar";
import { RunNavigation, chronological, runSequence, type RunSequence } from "./RunNavigation";
import { RunProgress } from "./RunProgress";
import { DeleteScreenshot, withoutScreenshots } from "./DeleteScreenshot";
import { RemoveRuns, type RemovalResult } from "./RemoveRuns";
import { QuitServer } from "./QuitServer";
import { CaptureSummary } from "./CaptureSummary";
import React, { useCallback, useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import { api, connect, downloadBackup, uploadFile } from "./api";
import type {
  Artifact,
  CapturePreview,
  Config,
  Run,
  Simulation,
  Version,
} from "./types";
import "./style.css";
import { RunArchive } from "./GitArchive";
import { RelocateSimulation } from "./RelocateSimulation";
import { GitHistory } from "./GitHistory";
import { LaunchSimulation } from "./LaunchSimulation";

const icons: Record<string, React.ReactNode> = {
  grid: (
    <>
      <rect x="3" y="3" width="7" height="7" rx="1.5" />
      <rect x="14" y="3" width="7" height="7" rx="1.5" />
      <rect x="3" y="14" width="7" height="7" rx="1.5" />
      <rect x="14" y="14" width="7" height="7" rx="1.5" />
    </>
  ),
  wave: <path d="M2 12c4 0 3-8 7-8s2 16 6 16 3-8 7-8" />,
  plus: <path d="M12 5v14M5 12h14" />,
  search: (
    <>
      <circle cx="10.5" cy="10.5" r="6.5" />
      <path d="m16 16 5 5" />
    </>
  ),
  terminal: (
    <>
      <rect x="3" y="4" width="18" height="16" rx="3" />
      <path d="m7 9 3 3-3 3m6 0h4" />
    </>
  ),
  arrow: <path d="m9 5 7 7-7 7" />,
  close: <path d="m6 6 12 12M6 18 18 6" />,
  power: <path d="M12 3v9m-5.7-6.7a8 8 0 1 0 11.4 0" />,
  download: (
    <>
      <path d="M12 3v12m-5-5 5 5 5-5M5 16v5h14v-5" />
    </>
  ),
  history: (
    <>
      <path d="M3 11a9 9 0 1 1 2 7M3 4v7h7M12 7v5l3 2" />
    </>
  ),
  folder: <path d="M3 7V5h7l2 2h9v13H3Z" />,
  table: (
    <>
      <rect x="3" y="4" width="18" height="16" rx="2" />
      <path d="M3 9h18M3 14h18M9 4v16" />
    </>
  ),
  image: (
    <>
      <rect x="3" y="3" width="18" height="18" rx="3" />
      <circle cx="8" cy="8" r="1" />
      <path d="m3 17 6-6 4 4 3-3 5 5" />
    </>
  ),
  check: <path d="m5 12 4 4L19 6" />,
  copy: (
    <>
      <rect x="8" y="8" width="12" height="13" rx="2" />
      <path d="M15 8V3H3v13h5" />
    </>
  ),
  info: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 11v6m0-11v1" />
    </>
  ),
  refresh: (
    <>
      <path d="M20 11a8 8 0 0 0-14-5L3 9m0-6v6h6m-5 4a8 8 0 0 0 14 5l3-3m0 6v-6h-6" />
    </>
  ),
};
function Icon({ name, size = 18 }: { name: string; size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {icons[name] || icons.folder}
    </svg>
  );
}
function formatBytes(n: number) {
  if (n < 1024) return `${n} B`;
  if (n < 1024 ** 2) return `${(n / 1024).toFixed(1)} KB`;
  if (n < 1024 ** 3) return `${(n / 1024 ** 2).toFixed(1)} MB`;
  return `${(n / 1024 ** 3).toFixed(2)} GB`;
}
function date(value: string, includeYear = false) {
  return new Date(value).toLocaleString(undefined, {
    year: includeYear ? "numeric" : undefined,
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
function duration(n: number | null) {
  return n == null
    ? "—"
    : n < 60
      ? `${n.toFixed(1)}s`
      : `${Math.floor(n / 60)}m ${Math.round(n % 60)}s`;
}
function value(v: unknown) {
  return v === undefined
    ? "—"
    : typeof v === "object"
      ? JSON.stringify(v)
      : String(v);
}
function quote(v: string) {
  return /^[a-zA-Z0-9_./:=+,-]+$/.test(v)
    ? v
    : `'${v.replaceAll("'", "'\\''")}'`;
}
function Status({ status }: { status: string }) {
  return (
    <span className={`status ${status}`}>
      <span className="status-dot" />
      {status[0].toUpperCase() + status.slice(1)}
    </span>
  );
}
function SourceBadge({ change }: { change: string }) {
  return change === "text-only" ? (
    <span className="source-note">Comments / formatting</span>
  ) : change === "changed" ? (
    <span className="source-note changed">Code changed within version</span>
  ) : null;
}
function Copy({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      className="icon-button"
      title="Copy to clipboard"
      aria-label="Copy to clipboard"
      onClick={() => {
        navigator.clipboard.writeText(text).then(() => {
          setCopied(true);
          setTimeout(() => setCopied(false), 1500);
        });
      }}
    >
      <Icon name={copied ? "check" : "copy"} />
    </button>
  );
}
function ErrorMessage({ message }: { message: string }) {
  return message ? (
    <div role="alert" className="error-banner">
      <Icon name="info" />
      {message}
    </div>
  ) : null;
}
function Modal({
  title,
  close,
  children,
  wide = false,
}: {
  title: string;
  close: () => void;
  children: React.ReactNode;
  wide?: boolean;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    ref.current?.showModal();
  }, []);
  return (
    <dialog
      ref={ref}
      className={wide ? "modal wide" : "modal"}
      onCancel={close}
      onClick={(e) => {
        if (e.target === e.currentTarget) close();
      }}
    >
      <div className="modal-heading">
        <h2>{title}</h2>
        <button
          className="icon-button"
          aria-label="Close dialog"
          onClick={close}
        >
          <Icon name="close" />
        </button>
      </div>
      {children}
    </dialog>
  );
}

function AddSimulation({
  close,
  done,
}: {
  close: () => void;
  done: (s: Simulation) => void;
}) {
  const [root, setRoot] = useState(""),
    [name, setName] = useState(""),
    [entry, setEntry] = useState(""),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      done(
        await api<Simulation>("/simulations", {
          method: "POST",
          body: JSON.stringify({
            root,
            name: name || null,
            entrypoint: entry || null,
          }),
        }),
      );
    } catch (e) {
      setError(String(e instanceof Error ? e.message : e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <Modal title="Add a simulation" close={close}>
      <p className="muted">
        Connect an existing source folder. Your scripts stay where they are.
      </p>
      <form onSubmit={submit}>
        <label>
          Simulation folder
          <input
            autoFocus
            required
            placeholder="/home/you/simulations/scalar-field"
            value={root}
            onChange={(e) => setRoot(e.target.value)}
          />
          <small>Use an absolute path on the computer running SimShelf.</small>
        </label>
        <div className="form-grid">
          <label>
            Name
            <input
              placeholder="Scalar field"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </label>
          <label>
            Entry file
            <input
              placeholder="field.py"
              value={entry}
              onChange={(e) => setEntry(e.target.value)}
            />
            <small>Relative to the simulation folder.</small>
          </label>
        </div>
        <div className="callout">
          <Icon name="history" />
          <div>
            Optional version tag<code>SIMSHELF_VERSION = "0.1.0"</code>
            <small>
              Add this to your entry file to name the simulation version. Every
              run gets an exact source snapshot either way.
            </small>
          </div>
        </div>
        <ErrorMessage message={error} />
        <div className="modal-actions">
          <button type="button" onClick={close}>
            Cancel
          </button>
          <button className="primary" disabled={busy || !root}>
            {busy ? "Adding…" : "Add simulation"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

function RecordHelp({
  simulation,
  workspace,
  close,
}: {
  simulation?: Simulation;
  workspace: string;
  close: () => void;
}) {
  const slug = simulation?.id || "your-simulation";
  const entry = simulation?.entrypoint || "field.py";
  const command = `simshelf --workspace ${quote(workspace)} record --simulation ${quote(slug)} -- python ${quote(entry)} --seed 42`;
  const snippet = `import simshelf\n\nwith simshelf.run(\n    ${JSON.stringify(slug)},\n    workspace=${JSON.stringify(workspace)},\n    parameters=vars(args),\n) as run:\n    # Your simulation runs here\n    run.metric("energy", energy, step=step, sim_time=t)\n    run.attach("outputs/overview.png")`;
  return (
    <Modal title="Record a run" close={close} wide>
      <p className="muted">
        Keep using your terminal or editor. The browser can stay closed.
      </p>
      <h3>From your terminal</h3>
      <p>
        Run this from{" "}
        {simulation ? <code>{simulation.root}</code> : "your simulation folder"}
        . Replace the sample arguments with your own.
      </p>
      <div className="code-block">
        <pre>{command}</pre>
        <Copy text={command} />
      </div>
      <h3>From your editor</h3>
      <p>
        Install SimShelf in the Python environment that runs your simulation,
        then wrap the simulation code.
      </p>
      <div className="code-block">
        <pre>{snippet}</pre>
        <Copy text={snippet} />
      </div>
      <div className="callout">
        <Icon name="info" />
        <small>
          The terminal wrapper records exact arguments and infers named flags.
          The Python API captures resolved values, including defaults. When
          combined, they join one run.
        </small>
      </div>
      <div className="modal-actions">
        <button className="primary" onClick={close}>
          Got it
        </button>
      </div>
    </Modal>
  );
}

function Comparison({ runs, close }: { runs: Run[]; close: () => void }) {
  const [different, setDifferent] = useState(true);
  const names = [
    ...new Set(runs.flatMap((r) => Object.keys(r.parameters))),
  ].sort();
  const fields: [string, (r: Run) => unknown][] = [
    ["Simulation version", (r) => r.version],
    ["Source snapshot", (r) => r.snapshot_id.slice(0, 12)],
    ["Status", (r) => r.status],
    ["Duration", (r) => duration(r.duration)],
    ...names.map(
      (n) => [n, (r: Run) => r.parameters[n]] as [string, (r: Run) => unknown],
    ),
  ];
  return (
    <Modal title={`Compare ${runs.length} runs`} close={close} wide>
      <div className="compare-options">
        <label className="check-label">
          <input
            type="checkbox"
            checked={different}
            onChange={(e) => setDifferent(e.target.checked)}
          />
          Show differences only
        </label>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Property</th>
              {runs.map((r) => (
                <th key={r.id}>
                  {r.name}
                  <small>{r.id.slice(0, 8)}</small>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {fields
              .filter(
                ([, get]) =>
                  !different ||
                  new Set(runs.map((r) => value(get(r)))).size > 1,
              )
              .map(([label, get]) => (
                <tr
                  key={label}
                  className={
                    new Set(runs.map((r) => value(get(r)))).size > 1
                      ? "different"
                      : ""
                  }
                >
                  <td>{label}</td>
                  {runs.map((r) => (
                    <td key={r.id}>{value(get(r))}</td>
                  ))}
                </tr>
              ))}
          </tbody>
        </table>
      </div>
      <p className="muted small">
        Version labels are explicit. Different source snapshots can belong to
        the same simulation version.
      </p>
    </Modal>
  );
}

function CaptureSettings({
  simulation,
  onSaved,
}: {
  simulation: Simulation;
  onSaved: () => void;
}) {
  const [config, setConfig] = useState<Config>(
    structuredClone(simulation.config),
  );
  const [result, setResult] = useState<CapturePreview | null>(null),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [saved, setSaved] = useState(false);
  useEffect(() => {
    setConfig(structuredClone(simulation.config));
    setResult(null);
    setSaved(false);
  }, [simulation.id]);
  function update(next: Config) {
    setConfig(next);
    setSaved(false);
    setResult(null);
  }
  async function action(save: boolean) {
    setBusy(true);
    setError("");
    try {
      if (save) {
        await api(`/simulations/${simulation.id}`, {
          method: "PATCH",
          body: JSON.stringify({ config }),
        });
        setSaved(true);
        onSaved();
      } else
        setResult(
          await api<CapturePreview>(
            `/simulations/${simulation.id}/capture-preview`,
            { method: "POST", body: JSON.stringify({ config }) },
          ),
        );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="settings-layout">
      <div className="surface">
        <h2>Keep the results that matter</h2>
        <p className="muted">
          Rules apply to new or changed outputs from future runs. The first
          matching rule wins.
        </p>
        <label>
          Output folder
          <input
            value={config.output_dir}
            onChange={(e) => update({ ...config, output_dir: e.target.value })}
          />
          <small>
            Relative to the simulation folder. Concurrent runs should use
            different output subfolders.
          </small>
        </label>
        <div className="rules-heading">
          <span>Filename or pattern</span>
          <span>Capture policy</span>
        </div>
        {config.rules.map((rule, i) => (
          <div className="rule-row" key={i}>
            <input
              aria-label={`Rule ${i + 1} pattern`}
              value={rule.pattern}
              onChange={(e) =>
                update({
                  ...config,
                  rules: config.rules.map((r, j) =>
                    i === j ? { ...r, pattern: e.target.value } : r,
                  ),
                })
              }
            />
            <select
              aria-label={`Rule ${i + 1} policy`}
              value={rule.action}
              onChange={(e) =>
                update({
                  ...config,
                  rules: config.rules.map((r, j) =>
                    i === j ? { ...r, action: e.target.value as "copy" } : r,
                  ),
                })
              }
            >
              <option value="copy">Keep a copy</option>
              <option value="reference">Reference only</option>
              <option value="ignore">Ignore</option>
            </select>
            <button
              className="icon-button"
              aria-label={`Remove rule ${i + 1}`}
              onClick={() =>
                update({
                  ...config,
                  rules: config.rules.filter((_, j) => j !== i),
                })
              }
            >
              <Icon name="close" size={16} />
            </button>
          </div>
        ))}
        <button
          className="text-button"
          onClick={() =>
            update({
              ...config,
              rules: [...config.rules, { pattern: "", action: "copy" }],
            })
          }
        >
          <Icon name="plus" size={16} />
          Add rule
        </button>
        <div className="form-grid">
          <label>
            Maximum file size to copy (MB)
            <input
              type="number"
              min="0.001"
              step="any"
              value={config.max_file_mb}
              onChange={(e) =>
                update({ ...config, max_file_mb: Number(e.target.value) })
              }
            />
          </label>
          <label>
            Copy budget per run (MB)
            <input
              type="number"
              min="0.001"
              step="any"
              value={config.max_run_mb}
              onChange={(e) =>
                update({ ...config, max_run_mb: Number(e.target.value) })
              }
            />
          </label>
        </div>
        <details>
          <summary>Source snapshot patterns</summary>
          <label>
            Include patterns, one per line
            <textarea
              value={config.source_include.join("\n")}
              onChange={(e) =>
                update({
                  ...config,
                  source_include: e.target.value.split("\n").filter(Boolean),
                })
              }
            />
          </label>
          <label>
            Exclude patterns, one per line
            <textarea
              value={config.source_exclude.join("\n")}
              onChange={(e) =>
                update({
                  ...config,
                  source_exclude: e.target.value.split("\n").filter(Boolean),
                })
              }
            />
          </label>
        </details>
        <ErrorMessage message={error} />
        <div className="settings-actions">
          <span aria-live="polite">
            {saved ? "Settings saved for future runs." : ""}
          </span>
          <button disabled={busy} onClick={() => action(false)}>
            Preview matches
          </button>
          <button
            className="primary"
            disabled={busy}
            onClick={() => action(true)}
          >
            Save rules
          </button>
        </div>
      </div>
      <aside className="policy-guide">
        <h3>Three ways to handle a file</h3>
        <dl>
          <dt>Keep a copy</dt>
          <dd>Preserve it inside SimShelf. Copies are included in backups.</dd>
          <dt>Reference only</dt>
          <dd>
            Remember its path and metadata. The original file stays in your
            output folder.
          </dd>
          <dt>Ignore</dt>
          <dd>
            Leave it out of the run record. The original is never removed.
          </dd>
        </dl>
        <div className="callout">
          Filtering the file list is separate from these rules. Hiding a file
          never changes what is saved.
        </div>
      </aside>
      {result && (
        <div className="surface capture-results">
          <h3>Current output-folder preview</h3>
          <p className="muted">
            {result.total_files} files · {result.counts.copy} copy matches ·{" "}
            {result.counts.reference} references · {result.counts.ignore}{" "}
            ignored · {formatBytes(result.copy_bytes)} within copy limits
          </p>
          {result.errors.map((e) => (
            <ErrorMessage key={e} message={e} />
          ))}
          {result.truncated && <p>Showing the first 1,000 matches.</p>}
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>File</th>
                  <th>Size</th>
                  <th>Policy</th>
                  <th>Limit</th>
                </tr>
              </thead>
              <tbody>
                {result.files.map((f) => (
                  <tr key={f.path}>
                    <td>
                      <code>{f.path}</code>
                    </td>
                    <td>{formatBytes(f.size)}</td>
                    <td>{f.action}</td>
                    <td>{f.reason || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {result.total_files === 0 && (
            <p className="muted">
              No output files yet. The rules are ready for your next run.
            </p>
          )}
        </div>
      )}
    </div>
  );
}

function Versions({
  simulation,
  selectVersion,
}: {
  simulation: Simulation;
  selectVersion: (v: string) => void;
}) {
  const [versions, setVersions] = useState<Version[]>([]),
    [error, setError] = useState("");
  useEffect(() => {
    let cancelled = false;
    api<Version[]>(`/simulations/${simulation.id}/versions`)
      .then((v) => {
        if (!cancelled) setVersions(v);
      })
      .catch((e) => setError(e.message));
    return () => {
      cancelled = true;
    };
  }, [simulation.id, simulation.run_count]);
  return (
    <div className="version-layout">
      <div className="surface">
        <h2>Simulation versions</h2>
        <p className="muted">
          A version changes when you change its tag. Source snapshots preserve
          every recorded revision within it.
        </p>
        <ErrorMessage message={error} />
        {versions.map((v) => (
          <article className="version-row" key={v.version}>
            <span className="version-node" />
            <div>
              <h3>
                {v.version === "unversioned"
                  ? "Unversioned"
                  : `Version ${v.version}`}
              </h3>
              <p>
                {v.snapshots} source{" "}
                {v.snapshots === 1 ? "snapshot" : "snapshots"} · {v.run_count}{" "}
                {v.run_count === 1 ? "run" : "runs"}
              </p>
              <small>Latest run {date(v.latest)}</small>
              {v.changed > 0 && (
                <p className="text-amber">
                  {v.changed} {v.changed === 1 ? "run has" : "runs have"} code
                  changes within this version.
                </p>
              )}
            </div>
            <button onClick={() => selectVersion(v.version)}>
              View runs <Icon name="arrow" size={15} />
            </button>
          </article>
        ))}
        {!versions.length && (
          <div className="empty-inline">
            Versions appear after your first recorded run.
          </div>
        )}
      </div>
      <aside className="policy-guide">
        <h3>You decide when the model changes</h3>
        <p>
          Add a literal tag to{" "}
          <code>
            {simulation.version_file ||
              simulation.entrypoint ||
              "your entry file"}
          </code>
          :
        </p>
        <pre className="tag-example">SIMSHELF_VERSION = "0.1.0"</pre>
        <p>
          Comments and formatting produce a new exact snapshot, but do not
          create a new named version.
        </p>
        <p>
          Progress bars and logging can change Python structure. Those changes
          remain visible within the same version; add a note to explain them.
        </p>
        <p className="muted small">
          Structural comparison is a review aid, not proof that two simulations
          behave identically.
        </p>
      </aside>
    </div>
  );
}

function RunDetails({
  id,
  simulation,
  changed,
  requestRemoval,
}: {
  id: string;
  simulation?: Simulation;
  changed: () => void;
  requestRemoval: (run: Run) => void;
}) {
  const [run, setRun] = useState<Run | null>(null),
    [tab, setTab] = useState("overview"),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [notice, setNotice] = useState("");
  const [notes, setNotes] = useState(""),
    [tags, setTags] = useState(""),
    [name, setName] = useState(""),
    [versionNote, setVersionNote] = useState("");
  const [sourcePath, setSourcePath] = useState(""),
    [sourceText, setSourceText] = useState(""),
    [diff, setDiff] = useState(false),
    [logStream, setLogStream] = useState("stdout"),
    [log, setLog] = useState<{ text: string; truncated: boolean }>({
      text: "",
      truncated: false,
    });
  const [deleteImage, setDeleteImage] = useState<Artifact | null>(null);
  const deletedScreenshots = useRef(new Set<string>());
  const screenshotsHeading = useRef<HTMLHeadingElement>(null);
  const deleteTrigger = useRef<HTMLButtonElement | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);
  const activeRunId = useRef(id);
  activeRunId.current = id;
  const refresh = useCallback(async () => {
    try {
      const r = await api<Run>(`/runs/${id}`);
      if (activeRunId.current === id) setRun(withoutScreenshots(r, deletedScreenshots.current));
      return r;
    } catch (e) {
      if (activeRunId.current === id) { setRun(null); setError((e as Error).message); }
      return null;
    }
  }, [id]);
  useEffect(() => {
    let live = true;
    setRun(null);
    setError("");
    setTab("overview");
    setDeleteImage(null);
    setNotice("");
    refresh().then((r) => {
      if (r && live) {
        setNotes(r.notes || "");
        setTags((r.tags || []).join(", "));
        setName(r.name);
        setVersionNote(r.version_note || "");
        setSourcePath(r.snapshot?.files[0]?.path || "");
      }
    });
    const timer = setInterval(() => {
      if (live) refresh();
    }, 3000);
    return () => {
      live = false;
      clearInterval(timer);
    };
  }, [id, refresh]);
  useEffect(() => {
    if (tab !== "source" || !sourcePath || !run) return;
    let live = true;
    api<{ text: string }>(
      `/runs/${id}/source?path=${encodeURIComponent(sourcePath)}${diff && run.baseline_run_id !== id ? `&compare=${run.baseline_run_id}` : ""}`,
    )
      .then((r) => {
        if (live) setSourceText(r.text);
      })
      .catch((e) => setError(e.message));
    return () => {
      live = false;
    };
  }, [tab, sourcePath, diff, id, run?.baseline_run_id]);
  useEffect(() => {
    if (tab !== "logs") return;
    let live = true;
    const load = () =>
      api<{ text: string; truncated: boolean }>(
        `/runs/${id}/logs?stream=${logStream}`,
      )
        .then((r) => {
          if (live) setLog(r);
        })
        .catch((e) => setError(e.message));
    load();
    const timer = setInterval(load, 3000);
    return () => {
      live = false;
      clearInterval(timer);
    };
  }, [tab, logStream, id]);
  async function save(data: Partial<Run>) {
    setBusy(true);
    setError("");
    try {
      const saved = await api<Run>(`/runs/${id}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      });
      if (activeRunId.current !== id) return;
      setRun(withoutScreenshots(saved, deletedScreenshots.current));
      if (data.tags) setTags(saved.tags.join(", "));
      changed();
      setNotice("Saved");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function upload(files: FileList | File[] | null) {
    if (!files?.length) return;
    const selected = Array.from(files);
    setBusy(true);
    setError("");
    try {
      for (const file of selected) await uploadFile(id, file);
      await refresh();
      changed();
      setNotice(
        `${selected.length} ${selected.length === 1 ? "file" : "files"} attached`,
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  useEffect(() => {
    if (tab !== "screenshots") return;
    function paste(e: ClipboardEvent) {
      const files = Array.from(e.clipboardData?.files || []).filter((f) =>
        f.type.startsWith("image/"),
      );
      if (files.length) {
        e.preventDefault();
        upload(files);
      }
    }
    document.addEventListener("paste", paste);
    return () => document.removeEventListener("paste", paste);
  }, [tab, id]);
  if (!run)
    return (
      <div className="detail-page">
        <ErrorMessage message={error} />
        <div className="empty-inline">{error ? "This run is unavailable. Return to the run list to refresh." : "Loading run…"}</div>
      </div>
    );
  const artifacts = run.artifacts || [];
  const images = artifacts.filter(
    (a) =>
      a.policy === "copy" && /^image\/(png|jpeg|webp|gif)$/.test(a.media_type),
  );
  const cover = images.find((a) => a.id === run.cover_id) || images[0];
  const latest = new Map((run.metrics || []).map((m) => [m.name, m]));
  const imageUrl = (a: Artifact) => `/api/artifacts/${a.id}/file`;
  return (
    <div className="detail-page">
      <header className="run-heading">
        <div>
          <div className="eyebrow">
            {simulation?.name || run.simulation_id} <span>/</span>{" "}
            {run.id.slice(0, 8)}
          </div>
          <h1>{run.name}</h1>
          <div className="run-meta">
            <Status status={run.status} />
            <span>Version {run.version}</span>
            <span>{date(run.started_at, true)}</span>
            <span className="run-duration">
              {duration(
                run.status === "running"
                  ? Math.max(
                      0,
                      (Date.now() - Date.parse(run.started_at)) / 1000,
                    )
                  : run.duration,
              )}
            </span>
          </div>
        </div>
        {run.can_stop && run.status === "running" && (
          <button
            disabled={busy || run.stop_requested}
            onClick={async () => {
              setBusy(true);
              setError("");
              try {
                await api(`/runs/${id}/stop`, { method: "POST" });
                setNotice(
                  "Stop requested. Waiting for the process to exit and final output capture to finish.",
                );
                await refresh();
              } catch (e) {
                setError((e as Error).message);
              } finally {
                setBusy(false);
              }
            }}
          >
            {run.stop_requested ? "Stopping…" : "Stop run"}
          </button>
        )}
        <button
          onClick={() =>
            save({
              tags: run.tags.includes("favorite")
                ? run.tags.filter((t) => t !== "favorite")
                : [...run.tags, "favorite"],
            })
          }
        >
          {run.tags.includes("favorite") ? "★ Favorited" : "☆ Favorite"}
        </button>
        <button disabled={busy || run.status === "running" || run.capture_status === "pending"} onClick={() => requestRemoval(run)}>Remove run…</button>
      </header>
      <RunProgress run={run} />
      <nav className="tabs" aria-label="Run detail sections">
        {[
          "overview",
          "parameters",
          "screenshots",
          "files",
          "source",
          "logs",
          "notes",
        ].map((t) => (
          <button
            key={t}
            className={tab === t ? "active" : ""}
            onClick={() => {
              setTab(t);
              setNotice("");
            }}
          >
            {t[0].toUpperCase() + t.slice(1)}
            {t === "screenshots" && images.length > 0 && (
              <span className="count">{images.length}</span>
            )}
          </button>
        ))}
      </nav>
      <ErrorMessage message={error} />
      {notice && (
        <div className="notice" role="status">
          {notice}
        </div>
      )}
      {run.status === "failed" && (
        <div className="error-banner" role="alert">
          The simulation exited with code {run.exit_code}. Open Logs → stderr
          for dependency, argument or script errors. No dependencies are
          installed automatically.
        </div>
      )}
      {run.status === "interrupted" && (
        <p className="notice">
          Execution was interrupted. Check logs and capture details before using
          partial results.
        </p>
      )}
      {run.status === "running" &&
        run.launch?.kind === "portal" &&
        !run.can_stop && (
          <p className="notice">
            This server does not own the recorder. A previous server's run may
            still be stopping or capturing outputs; refresh to see recovery
            status.
          </p>
        )}
      {tab === "overview" && (
        <>
          <div className="overview-grid">
            <section className="surface run-preview">
              {cover ? (
                <>
                  <a href={imageUrl(cover)} target="_blank" rel="noreferrer">
                    <img
                      src={imageUrl(cover)}
                      alt={cover.caption || cover.name}
                    />
                  </a>
                  <div className="image-caption">
                    <span>{cover.caption || cover.name}</span>
                    <span>Cover image</span>
                  </div>
                </>
              ) : (
                <div className="no-cover">
                  <Icon name="image" size={35} />
                  <h3>Give this run a visual reference</h3>
                  <p>Add a screenshot now or after you inspect the results.</p>
                  <button onClick={() => setTab("screenshots")}>
                    Add a screenshot
                  </button>
                </div>
              )}
            </section>
            <section className="surface run-facts">
              <h3>Run record</h3>
              <dl>
                <dt>Simulation version</dt>
                <dd>
                  <code>{run.version}</code>
                </dd>
                <dt>Source snapshot</dt>
                <dd>
                  <code>{run.snapshot_id.slice(0, 12)}</code>
                </dd>
                <dt>Source comparison</dt>
                <dd>
                  {
                    (
                      {
                        baseline: "First snapshot in version",
                        same: "Matches version baseline",
                        "text-only": "Comments / formatting only",
                        changed: "Code changed within version",
                      } as Record<string, string>
                    )[run.source_change]
                  }
                </dd>
                <dt>Git commit</dt>
                <dd>
                  {run.git.commit ? (
                    <code>
                      {run.git.commit.slice(0, 9)}
                      {run.git.dirty === null ? " · working tree unknown" : run.git.dirty ? " + local changes" : ""}
                    </code>
                  ) : (
                    "No Git commit"
                  )}
                </dd>
                {run.git.availability && <>
                  <dt>Git observation</dt><dd>{run.git.availability === "available" ? (run.git.branch || "Detached HEAD") : (run.git.reason || run.git.availability)}</dd>
                  <dt>Captured source vs Git</dt><dd>{run.git.snapshot_relation === "captured_files_match_commit" ? "Captured files match commit bytes; uncaptured files are not compared" : run.git.snapshot_relation === "captured_files_differ" ? "Captured files differ from commit" : "Not compared"}</dd>
                </>}
                <dt>Exit code</dt>
                <dd>{run.exit_code ?? "—"}</dd>
                <dt>Capture inspection</dt>
                <dd>
                  <span
                    className={
                      run.capture_status === "complete"
                        ? "text-green"
                        : "text-amber"
                    }
                  >
                    {run.capture_status}
                  </span>
                </dd>
              </dl>
              {run.source_change === "changed" && (
                <div className="callout small">
                  The code changed within this named version. Inspect the source
                  and note whether the change affects the model.
                </div>
              )}
              {run.version_note && (
                <p className="version-note">{run.version_note}</p>
              )}
            </section>
          </div>
          <section className="surface command-surface">
            <h3>Recorded command</h3>
            <div className="code-block">
              <pre>{run.command.map(quote).join(" ")}</pre>
              <Copy text={run.command.map(quote).join(" ")} />
            </div>
            <small>
              Working directory: <code>{run.cwd}</code>
            </small>
          </section>
          {latest.size > 0 && (
            <section className="surface">
              <h3>Latest measurements</h3>
              <div className="measurement-grid">
                {[...latest.values()].map((m) => (
                  <div key={m.name}>
                    <span>{m.name.replaceAll("_", " ")}</span>
                    <strong>
                      {m.value.toPrecision(5)} <small>{m.unit || ""}</small>
                    </strong>
                    <small>
                      {m.sim_time != null
                        ? `Simulation time ${m.sim_time}`
                        : m.step != null
                          ? `Step ${m.step}`
                          : "Recorded value"}
                    </small>
                  </div>
                ))}
              </div>
              {(run.metric_count || 0) > 5000 && (
                <small>
                  Showing the first 5,000 recorded measurements in this initial
                  version.
                </small>
              )}
            </section>
          )}
          {run.notes && (
            <section className="surface">
              <h3>Notes</h3>
              <p className="preserve-lines">{run.notes}</p>
            </section>
          )}
          <CaptureSummary run={run} />
          {run.capture_errors?.length > 0 && (
            <section className="surface">
              <h3>Capture details</h3>
              {run.capture_errors.map((e, i) => (
                <p className="text-amber" key={i}>
                  {e}
                </p>
              ))}
            </section>
          )}
          {run.error && (
            <section className="surface">
              <h3>Execution details</h3>
              <pre className="log-block">{run.error}</pre>
            </section>
          )}
        </>
      )}
      {tab === "parameters" && (
        <section className="surface">
          <h2>Parameters used for this run</h2>
          <p className="muted">
            The Python API records resolved values. Command-line flags are
            inferred; exact arguments remain in the run record.
          </p>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Parameter</th>
                  <th>Value</th>
                  <th>Recorded by</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(run.parameters).map(([key, v]) => (
                  <tr key={key}>
                    <td>{key}</td>
                    <td>
                      <code>{value(v)}</code>
                    </td>
                    <td className="muted">
                      {run.parameter_sources[key] || "Unknown"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {!Object.keys(run.parameters).length && (
            <p className="empty-inline">
              No parameters were logged. Pass parameters=vars(args) to the
              Python API.
            </p>
          )}
          <details>
            <summary>Python environment</summary>
            <dl className="environment">
              <dt>Python</dt>
              <dd>{run.environment.python}</dd>
              <dt>Interpreter</dt>
              <dd>
                <code>{run.environment.executable}</code>
              </dd>
              <dt>Platform</dt>
              <dd>{run.environment.platform}</dd>
              <dt>Captured from</dt>
              <dd>{run.environment.source}</dd>
            </dl>
            <pre className="log-block">
              {run.environment.packages
                .map((p) => `${p.name}==${p.version}`)
                .join("\n")}
            </pre>
          </details>
        </section>
      )}
      {tab === "screenshots" && (
        <section className="surface">
          <div className="section-heading">
            <div>
              <h2 ref={screenshotsHeading} tabIndex={-1}>Screenshots & visual results</h2>
              <p className="muted">
                Drop images here, paste from your clipboard, or choose files.
              </p>
            </div>
            <button disabled={busy} onClick={() => fileInput.current?.click()}>
              <Icon name="plus" />
              Add images
            </button>
          </div>
          <input
            className="visually-hidden"
            ref={fileInput}
            type="file"
            accept="image/png,image/jpeg,image/webp,image/gif"
            multiple
            onChange={(e) => {
              upload(e.target.files);
              e.target.value = "";
            }}
          />
          <div
            className="image-drop"
            onDragOver={(e) => {
              e.preventDefault();
            }}
            onDrop={(e) => {
              e.preventDefault();
              upload(
                Array.from(e.dataTransfer.files).filter((f) =>
                  f.type.startsWith("image/"),
                ),
              );
            }}
          >
            {images.length ? (
              <div className="screenshots-grid">
                {images.map((image) => (
                  <figure key={image.id}>
                    {image.availability === "missing" ? <div className="empty-inline">Image file is missing.</div> : <a href={imageUrl(image)} target="_blank" rel="noreferrer">
                      <img
                        src={imageUrl(image)}
                        alt={image.caption || image.name}
                        loading="lazy"
                      />
                    </a>}
                    <figcaption>
                      <strong>{image.name}</strong>
                      <input
                        key={`${image.id}-caption`}
                        aria-label={`Caption for ${image.name}`}
                        defaultValue={image.caption}
                        placeholder="Add a caption…"
                        onBlur={async (e) => {
                          if (e.target.value === image.caption) return;
                          try {
                            await api(`/artifacts/${image.id}`, {
                              method: "PATCH",
                              body: JSON.stringify({ caption: e.target.value }),
                            });
                            await refresh();
                            setNotice("Caption saved");
                          } catch (e) {
                            setError((e as Error).message);
                          }
                        }}
                      />
                      <button
                        className="text-button"
                        onClick={() => save({ cover_id: image.id })}
                      >
                        {cover?.id === image.id
                          ? "✓ Cover image"
                          : "Use as cover"}
                      </button>
                      <button className="text-button" disabled={busy || image.screenshot_deletion_reason !== null}
                        aria-label={`Delete screenshot: ${image.name}`}
                        aria-describedby={image.screenshot_deletion_reason ? `deletion-reason-${image.id}` : undefined}
                        onClick={e => { deleteTrigger.current = e.currentTarget; setDeleteImage(image); }}>
                        Delete screenshot
                      </button>
                      {image.screenshot_deletion_reason && <small id={`deletion-reason-${image.id}`}>{image.screenshot_deletion_reason}</small>}
                    </figcaption>
                  </figure>
                ))}
              </div>
            ) : (
              <div className="empty-inline">
                <Icon name="image" size={32} />
                <h3>No screenshots yet</h3>
                <p>Keep a visual record of what made this run interesting.</p>
              </div>
            )}
          </div>
          <small>PNG, JPEG, WebP, or GIF · up to 25 MB per image. Only manually attached managed images on finished runs can be deleted. Captured outputs are preserved; external references remain in Files.</small>
        </section>
      )}
      {tab === "files" && (
        <section className="surface">
          <RunArchive key={run.id} run={run} reload={() => void refresh()} openSource={path => {setSourcePath(path); setTab("source");}} />
          <CaptureSummary run={run} />
        </section>
      )}
      {tab === "source" && (
        <section className="surface">
          <h2>Exact source snapshot</h2>
          <p className="muted">
            Saved at the start of the run. Changes you make afterward do not
            replace these files.
          </p>
          <div className="toolbar">
            <select
              aria-label="Source file"
              value={sourcePath}
              onChange={(e) => setSourcePath(e.target.value)}
            >
              {run.snapshot?.files.map((f) => (
                <option key={f.path}>{f.path}</option>
              ))}
            </select>
            <label className="check-label">
              <input
                type="checkbox"
                checked={diff}
                disabled={run.baseline_run_id === id}
                onChange={(e) => setDiff(e.target.checked)}
              />
              Compare with version baseline{run.baseline_deleted ? " (run removed; snapshot retained)" : ""}
            </label>
          </div>
          <pre className="source-block">
            {sourceText || "Select a source file."}
          </pre>
          <label>
            Note about changes within this version
            <textarea
              value={versionNote}
              onChange={(e) => setVersionNote(e.target.value)}
              placeholder="For example: progress reporting only; numerical update unchanged."
            />
          </label>
          <div className="settings-actions">
            <button
              className="primary"
              disabled={busy}
              onClick={() => save({ version_note: versionNote })}
            >
              Save version note
            </button>
          </div>
        </section>
      )}
      {tab === "logs" && (
        <section className="surface">
          <div className="section-heading">
            <h2>Terminal output</h2>
            <select
              aria-label="Log stream"
              value={logStream}
              onChange={(e) => setLogStream(e.target.value)}
            >
              <option value="stdout">Standard output</option>
              <option value="stderr">Standard error</option>
            </select>
          </div>
          {log.truncated && (
            <p className="muted small">Showing the most recent 200 KB.</p>
          )}
          <pre className="log-block">
            {log.text || "No output was recorded for this stream."}
          </pre>
        </section>
      )}
      {tab === "notes" && (
        <section className="surface notes-surface">
          <h2>Keep the context</h2>
          <p className="muted">Notes are preserved in this workspace; they are not exported to the Git archive.</p>
          <label>
            Run name
            <input value={name} onChange={(e) => setName(e.target.value)} />
          </label>
          <label>
            Notes
            <textarea
              className="notes-editor"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="What did you try? What did you notice? What should you compare next?"
            />
          </label>
          <label>
            Tags
            <input
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder="baseline, boundary-test, interesting"
            />
            <small>Separate tags with commas.</small>
          </label>
          <div className="settings-actions">
            <span className="muted small">
              Notes are separate from the execution record.
            </span>
            <button
              className="primary"
              disabled={busy || !name.trim()}
              onClick={() =>
                save({
                  name: name.trim(),
                  notes,
                  tags: tags
                    .split(",")
                    .map((t) => t.trim())
                    .filter(Boolean),
                })
              }
            >
              Save notes
            </button>
          </div>
          {(run.annotation_history?.length || 0) > 0 && (
            <details>
              <summary>
                Annotation history ({run.annotation_history?.length})
              </summary>
              {run.annotation_history?.map((a, i) => (
                <div className="annotation-entry" key={i}>
                  <small>{date(String(a.at))}</small>
                  <pre>{JSON.stringify(a, null, 2)}</pre>
                </div>
              ))}
            </details>
          )}
        </section>
      )}
      {deleteImage && <DeleteScreenshot image={deleteImage} run={run}
        close={() => { setDeleteImage(null); setTimeout(() => deleteTrigger.current?.focus(), 0); }}
        deleted={result => {
          deletedScreenshots.current.add(result.deleted_id);
          setRun(current => current ? withoutScreenshots(current, deletedScreenshots.current) : current);
          setDeleteImage(null);
          setError("");
          setNotice(result.cleanup_errors.length
            ? "Screenshot removed from the gallery. File cleanup is pending: " + result.cleanup_errors.join("; ")
            : result.already_deleted ? "Screenshot was already deleted." : "Screenshot deleted.");
          setTimeout(() => screenshotsHeading.current?.focus(), 0);
          changed();
          refresh();
        }} />}

    </div>
  );
}

function App() {
  const sidebar = useSidebar();
  const [workspace, setWorkspace] = useState(""),
    [applicationVersion, setApplicationVersion] = useState<string | null>(null),
    [simulations, setSimulations] = useState<Simulation[]>([]),
    [simulationId, setSimulationId] = useState(""),
    [runs, setRuns] = useState<Run[]>([]),
    [page, setPage] = useState("runs"),
    [view, setView] = useState(
      localStorage.getItem("simshelf-view") || "table",
    ),
    [selected, setSelected] = useState<string[]>([]),
    [search, setSearch] = useState(""),
    [status, setStatus] = useState(""),
    [version, setVersion] = useState(""),
    [param, setParam] = useState(""),
    [operator, setOperator] = useState("eq"),
    [paramValue, setParamValue] = useState(""),
    [imagesOnly, setImagesOnly] = useState(false),
    [filters, setFilters] = useState(false),
    [error, setError] = useState(""),
    [loading, setLoading] = useState(true),
    [modal, setModal] = useState(""),
    [detail, setDetail] = useState(
      location.hash.startsWith("#run/") ? location.hash.slice(5) : "",
    ),
    [limit, setLimit] = useState(200),
    [backingUp, setBackingUp] = useState(false),
    [notice, setNotice] = useState("");
  const [sequence, setSequence] = useState<RunSequence | null>(null);
  const [removalRuns, setRemovalRuns] = useState<Run[] | null>(null);
  const removedIds = useRef(new Set<string>());
  const removedSimulationIds = useRef(new Set<string>());
  const simulationSettingsTrigger = useRef<HTMLButtonElement>(null);
  const administrationReturnFocus = useRef<HTMLButtonElement | null>(null);
  const [quitting, setQuitting] = useState(false);
  const [theme, setTheme] = useState(
    localStorage.getItem("simshelf-theme") || "system",
  );
  const simulation = simulations.find((s) => s.id === simulationId);
  const refreshSequence = useRef(0);
  const activeQuery = useRef("");
  activeQuery.current = JSON.stringify([
    simulationId,
    status,
    version,
    search,
    limit,
  ]);
  const refresh = useCallback(async () => {
    const sequence = ++refreshSequence.current;
    const requestKey = JSON.stringify([
      simulationId,
      status,
      version,
      search,
      limit,
    ]);
    try {
      const sims = await api<Simulation[]>("/simulations");
      setSimulations(sims.filter(s => !removedSimulationIds.current.has(s.id)));
      const query = new URLSearchParams({ limit: String(limit) });
      if (simulationId) query.set("simulation", simulationId);
      if (status) query.set("status", status);
      if (version) query.set("version", version);
      if (search) query.set("q", search);
      const nextRuns = await api<Run[]>(`/runs?${query}`);
      if (activeQuery.current !== requestKey || sequence !== refreshSequence.current) return;
      const retained = nextRuns.filter(r => !removedIds.current.has(r.id) && !removedSimulationIds.current.has(r.simulation_id));
      setRuns(chronological(retained));
      setSelected(previous => previous.filter(id => retained.some(r => r.id === id)));
      setError("");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, [simulationId, status, version, search, limit]);
  useEffect(() => {
    setSelected([]);
  }, [simulationId, status, version, search]);
  useEffect(() => {
    if (modal === "compare" && selected.length < 2) {
      setModal("");
      setNotice("Comparison closed: fewer than two selected runs remain in this view.");
    }
  }, [modal, selected.length]);
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("simshelf-theme", theme);
  }, [theme]);
  useEffect(() => {
    connect()
      .then((info) => {
        setWorkspace(info.path);
        setApplicationVersion(info.version);
      })
      .catch((e) => {
        setError(e.message);
        setLoading(false);
      });
  }, []);
  useEffect(() => {
    if (!workspace || quitting) return;
    let active = true;
    const timer = setTimeout(() => {
      if (active) refresh();
    }, 150);
    const interval = setInterval(() => {
      if (active) refresh();
    }, 3000);
    return () => {
      active = false;
      clearTimeout(timer);
      clearInterval(interval);
    };
  }, [workspace, refresh, quitting]);
  useEffect(() => {
    const handler = () =>
      setDetail(
        location.hash.startsWith("#run/") ? location.hash.slice(5) : "",
      );
    window.addEventListener("hashchange", handler);
    return () => window.removeEventListener("hashchange", handler);
  }, []);
  // A captured list is independent of polling and of later filter/result changes.
  // Hash entry, reload and newly launched runs have no captured list.
  useEffect(() => {
    if (!detail || (sequence && sequence.ids.includes(detail))) return;
    let live = true;
    setSequence(null);
    (async () => {
      const run = await api<Run>(`/runs/${detail}`);
      if (!live) return;
      // Keep Back scoped correctly even if the adjacent-list request fails.
      setSequence(runSequence([run], run.simulation_id, true));
      const recent = await api<Run[]>(`/runs?${new URLSearchParams({ simulation: run.simulation_id, limit: "1000" })}`);
      if (!live) return;
      const context = runSequence(chronological(recent), run.simulation_id, true);
      // An older direct-linked run stays viewable, but cannot skip the omitted interval.
      if (!context.ids.includes(detail)) context.ids = [detail];
      setSequence(context);
    })().catch(() => { /* The detail view reports unavailable runs; Back remains usable. */ });
    return () => { live = false; };
  }, [detail]);
  function backToRuns() {
    if (sequence) setSimulationId(sequence.simulationId);
    if (sequence?.fallback) {
      setSearch(""); setStatus(""); setVersion(""); setParam(""); setImagesOnly(false); setLimit(1000);
    }
    setPage("runs");
    setSelected([]);
    location.hash = "";
    setDetail("");
    refresh();
  }
  function removed(result: RemovalResult) {
    for (const id of result.removed_ids) removedIds.current.add(id);
    setRuns(previous => previous.filter(r => !removedIds.current.has(r.id)));
    setSequence(previous => previous && ({ ...previous, ids: previous.ids.filter(id => !removedIds.current.has(id)) }));
    setSelected([]);
    setModal("");
    setRemovalRuns(null);
    if (removedIds.current.has(detail)) backToRuns();
    setNotice(`${result.removed_ids.length} run(s) removed. ${result.cleanup_errors.length ? "Managed file cleanup is pending; recovery will retry. " + result.cleanup_errors.join("; ") : "Eligible managed files reclaimed; shared files retained."}`);
    refresh();
  }
  function closeSimulationAdministration() {
    setModal("");
    setTimeout(() => (administrationReturnFocus.current?.isConnected ? administrationReturnFocus.current : simulationSettingsTrigger.current)?.focus(), 0);
  }
  function simulationRemoved(result: SimulationRemovalResult) {
    removedSimulationIds.current.add(result.simulation_id);
    refreshSequence.current++;
    setSimulations(previous => previous.filter(s => s.id !== result.simulation_id));
    setRuns(previous => previous.filter(r => r.simulation_id !== result.simulation_id));
    setModal(""); setRemovalRuns(null); chooseSimulation("");
    setParamValue(""); setImagesOnly(false); setFilters(false);
    setNotice(`Simulation removed from this workspace. Original files and Git archive history retained. ${result.cleanup_errors.length ? "Managed file cleanup is pending: " + result.cleanup_errors.join("; ") : "Eligible unshared managed files reclaimed."}`);
  }
  function chooseSimulation(id: string) {
    setSimulationId(id);
    setSequence(null);
    setPage("runs");
    setSearch("");
    setStatus("");
    setVersion("");
    setParam("");
    setSelected([]);
    setLimit(200);
    location.hash = "";
    setDetail("");
  }
  function showRun(id: string) {
    const opened = visible.find(r => r.id === id);
    setSequence(opened ? runSequence(visible, opened.simulation_id) : null);
    navigateRun(id);
  }
  function navigateRun(id: string) {
    location.hash = `run/${id}`;
    setDetail(id);
  }
  function setRunView(v: string) {
    setView(v);
    localStorage.setItem("simshelf-view", v);
  }
  const params = [
    ...new Set(runs.flatMap((r) => Object.keys(r.parameters))),
  ].sort();
  const visible = runs.filter((r) => {
    if (simulation && r.simulation_id !== simulation.id) return false;
    if (imagesOnly && !r.image_count) return false;
    if (!param || paramValue === "") return true;
    const v = r.parameters[param];
    if (operator === "eq")
      return typeof v === "number" && Number.isFinite(Number(paramValue))
        ? v === Number(paramValue)
        : value(v).toLowerCase() === paramValue.toLowerCase();
    if (typeof v !== "number" || !Number.isFinite(Number(paramValue)))
      return false;
    return operator === "lt"
      ? v < Number(paramValue)
      : operator === "gt"
        ? v > Number(paramValue)
        : operator === "le"
          ? v <= Number(paramValue)
          : v >= Number(paramValue);
  });
  const columns = params
    .filter(
      (p) =>
        !["output", "output_dir", "simulation", "sleep", "fail_at"].includes(p),
    )
    .slice(0, 3);
  async function backup() {
    setBackingUp(true);
    setError("");
    try {
      await downloadBackup();
      setNotice(
        "Backup downloaded. Referenced external files stay outside the backup.",
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBackingUp(false);
    }
  }
  if (quitting) return <main className="content"><h1>SimShelf is shutting down</h1>
    <p>Cancellation requested for portal runs; final capture is attempted. Slow capture may continue after the server exits.</p>
    <p>You can close this tab. Terminal/editor recorders remain independent. Restart using the launcher when needed.</p>
    <p className="muted">Interrupted status does not guarantee detached processes stopped. Check retained runs and capture status after restarting.</p></main>;
  return (
    <div className={`app-shell${sidebar.collapsed ? " sidebar-collapsed" : ""}${sidebar.dragging ? " sidebar-dragging" : ""}`} style={sidebar.style}>
      <div className="sidebar-frame" hidden={sidebar.collapsed}>
      <aside className="sidebar" id="sidebar-navigation" aria-label="Workspace navigation">
        <a className="brand" href="#" onClick={() => chooseSimulation("")}>
          <span className="brand-row">
            <span className="brand-symbol">
              <Icon name="wave" size={25} />
            </span>
            SimShelf<span className="beta">local</span>
          </span>
          <span className="brand-tagline">Your simulations, one library.</span>
        </a>
        <div className="sidebar-section">
          <span className="nav-caption">WORKSPACE</span>
          <button
            className={`nav-item ${!simulationId ? "active" : ""}`}
            onClick={() => chooseSimulation("")}
          >
            <Icon name="grid" />
            All simulations
            <span className="nav-count">{simulations.length}</span>
          </button>
        </div>
        <div className="sidebar-section simulation-nav">
          <div className="nav-section-title">
            <span className="nav-caption">SIMULATIONS</span>
            <button
              className="icon-button"
              aria-label="Add simulation"
              onClick={() => setModal("add")}
            >
              <Icon name="plus" size={16} />
            </button>
          </div>
          {simulations.map((s) => (
            <button
              className={`nav-item ${s.id === simulationId ? "active" : ""}`}
              key={s.id}
              onClick={() => chooseSimulation(s.id)}
            >
              <Icon name="wave" />
              <span className="nav-name">{s.name}</span>
              <span className="nav-count">{s.run_count}</span>
            </button>
          ))}
          {!simulations.length && (
            <p className="sidebar-hint">Your simulations will appear here.</p>
          )}
        </div>
        <div className="sidebar-bottom">
          <button className="nav-item sidebar-utility" onClick={() => setModal("quit")}>
            <Icon name="power" />
            <span>Quit SimShelf</span>
          </button>
          <button className="nav-item sidebar-utility sidebar-backup" onClick={backup} disabled={backingUp}>
            <Icon name="download" />
            <span>{backingUp ? "Preparing backup…" : "Back up workspace"}</span>
          </button>
          <label className="theme-label">
            <span>Appearance</span>
            <select
              aria-label="Appearance"
              value={theme}
              onChange={(e) => setTheme(e.target.value)}
            >
              <option value="system">System</option>
              <option value="light">Light</option>
              <option value="dark">Dark</option>
              <option value="onyx">Onyx</option>
              <option value="slate">Slate</option>
              <option value="linen">Linen</option>
            </select>
          </label>
          <div className="local-indicator">
            <span />
            <div>
              Stored on this computer
              <small title={workspace}>{workspace || "Connecting…"}</small>
            </div>
          </div>
        </div>
      </aside>
      {sidebar.separator}
      </div>
      <main className="main">
        <div className="topbar">
          {sidebar.toggle}
          <div className="workspace-breadcrumb">
            Personal workspace <span>/</span>{" "}
            {detail ? "Run record" : simulation?.name || "Overview"}
          </div>
          <span className="local-badge">
            <span />
            Local · {applicationVersion || "Version unavailable"}
          </span>
        </div>
        <div className="main-content">
          <ErrorMessage message={error} />
          {notice && (
            <div role="status" className="notice dismissible">
              {notice}
              <button
                className="icon-button"
                aria-label="Dismiss notification"
                onClick={() => setNotice("")}
              >
                <Icon name="close" size={15} />
              </button>
            </div>
          )}
          {detail ? (
            <>
            <RunNavigation id={detail} sequence={sequence} navigate={navigateRun} close={backToRuns} />
            <RunDetails
              key={detail}
              id={detail}
              simulation={simulations.find(
                (s) =>
                  s.id === sequence?.simulationId,
              )}
              changed={refresh}
              requestRemoval={run => setRemovalRuns([run])}
            />
            </>
          ) : (
            <>
              <header className="page-heading">
                <div>
                  <div className="eyebrow">SIMULATION JOURNAL</div>
                  <h1>{simulation?.name || "All simulations"}</h1>
                  {simulation?.description && <p>{simulation.description}</p>}
                </div>
                <div className="heading-actions">
                  <button onClick={() => setModal("add")}>
                    <Icon name="plus" />
                    Add simulation
                  </button>
                  <button
                    onClick={() => setModal("record")}
                    disabled={!simulations.length}
                  >
                    <Icon name="terminal" />
                    Terminal / editor
                  </button>
                  <button
                    className="primary"
                    title={
                      !simulation
                        ? "Select a simulation in the sidebar first"
                        : "Configure and launch this simulation"
                    }
                    disabled={!simulation || !simulation.available}
                    onClick={() => setModal("launch")}
                  >
                    Start simulation
                  </button>
                </div>
                {simulation && <button ref={simulationSettingsTrigger} className="icon-button simulation-settings-trigger"
                  aria-label="Simulation settings" title="Simulation settings" aria-haspopup="dialog"
                  onClick={e => { administrationReturnFocus.current = e.currentTarget; setModal("simulation-settings"); }}>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden="true">
                    <path d="m9 3-.6 2.4-2 .9-2.3-.7-2 3.4 1.7 1.8v2.4L2.1 15l2 3.4 2.3-.7 2 .9L9 21h4l.6-2.4 2-.9 2.3.7 2-3.4-1.7-1.8v-2.4L19.9 9l-2-3.4-2.3.7-2-.9L13 3Z" />
                    <circle cx="11" cy="12" r="3" />
                  </svg>
                </button>}
              </header>
              {simulation && !simulation.available && (
                <ErrorMessage message="This simulation’s source folder is unavailable on this computer. Existing run records and saved copies remain accessible." />
              )}
              {simulation && <div className="source-location">
                <span>Source folder: <code style={{ overflowWrap: "anywhere" }}>{simulation.root}</code></span>{" "}
                {!simulation.available && <button onClick={e => {
                  administrationReturnFocus.current = e.currentTarget; setModal("relocate");
                }}>Locate source folder…</button>}
              </div>}
              {simulation && (
                <nav className="tabs" aria-label="Simulation sections">
                  <button
                    className={page === "runs" ? "active" : ""}
                    onClick={() => setPage("runs")}
                  >
                    Runs <span className="count">{simulation.run_count}</span>
                  </button>
                  <button
                    className={page === "versions" ? "active" : ""}
                    onClick={() => setPage("versions")}
                  >
                    Version history
                  </button>
                  <button className={page === "git" ? "active" : ""} onClick={() => setPage("git")}>Git history</button>
                  <button
                    className={page === "capture" ? "active" : ""}
                    onClick={() => setPage("capture")}
                  >
                    File capture
                  </button>
                </nav>
              )}
              {page === "runs" && (
                <>
                  {!simulation && simulations.length > 0 && (
                    <div className="simulation-cards">
                      {simulations.slice(0, 4).map((s) => (
                        <button
                          key={s.id}
                          className="simulation-card"
                          onClick={() => chooseSimulation(s.id)}
                        >
                          <span className="simulation-icon">
                            <Icon name="wave" size={22} />
                          </span>
                          <strong>{s.name}</strong>
                          <small>
                            {s.run_count} {s.run_count === 1 ? "run" : "runs"}
                            {s.last_run ? ` · ${date(s.last_run)}` : ""}
                          </small>
                          <Icon name="arrow" size={15} />
                        </button>
                      ))}
                    </div>
                  )}
                  {loading ? (
                    <div className="empty-inline">Loading your workspace…</div>
                  ) : !simulations.length ? (
                    <section className="welcome surface">
                      <div className="welcome-symbol">
                        <Icon name="wave" size={46} />
                      </div>
                      <div className="eyebrow">
                        A LITTLE STRUCTURE FOR YOUR NEXT IDEA
                      </div>
                      <h2>Start with a simulation you already have.</h2>
                      <p>
                        Keep running Python your way. SimShelf remembers the
                        code, arguments, screenshots, and selected results.
                      </p>
                      <button
                        className="primary"
                        onClick={() => setModal("add")}
                      >
                        <Icon name="plus" />
                        Add your first simulation
                      </button>
                      <div className="welcome-steps">
                        <div>
                          <span>01</span>
                          <strong>Connect a folder</strong>
                          <small>Your scripts stay in place.</small>
                        </div>
                        <div>
                          <span>02</span>
                          <strong>Choose Python and start</strong>
                          <small>Or keep using your terminal or editor.</small>
                        </div>
                        <div>
                          <span>03</span>
                          <strong>Come back to the results</strong>
                          <small>Find, compare, and annotate.</small>
                        </div>
                      </div>
                    </section>
                  ) : (
                    <section className="runs-section">
                      <div className="section-heading">
                        <h2>{simulation ? "Run history" : "Recent runs"}</h2>
                        <span className="muted small">
                          Updates every 3 seconds
                        </span>
                      </div>
                      <div className="toolbar">
                        <div className="search-input">
                          <Icon name="search" />
                          <input
                            aria-label="Search runs"
                            placeholder="Search runs, parameters, or notes…"
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                          />
                        </div>
                        <select
                          aria-label="Run status"
                          value={status}
                          onChange={(e) => setStatus(e.target.value)}
                        >
                          <option value="">All statuses</option>
                          <option value="completed">Completed</option>
                          <option value="running">Running</option>
                          <option value="failed">Failed</option>
                          <option value="interrupted">Interrupted</option>
                        </select>
                        <button
                          className={filters ? "selected-button" : ""}
                          onClick={() => setFilters(!filters)}
                        >
                          Filters
                          {(param || version || imagesOnly) && (
                            <span className="filter-dot" />
                          )}
                        </button>
                        <div className="view-switch">
                          <button
                            aria-label="Table view"
                            aria-pressed={view === "table"}
                            onClick={() => setRunView("table")}
                          >
                            <Icon name="table" />
                          </button>
                          <button
                            aria-label="Gallery view"
                            aria-pressed={view === "gallery"}
                            onClick={() => setRunView("gallery")}
                          >
                            <Icon name="grid" />
                          </button>
                        </div>
                      </div>
                      {filters && (
                        <div className="filter-panel">
                          <label>
                            Parameter
                            <select
                              value={param}
                              onChange={(e) => setParam(e.target.value)}
                            >
                              <option value="">Any parameter</option>
                              {params.map((p) => (
                                <option key={p}>{p}</option>
                              ))}
                            </select>
                          </label>
                          <label>
                            Condition
                            <select
                              aria-label="Parameter condition"
                              value={operator}
                              onChange={(e) => setOperator(e.target.value)}
                            >
                              <option value="eq">equals</option>
                              <option value="lt">less than</option>
                              <option value="le">at most</option>
                              <option value="gt">greater than</option>
                              <option value="ge">at least</option>
                            </select>
                          </label>
                          <label>
                            Value
                            <input
                              value={paramValue}
                              onChange={(e) => setParamValue(e.target.value)}
                              placeholder="0.05 or 1e-3"
                            />
                          </label>
                          <label>
                            Version
                            <input
                              value={version}
                              onChange={(e) => setVersion(e.target.value)}
                              placeholder="Any version"
                            />
                          </label>
                          <label className="check-label">
                            <input
                              type="checkbox"
                              checked={imagesOnly}
                              onChange={(e) => setImagesOnly(e.target.checked)}
                            />
                            Has screenshots
                          </label>
                          <button
                            className="text-button"
                            onClick={() => {
                              setParam("");
                              setParamValue("");
                              setVersion("");
                              setImagesOnly(false);
                            }}
                          >
                            Clear filters
                          </button>
                        </div>
                      )}
                      {version && !filters && (
                        <div className="active-filter">
                          Version {version}
                          <button
                            className="icon-button"
                            aria-label="Clear version filter"
                            onClick={() => setVersion("")}
                          >
                            <Icon name="close" size={13} />
                          </button>
                        </div>
                      )}
                      {selected.length > 0 && (
                        <div className="selection-bar">
                          <span>{selected.length} selected</span>
                          <button
                            disabled={selected.length < 2}
                            onClick={() => setModal("compare")}
                          >
                            Compare runs
                          </button>
                          <button onClick={() => setRemovalRuns(runs.filter(r => selected.includes(r.id)))}>Remove selected…</button>
                          <button
                            className="text-button"
                            onClick={() => setSelected([])}
                          >
                            Clear selection
                          </button>
                        </div>
                      )}
                      {view === "table" ? (
                        <div className="table-wrap run-table">
                          <table>
                            <thead>
                              <tr>
                                <th>
                                  <span className="visually-hidden">
                                    Select
                                  </span>
                                </th>
                                <th>Run</th>
                                {!simulation && <th>Simulation</th>}
                                <th>Version</th>
                                {columns.map((p) => (
                                  <th key={p}>{p.replaceAll("_", " ")}</th>
                                ))}
                                <th>Duration</th>
                                <th>Status</th>
                              </tr>
                            </thead>
                            <tbody>
                              {visible.map((r) => (
                                <tr
                                  key={r.id}
                                  className={
                                    selected.includes(r.id)
                                      ? "row-selected"
                                      : ""
                                  }
                                >
                                  <td>
                                    <input
                                      type="checkbox"
                                      aria-label={`Select ${r.name}`}
                                      checked={selected.includes(r.id)}
                                      onChange={(e) =>
                                        setSelected(
                                          e.target.checked
                                            ? [...selected, r.id]
                                            : selected.filter(
                                                (id) => id !== r.id,
                                              ),
                                        )
                                      }
                                    />
                                  </td>
                                  <td>
                                    <button
                                      className="run-link"
                                      onClick={() => showRun(r.id)}
                                    >
                                      {r.name}
                                      {!!r.archive_commits && <small>{r.archive_commits} archive commits</small>}
                                      {r.tags.includes("favorite") && (
                                        <span className="favorite-star">★</span>
                                      )}
                                      <small>
                                        {date(r.started_at)} <span>·</span>{" "}
                                        {r.id.slice(0, 8)}
                                      </small>
                                    </button>
                                    {r.tags
                                      .filter((t) => t !== "favorite")
                                      .slice(0, 2)
                                      .map((t) => (
                                        <span className="tag" key={t}>
                                          {t}
                                        </span>
                                      ))}
                                  </td>
                                  {!simulation && (
                                    <td className="muted">
                                      {simulations.find(
                                        (s) => s.id === r.simulation_id,
                                      )?.name || r.simulation_id}
                                    </td>
                                  )}
                                  <td>
                                    <code className="version-code">
                                      {r.version}
                                    </code>
                                    <SourceBadge change={r.source_change} />
                                  </td>
                                  {columns.map((p) => (
                                    <td key={p} className="numeric">
                                      {value(r.parameters[p])}
                                    </td>
                                  ))}
                                  <td className="muted numeric">
                                    {duration(r.duration)}
                                  </td>
                                  <td>
                                    <Status status={r.status} />
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      ) : (
                        <div className="run-gallery">
                          {visible.map((r) => (
                            <article className="run-card" key={r.id}>
                              <button
                                className="gallery-preview"
                                onClick={() => showRun(r.id)}
                                aria-label={`Open ${r.name}`}
                              >
                                {r.cover_id ? (
                                  <img
                                    src={`/api/artifacts/${r.cover_id}/file`}
                                    alt={`Cover for ${r.name}`}
                                    loading="lazy"
                                  />
                                ) : (
                                  <div className="gallery-placeholder">
                                    <Icon name="image" size={30} />
                                    <span>No screenshot yet</span>
                                  </div>
                                )}
                              </button>
                              <div className="run-card-body">
                                <button
                                  className="run-link"
                                  onClick={() => showRun(r.id)}
                                >
                                  {r.name}
                                  {!!r.archive_commits && <small>{r.archive_commits} archive commits</small>}
                                </button>
                                <div className="gallery-meta">
                                  <code>{r.version}</code>
                                  <Status status={r.status} />
                                </div>
                                <small>
                                  {date(r.started_at)} · {duration(r.duration)}
                                </small>
                                <label className="check-label small">
                                  <input
                                    type="checkbox"
                                    checked={selected.includes(r.id)}
                                    onChange={(e) =>
                                      setSelected(
                                        e.target.checked
                                          ? [...selected, r.id]
                                          : selected.filter(
                                              (id) => id !== r.id,
                                            ),
                                      )
                                    }
                                  />
                                  Select for comparison
                                </label>
                              </div>
                            </article>
                          ))}
                        </div>
                      )}
                      {!visible.length && (
                        <div className="empty-inline">
                          <Icon name="terminal" size={30} />
                          <h3>
                            {search || status || param || version || imagesOnly
                              ? "No runs match your filters."
                              : "Ready for your first run."}
                          </h3>
                          <p>
                            {search || status || param || version || imagesOnly
                              ? "Try a different parameter, status, or search."
                              : "Select a simulation and start it here, or record from your terminal or editor."}
                          </p>
                          {!(
                            search ||
                            status ||
                            param ||
                            version ||
                            imagesOnly
                          ) && (
                            <button onClick={() => setModal("record")}>
                              Show recording instructions
                            </button>
                          )}
                        </div>
                      )}
                      <div className="table-footer">
                        <span>
                          {visible.length}{" "}
                          {visible.length === 1 ? "run" : "runs"} shown
                          {runs.length >= limit
                            ? ` · newest ${limit} loaded`
                            : ""}
                        </span>
                        {runs.length >= limit && limit < 1000 && (
                          <button
                            onClick={() =>
                              setLimit(Math.min(1000, limit + 200))
                            }
                          >
                            Load more
                          </button>
                        )}
                        <span>Source snapshots preserved automatically</span>
                      </div>
                    </section>
                  )}
                </>
              )}
              {page === "versions" && simulation && (
                <Versions
                  simulation={simulation}
                  selectVersion={(v) => {
                    setVersion(v);
                    setPage("runs");
                  }}
                />
              )}
              {page === "git" && simulation && <GitHistory key={`${simulation.id}:${simulation.root}`} simulation={simulation} simulations={simulations} />}
              {page === "capture" && simulation && (
                <CaptureSettings key={`${simulation.id}:${simulation.root}`} simulation={simulation} onSaved={refresh} />
              )}
            </>
          )}
        </div>
      </main>
      {modal === "quit" && <Modal title="Quit SimShelf" close={() => setModal("")}><QuitServer close={() => setModal("")} accepted={() => setQuitting(true)} /></Modal>}
      {modal === "add" && (
        <AddSimulation
          close={() => setModal("")}
          done={(s) => {
            setModal("");
            chooseSimulation(s.id);
            refresh();
          }}
        />
      )}
      {modal === "simulation-settings" && simulation && <SimulationSettings
        close={closeSimulationAdministration} relocate={() => setModal("relocate")} remove={() => setModal("remove-simulation")} />}
      {modal === "remove-simulation" && simulation && <Modal title="Remove simulation" close={closeSimulationAdministration}>
        <RemoveSimulation key={simulation.id} id={simulation.id} close={closeSimulationAdministration} removed={simulationRemoved} />
      </Modal>}
      {modal === "relocate" && simulation && <RelocateSimulation key={simulation.id}
        simulation={simulation} close={closeSimulationAdministration} relocated={() => {
          administrationReturnFocus.current = simulationSettingsTrigger.current;
          closeSimulationAdministration(); setNotice("Source location updated. Review launch settings and Git archival preferences before your next run."); refresh();
        }} />}
      {modal === "launch" && simulation && (
        <Modal title="Start a simulation" close={() => setModal("")} wide>
          <LaunchSimulation
            simulation={simulation}
            saved={refresh}
            done={(id) => {
              setModal("");
              showRun(id);
              refresh();
            }}
          />
        </Modal>
      )}
      {modal === "record" && (
        <RecordHelp
          simulation={simulation || simulations[0]}
          workspace={workspace}
          close={() => setModal("")}
        />
      )}{" "}
      {removalRuns && <Modal title="Remove runs" close={() => setRemovalRuns(null)}>
        <RemoveRuns runs={removalRuns} close={() => setRemovalRuns(null)} removed={removed} />
      </Modal>}
      {modal === "compare" && (
        <Comparison
          runs={runs.filter((r) => selected.includes(r.id))}
          close={() => setModal("")}
        />
      )}
    </div>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
