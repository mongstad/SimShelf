// Full App regression harness. Build with scripts/test_journal_browser.mjs.
// Fetch, timers and persistent policy are controlled; React mounts real DOM.
import { act } from "react";

globalThis.IS_REACT_ACT_ENVIRONMENT = true;
const resultNode = document.querySelector("#results");
const runButton = document.querySelector("#run-tests");
const storageKey = "simshelf-journal-regression";
const clone = (value) => structuredClone(value);
const config = {
  output_dir: "outputs",
  source_include: ["*.py"],
  source_exclude: [],
  max_file_mb: 25,
  max_run_mb: 100,
  rules: [{ pattern: "**/*.json", action: "copy" }],
};
const options = {
  enabled: true,
  all_sources: true,
  sources: [],
  extensions: [".json", ".csv", ".log"],
  process_logs: false,
};
const fresh = () => ({
  global: true,
  connected: true,
  alpha: { participating: true, reviewed: true },
  beta: { participating: false, reviewed: false },
});
let saved = JSON.parse(localStorage.getItem(storageKey) || "null") || fresh();
const persist = () => localStorage.setItem(storageKey, JSON.stringify(saved));
const simulations = ["alpha", "beta"].map((id) => ({
  id,
  name: id,
  root: `/disposable/${id}`,
  entrypoint: "sim.py",
  config,
  available: true,
  run_count: 1,
  description: "",
  last_run: "2026-10-21T12:00:00Z",
}));
const runs = simulations.map((s) => ({
  id: `run-${s.id}`,
  simulation_id: s.id,
  name: s.name,
  status: "completed",
  version: "1.0",
  started_at: s.last_run,
  duration: 1,
  parameters: {},
  tags: [],
  image_count: 0,
  archive_commits: 1,
}));
const requests = [],
  failures = [],
  errors = [],
  results = [];
const originalError = console.error;
console.error = (...args) => {
  errors.push(args.join(" "));
  originalError(...args);
};
const intervals = new Map();
let timerId = 0;
window.setInterval = (callback, delay) => {
  const id = ++timerId;
  intervals.set(id, { callback, delay });
  return id;
};
window.clearInterval = (id) => intervals.delete(id);
const listeners = new Map();
const add = window.addEventListener.bind(window),
  remove = window.removeEventListener.bind(window);
window.addEventListener = (name, fn, ...rest) => {
  if (!listeners.has(name)) listeners.set(name, new Set());
  listeners.get(name).add(fn);
  add(name, fn, ...rest);
};
window.removeEventListener = (name, fn, ...rest) => {
  listeners.get(name)?.delete(fn);
  remove(name, fn, ...rest);
};
const listenerCount = () =>
  [...listeners.values()].reduce((n, s) => n + s.size, 0);
const holds = [];
function hold(path, method = "GET") {
  const pending = { path, method, release: null };
  holds.push(pending);
  return pending;
}
function policy(id) {
  const p = saved[id];
  return {
    config,
    policy: p.reviewed
      ? { options: { ...options, enabled: p.participating } }
      : null,
    legacy: null,
    status: {
      global_enabled: saved.global,
      participating: p.participating,
      can_resume: p.reviewed,
      connection: saved.connected ? "connected" : "unavailable",
      state: !saved.global
        ? "disabled"
        : !saved.connected
          ? "unavailable"
          : p.participating
            ? "enabled"
            : "disabled",
      reason: !saved.global
        ? "Master Git Archive is OFF."
        : !saved.connected
          ? "Repository unavailable."
          : null,
    },
  };
}
const reply = (value) =>
  new Response(JSON.stringify(value), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
window.fetch = async (input, init = {}) => {
  const url = new URL(input, location.href),
    path = url.pathname.replace(/^\/api/, ""),
    method = init.method || "GET";
  const body = init.body ? JSON.parse(init.body) : null;
  requests.push({ path, method, body });
  const id = path.split("/")[2];
  let value;
  if (path === "/workspace")
    value = {
      path: "/disposable/library",
      version: "0.1.0.43",
      token: "fixture-only",
    };
  else if (path === "/simulations") value = simulations;
  else if (path === "/runs")
    value = url.searchParams.has("simulation")
      ? runs.filter(
          (r) => r.simulation_id === url.searchParams.get("simulation"),
        )
      : runs;
  else if (path.endsWith("/versions")) value = [];
  else if (path === "/workspace/git") value = { connection: null };
  else if (path.endsWith("/git/discovery"))
    value = {
      status: "not_found",
      reason: null,
      preview: null,
      eligible: [],
      partial: false,
    };
  else if (path.endsWith("/git"))
    value = { availability: "disabled", history: [] };
  else if (path.endsWith("/preservation/preview"))
    value = {
      config: body.config,
      options: body.options,
      sources: [],
      outputs: { total_files: 0, files: [], errors: [] },
      warnings: [],
      record_scope: ["exact argv"],
    };
  else if (path.endsWith("/preservation/save")) {
    saved[id] = { participating: body.review.options.enabled, reviewed: true };
    persist();
    value = policy(id);
  } else if (path.endsWith("/preservation/participation")) {
    saved[id].participating = body.enabled;
    persist();
    value = policy(id);
  } else if (path.endsWith("/preservation")) value = policy(id);
  else if (path === "/workspace/archive/automatic") {
    saved.global = body.enabled;
    persist();
    value = {};
  } else if (path === "/workspace/archive")
    value = {
      enabled: saved.global,
      status: { state: saved.connected ? "connected" : "unavailable" },
      connection: { path: "/disposable/archive" },
    };
  else if (path.endsWith("/archive"))
    value = { runs: [], settings: null, status: policy(id).status };
  else {
    failures.push(`Unexpected request ${method} ${path}`);
    throw Error(failures.at(-1));
  }
  const frozen = clone(value),
    pending = holds.find(
      (h) => h.path === path && h.method === method && !h.release,
    );
  if (pending)
    return new Promise((resolve) => {
      pending.release = (override = frozen, status = 200) =>
        resolve(
          new Response(JSON.stringify(override), {
            status,
            headers: { "Content-Type": "application/json" },
          }),
        );
    });
  return reply(frozen);
};
const check = (value, message) => {
  if (!value) throw Error(message);
};
const all = (selector) => [...document.querySelectorAll(selector)];
const toggle = () =>
  document.querySelector(
    '[role="switch"][aria-label="Archive this simulation"]',
  );
const nav = () =>
  document.querySelector('nav[aria-label="Simulation sections"]');
function single() {
  check(
    all('[role="switch"][aria-label="Archive this simulation"]').length === 1,
    "Expected exactly one archive participation control",
  );
  check(
    all('nav[aria-label="Simulation sections"]').length === 1,
    "Expected exactly one simulation navigation bar",
  );
}
const settle = async () => {
  for (let i = 0; i < 12; i++) await Promise.resolve();
};
async function flush(work = () => {}) {
  await act(async () => {
    await work();
    await settle();
  });
}
async function clickElement(el) {
  check(el, "Missing control");
  check(!el.disabled, "Control disabled");
  await flush(() => el.click());
}
async function click(text, scope = document) {
  await clickElement(
    [...scope.querySelectorAll("button")].find(
      (b) => b.textContent.trim() === text,
    ),
  );
}
async function choose(id) {
  await clickElement(
    [...document.querySelectorAll("aside button")].find(
      (b) => b.textContent.trim() === id + "1",
    ),
  );
  await tick();
  single();
}
async function tick() {
  await flush(() => {
    for (const timer of [...intervals.values()]) timer.callback();
  });
}
async function release(pending, value, status) {
  check(pending.release, "Deferred request was not issued");
  await flush(() => pending.release(value, status));
}
function state(checked, text) {
  single();
  check(
    toggle().getAttribute("aria-checked") === String(checked),
    `Expected participation ${checked}`,
  );
  check(
    document
      .querySelector(".simulation-preservation")
      .textContent.includes(text),
    `Missing status ${text}`,
  );
}
async function test(name, work) {
  await work();
  results.push(name);
  resultNode.textContent = results.map((n) => "PASS " + n).join("\n");
}

async function start() {
  runButton.disabled = true;
  const resumed = sessionStorage.getItem(storageKey) === "reload";
  if (!resumed) {
    saved = fresh();
    persist();
  }
  try {
    await flush(() => import("./main.tsx"));
    await flush(() => new Promise((resolve) => setTimeout(resolve, 200)));
    await tick();
    const baseListeners = listenerCount();
    if (resumed) {
      results.push(
        ...JSON.parse(sessionStorage.getItem(storageKey + "-results")),
      );
      await test("real document reload retains confirmed participation without duplicate controls", async () => {
        await choose("beta");
        state(true, "Git active");
        await tick();
        single();
      });
      sessionStorage.removeItem(storageKey);
    } else {
      await test("Source Git and repeated polling retain one control, navigation, and polling subscription", async () => {
        await choose("alpha");
        await click("Source Git", nav());
        for (let i = 0; i < 8; i++) {
          await tick();
          single();
          check(intervals.size === 2, "Polling subscriptions accumulated");
        }
        const before = requests.length;
        await tick();
        check(
          requests
            .slice(before)
            .filter((r) => r.path === "/simulations/alpha/preservation")
            .length === 1,
          "Duplicate preservation GET per tick",
        );
        check(
          !requests.some((r) => r.method !== "GET"),
          "Navigation unexpectedly wrote persistent state",
        );
      });
      await test("all four tabs retain the same participation DOM node", async () => {
        const original = toggle();
        for (let i = 0; i < 3; i++)
          for (const tab of [
            "Runs 1",
            "Version history",
            "Source Git",
            "Preservation settings",
          ]) {
            await click(tab, nav());
            await tick();
            single();
            check(toggle() === original, "Participation remounted on tab/poll");
          }
        check(
          all('[role="switch"]').length === 1,
          "Extra activation in advanced settings",
        );
      });
      await test("confirmed OFF/ON sends exactly one mutation each and retains focus", async () => {
        const writes = requests.filter((r) => r.method === "POST").length;
        await clickElement(toggle());
        state(false, "Git archiving off");
        check(document.activeElement === toggle(), "OFF focus");
        await clickElement(toggle());
        state(true, "Git active");
        check(document.activeElement === toggle(), "ON focus");
        check(
          requests.filter((r) => r.method === "POST").length === writes + 2,
          "Duplicate participation mutation",
        );
      });
      await test("first participation review cancel leaves policy unchanged and restores focus", async () => {
        await choose("beta");
        const before = JSON.stringify(saved);
        await clickElement(toggle());
        check(
          document.activeElement.textContent === "Review future preservation",
          "Review focus",
        );
        state(false, "Git archiving off");
        await click("Cancel");
        state(false, "Git archiving off");
        check(JSON.stringify(saved) === before, "Cancel changed policy");
        check(document.activeElement === toggle(), "Cancel focus");
      });
      await test("first participation remains OFF until explicit confirmation and backend acknowledgement", async () => {
        await clickElement(toggle());
        const pending = hold("/simulations/beta/preservation/save", "POST");
        await click("Confirm preservation settings");
        state(false, "Git archiving off");
        check(toggle().disabled, "Pending save must be disabled");
        await release(pending);
        state(true, "Git active");
        check(
          requests.filter((r) => r.path.endsWith("/preservation/save"))
            .length === 1,
          "Duplicate save",
        );
      });
      await test("older status completion cannot override a newer confirmed status", async () => {
        const pending = hold("/simulations/beta/preservation");
        await tick();
        await clickElement(toggle());
        state(false, "Git archiving off");
        await release(pending);
        state(false, "Git archiving off");
        const error = hold("/simulations/beta/preservation");
        await tick();
        await tick();
        await release(error, { detail: "stale failure" }, 503);
        state(false, "Git archiving off");
        check(
          !document.querySelector("main").textContent.includes("stale failure"),
          "Stale error leaked",
        );
      });
      await test("loading has no false active/off result and a departed response cannot affect the next simulation", async () => {
        await choose("alpha");
        const pending = hold("/simulations/beta/preservation");
        await clickElement(
          [...document.querySelectorAll("aside button")].find(
            (b) => b.textContent.trim() === "beta1",
          ),
        );
        single();
        check(toggle().disabled, "Loading toggle enabled");
        const text = document.querySelector(
          ".simulation-preservation",
        ).textContent;
        check(
          text.includes("Checking archive status"),
          "Missing loading state",
        );
        check(
          !text.includes("Git archiving off") && !text.includes("Git active"),
          "Loading claims known state",
        );
        await choose("alpha");
        await release(pending);
        state(true, "Git active");
      });
      await test("repeated A/B navigation cleans up subscriptions and event listeners", async () => {
        for (let i = 0; i < 10; i++)
          for (const id of ["beta", "alpha"]) {
            await choose(id);
            await click("Source Git", nav());
            await tick();
            single();
            check(intervals.size === 2, "Leaked polling");
            check(listenerCount() === baseListeners, "Leaked window listeners");
          }
        const before = requests.length;
        await tick();
        const reads = requests
          .slice(before)
          .filter((r) => r.path.endsWith("/preservation"));
        check(
          reads.length === 1 && reads[0].path.includes("/alpha/"),
          "Inactive simulation still polls",
        );
      });
      await test("master health matrix, pending/error refresh and recovery stay separate from activation", async () => {
        await click("Master Git Archive", document.querySelector("aside"));
        const section = document.querySelector(".master-archive-settings");
        const status = () => section.querySelector(".automatic-archive-line [role=status]");
        const setup = section.querySelector("details");
        check(!setup.open, "Repository setup should start collapsed");
        check(setup.querySelector(".archive-connected"), "Repository health must live in setup");
        check(setup.querySelector("input").value === "/disposable/archive", "Configured path lost");
        setup.open = true;
        for (const enabled of [false, true]) {
          for (const health of ["connected", "disconnected", "invalid", "unavailable"]) {
            const pending = hold("/workspace/archive");
            await click("Refresh archive status", setup);
            check(status().textContent === "Checking archive status…", "Refresh claims stale effective status");
            check(setup.textContent.includes("Checking availability"), "Repository pending state missing");
            await release(pending, {enabled, status: {state:health}, connection:{path:"/disposable/archive"}});
            const expected = !enabled ? "Git archiving disabled" : health === "connected" ? "Git active" : "Git unavailable";
            check(status().textContent.includes(expected), "Incorrect master matrix state");
            check(status().classList.contains("archive-connected") === (enabled && health === "connected"), "False green master status");
          }
        }
        // Both the failed refresh and its recovery read fail, then a new explicit refresh succeeds.
        const first = hold("/workspace/archive"), retry = hold("/workspace/archive");
        await click("Refresh archive status", setup);
        await release(first, {detail:"Fixture read failure"}, 503);
        await release(retry, {detail:"Fixture read failure"}, 503);
        check(status().textContent.includes("Archive status unavailable"), "Failed load still claims known status");
        check(section.querySelector('[role="switch"]').disabled, "Unknown preference remains editable");
        check(!setup.textContent.includes("Checking availability"), "Error looks pending forever");
        await click("Refresh archive status", setup);
        check(status().textContent.includes("Git active"), "Refresh recovery failed");
        check(section.querySelector('[role="switch"]').getAttribute("aria-describedby") === status().id, "Switch status is not accessible");
        await choose("alpha");
      });
      await test("global OFF preserves individual ON; unavailable preserves preference without claiming active", async () => {
        await click("Master Git Archive", document.querySelector("aside"));
        check(
          all('[role="switch"]').length === 1 && !nav(),
          "Global hierarchy duplicated",
        );
        await clickElement(
          document.querySelector(
            '[role="switch"][aria-label="Master Git Archive"]',
          ),
        );
        await flush();
        check(document.querySelector(".master-archive-settings .automatic-archive-line [role=status]").textContent === "Git archiving disabled", "Successful OFF did not update master status");
        await choose("alpha");
        state(true, "Master Git Archive disabled");
        check(!toggle().disabled, "Master OFF must allow editing participation");
        await clickElement(toggle());
        state(false, "Git archiving off");
        saved.global = true;
        await tick();
        state(false, "Git archiving off");
        saved.global = false;
        await tick();
        await clickElement(toggle());
        state(true, "Master Git Archive disabled");
        check(!document.querySelector(".simulation-preservation p"), "Verbose status paragraph");
        saved.global = true;
        saved.connected = false;
        await tick();
        state(true, "Git unavailable");
        saved.connected = true;
        persist();
        await tick();
        state(true, "Git active");
      });
      await test("navigation and status reads cause no extra persistent writes or archive operations", async () => {
        check(!failures.length, failures.join("\n"));
        check(
          requests.filter((r) => r.method === "POST").length === 9,
          "Unexpected write count",
        );
        check(
          requests
            .filter((r) => r.method === "POST")
            .every((r) =>
              /\/(participation|preview|save|automatic)$/.test(r.path),
            ),
          "Unexpected archive operation",
        );
        check(!errors.length, errors.join("\n"));
      });
      await choose("beta");
      await clickElement(toggle());
      state(true, "Git active");
      sessionStorage.setItem(storageKey + "-results", JSON.stringify(results));
      sessionStorage.setItem(storageKey, "reload");
      location.reload();
      return;
    }
    check(!failures.length, failures.join("\n"));
    check(!errors.length, errors.join("\n"));
    resultNode.textContent =
      results.map((n) => "PASS " + n).join("\n") +
      `\n${results.length} passed; 0 failed`;
    resultNode.dataset.status = "passed";
  } catch (e) {
    resultNode.textContent +=
      "\nFAIL " + e.stack + "\nConsole: " + errors.join("\n");
    resultNode.dataset.status = "failed";
  }
}
runButton.addEventListener("click", start);
if (sessionStorage.getItem(storageKey) === "reload") void start();
