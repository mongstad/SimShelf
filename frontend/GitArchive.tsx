import React, { useEffect, useState } from "react";
import { api, uploadFile } from "./api";
import type { Run, Simulation } from "./types";

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
  const [settings, setSettings] = useState<Review | null>(null);
  const [runs, setRuns] = useState<Review[]>([]);
  const [path, setPath] = useState("");
  const [initialize, setInitialize] = useState(false);
  const [future, setFuture] = useState("");
  const [review, setReview] = useState<Review | null>(null);
  const [busy, setBusy] = useState(false),
    [message, setMessage] = useState("");
  async function load() {
    const c = await api<Review>("/workspace/archive");
    const s = await api<Review>(`/simulations/${simulation.id}/archive`);
    setConnection(c.connection);
    setSettings(s.settings);
    setRuns(s.runs);
    setPath(c.connection?.path || "");
    setFuture(s.settings?.future.join("\n") || "");
  }
  useEffect(() => {
    void load().catch((e) => setMessage(e.message));
  }, [simulation.id]);
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
  const post = (path: string, body: Review = {}) =>
    api<Review>(path, { method: "POST", body: JSON.stringify(body) });
  return (
    <section className="git-archive">
      <h2>Shared master Git archive</h2>
      <p>
        One separate local repository for all simulations. Archive commits are
        independent of scientific versions and source Git history. No uploads or
        remote synchronization.
      </p>
      {message && <p role="status">{message}</p>}
      {connection && (
        <p>
          Configured archive: <code>{connection.path}</code>
        </p>
      )}
      <details>
        <summary>
          {connection
            ? "Reconnect or disconnect archive"
            : "Set up archive repository"}
        </summary>
        <label>
          Dedicated archive directory
          <input
            value={path}
            disabled={busy}
            onChange={(e) => setPath(e.target.value)}
          />
        </label>
        <label className="archive-choice">
          <input
            type="checkbox"
            checked={initialize}
            disabled={busy}
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
          disabled={busy || !path.trim()}
          onClick={() =>
            void action(async () => {
              await post("/workspace/archive/connect", {
                path,
                initialize,
                confirmed: true,
              });
              await load();
              setMessage(
                "Archive connected. Review per-simulation consent below.",
              );
            })
          }
        >
          {initialize
            ? "Initialize and connect archive"
            : "Connect archive locally"}
        </button>{" "}
        {connection && (
          <button
            disabled={busy}
            onClick={() =>
              void action(async () => {
                await post("/workspace/archive/disconnect");
                await load();
              })
            }
          >
            Disconnect archive
          </button>
        )}
      </details>
      <h3>Automatic archive for {simulation.name}</h3>
      <p>
        {settings
          ? "Consent saved. Changed locations or capture settings require review again."
          : "Automatic archival is off."}{" "}
        Existing file choices come from Manage Git files above; saving those
        choices alone never enables archival.
      </p>
      <label>
        Future outputs — one filename or pattern per line
        <textarea
          value={future}
          disabled={busy}
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
      <button
        disabled={busy || !connection}
        onClick={() =>
          void action(async () =>
            setReview(
              await post(`/simulations/${simulation.id}/archive/preview`, {
                future: future
                  .split("\n")
                  .map((s) => s.trim())
                  .filter(Boolean),
              }),
            ),
          )
        }
      >
        Review automatic archive
      </button>{" "}
      {settings && (
        <button
          disabled={busy}
          onClick={() =>
            void action(async () => {
              await post(`/simulations/${simulation.id}/archive/disable`);
              setReview(null);
              await load();
            })
          }
        >
          Disable for future runs
        </button>
      )}
      {review && (
        <section aria-label="Automatic archive consent">
          <h3>Review and enable</h3>
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
                setMessage("Automatic archive enabled for future runs.");
              })
            }
          >
            Enable automatic archive for this simulation
          </button>{" "}
          <button disabled={busy} onClick={() => setReview(null)}>
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

export function ArchiveInventory({
  runId,
  events,
}: {
  runId: string;
  events: Review[];
}) {
  return (
    <>
      {events.map((e) => (
        <section key={e.id}>
          <h3>
            {e.kind === "initial"
              ? "Initial run archive"
              : "Post-run additions"}{" "}
            · <code>{e.commit.slice(0, 9)}</code>
          </h3>
          <ul>
            {e.files.map((f: Review, i: number) => (
              <li key={f.path}>
                <a href={`/api/runs/${runId}/archive/${e.id}/${i}/file`}>
                  Download {f.name}
                </a>{" "}
                <small>
                  {f.category} · {f.size.toLocaleString()} bytes
                </small>
              </li>
            ))}
          </ul>
          {!!e.skipped.length && (
            <details>
              <summary>Not archived ({e.skipped.length})</summary>
              <ul>
                {e.skipped.map((s: Review, i: number) => (
                  <li key={i}>
                    {s.name}: {s.reason}
                  </li>
                ))}
              </ul>
            </details>
          )}
        </section>
      ))}
    </>
  );
}
export function RunArchive({ run, reload }: { run: Run; reload: () => void }) {
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
          if (active) setMessage(e.message);
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
  const used = new Set(
    view?.events.flatMap((e: Review) =>
      e.files.map((f: Review) => f.artifact_id),
    ) || [],
  );
  return (
    <section className="git-archive">
      <h2>Git-archived files</h2>
      <p>
        Historical downloads use each file’s exact commit. Earlier filename
        revisions remain available. {archiveLimits}
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
      {view && <ArchiveInventory runId={run.id} events={view.events} />}
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
                    "Files attached. Select attachments below to archive them.",
                  );
                });
              }}
            />
          </label>
          <fieldset disabled={busy || !!view?.pending}>
            <legend>Managed attachments to archive</legend>
            {(run.artifacts || [])
              .filter(
                (a) => a.policy === "copy" && !a.automatic && !used.has(a.id),
              )
              .map((a) => (
                <label className="archive-choice" key={a.id}>
                  <input
                    type="checkbox"
                    checked={selected.includes(a.id)}
                    onChange={(e) => {
                      setSelected(
                        e.target.checked
                          ? [...selected, a.id]
                          : selected.filter((id) => id !== a.id),
                      );
                      setReview(null);
                    }}
                  />
                  {a.name} · {a.size.toLocaleString()} bytes
                </label>
              ))}
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
