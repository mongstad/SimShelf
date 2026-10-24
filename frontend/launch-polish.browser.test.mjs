// Disposable visual/interaction fixture. Build and serve outside the checkout.
// ?state=ready|required|blocked|manual|migration; requests never execute code.
import React from "react";
import { createRoot } from "react-dom/client";
import { LaunchSimulation } from "./LaunchSimulation";
import "./style.css";
const query = new URLSearchParams(location.search);
document.documentElement.dataset.theme = query.get("theme") || "system";
const state = query.get("state") || "ready";
const base = {
  flags: ["--steps"],
  name: "--steps",
  type: "int",
  action: "store",
  required: true,
  supported: true,
  default_known: true,
  default: 1000,
  help: "Number of integration steps.",
  choices: null,
};
const parameters = [
  base,
  {
    ...base,
    name: "--damping",
    flags: ["--damping"],
    type: "float",
    required: false,
    default: 0.02,
    help: "Damping coefficient.",
  },
  {
    ...base,
    name: "--label",
    flags: ["--label"],
    type: "str",
    required: false,
    default: "",
    help: "Label saved with the results.",
  },
  {
    ...base,
    name: "--headless",
    flags: ["--headless"],
    type: "bool",
    action: "store_true",
    required: false,
    default: false,
    help: "Run without opening a display.",
  },
];
const args =
  state === "required"
    ? []
    : ["--steps", "001000", "--damping=1e-3", "--label", ""];
const simulation = {
  id: "polish",
  name: "Damped wave experiment",
  root: "/disposable/damped-wave",
  entrypoint: "simulate.py",
  config: { output_dir: "outputs" },
  execution: {
    interpreter: "/disposable/wave-env/bin/python",
    cwd: ".",
    arguments: args,
    output_dir: "outputs",
    output_policy: state === "blocked" ? "per_run" : "fixed",
    parameter_review:
      state === "manual" ? { mode: "manual", fingerprint: null } : undefined,
  },
};
const review = (data) => ({
  output_policy: data.output_policy,
  output_path: "/disposable/damped-wave/" + data.output_dir,
  requires_acknowledgement:
    data.output_mappings?.some((m) => m.value.startsWith("../")) || false,
  targets: (data.output_mappings || []).map((m) => ({
    resolved_path: "/disposable/damped-wave/" + m.value,
    covered: !m.value.startsWith("../"),
    reason: m.value.startsWith("../")
      ? "Outside the capture folder; this output may not be retained."
      : "Inside the capture folder.",
    suggested_argument: null,
  })),
});
window.fetch = async (url, options = {}) => {
  const path = new URL(url, location.origin).pathname,
    data = options.body ? JSON.parse(options.body) : {};
  if (options.method)
    console.info(
      "FIXTURE REQUEST " +
        JSON.stringify({ path, method: options.method, data }),
    );
  let value;
  if (path.endsWith("/workspace"))
    value = { schema_version: state === "migration" ? 3 : 4 };
  else if (path.endsWith("/parameters"))
    value = {
      parameters: state === "manual" ? [] : parameters,
      warnings:
        state === "manual"
          ? ["No SWSS companion; explicit manual argv selected."]
          : [],
      fingerprint: "polish-fixture",
      source: "swss.toml",
      provenance:
        state === "manual"
          ? null
          : { binding_status: "binding unverified", binding_reasons: [] },
      output_policy: {
        state: state === "manual" ? "absent" : "valid",
        binding: "binding unverified",
        launcher_allowed: state === "manual",
        reason:
          state === "manual"
            ? "No SWSS metadata. Launcher-coordinated allocation requires explicit script support."
            : "Use Fixed output parent: the simulation creates its unique run directory and SimShelf watches the parent. Metadata does not establish a coordinated-root agreement.",
      },
    };
  else if (path.endsWith("/interpreters"))
    value = {
      candidates: [
        {
          path: simulation.execution.interpreter,
          sources: ["Saved selection"],
          kind: "Virtual environment",
          available: true,
          simshelf_runtime: false,
          state: "Not checked",
        },
      ],
    };
  else if (path.endsWith("/interpreter/check"))
    return new Response(
      JSON.stringify({
        detail:
          "Selected Python is unavailable. Choose an existing interpreter.",
      }),
      { status: 400 },
    );
  else if (path.endsWith("/dependencies/check")) {
    await new Promise((r) => setTimeout(r, 1500));
    value = {
      python: { version: "3.14", prefix: "/disposable/wave-env" },
      files: [],
      requirements: [],
      warnings: [],
      undeclared: true,
      message: "No declared dependencies found.",
    };
  } else if (path.endsWith("/execution/outputs")) value = review(data);
  else if (path.endsWith("/execution/validate"))
    value = {
      output_review: review(data),
      command: data.arguments,
      cwd: simulation.root,
      output_path: simulation.root + "/outputs",
      validation: {
        version: "3.14",
        message:
          "Interpreter and paths checked; scientific dependencies remain unverified.",
      },
    };
  else if (path.endsWith("/execution")) value = {};
  else throw Error("Unexpected fixture request " + path);
  return new Response(JSON.stringify(value), {
    headers: { "Content-Type": "application/json" },
  });
};
const dialog = document.createElement("dialog");
dialog.className = "modal wide";
dialog.setAttribute("aria-label", "New run audit fixture");
document.body.append(dialog);
const title = document.createElement("div");
title.className = "modal-heading";
title.innerHTML =
  '<h2>New run</h2><button aria-label="Close dialog">×</button>';
dialog.append(title);
title.querySelector("button").onclick = () => dialog.close();
const root = document.createElement("div");
dialog.append(root);
createRoot(root).render(
  React.createElement(LaunchSimulation, {
    simulation,
    done() {
      throw Error("No launch is allowed in this fixture");
    },
    saved() {},
  }),
);
dialog.showModal();

// Opt-in repeatable DOM checks: append &test=1. No launch/migration route exists.
const requests = [];
const fetchFixture = window.fetch;
window.fetch = async (url, options = {}) => {
  requests.push({
    url,
    method: options.method || "GET",
    data: options.body ? JSON.parse(options.body) : null,
  });
  return fetchFixture(url, options);
};
if (new URLSearchParams(location.search).has("test")) {
  const result = document.createElement("pre");
  result.id = "results";
  result.setAttribute("role", "status");
  dialog.append(result);
  const wait = () => new Promise((r) => setTimeout(r, 400));
  const assert = (ok, msg) => {
    if (!ok) throw Error(msg);
  };
  const button = (text) =>
    [...dialog.querySelectorAll("button")].find(
      (b) => b.textContent.trim() === text,
    );
  const click = async (node) => {
    assert(node, "missing control");
    node.click();
    await wait();
  };
  const fill = async (node, value) => {
    Object.getOwnPropertyDescriptor(
      HTMLInputElement.prototype,
      "value",
    ).set.call(node, value);
    node.dispatchEvent(new Event("input", { bubbles: true }));
    await wait();
  };
  (async () => {
    await wait();
    assert(
      !requests.some((r) => /\/(check|launch|enable)$/.test(r.url)),
      "no automatic code execution or migration",
    );
    assert(
      dialog
        .querySelector(".launch-output")
        .contains(dialog.querySelector(".output-paths")) || state === "blocked",
      "capture and mappings colocated",
    );
    assert(
      !dialog.querySelector(".progress-settings").open,
      "progress optional and collapsed",
    );
    if (state === "blocked") {
      assert(
        button("Save settings").disabled && button("Start simulation").disabled,
        "incompatible policy blocks execution",
      );
      assert(!requests.some((r) => r.method === "PUT"), "no implicit save");
      await click(button("Use fixed output parent"));
      assert(
        !requests.some((r) => r.method === "PUT"),
        "policy correction stays draft",
      );
    }
    if (state === "required") {
      await click(button("Validate interpreter & paths"));
      assert(
        document.activeElement?.getAttribute("aria-label") ===
          "Value for --steps",
        "required omission revealed and focused",
      );
      assert(
        document.activeElement.getAttribute("aria-invalid") === "true",
        "required invalid semantics",
      );
    } else if (state === "migration") {
      await click(dialog.querySelector(".progress-settings summary"));
      await click(button("Enable progress reporting…"));
      assert(
        button("Enable progress reporting for this library").disabled,
        "migration requires explicit backup consent",
      );
      await click(button("Cancel"));
      assert(
        !requests.some((r) => r.url.endsWith("/progress/enable")),
        "migration canceled without request",
      );
    } else {
      await click(button("Save settings"));
      assert(
        JSON.stringify(
          requests.find((r) => r.method === "PUT").data.arguments,
        ) === JSON.stringify(args),
        "save preserves exact argv",
      );
      assert(!button("Start simulation").disabled, "validation unlocks launch");
      const checks = dialog.querySelector(".interpreter-checks");
      await click(checks.querySelector("summary"));
      assert(
        !requests.some((r) => r.url.endsWith("/interpreter/check")),
        "opening checks does not execute",
      );
      await click(button("Check selected Python"));
      await click(checks.querySelector("summary"));
      assert(
        [...dialog.querySelectorAll("[role=alert]")].some(
          (e) =>
            e.textContent.includes("Selected Python is unavailable") &&
            e.getBoundingClientRect().height > 0,
        ),
        "check error stays visible after collapse",
      );
      await click(button("Paste arguments"));
      assert(
        button("Save settings").disabled,
        "pending paste blocks validation",
      );
      await click(button("Cancel paste"));
      await click(button("Declare output path"));
      assert(
        button("Save settings").disabled,
        "incomplete mapping blocks validation",
      );
      assert(
        dialog.textContent.includes("Output 1 is incomplete"),
        "incomplete mapping diagnosis",
      );
      await click(button("Remove mapping"));
      await click(button("Declare output path"));
      await fill(
        dialog.querySelector('[aria-label="Output 1 path"]'),
        "../external/results.csv",
      );
      await click(button("Validate interpreter & paths"));
      const acknowledgement = [
        ...dialog.querySelectorAll('input[type="checkbox"]'),
      ].find((e) =>
        e.parentElement.textContent.includes(
          "Proceed with declared outputs outside capture coverage",
        ),
      );
      assert(
        acknowledgement &&
          !acknowledgement.checked &&
          button("Start simulation").disabled,
        "outside-capture consent required",
      );
      await click(acknowledgement);
      assert(
        !button("Start simulation").disabled,
        "explicit capture acknowledgement unlocks launch",
      );
      assert(
        !requests.some((r) => r.url.endsWith("/launch")),
        "fixture never launches code",
      );
    }
    assert(
      dialog.scrollWidth <= dialog.clientWidth,
      "dialog has no horizontal overflow",
    );
    result.textContent =
      "PASS " + state + " layout, consent and interaction checks";
  })().catch((e) => {
    result.textContent = "FAIL " + e.stack;
  });
}
