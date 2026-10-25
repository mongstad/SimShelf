// Real App fixture with immutable synthetic run records. No writes or execution.
import "./style.css";
const query = new URLSearchParams(location.search);
localStorage.setItem("simshelf-theme", query.get("theme") || "system");
let mode = query.get("state") || "healthy";
const entrypointCase = query.get("entrypoint");
const entrypointWarns = ["changed", "comment"].includes(entrypointCase);
location.hash = "#run/fixture-run";
const requests = [];
const simulation = {
  id: "sim",
  name: "Conservative cascade fixture",
  root: "/disposable/source",
  entrypoint: "simulate.py",
  description: "",
  available: true,
  run_count: 1,
  last_run: "2026-10-24T06:00:00Z",
  config: {
    output_dir: "outputs",
    source_include: ["*.py"],
    source_exclude: [],
    rules: [],
    max_file_mb: 25,
    max_run_mb: 100,
  },
};
function run() {
  const active = ["running", "stopping"].includes(mode);
  return {
    id: "fixture-run",
    simulation_id: "sim",
    name: "Conservative cascade · 50,000 steps",
    status: active
      ? "running"
      : mode === "failed"
        ? "failed"
        : mode === "interrupted"
          ? "interrupted"
          : "completed",
    version: "0.1.3",
    started_at: active
      ? new Date(Date.now() - 5000).toISOString()
      : "2026-10-24T06:00:00Z",
    ended_at: active ? null : "2026-10-24T06:02:00Z",
    duration: active ? null : 120,
    command: [
      "/disposable/env/bin/python",
      "simulate.py",
      "--steps",
      "50000",
      "--label",
      "",
    ],
    cwd: "/disposable/source",
    parameters: { steps: 50000 },
    parameter_sources: { steps: "python" },
    notes: "",
    tags: [],
    version_note: "",
    source_change: entrypointCase === "comment" ? "text-only" : entrypointCase ? "changed" : "same",
    entrypoint_warning: entrypointCase ? {warn:entrypointWarns,
      status:entrypointCase === "unavailable" ? "unavailable" : entrypointWarns ? "changed" : "same",
      detail:entrypointCase === "unavailable" ? "Fixture retained source is missing" : undefined} : undefined,
    snapshot_id: "0123456789abcdef",
    structure_id: "source-structure",
    baseline_run_id: "fixture-run",
    git: {
      commit: "abcd123456789",
      branch: "main",
      dirty: false,
      availability: "available",
      snapshot_relation: "captured_files_match_commit",
    },
    snapshot: {
      files: [{ path: "simulate.py", size: 20, blob: "sourcehash" }],
    },
    environment: {
      python: "3.14",
      executable: "/disposable/env/bin/python",
      platform: "Linux",
      source: "fixture",
      packages: [],
    },
    exit_code:
      active || mode === "interrupted" ? null : mode === "failed" ? 2 : 0,
    error: mode === "failed" ? "Specific fixture execution failure" : null,
    capture_root: "/disposable/source/outputs/run_fixture",
    capture_status:
      active || mode === "finalizing"
        ? "pending"
        : mode === "partial"
          ? "partial"
          : mode === "incomplete"
            ? "incomplete"
            : "complete",
    capture_counts: active
      ? undefined
      : { copied: 3, referenced: 1, ignored: 2, skipped: 0, unchanged: 1 },
    capture_errors:
      mode === "partial" ? ["Fixture copy budget exceeded for large.bin"] : [],
    source_warnings: [],
    can_stop: active,
    stop_requested: mode === "stopping",
    launch: { kind: "portal" },
    progress_mode: "step",
    progress: {
      current: active ? 25000 : 49999,
      total: 50000,
      stage: "Integration",
      source: "structured",
    },
    artifacts: [
      {
        id: "result",
        name: "result.csv",
        size: 12,
        blob: "resulthash",
        policy: "copy",
        availability: "available",
        media_type: "text/csv",
        caption: "",
        automatic: true,
      },
    ],
    metrics: [{ name: "energy", value: 0.002, step: 50000 }],
    metric_count: 1,
  };
}
function archive() {
  const state =
    mode === "git-partial"
      ? "partial"
      : mode === "git-failed"
        ? "failed"
        : mode === "pending"
          ? "pending"
          : mode === "not-enabled"
            ? "not_enabled"
            : "verified";
  return {
    events:
      state === "not_enabled"
        ? []
        : [
            {
              id: "initial",
              kind: "initial",
              commit: "abcdef123456789",
              repository: { identity: "repo" },
              files: [
                {
                  name: "simulate.py",
                  size: 20,
                  blob: "sourcehash",
                  category: "source",
                  artifact_id: null,
                },
                {
                  name: "result.csv",
                  size: 12,
                  blob: "resulthash",
                  category: "result",
                  artifact_id: "result",
                },
              ],
              skipped: [],
              record: {
                completeness: "verified",
                unknown_coverage: [],
                evidence: [],
                annotations: [
                  {
                    id: "annotation",
                    data: { notes: "Preserved fixture annotation" },
                  },
                ],
              },
            },
          ],
    pending: null,
    error: null,
    connection_status: {
      state: mode === "repository-unavailable" ? "unavailable" : "connected",
      identity: "repo",
      reason:
        mode === "repository-unavailable"
          ? "Fixture repository is offline"
          : null,
    },
    preservation: {
      state,
      reason:
        state === "partial"
          ? "Legacy selection has unknown scope."
          : "Fixture reviewed scope.",
      source_files: 1,
      output_files: 1,
      copied_outputs: 3,
      events: 1,
      annotations: 1,
      connection:
        mode === "repository-unavailable" ? "unavailable" : "connected",
    },
  };
}
window.fetch = async (url, options = {}) => {
  const path = new URL(url, location.origin).pathname;
  requests.push({ path, method: options.method || "GET" });
  if (options.method && options.method !== "GET")
    throw Error("Unexpected write " + path);
  let value;
  if (path === "/api/workspace")
    value = {
      path: "/disposable/library",
      version: "fixture",
      token: "fixture",
      schema_version: 4,
    };
  else if (path === "/api/simulations") value = [simulation];
  else if (path === "/api/runs") value = [run()];
  else if (path === "/api/simulations/sim/versions")
    value = [{version:"0.1.3",run_count:1,snapshots:2,structures:2,latest:run().started_at,changed:entrypointWarns?1:0}];
  else if (path === "/api/simulations/sim/preservation")
    value = {config:simulation.config,status:{connection:"connected",participating:false,global_enabled:false}};
  else if (path === "/api/runs/fixture-run") value = run();
  else if (path === "/api/runs/fixture-run/archive") {
    if (mode === "unavailable")
      return new Response(
        JSON.stringify({ detail: "Fixture archive inspection failed" }),
        { status: 503 },
      );
    value = archive();
  } else if (path === "/api/runs/fixture-run/source-comparison")
    value = {run_id:"fixture-run",version:"0.1.3",recorded_change:"same",snapshot_id:"0123456789abcdef",
      baseline:{id:"fixture-run",version:"0.1.3",snapshot_id:"0123456789abcdef",deleted:false},
      counts:{added:0,removed:0,changed:0,unchanged:1},total:0,offset:0,limit:100,changes:[],notes:[],selection_changes:[]};
  else if (path === "/api/runs/fixture-run/source")
    value = { text: 'print("immutable fixture source")' };
  else if (path === "/api/runs/fixture-run/logs")
    value = { text: "Fixture stderr/stdout evidence", truncated: false };
  else throw Error("Unmocked " + path);
  return new Response(JSON.stringify(value), {
    headers: { "Content-Type": "application/json" },
  });
};
await import("./main");
if (query.has("test")) {
  const result = document.createElement("pre");
  result.id = "results";
  result.setAttribute("role", "status");
  document.body.prepend(result);
  const wait = (ms) => new Promise((r) => setTimeout(r, ms));
  const assert = (ok, text) => {
    if (!ok) throw Error(text);
  };
  const tab = (name) =>
    [...document.querySelectorAll(".detail-page .tabs button")].find(
      (b) => b.textContent === name,
    );
  const click = async (element) => {
    assert(element, "missing control");
    element.click();
    await wait(450);
  };
  (async () => {
    await wait(600);
    const page = document.querySelector(".detail-page");
    assert(page, "run detail mounted");
    assert(
      !page.querySelector(".preservation-status,.capture-summary"),
      "routine panels absent from Overview",
    );
    assert(
      page.textContent.includes("Recorded command") &&
        page.textContent.includes("Run record"),
      "core Overview content retained",
    );
    if (mode === "healthy" || mode === "not-enabled")
      assert(
        !page.querySelector(".run-overview-warnings"),
        "no routine success/disabled archive notice",
      );
    else if (mode === "failed" || mode === "interrupted")
      assert(
        page.textContent.includes(
          mode === "failed" ? "Execution failed" : "Execution was interrupted",
        ),
        "execution warning remains separate from capture/preservation",
      );
    else
      assert(
        page.querySelector(".run-overview-warnings"),
        "actionable capture/preservation warning remains visible",
      );
    const link = page.querySelector(".run-overview-warnings button");
    await click(link || tab("Files"));
    assert(
      page.querySelectorAll(".capture-summary").length === 1,
      "one detailed capture surface",
    );
    assert(
      page.textContent.includes("/disposable/source/outputs/run_fixture"),
      "inspected path retained",
    );
    assert(
      page.textContent.includes("3 copied") ||
        ["running", "stopping"].includes(mode),
      "actual counts retained",
    );
    if (link)
      assert(
        document.activeElement.getAttribute("aria-label") ===
          "Run files and preservation details",
        "warning route focuses Files",
      );
    if (mode === "partial")
      assert(
        page.textContent.includes("Fixture copy budget exceeded"),
        "specific capture error retained",
      );
    if (mode !== "unavailable" && mode !== "not-enabled") {
      assert(
        page.querySelector(".preservation-status"),
        "aggregate preservation details discoverable",
      );
      const record = [...page.querySelectorAll("summary")].find((e) =>
        e.textContent.includes("Preservation records and omissions"),
      );
      await click(record);
      assert(
        page.textContent.includes("Preserved annotations"),
        "annotation evidence retained",
      );
      assert(
        page.querySelector('a[href$="/record"]') ||
          mode === "repository-unavailable",
        "verified record access preserved",
      );
    }
    await click(tab("Source"));
    assert(
      page.textContent.includes("immutable fixture source"),
      "source preview remains available",
    );
    await click(tab("Logs"));
    assert(
      page.textContent.includes("Fixture stderr/stdout evidence"),
      "logs remain available",
    );
    if (mode === "failed")
      assert(
        page.textContent.includes("Specific fixture execution failure"),
        "full execution error retained in Logs",
      );
    await click(tab("Overview"));
    if (mode === "healthy") {
      mode = "pending";
      await wait(3300);
      assert(
        page.textContent.includes("Git preservation is pending"),
        "live pending update",
      );
      mode = "healthy";
      await wait(3300);
      assert(
        !page.querySelector(".run-overview-warnings"),
        "healthy recovery clears notice",
      );
      await click(tab("Files"));
      mode = "unavailable";
      await wait(3300);
      assert(
        page
          .querySelector(".preservation-status")
          .textContent.includes("status unavailable"),
        "failed detail refresh clears stale preservation status",
      );
      assert(
        page.querySelector('.run-files-list a[href*="/artifacts/result/file"]'),
        "library download retained during archive failure",
      );
      mode = "healthy";
      await wait(3300);
      assert(
        page
          .querySelector(".preservation-status")
          .textContent.includes("Verified for the reviewed scope"),
        "detail refresh recovery",
      );
    }
    assert(!requests.some((r) => r.method !== "GET"), "read-only inspection");
    assert(
      document.documentElement.scrollWidth <= innerWidth,
      "no horizontal page overflow",
    );
    result.textContent =
      "PASS " +
      (query.get("state") || "healthy") +
      " Overview, details, focus and live-state checks";
  })().catch((error) => {
    result.textContent = "FAIL " + error.stack;
  });
}
