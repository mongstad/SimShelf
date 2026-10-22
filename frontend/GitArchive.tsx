import React, { useEffect, useRef, useState } from "react";
import { api, uploadFile } from "./api";
import type { Artifact, Run, Simulation } from "./types";

type Review = Record<string, any>;
export const archiveLimits =
  "1,000 files · 25 MiB per file · 100 MiB per run, including later additions and preservation records.";
export function ArchiveSwitch({
  label,
  checked,
  disabled,
  onChange,
  actionRef,
  describedBy,
}: {
  label: string;
  checked: boolean | null;
  disabled: boolean;
  onChange: () => void;
  actionRef?: React.RefObject<HTMLButtonElement | null>;
  describedBy?: string;
}) {
  return (
    <button
      ref={actionRef}
      type="button"
      role="switch"
      aria-label={label}
      aria-checked={checked === true}
      aria-describedby={describedBy}
      className="archive-toggle"
      disabled={disabled}
      onClick={onChange}
    >
      <span className="archive-toggle-knob" aria-hidden="true" />
      {checked === null ? "—" : checked ? "ON" : "OFF"}
    </button>
  );
}

export function ArchiveSettings() {
  const [state, setState] = useState<Review | null>(null);
  const [path, setPath] = useState(""),
    [initialize, setInitialize] = useState(false);
  const [busy, setBusy] = useState(false),
    [message, setMessage] = useState("");
  const [activating, setActivating] = useState(false);
  const request = useRef(0);
  const panel = useRef<HTMLDetailsElement>(null),
    input = useRef<HTMLInputElement>(null),
    toggle = useRef<HTMLButtonElement>(null);
  async function load() {
    const sequence = ++request.current;
    const c = await api<Review>("/workspace/archive");
    if (sequence !== request.current) return;
    setState(c);
    setPath(c.connection?.path || c.remembered_connection?.path || "");
  }
  useEffect(() => {
    void load().catch((e) => setMessage(e.message));
  }, []);
  const post = (suffix: string, body: Review = {}) =>
    api<Review>("/workspace/archive/" + suffix, {
      method: "POST",
      body: JSON.stringify(body),
    });
  async function action(work: () => Promise<void>) {
    request.current++;
    setBusy(true);
    setMessage("");
    try {
      await work();
      await load();
    } catch (e) {
      setMessage((e as Error).message);
      await load().catch(() => setState(null));
    } finally {
      setBusy(false);
    }
  }
  function change() {
    if (state?.enabled || state?.status.state === "connected") {
      void action(async () => {
        await post("automatic", { enabled: !state?.enabled });
      });
    } else {
      setActivating(true);
      if (panel.current) panel.current.open = true;
      input.current?.focus();
      setMessage("Connect a local repository to turn Master Git Archive ON.");
    }
  }
  async function connect() {
    await post("connect", {
      path,
      initialize,
      confirmed: true,
      expected_connection:
        state?.remembered_connection?.path === path
          ? state.remembered_connection
          : undefined,
    });
    setInitialize(false);
    if (activating) {
      await post("automatic", { enabled: true });
      setActivating(false);
    }
    setMessage(
      "Repository connected. Individual participation choices are unchanged.",
    );
  }
  return (
    <section
      className="surface master-archive-settings"
      aria-label="Global Master Git Archive"
    >
      <div className="automatic-archive-line">
        <h2>Master Git Archive</h2>
        <ArchiveSwitch
          label="Master Git Archive"
          checked={!!state?.enabled}
          disabled={busy || !state}
          onChange={change}
          actionRef={toggle}
        />
      </div>
      <p>
        One shared local repository. SimShelf always captures runs in your local
        library.
      </p>
      <MasterArchiveStatus
        status={state?.status}
        configured={!!state?.connection}
      />
      <p className="path">
        Repository:{" "}
        <code>
          {state?.connection?.path ||
            state?.remembered_connection?.path ||
            "Not configured"}
        </code>
      </p>
      <p role="status">
        {state?.enabled
          ? state.status.state === "connected"
            ? "ON for participating simulations."
            : "Git unavailable. Local library capture continues."
          : "OFF. Saved simulation choices are retained."}
      </p>
      {message && <p role="status">{message}</p>}
      <details ref={panel}>
        <summary>Repository location and setup</summary>
        <p>
          Use a dedicated bare SimShelf archive outside source folders and the
          library. No uploads or remote synchronization. Back it up separately.
        </p>
        <label>
          Dedicated archive directory
          <input
            ref={input}
            value={path}
            disabled={busy || !!state?.connection}
            onChange={(e) => setPath(e.target.value)}
          />
        </label>
        {state?.connection ? (
          <button
            disabled={busy}
            onClick={() =>
              void action(async () => {
                await post("disconnect");
              })
            }
          >
            Disconnect repository
          </button>
        ) : (
          <>
            <label className="archive-choice">
              <input
                type="checkbox"
                checked={initialize}
                disabled={busy}
                onChange={(e) => setInitialize(e.target.checked)}
              />{" "}
              Initialize this existing empty directory as a dedicated archive
            </label>
            <button
              disabled={busy || !path.trim()}
              onClick={() => void action(connect)}
            >
              {activating
                ? "Confirm repository and turn ON"
                : initialize
                  ? "Initialize and connect repository"
                  : "Connect repository"}
            </button>
          </>
        )}
        {activating && (
          <button
            disabled={busy}
            onClick={() => {
              setActivating(false);
              setMessage("");
              toggle.current?.focus();
            }}
          >
            Cancel setup
          </button>
        )}
      </details>
      <button disabled={busy} onClick={() => void action(async () => {})}>
        Refresh archive status
      </button>
    </section>
  );
}

export function SimulationArchiveHistory({
  simulation,
}: {
  simulation: Simulation;
}) {
  const [runs, setRuns] = useState<Review[]>([]),
    [error, setError] = useState("");
  useEffect(() => {
    void api<Review>(`/simulations/${simulation.id}/archive`)
      .then((s) => setRuns(s.runs))
      .catch((e) => setError(e.message));
  }, [simulation.id]);
  return (
    <>
      {error && <p role="alert">{error}</p>}
      <details>
        <summary>This simulation’s Git preservation history</summary>
        <p>
          Latest 200 runs; other simulations are excluded. Open a run’s Files
          view for exact revisions and downloads.
        </p>
        <ul>
          {runs
            .filter((r) => r.events.length)
            .map((r) => (
              <li key={r.run}>
                {r.name} · <code>{r.run}</code>:{" "}
                {r.preservation?.state || "scope unknown"};{" "}
                {r.preservation?.output_files ?? 0} outputs in initial
                preservation.
                {r.events.map((e: Review) => (
                  <span key={e.id}>
                    {" "}
                    <code>{e.commit.slice(0, 9)}</code> ({e.files.length} files
                    {!e.files.length ? "; manifest only" : ""})
                  </span>
                ))}
              </li>
            ))}
        </ul>
      </details>
    </>
  );
}

export function RunArchive({
  run,
  reload,
  openSource,
}: {
  run: Run;
  reload: () => void;
  openSource?: (path: string) => void;
}) {
  const [search, setSearch] = useState(""),
    [filter, setFilter] = useState("all");
  const [view, setView] = useState<Review | null>(null),
    [selected, setSelected] = useState<string[]>([]);
  const [includeNotes, setIncludeNotes] = useState(false),
    [review, setReview] = useState<Review | null>(null),
    [operation, setOperation] = useState("");
  const [busy, setBusy] = useState(false),
    [message, setMessage] = useState("");
  const afterReview = useRef<HTMLHeadingElement>(null);
  const cancel = useRef<HTMLButtonElement>(null),
    trigger = useRef<HTMLButtonElement>(null),
    restore = useRef(false);
  const load = async () =>
    setView(await api<Review>(`/runs/${run.id}/archive`));
  useEffect(() => {
    let active = true;
    const refresh = () =>
      api<Review>(`/runs/${run.id}/archive`)
        .then((v) => {
          if (active) setView(v);
        })
        .catch((e) => {
          if (active) {
            setView((old) =>
              old ? { ...old, connection_status: null } : null,
            );
            setMessage(e.message);
          }
        });
    void refresh();
    const timer = setInterval(refresh, 3000);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [run.id]);
  useEffect(() => {
    if (review) {
      cancel.current?.focus();
      restore.current = true;
    } else if (!busy && restore.current) {
      if (trigger.current?.disabled) afterReview.current?.focus();
      else trigger.current?.focus();
      restore.current = false;
    }
  }, [review, busy]);
  async function action(work: () => Promise<void>) {
    setBusy(true);
    setMessage("");
    try {
      await work();
    } catch (e) {
      setMessage((e as Error).message);
      setReview(null);
      await load().catch(() => {});
    } finally {
      setBusy(false);
    }
  }
  const post = (suffix: string, body: Review) =>
    api<Review>(`/runs/${run.id}/${suffix}`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  return (
    <section className="git-archive">
      <h2>Run files</h2>
      <p>
        One list for retained sources, results and attachments. Downloads verify
        retained bytes; exact Git revisions stay available after later commits.
        Choose Identity and revisions for alternate sources.
      </p>
      {message && <p role="status">{message}</p>}
      {view?.error && <p role="alert">Preservation: {view.error}</p>}
      <div className="toolbar">
        <input
          aria-label="Filter filenames"
          placeholder="Filter filenames…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select
          aria-label="File policy filter"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
        >
          <option value="all">All recorded files</option>
          <option value="copy">Library copies</option>
          <option value="archive">Preserved in Git</option>
          <option value="reference">References</option>
          <option value="skipped">Skipped</option>
        </select>
      </div>
      {!view && (
        <p role="status">
          Git history unavailable until loaded. Library files remain accessible.
        </p>
      )}
      <RunFilesTable
        run={run}
        openSource={openSource}
        events={view?.events || []}
        connection={view?.connection_status}
        search={search}
        filter={filter}
        selected={selected}
        disabled={
          busy ||
          !!review ||
          !!view?.pending ||
          !view ||
          run.status === "running"
        }
        onSelect={(id) => {
          setSelected(
            selected.includes(id)
              ? selected.filter((x) => x !== id)
              : [...selected, id],
          );
          setReview(null);
        }}
      />
      {view && (
        <details>
          <summary>
            Preservation records and omissions ({view.events.length})
          </summary>
          <p>
            {archiveLimits} Library backups include retained records and bytes;
            preserve the external Git repository separately.
          </p>
          {view.events.map((e: Review) => (
            <section key={e.id}>
              <h3>
                {e.kind === "initial"
                  ? "Initial preservation"
                  : "Reviewed later additions"}{" "}
                · <code>{e.commit.slice(0, 9)}</code>
              </h3>
              <p>
                {e.files.length} files ·{" "}
                {e.record
                  ? e.record.completeness + " for this event’s reviewed scope"
                  : "legacy scope unknown"}
                {!e.files.length
                  ? " · manifest only; no scientific file payloads"
                  : ""}
                .
              </p>
              {view.connection_status?.state === "connected" &&
                view.connection_status.identity === e.repository.identity && (
                  <a href={`/api/runs/${run.id}/archive/${e.id}/record`}>
                    {e.record
                      ? "Download verified record"
                      : "Download verified legacy manifest"}
                  </a>
                )}
              <ul>
                {e.skipped.map((s: Review, i: number) => (
                  <li key={i}>
                    {s.name}: {s.reason}
                  </li>
                ))}
              </ul>
              {e.record && (
                <>
                  <ul>
                    {e.record.unknown_coverage.map((s: string, i: number) => (
                      <li key={i}>Unknown coverage: {s}</li>
                    ))}
                  </ul>
                  <ul>
                    {e.record.evidence
                      .filter((f: Review) => f.disposition === "not_retained")
                      .map((f: Review, i: number) => (
                        <li key={i}>
                          {f.name}: {f.reason}
                        </li>
                      ))}
                  </ul>
                  {e.record.annotations.length > 0 && (
                    <details>
                      <summary>
                        Preserved annotations ({e.record.annotations.length})
                      </summary>
                      {e.record.annotations.map((a: Review) => (
                        <pre className="source-block" key={a.id}>
                          {JSON.stringify(a.data, null, 2)}
                        </pre>
                      ))}
                    </details>
                  )}
                </>
              )}
            </section>
          ))}
        </details>
      )}
      {view && !view.events.length && (
        <p>No verified Git preservation events for this run.</p>
      )}
      {view?.pending && (
        <>
          <p>
            A previously approved operation is pending. Retry uses its original
            managed bytes and record, without recapturing live outputs.
          </p>
          <button
            disabled={busy}
            onClick={() =>
              void action(async () => {
                await post("archive/retry", { confirmed: true });
                await load();
              })
            }
          >
            Retry approved preservation
          </button>
        </>
      )}
      {run.status !== "running" && (
        <>
          <h3 ref={afterReview} tabIndex={-1}>
            Add evidence after execution
          </h3>
          <p>
            Attach screenshots or analysis files, save notes and captions, then
            explicitly review them for Git. Attaching alone does not commit
            anything. Earlier scientific records and Git events remain
            unchanged.
          </p>
          <label>
            Attach files
            <input
              type="file"
              multiple
              disabled={busy || !!review}
              onChange={(e) => {
                const files = Array.from(e.target.files || []);
                e.target.value = "";
                void action(async () => {
                  for (const f of files) await uploadFile(run.id, f);
                  reload();
                  setMessage(
                    "Files attached. Select them in the list to review preservation.",
                  );
                });
              }}
            />
          </label>
          <fieldset
            disabled={
              busy ||
              !!review ||
              !!view?.pending ||
              view?.connection_status?.state !== "connected"
            }
          >
            <legend>
              Review later evidence ({selected.length} selected attachments)
            </legend>
            <label className="archive-choice">
              <input
                type="checkbox"
                checked={includeNotes}
                onChange={(e) => setIncludeNotes(e.target.checked)}
              />{" "}
              Include all saved run-note, name, tag and version-note revisions
            </label>
            <p>
              Selected attachments include saved caption history. Select an
              already preserved attachment to append a revised caption. All
              selected revisions count toward cumulative limits; no text is
              silently truncated.
            </p>
            <button
              ref={trigger}
              disabled={!selected.length && !includeNotes}
              onClick={() =>
                void action(async () => {
                  setReview(
                    await post("preservation/preview", {
                      artifact_ids: selected,
                      include_notes: includeNotes,
                    }),
                  );
                  setOperation(crypto.randomUUID().replaceAll("-", ""));
                })
              }
            >
              Review archive additions
            </button>
          </fieldset>
          {review && (
            <section
              className="preservation-review"
              aria-label="Archive additions review"
            >
              <h3>Confirm append-only preservation</h3>
              <ul>
                {review.files.map((f: Review) => (
                  <li key={f.artifact_id}>
                    {f.name} · {f.size.toLocaleString()} bytes ·{" "}
                    <code>{f.blob}</code>
                  </li>
                ))}
              </ul>
              <p>
                {review.record.annotations.length} annotation entries. 64 KiB
                per note/caption, 1 MiB per record, 1,000 annotation entries per
                run including revisions. Records include local paths and
                parameters.
              </p>
              <details open>
                <summary>Exact record to preserve</summary>
                <pre className="source-block">{review.record_json}</pre>
              </details>
              <div className="settings-actions">
                <button
                  ref={cancel}
                  disabled={busy}
                  onClick={() => setReview(null)}
                >
                  Cancel
                </button>
                <button
                  className="primary"
                  disabled={busy}
                  onClick={() =>
                    void action(async () => {
                      await post("preservation/add", {
                        review,
                        operation,
                        confirmed: true,
                      });
                      setReview(null);
                      setSelected([]);
                      setIncludeNotes(false);
                      await load();
                      setMessage("Reviewed additions preserved.");
                    })
                  }
                >
                  Preserve reviewed additions
                </button>
              </div>
            </section>
          )}
        </>
      )}
    </section>
  );
}

export function MasterArchiveStatus({
  status,
}: {
  status?: Review | null;
  configured?: boolean;
}) {
  const connected = status?.state === "connected";
  return (
    <div className="automatic-archive-control">
      <span role="status" className={connected ? "archive-connected" : ""}>
        {connected && <span aria-hidden="true">✓ </span>}Repository —{" "}
        {connected
          ? "Connected"
          : status?.state === "disconnected"
            ? "Disconnected"
            : "Unavailable"}
      </span>
      {status?.reason && <p>{status.reason}</p>}
      {!status && <small>Checking repository availability…</small>}
    </div>
  );
}

type Revision = { event: Review; file: Review; index: number };
type FileRow = {
  key: string;
  name: string;
  size: number;
  artifact?: Artifact;
  source?: { path: string; size: number; blob: string };
  archived?: Revision;
  revisions: Revision[];
};
export function runFileRows(run: Run, events: Review[]): FileRow[] {
  const rows: FileRow[] = [
    ...(run.artifacts || []).map((artifact) => ({
      key: `artifact:${artifact.id}`,
      name: artifact.name,
      size: artifact.size,
      artifact,
      revisions: [],
    })),
    ...(run.snapshot?.files || []).map((source) => ({
      key: `source:${source.path}`,
      name: source.path,
      size: source.size,
      source,
      revisions: [],
    })),
  ];
  for (const event of events)
    event.files.forEach((file: Review, index: number) => {
      // A repeated explicit event is another revision of the same evidence only
      // when identity, category, name, size and hash all match. Never join by name.
      let row = rows.find(
        (r) =>
          !!file.blob &&
          r.size === file.size &&
          (file.artifact_id
            ? r.artifact?.id === file.artifact_id &&
              r.artifact?.policy === "copy" &&
              r.artifact?.blob === file.blob
            : file.category === "source" &&
              r.source?.path === file.name &&
              r.source?.blob === file.blob),
      );
      if (!row)
        row = rows.find((r) =>
          r.revisions.some(
            (v) =>
              v.file.category === file.category &&
              v.file.artifact_id === file.artifact_id &&
              v.file.name === file.name &&
              v.file.blob === file.blob &&
              v.file.size === file.size,
          ),
        );
      const revision = { event, file, index };
      if (row) {
        row.archived ||= revision;
        row.revisions.push(revision);
      } else
        rows.push({
          key: `event:${event.id}:${index}`,
          name: file.name,
          size: file.size,
          archived: revision,
          revisions: [revision],
        });
    });
  return rows;
}
export function RunFilesTable({
  run,
  events,
  connection,
  search = "",
  filter = "all",
  selected = [],
  disabled = false,
  onSelect = () => {},
  openSource,
}: {
  run: Run;
  events: Review[];
  connection?: Review | null;
  search?: string;
  filter?: string;
  selected?: string[];
  disabled?: boolean;
  onSelect?: (id: string) => void;
  openSource?: (path: string) => void;
}) {
  const [downloadError, setDownloadError] = useState("");
  const rows = runFileRows(run, events).filter(
    (r) =>
      r.name.toLowerCase().includes(search.toLowerCase()) &&
      (filter === "all" ||
        (filter === "archive"
          ? !!r.archived
          : filter === "copy"
            ? !!r.source || r.artifact?.policy === "copy"
            : r.artifact?.policy === filter)),
  );
  async function download(
    event: React.MouseEvent<HTMLAnchorElement>,
    url: string,
    name: string,
  ) {
    if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey)
      return;
    event.preventDefault();
    setDownloadError("");
    try {
      const response = await fetch(url);
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(
          typeof body.detail === "string"
            ? body.detail
            : "Verified download unavailable. Check the original archive or managed copy.",
        );
      }
      const object = URL.createObjectURL(await response.blob()),
        anchor = document.createElement("a");
      anchor.href = object;
      anchor.download = name;
      anchor.click();
      setTimeout(() => URL.revokeObjectURL(object), 30000);
    } catch (e) {
      setDownloadError((e as Error).message);
    }
  }
  const connected = (r: Revision) =>
    connection?.state === "connected" &&
    connection.identity === r.event.repository?.identity;
  const gitUrl = (r: Revision) =>
    `/api/runs/${run.id}/archive/${r.event.id}/${r.index}/file`;
  return (
    <div className="run-files-list">
      {downloadError && <p role="alert">{downloadError}</p>}
      {!rows.length && <p>No files match this view.</p>}
      {rows.map((row) => {
        const a = row.artifact,
          rev = row.archived;
        const local =
          !!row.source ||
          (a?.policy === "copy" && a.availability === "available");
        const localUrl = row.source
          ? `/api/runs/${run.id}/source-file?path=${encodeURIComponent(row.source.path)}`
          : `/api/artifacts/${a?.id}/file?download=true`;
        const primary = local
          ? localUrl
          : rev && connected(rev)
            ? gitUrl(rev)
            : null;
        const eligible =
          a?.policy === "copy" && !a.automatic && run.status !== "running";
        return (
          <article key={row.key} className="run-file-row" aria-label={row.name}>
            <div className="run-file-name">
              <strong>{row.name}</strong>
              <small>{row.size.toLocaleString()} bytes</small>
              {eligible && (
                <label className="archive-choice">
                  <input
                    type="checkbox"
                    disabled={disabled}
                    checked={selected.includes(a.id)}
                    onChange={() => onSelect(a.id)}
                    aria-label={`Select ${row.name} for archive`}
                  />
                  Select for archive
                </label>
              )}
            </div>
            <div className="run-file-storage">
              {row.source && <span>Retained source snapshot</span>}
              {a && (
                <span>
                  {a.policy === "copy"
                    ? "Retained in library"
                    : a.policy === "reference"
                      ? "Reference only"
                      : "Not retained"}{" "}
                  · {a.availability.replaceAll("-", " ")}
                </span>
              )}
              {rev ? (
                <span>
                  Preserved in Git · {rev.file.category} ·{" "}
                  <code>{rev.event.commit.slice(0, 9)}</code>
                  {row.revisions.length > 1
                    ? ` · ${row.revisions.length} events`
                    : ""}
                </span>
              ) : (
                <span>No Git copy recorded</span>
              )}
              {rev && !connected(rev) && (
                <small>
                  Git download unavailable — connect the original archive for
                  this revision.
                </small>
              )}
              {a?.original_path && a.policy === "reference" && (
                <small className="path">{a.original_path}</small>
              )}
              {a?.reason && <small className="text-amber">{a.reason}</small>}
              {a?.caption && <span>Current caption: {a.caption}</span>}
            </div>
            <div className="run-file-download">
              {row.source && openSource && (
                <button onClick={() => openSource(row.source!.path)}>
                  View in Source
                </button>
              )}
              {primary ? (
                <a
                  href={primary}
                  onClick={(e) => void download(e, primary, row.name)}
                  aria-label={`Download ${local ? "library copy" : "Git revision"} of ${row.name}`}
                >
                  {local ? "Download library copy" : "Download Git revision"}
                </a>
              ) : (
                <span>No downloadable copy available</span>
              )}
              <details>
                <summary>Identity and revisions</summary>
                <p>
                  Run: <code>{run.id}</code>
                  <br />
                  SHA-256:{" "}
                  <code>
                    {row.source?.blob ||
                      a?.blob ||
                      rev?.file.blob ||
                      "No retained bytes"}
                  </code>
                </p>
                {row.revisions.map((r) => (
                  <p key={r.event.id + ":" + r.index}>
                    Event: {r.event.kind}
                    <br />
                    Commit: <code>{r.event.commit}</code>
                    <br />
                    {connected(r) && (
                      <a
                        href={gitUrl(r)}
                        onClick={(e) => void download(e, gitUrl(r), row.name)}
                      >
                        Retrieve this Git revision
                      </a>
                    )}
                  </p>
                ))}
                <p>
                  Downloads verify exact retained bytes. Current source and
                  external references are never substituted. Captions and notes
                  have separate reviewed revision records.
                </p>
              </details>
            </div>
          </article>
        );
      })}
    </div>
  );
}

export function PreservationStatus({
  run,
  value,
}: {
  run: Run;
  value: Review | null;
}) {
  const counts = run.capture_counts || {};
  return (
    <section
      className="preservation-status"
      aria-label="Run preservation status"
    >
      <p>
        <strong>Execution:</strong> {run.status} ·{" "}
        <strong>Workspace capture:</strong> {run.capture_status || "unknown"} (
        {counts.copied || 0} copied, {counts.referenced || 0} referenced,{" "}
        {counts.ignored || 0} ignored, {counts.skipped || 0} skipped)
      </p>
      <p>
        <strong>Master Git preservation:</strong>{" "}
        {value?.state === "verified"
          ? "Verified for the reviewed scope"
          : value?.state?.replaceAll("_", " ") || "status unavailable"}
        .{" "}
        {value?.state === "verified"
          ? "Verified at publication; inspect each event for exclusions."
          : value?.reason}
      </p>
      {value && (
        <p>
          {value.source_files} source files and {value.output_files} of{" "}
          {value.copied_outputs} copied outputs in initial preservation;{" "}
          {value.annotations} annotation entries in {value.events} events.
          Repository access: {value.connection}.
        </p>
      )}
    </section>
  );
}
export function PreservationSummary({ run }: { run: Run }) {
  const [value, setValue] = useState<Review | null>(null);
  useEffect(() => {
    let active = true;
    const load = () =>
      api<Review>(`/runs/${run.id}/archive`)
        .then((v) => {
          if (active) setValue(v.preservation);
        })
        .catch(() => {
          if (active) setValue(null);
        });
    void load();
    const timer = setInterval(load, 3000);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [run.id]);
  return <PreservationStatus run={run} value={value} />;
}
