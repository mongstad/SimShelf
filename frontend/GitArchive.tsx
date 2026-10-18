import React, { useEffect, useRef, useState } from "react";
import { api, uploadFile } from "./api";
import type { Artifact, Run, Simulation } from "./types";

type Review = Record<string, any>;
export const archiveLimits =
  "1,000 files · 25 MiB per file · 100 MiB per run, including later additions.";
export function FutureOutputHelp({ directory }: { directory: string }) {
  return (
    <p className="muted">
      Future outputs are relative to the capture directory{" "}
      <code>{directory}</code>, not the Python source folder. For example:{" "}
      <code>result.csv</code> or <code>logs/*.csv</code>. CSVs beside your
      Python script, outside this directory, require manual post-run attachment.
      No simulation is launched to discover files.
    </p>
  );
}
export function ArchiveSettings({ simulation }: { simulation: Simulation }) {
  const [connection, setConnection] = useState<Review | null>(null);
  const [status, setStatus] = useState<Review | null>(null);
  const [automatic, setAutomatic] = useState<Review | null>(null);
  const rememberedConnection = useRef<Review | null>(null);
  const setupPanel = useRef<HTMLDetailsElement | null>(null);
  const setupPath = useRef<HTMLInputElement | null>(null);
  const returnFocus = useRef<HTMLElement | null>(null);
  const cancelReview = useRef<HTMLButtonElement | null>(null);
  const reviewAction = useRef<HTMLButtonElement | null>(null);
  const automaticPanel = useRef<HTMLDetailsElement | null>(null);
  const restoreFocus = useRef(false);
  const [runs, setRuns] = useState<Review[]>([]);
  const [path, setPath] = useState("");
  const [initialize, setInitialize] = useState(false);
  const [future, setFuture] = useState("");
  const [review, setReview] = useState<Review | null>(null);
  const [busy, setBusy] = useState(false),
    [message, setMessage] = useState("");
  async function load(refreshDraft = true) {
    const c = await api<Review>("/workspace/archive");
    const s = await api<Review>(`/simulations/${simulation.id}/archive`);
    setConnection(c.connection);
    rememberedConnection.current =
      c.connection || c.remembered_connection || null;
    setStatus(c.status);
    setAutomatic(s.automatic_status);
    setRuns(s.runs);
    if (refreshDraft || c.connection)
      setPath(c.connection?.path || rememberedConnection.current?.path || "");
    if (refreshDraft) setFuture(s.settings?.future.join("\n") || "");
  }
  useEffect(() => {
    void load().catch((e) => {
      setStatus(null);
      setAutomatic(null);
      setMessage(e.message);
    });
  }, [simulation.id]);
  useEffect(() => {
    if (review) {
      cancelReview.current?.focus();
      restoreFocus.current = true;
    } else if (!busy && restoreFocus.current) {
      const target = returnFocus.current?.isConnected
        ? returnFocus.current
        : reviewAction.current;
      if (target === reviewAction.current && automaticPanel.current)
        automaticPanel.current.open = true;
      target?.focus();
      restoreFocus.current = false;
    }
  }, [review, busy]);
  async function action(work: () => Promise<void>) {
    setBusy(true);
    setMessage("");
    try {
      await work();
    } catch (e) {
      setReview(null);
      // Refresh authoritative state after rejection or a lost response. Never
      // infer enablement from an attempted request; keep editable rules intact.
      try {
        await load(false);
      } catch {
        setStatus(null);
        setAutomatic(null);
      }
      setMessage((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  const post = (path: string, body: Review = {}) =>
    api<Review>(path, { method: "POST", body: JSON.stringify(body) });
  const enabled = automatic?.state === "enabled";
  async function requestReview(trigger: HTMLElement) {
    returnFocus.current = trigger;
    restoreFocus.current = true;
    await action(async () => {
      setReview(
        await post(`/simulations/${simulation.id}/archive/preview`, {
          future: future
            .split("\n")
            .map((s) => s.trim())
            .filter(Boolean),
        }),
      );
    });
  }
  return (
    <section className="git-archive">
      <h2>Shared master Git archive</h2>
      <MasterArchiveStatus
        status={status}
        configured={!!connection}
        busy={busy || !!review}
        onChange={(trigger) => {
          returnFocus.current = trigger;
          restoreFocus.current = true;
          if (connection) {
            void action(async () => {
              await post("/workspace/archive/disconnect");
              setReview(null);
              await load();
            });
          } else {
            const previous = connection || rememberedConnection.current;
            if (
              !previous?.path ||
              !previous?.identity ||
              !previous?.workspace
            ) {
              restoreFocus.current = false;
              if (setupPanel.current) setupPanel.current.open = true;
              setupPath.current?.focus();
              setMessage(
                "Choose an archive location and confirm setup to connect.",
              );
            } else {
              void action(async () => {
                await post("/workspace/archive/connect", {
                  path: previous.path,
                  expected_connection: previous,
                  confirmed: true,
                });
                await load();
                setMessage(
                  "Original archive reconnected. Saved consent was not changed.",
                );
              });
            }
          }
        }}
      />
      {connection && (
        <p className="path">
          {status?.state === "connected"
            ? "Verified archive:"
            : "Configured path (unavailable):"}{" "}
          <code>{connection.path}</code>
        </p>
      )}
      {message && <p role="alert">{message}</p>}
      <AutomaticArchiveToggle
        name={simulation.name}
        automatic={automatic}
        busy={busy || !!review}
        available={status?.state === "connected"}
        onChange={(trigger) => {
          returnFocus.current = trigger;
          restoreFocus.current = true;
          if (!enabled) void requestReview(trigger);
          else
            void action(async () => {
              await post(`/simulations/${simulation.id}/archive/disable`);
              setReview(null);
              await load();
            });
        }}
      />
      <button
        disabled={busy}
        onClick={() => {
          setReview(null);
          void action(() => load());
        }}
      >
        Refresh archive status
      </button>
      <p>
        One separate local repository for all simulations. Archive commits are
        independent of scientific versions and source Git history. No uploads or
        remote synchronization.
      </p>
      <details ref={setupPanel}>
        <summary>Archive location and setup</summary>
        <label>
          Dedicated archive directory
          <input
            ref={setupPath}
            value={connection?.path || path}
            readOnly={!!connection}
            disabled={busy}
            aria-describedby="archive-location-help"
            onChange={(e) => setPath(e.target.value)}
          />
        </label>
        <p id="archive-location-help" className="muted">
          {connection
            ? "Disconnect the master archive before changing its location."
            : rememberedConnection.current
              ? path === rememberedConnection.current.path
                ? "Last connected directory, remembered only. Switch ON or confirm the location to verify and reconnect."
                : `Proposed directory, not connected. Last connected: ${rememberedConnection.current.path}`
              : "Choose a dedicated archive directory. Nothing connects automatically."}
        </p>
        <label className="archive-choice">
          <input
            type="checkbox"
            checked={initialize}
            disabled={busy || !!connection}
            onChange={(e) => setInitialize(e.target.checked)}
          />
          Initialize this existing empty directory as a dedicated archive
        </label>
        <p>
          Connect only a SimShelf archive, or explicitly initialize an empty
          directory. Keep it separate from source folders and the library. This
          uses a bare Git repository with no working tree. Existing source
          repositories cannot be used.
        </p>
        <button
          disabled={busy || !!review || !!connection || !path.trim()}
          onClick={(e) => {
            returnFocus.current = e.currentTarget;
            restoreFocus.current = true;
            void action(async () => {
              await post("/workspace/archive/connect", {
                path,
                initialize,
                confirmed: true,
              });
              await load();
              setMessage(
                "Archive location confirmed. Automatic archival uses its separate consent.",
              );
              setInitialize(false);
            });
          }}
        >
          {initialize
            ? "Initialize and connect archive"
            : "Confirm archive location"}
        </button>{" "}
      </details>
      <p className="muted">
        Workspace backups do not include the external Git archive.
      </p>
      <details ref={automaticPanel}>
        <summary>Automatic archival settings</summary>
        <p>
          File choices come from Manage Git files in the Source Git section.
          Changing settings requires a fresh review; saving file choices alone
          never enables archival.
        </p>
        <label>
          Future outputs — one filename or pattern per line
          <textarea
            value={future}
            disabled={busy || !!review}
            onChange={(e) => {
              setFuture(e.target.value);
              setReview(null);
            }}
            placeholder={"result.csv\nlogs/*.csv"}
          />
        </label>
        <FutureOutputHelp directory={simulation.config.output_dir} />
        <p>
          {archiveLimits} Git retains earlier versions even after a run or
          attachment is deleted. Back up this repository separately from your
          library.
        </p>
        {!review && (
          <button
            ref={reviewAction}
            disabled={busy || status?.state !== "connected"}
            onClick={(e) => void requestReview(e.currentTarget)}
          >
            Review archival settings
          </button>
        )}
        {message && <p role="alert">{message}</p>}
      </details>
      {review && (
        <section aria-label="Automatic archive consent">
          <h3>
            {enabled ? "Review archival changes" : "Review automatic archival"}
          </h3>
          <p>
            Future runs will automatically create local commits from selected
            run-start source snapshots and verified managed output copies.
            Failed runs may archive partial results. Process status is
            independent.
          </p>
          <p>
            These future-output rules request Keep a copy before other capture
            rules, inside <code>{review.capture_config.output_dir}</code>.
            Existing capture size limits still apply.
          </p>
          <ul>
            {review.future.map((r: string) => (
              <li key={r}>
                <code>{r}</code> — copy and archive when attributable
              </li>
            ))}
          </ul>
          <p>Existing file selection rules:</p>
          <ul>
            {review.rules.map((r: Review, i: number) => (
              <li key={i}>
                {r.kind}: <code>{r.value}</code>
              </li>
            ))}
          </ul>
          <p>
            Other selected outputs must already have Keep a copy coverage.
            Missing, unchanged, unstable or oversized outputs are skipped.
            Source files excluded from the run snapshot cannot be archived
            automatically.
          </p>
          <button
            disabled={busy}
            onClick={() =>
              void action(async () => {
                await post(`/simulations/${simulation.id}/archive/enable`, {
                  review,
                  confirmed: true,
                });
                setReview(null);
                await load();
                setMessage("Archival settings saved for future runs.");
              })
            }
          >
            Confirm changes
          </button>{" "}
          <button
            ref={cancelReview}
            disabled={busy}
            onClick={() => {
              setReview(null);
              setMessage("Review canceled. Settings unchanged.");
            }}
          >
            Cancel
          </button>
        </section>
      )}
      <details>
        <summary>This simulation’s archive history</summary>
        <p>Latest 200 runs only; other simulations are excluded.</p>
        <ul>
          {runs
            .filter((r) => r.events.length)
            .map((r) => (
              <li key={r.run}>
                {r.name}: {r.events.length} archive commits{" "}
                {r.events.map((e: Review) => (
                  <code key={e.id}> {e.commit.slice(0, 9)}</code>
                ))}
              </li>
            ))}
        </ul>
      </details>
    </section>
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
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");
  const [view, setView] = useState<Review | null>(null),
    [selected, setSelected] = useState<string[]>([]);
  const [review, setReview] = useState<Review | null>(null),
    [operation, setOperation] = useState("");
  const [busy, setBusy] = useState(false),
    [message, setMessage] = useState("");
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
  async function action(work: () => Promise<void>) {
    setBusy(true);
    setMessage("");
    try {
      await work();
    } catch (e) {
      setMessage((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  const post = (suffix: string, body: Review) =>
    api<Review>(`/runs/${run.id}/archive/${suffix}`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  return (
    <section className="git-archive">
      <h2>Run files</h2>
      <p>
        Workspace copies download without Git. Git revisions use their exact
        archived commit. Earlier filename revisions remain separate.
      </p>
      {message && <p role="status">{message}</p>}
      {view?.error && <p role="alert">Archive: {view.error}</p>}
      {view?.initial?.state === "prepared" && run.status !== "running" && (
        <p>
          Initial archive is not yet verified. If the recorder has stopped, no
          live files will be recovered automatically; attach verified files
          manually if needed.
        </p>
      )}
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
          <option value="copy">Saved copies</option>
          <option value="archive">Archived in Git</option>
          <option value="reference">References</option>
          <option value="skipped">Skipped</option>
        </select>
      </div>
      {!view && (
        <p role="status">
          Archive history unavailable until loaded. Workspace files remain
          accessible.
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
        disabled={busy || !!view?.pending || !view || run.status === "running"}
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
          <summary>Archive events and omissions ({view.events.length})</summary>
          <p>
            {archiveLimits} Workspace backups do not include the external Git
            archive.
          </p>
          {view.events.map((e: Review) => (
            <section key={e.id}>
              <h3>
                {e.kind === "initial"
                  ? "Initial run archive"
                  : "Post-run additions"}{" "}
                · <code>{e.commit.slice(0, 9)}</code>
              </h3>
              <ul>
                {e.skipped.map((s: Review, i: number) => (
                  <li key={i}>
                    {s.name}: {s.reason}
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </details>
      )}
      {view && !view.events.length && (
        <p>No verified archive commits for this run.</p>
      )}
      {view?.pending && (
        <>
          <p>
            A previously approved archive operation is pending. Retry uses its
            original managed bytes.
          </p>
          <button
            disabled={busy}
            onClick={() =>
              void action(async () => {
                await post("retry", { confirmed: true });
                await load();
              })
            }
          >
            Retry approved archive
          </button>
        </>
      )}
      {run.status !== "running" && (
        <>
          <h3>Add files after execution</h3>
          <p>
            Attach screenshots or analysis files to this run, then optionally
            select them for Git. Attaching alone does not commit anything.
            Archive copies remain in Git history after an attachment is removed.
          </p>
          <label>
            Attach files
            <input
              type="file"
              multiple
              disabled={busy}
              onChange={(e) => {
                const files = Array.from(e.target.files || []);
                e.target.value = "";
                void action(async () => {
                  for (const f of files) await uploadFile(run.id, f);
                  reload();
                  setMessage(
                    "Files attached. Select attachments in Run files to archive them.",
                  );
                });
              }}
            />
          </label>
          <fieldset
            disabled={
              busy ||
              !!view?.pending ||
              view?.connection_status?.state !== "connected"
            }
          >
            <legend>Archive selected attachments ({selected.length})</legend>
            <p>
              Select eligible workspace attachments in the Run files list, then
              review.
            </p>
            <button
              disabled={!selected.length}
              onClick={() =>
                void action(async () => {
                  setReview(await post("preview", { artifact_ids: selected }));
                  setOperation(crypto.randomUUID().replaceAll("-", ""));
                })
              }
            >
              Review archive additions
            </button>
          </fieldset>
          {review && (
            <section aria-label="Archive additions review">
              <h3>Confirm new archival commit</h3>
              <ul>
                {review.files.map((f: Review) => (
                  <li key={f.artifact_id}>
                    {f.name} · {f.size.toLocaleString()} bytes
                  </li>
                ))}
              </ul>
              <p>
                These additions belong to this existing run. Earlier commits and
                scientific records stay unchanged.
              </p>
              <button
                disabled={busy}
                onClick={() =>
                  void action(async () => {
                    await post("add", { review, operation, confirmed: true });
                    setReview(null);
                    setSelected([]);
                    await load();
                    setMessage("Additions archived.");
                  })
                }
              >
                Archive selected attachments
              </button>{" "}
              <button disabled={busy} onClick={() => setReview(null)}>
                Cancel
              </button>
            </section>
          )}
        </>
      )}
    </section>
  );
}

export function MasterArchiveStatus({
  status,
  busy = false,
  configured = false,
  onChange,
}: {
  status?: Review | null;
  busy?: boolean;
  configured?: boolean;
  onChange?: (trigger: HTMLButtonElement) => void;
}) {
  const connected = status?.state === "connected";
  return (
    <div className="automatic-archive-control">
      <div className="automatic-archive-line">
        <span
          role="status"
          aria-live="polite"
          className={connected ? "archive-connected" : ""}
        >
          {connected && <span aria-hidden="true">✓ </span>}
          Master simulation archive —{" "}
          {connected
            ? "Connected"
            : status?.state === "disconnected"
              ? "Disconnected"
              : configured
                ? "Unavailable — configured"
                : "Unavailable"}
        </span>
        {onChange && (
          <button
            type="button"
            role="switch"
            aria-label="Master simulation archive connection"
            aria-checked={connected || configured}
            aria-describedby="master-archive-help"
            className="archive-toggle"
            disabled={busy || !status}
            onClick={(e) => onChange(e.currentTarget)}
          >
            <span className="archive-toggle-knob" aria-hidden="true" />
            {connected || configured ? "ON" : "OFF"}
          </button>
        )}
      </div>
      <small id="master-archive-help">
        {status?.reason ||
          "Shared repository access. Automatic archival is set separately for each simulation."}
      </small>
    </div>
  );
}

type FileRow = {
  key: string;
  name: string;
  size: number;
  artifact?: Artifact;
  archived?: { event: Review; file: Review; index: number };
};
export function runFileRows(run: Run, events: Review[]): FileRow[] {
  const rows: FileRow[] = (run.artifacts || []).map((artifact) => ({
    key: `artifact:${artifact.id}`,
    name: artifact.name,
    size: artifact.size,
    artifact,
  }));
  for (const event of events)
    event.files.forEach((file: Review, index: number) => {
      // Identity plus content: neither a coincident filename nor identical bytes
      // alone identify a historical attachment. Never collapse separate events.
      const row =
        file.artifact_id &&
        rows.find(
          (r) =>
            !r.archived &&
            r.artifact?.id === file.artifact_id &&
            r.artifact?.policy === "copy" &&
            !!file.blob &&
            r.artifact?.blob === file.blob &&
            r.size === file.size,
        );
      const archived = { event, file, index };
      if (row) row.archived = archived;
      else
        rows.push({
          key: `event:${event.id}:${index}`,
          name: file.name,
          size: file.size,
          archived,
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
  const used = new Set(
    events.flatMap((e) => e.files.map((f: Review) => f.artifact_id)),
  );
  const rows = runFileRows(run, events).filter(
    (r) =>
      r.name.toLowerCase().includes(search.toLowerCase()) &&
      (filter === "all" ||
        (filter === "archive" ? !!r.archived : r.artifact?.policy === filter)),
  );
  async function downloadGit(
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
            : "Historical download unavailable. Check the master archive and retry.",
        );
      }
      const blob = await response.blob(),
        object = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = object;
      anchor.download = name;
      anchor.click();
      setTimeout(() => URL.revokeObjectURL(object), 30000);
    } catch (error) {
      setDownloadError((error as Error).message);
    }
  }
  return (
    <div className="run-files-list">
      {downloadError && <p role="alert">{downloadError}</p>}
      {!rows.length && <p>No files match this view.</p>}
      {rows.map((row) => {
        const a = row.artifact,
          archived = row.archived;
        const local = a?.policy === "copy" && a.availability === "available";
        const connected =
          !!archived &&
          connection?.state === "connected" &&
          connection.identity === archived.event.repository?.identity;
        const snapshot =
          archived?.file.category === "source" &&
          run.snapshot?.files.find(
            (f) =>
              f.path === archived.file.name &&
              f.blob === archived.file.blob &&
              f.size === archived.file.size,
          );
        const gitUrl = archived
          ? `/api/runs/${run.id}/archive/${archived.event.id}/${archived.index}/file`
          : "";
        const eligible =
          a?.policy === "copy" &&
          !a.automatic &&
          !used.has(a.id) &&
          run.status !== "running";
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
              {a && (
                <span>
                  {a.policy === "copy"
                    ? "Preserved in workspace"
                    : a.policy === "reference"
                      ? "Reference only"
                      : "Not preserved"}{" "}
                  · {a.availability.replaceAll("-", " ")}
                </span>
              )}
              {archived && (
                <span>
                  Archived in Git · {archived.file.category} ·{" "}
                  <code>{archived.event.commit.slice(0, 9)}</code>
                </span>
              )}
              {archived && !connected && (
                <small>
                  {connection?.state === "connected"
                    ? "Connect the original archive for this revision."
                    : "Git download unavailable — connect or check the master archive."}
                </small>
              )}
              {a?.original_path && a.policy === "reference" && (
                <small className="path">{a.original_path}</small>
              )}
              {a?.reason && <small className="text-amber">{a.reason}</small>}
            </div>
            <div className="run-file-download">
              {snapshot && (
                <p>
                  Matching workspace source snapshot.{" "}
                  {openSource && (
                    <button onClick={() => openSource(snapshot.path)}>
                      View in Source
                    </button>
                  )}
                </p>
              )}
              {local ? (
                <a
                  href={`/api/artifacts/${a.id}/file?download=true`}
                  aria-label={`Download workspace copy of ${row.name}`}
                >
                  Download workspace copy
                </a>
              ) : connected ? (
                <a
                  href={gitUrl}
                  onClick={(e) => void downloadGit(e, gitUrl, row.name)}
                  aria-label={`Download Git revision of ${row.name}`}
                >
                  Download Git revision
                </a>
              ) : (
                <span>
                  {snapshot
                    ? "Git download unavailable"
                    : "No downloadable copy available"}
                </span>
              )}
              {archived && (
                <details>
                  <summary>Revision details</summary>
                  <p>
                    Archive event: {archived.event.kind}
                    <br />
                    Commit: <code>{archived.event.commit}</code>
                    <br />
                    SHA-256: <code>{archived.file.blob}</code>
                  </p>
                  {local && connected && (
                    <a
                      href={gitUrl}
                      onClick={(e) => void downloadGit(e, gitUrl, row.name)}
                      aria-label={`Download Git revision of ${row.name}`}
                    >
                      Download Git revision
                    </a>
                  )}
                  <p>
                    Git downloads verify this exact event and path, never the
                    current source file.
                  </p>
                </details>
              )}
            </div>
          </article>
        );
      })}
    </div>
  );
}

export function AutomaticArchiveToggle({
  name,
  automatic,
  busy,
  available,
  onChange,
}: {
  name: string;
  automatic: Review | null;
  busy: boolean;
  available: boolean;
  onChange: (trigger: HTMLButtonElement) => void;
}) {
  const enabled = automatic?.state === "enabled";
  const label = enabled
    ? "Enabled"
    : automatic?.state === "disabled"
      ? "Disabled"
      : automatic
        ? "Disabled — review required"
        : "Status unavailable";
  return (
    <div className="automatic-archive-control">
      <div className="automatic-archive-line">
        <span role="status" aria-live="polite">
          Automatic archival — {name} — <strong>{label}</strong>
        </span>
        <button
          type="button"
          role="switch"
          aria-checked={enabled}
          aria-label={`Automatic archival for ${name}`}
          aria-describedby="automatic-archive-help"
          className="archive-toggle"
          disabled={busy || !automatic || (!enabled && !available)}
          onClick={(e) => onChange(e.currentTarget)}
        >
          <span className="archive-toggle-knob" aria-hidden="true" />
          {enabled ? "ON" : "OFF"}
        </button>
      </div>
      <small id="automatic-archive-help">
        {automatic?.reason ||
          (!available
            ? "Connect an available master archive to request activation."
            : "Future runs only. Turning on requires review and confirmation.")}
      </small>
    </div>
  );
}
