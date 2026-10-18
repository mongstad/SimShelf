import React, { useState } from "react";
import { api } from "./api";

export type Rule = { kind: "file" | "folder" | "extension"; value: string };
export type FileItem = {
  path: string;
  size: number;
  state: string;
  risk: string;
  ignored_rule?: boolean;
};
type Inventory = {
  source: string;
  capture_directory: string;
  repository: { root: string } | null;
  reason: string | null;
  files: FileItem[];
  ignore_files: { path: string; text: string }[];
  blocked: string[];
  rules: Rule[];
  revision: string;
  ignore_writable: boolean;
};
type Selection = {
  revision: string;
  rules: Rule[];
  matches: { rule: Rule; paths: string[] }[];
  selected: string[];
};
type Ignore = {
  revision: string;
  paths: string[];
  target: string;
  before: string;
  addition: string;
};
export function included(path: string, rules: Rule[]) {
  return rules.some((r) =>
    r.kind === "file"
      ? path === r.value
      : r.kind === "folder"
        ? path.startsWith(r.value + "/")
        : path.lastIndexOf(".") > path.lastIndexOf("/") + 1 &&
          path.slice(path.lastIndexOf(".")) === r.value,
  );
}
export function FileLabel({ file }: { file: FileItem }) {
  return (
    <>
      <code>{file.path}</code>{" "}
      <small>
        {file.size.toLocaleString()} bytes ·{" "}
        {file.state === "tracked"
          ? "Already tracked"
          : file.state === "ignored"
            ? "Ignored by existing Git rules"
            : file.state === "untracked"
              ? "Untracked"
              : "Git state unknown"}
        {file.state === "tracked" && file.ignored_rule
          ? " · Also matches ignore rules; remains tracked"
          : ""}
      </small>
      {file.risk && <small className="git-file-warning">{file.risk}</small>}
    </>
  );
}
export function sameRules(left: Rule[], right: Rule[]) {
  const keys = (rules: Rule[]) =>
    rules.map((r) => JSON.stringify([r.kind, r.value])).sort();
  return JSON.stringify(keys(left)) === JSON.stringify(keys(right));
}

export async function saveSelection(
  base: string,
  revision: string,
  rules: Rule[],
  request: typeof api = api,
) {
  const review = await request<Selection>(base + "/files/preview", {
    method: "POST",
    body: JSON.stringify({ revision, rules }),
  });
  await request(base + "/files/save", {
    method: "POST",
    body: JSON.stringify({ review, confirmed: true }),
  });
}

export function SelectedRules({
  rules,
  files,
  remove,
}: {
  rules: Rule[];
  files: FileItem[];
  remove: (rule: Rule) => void;
}) {
  return (
    <details>
      <summary>Selected rules ({rules.length})</summary>
      {rules.map((rule) => {
        const paths = files
          .filter((f) => included(f.path, [rule]))
          .map((f) => f.path);
        return (
          <details key={JSON.stringify([rule.kind, rule.value])}>
            <summary>
              {rule.kind}: <code>{rule.value}</code> — {paths.length} matches
            </summary>
            <p>
              {rule.kind === "file"
                ? "This path only."
                : "Includes future matching files; review again before committing."}
            </p>
            <ul>
              {paths.map((path) => (
                <li key={path}>
                  <code>{path}</code>
                </li>
              ))}
            </ul>
            <button type="button" onClick={() => remove(rule)}>
              Remove {rule.kind} rule: {rule.value}
            </button>
          </details>
        );
      })}
    </details>
  );
}

export function SelectionStatus({
  count,
  dirty,
}: {
  count: number;
  dirty: boolean;
}) {
  return (
    <p role="status">
      {count} files selected ·{" "}
      {dirty ? "Unsaved changes" : "No unsaved changes"}
    </p>
  );
}

export function GitFiles({ simulationId }: { simulationId: string }) {
  const [open, setOpen] = useState(false),
    [data, setData] = useState<Inventory | null>(null);
  const [rules, setRules] = useState<Rule[]>([]),
    [ignorePaths, setIgnorePaths] = useState<string[]>([]);
  const [ignore, setIgnore] = useState<Ignore | null>(null);
  const [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [message, setMessage] = useState("");
  const base = `/simulations/${simulationId}/git`;
  async function action(work: () => Promise<void>) {
    setBusy(true);
    setError("");
    setMessage("");
    try {
      await work();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function load() {
    const d = await api<Inventory>(base + "/files");
    setData(d);
    setRules(d.rules);
    setIgnorePaths([]);
    setIgnore(null);
  }
  function toggle(rule: Rule, checked: boolean) {
    setMessage("");
    setRules(
      checked
        ? [...rules, rule]
        : rules.filter((r) => r.kind !== rule.kind || r.value !== rule.value),
    );
  }
  const has = (rule: Rule) =>
    rules.some((r) => r.kind === rule.kind && r.value === rule.value);
  const post = <T,>(path: string, body: unknown) =>
    api<T>(base + path, { method: "POST", body: JSON.stringify(body) });
  const extensions = Array.from(
    new Set(
      data?.files
        .map((f) => f.path.split("/").pop()!)
        .filter((n) => n.includes(".") && !n.startsWith("."))
        .map((n) => n.slice(n.lastIndexOf("."))) || [],
    ),
  ).sort();
  const folders = Array.from(
    new Set(
      data?.files.flatMap((f) => {
        const p = f.path.split("/");
        return p.slice(0, -1).map((_, i) => p.slice(0, i + 1).join("/"));
      }) || [],
    ),
  ).sort();
  return (
    <section className="git-files">
      <button
        disabled={busy}
        aria-expanded={open}
        onClick={() => {
          if (open) {
            setOpen(false);
            setData(null);
            setIgnore(null);
          } else {
            setOpen(true);
            void action(load);
          }
        }}
      >
        {open ? "Close file selection" : "Manage Git files"}
      </button>
      {open && (
        <>
          <h3>Include for future Git commits</h3>
          <p>
            Selections are saved for future Git commits. Saving does not stage
            or commit files.
          </p>
          {error && <p role="alert">{error}</p>}
          {message && <p role="status">{message}</p>}
          {busy && <p role="status">Checking files…</p>}
          <button disabled={busy} onClick={() => void action(load)}>
            Refresh files / discard edits
          </button>
          {data && (
            <>
              <p>
                <code>{data.source}</code>
              </p>
              {data.reason && <p role="status">{data.reason}</p>}
              <p className="muted">
                Capture directory <code>{data.capture_directory}/</code> is excluded
                from source inventory. Select generated results with Future outputs
                in Automatic archival settings. Other source files and configurations
                remain selectable; Git ignore rules do not hide them.
              </p>
              <p className="muted">
                Unchecking a tracked file leaves it tracked.
              </p>
              <fieldset disabled={busy}>
                <legend>Inclusion choices</legend>
                <details>
                  <summary>Folders and file types</summary>
                  <p>
                    Folder and extension rules include future matching files in
                    this simulation folder.
                  </p>
                  {extensions.map((value) => (
                    <label key={value}>
                      <input
                        type="checkbox"
                        checked={has({ kind: "extension", value })}
                        onChange={(e) =>
                          toggle({ kind: "extension", value }, e.target.checked)
                        }
                      />{" "}
                      All {value} files
                    </label>
                  ))}
                  {folders.map((value) => (
                    <label key={value}>
                      <input
                        type="checkbox"
                        checked={has({ kind: "folder", value })}
                        onChange={(e) =>
                          toggle({ kind: "folder", value }, e.target.checked)
                        }
                      />{" "}
                      Folder <code>{value}/</code>
                    </label>
                  ))}
                </details>
                <div
                  className="git-file-list"
                  aria-label="Source file selections"
                >
                  {data.files.map((file) => {
                    const direct = has({ kind: "file", value: file.path }),
                      group = included(
                        file.path,
                        rules.filter((r) => r.kind !== "file"),
                      );
                    return (
                      <div className="git-file-row" key={file.path}>
                        <label>
                          <input
                            type="checkbox"
                            checked={direct || group}
                            disabled={group}
                            onChange={(e) =>
                              toggle(
                                { kind: "file", value: file.path },
                                e.target.checked,
                              )
                            }
                            aria-label={`Include ${file.path}`}
                          />
                          <span>
                            <FileLabel file={file} />
                            {group && (
                              <small>
                                Included by folder/type choice; change that
                                choice to exclude.
                              </small>
                            )}
                          </span>
                        </label>
                      </div>
                    );
                  })}
                </div>
                {rules.length > 0 && (
                  <SelectedRules
                    rules={rules}
                    files={data.files}
                    remove={(rule) => toggle(rule, false)}
                  />
                )}
              </fieldset>
              <button
                disabled={busy || sameRules(rules, data.rules)}
                onClick={() =>
                  void action(async () => {
                    await saveSelection(base, data.revision, rules);
                    await load();
                    setMessage("Selection saved.");
                  })
                }
              >
                Save selection
              </button>
              <SelectionStatus
                count={
                  data.files.filter((file) => included(file.path, rules)).length
                }
                dirty={!sameRules(rules, data.rules)}
              />
              <details>
                <summary>Optional Git ignore additions</summary>
                <p>
                  Separate approval is required. Select exact untracked paths to
                  add to this folder’s .gitignore. Nothing is deleted.
                  Scientific data may be inputs: review it carefully.
                </p>
                <p className="muted">
                  Existing Git rules include parent/nested ignore files and
                  repository exclusions. Global Git configuration is not loaded.
                  Files beneath nested ignore rules require your Git tools.
                </p>
                {data.ignore_files.map((r) => (
                  <details key={r.path}>
                    <summary>
                      Existing rules: <code>{r.path}</code>
                    </summary>
                    <pre>{r.text}</pre>
                  </details>
                ))}
                <fieldset disabled={busy || !data.ignore_writable}>
                  <legend>Untracked paths to ignore</legend>
                  <div className="git-file-list">
                    {data.files
                      .filter(
                        (f) =>
                          f.state === "untracked" &&
                          f.path !== ".gitignore" &&
                          !f.path.endsWith("/.gitignore"),
                      )
                      .map((f) => (
                        <label key={f.path}>
                          <input
                            type="checkbox"
                            aria-label={`Ignore ${f.path}`}
                            checked={ignorePaths.includes(f.path)}
                            onChange={(e) => {
                              setIgnorePaths(
                                e.target.checked
                                  ? [...ignorePaths, f.path]
                                  : ignorePaths.filter((p) => p !== f.path),
                              );
                              setIgnore(null);
                            }}
                          />
                          <span>
                            <FileLabel file={f} />
                            {included(f.path, rules) && (
                              <small>
                                Also selected for future inclusion; review this
                                conflicting intent.
                              </small>
                            )}
                          </span>
                        </label>
                      ))}
                  </div>
                </fieldset>
                <button
                  disabled={
                    busy || !data.ignore_writable || !ignorePaths.length
                  }
                  onClick={() =>
                    void action(async () =>
                      setIgnore(
                        await post<Ignore>("/ignore/preview", {
                          revision: data.revision,
                          paths: ignorePaths,
                        }),
                      ),
                    )
                  }
                >
                  Preview ignore additions
                </button>
                {ignore && (
                  <section aria-label="Ignore preview">
                    <h4>Review .gitignore additions</h4>
                    <p>
                      Append only to <code>{ignore.target}</code>
                    </p>
                    <pre>{ignore.addition}</pre>
                    <p>
                      Only these exact paths will be ignored. Existing content
                      remains unchanged. No staging, commits or uploads.
                    </p>
                    <button
                      disabled={busy}
                      onClick={() =>
                        void action(async () => {
                          await post("/ignore/apply", {
                            review: ignore,
                            confirmed: true,
                          });
                          await load();
                          setMessage(
                            "Approved ignore additions applied. No files were staged or committed.",
                          );
                        })
                      }
                    >
                      Apply ignore additions
                    </button>{" "}
                    <button disabled={busy} onClick={() => setIgnore(null)}>
                      Cancel ignore preview
                    </button>
                  </section>
                )}
              </details>
              {data.blocked.length > 0 && (
                <details>
                  <summary>
                    Excluded from this inventory ({data.blocked.length})
                  </summary>
                  <ul>
                    {data.blocked.map((p, i) => (
                      <li key={i}>{p}</li>
                    ))}
                  </ul>
                </details>
              )}
            </>
          )}
        </>
      )}
    </section>
  );
}
