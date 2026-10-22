// Real DOM regression harness for the launch form; network responses are fixtures.
import React, { act } from "react";
import { createRoot } from "react-dom/client";
import { LaunchSimulation } from "./LaunchSimulation";
import "./style.css";

globalThis.IS_REACT_ACT_ENVIRONMENT = true;
const root = createRoot(document.querySelector("#root"));
const results = document.querySelector("#results");
const argv = ["--label", "", "-n", "0010", "--repeat=1e-3", "--repeat=2", "--", "--literal"];
const clone = value => structuredClone(value);
let kind = "valid", binding = "listed bytes verified", requests = [], scanFails = false;
const errors = [];
const originalError = console.error;
console.error = (...args) => { errors.push(args.join(" ")); originalError(...args); };
function discovery() {
  return { parameters: [], warnings: [], source: "swss.toml", fingerprint: kind,
    provenance: kind === "valid" ? {binding_status: binding, binding_reasons: []} : null,
    output_policy: {state: kind, binding, launcher_allowed: kind === "absent",
      reason: kind === "valid" ? "Use Fixed output parent: the simulation creates its unique run directory and SimShelf watches the parent. Metadata does not establish a coordinated-root agreement."
        : kind === "absent" ? "No SWSS metadata. Launcher-coordinated allocation requires explicit script support."
        : "SWSS metadata is unavailable. Output ownership is unknown. Review the capture parent and choose Fixed output parent for manual execution."}};
}
const output = data => ({output_policy: data.output_policy, output_path: "/disposable/outputs", targets: [], requires_acknowledgement: false});
window.fetch = async (url, options = {}) => {
  const data = options.body ? JSON.parse(options.body) : {};
  requests.push({url, method: options.method || "GET", data});
  let value;
  if (url.endsWith("/workspace")) value = {schema_version: 4};
  else if (url.endsWith("/parameters")) {
    if (scanFails) return new Response(JSON.stringify({detail: "Fixture discovery unavailable"}), {status: 500});
    value = discovery();
  } else if (url.endsWith("/interpreters")) value = {candidates: []};
  else if (url.endsWith("/execution/outputs")) value = output(data);
  else if (url.endsWith("/execution/validate")) value = {output_review: output(data), command: data.arguments,
    cwd: "/disposable", output_path: "/disposable/outputs", validation: {version: "3.14", message: "Fixture only"}};
  else if (url.endsWith("/execution")) value = {};
  else throw Error(`Unexpected request ${url}`);
  return new Response(JSON.stringify(value), {headers: {"Content-Type": "application/json"}});
};
const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
const assert = (condition, message) => { if (!condition) throw Error(message); };
const button = text => [...document.querySelectorAll("button")].find(b => b.textContent === text);
const policy = () => document.querySelector('select[aria-describedby="output-policy-help"]');
const coordinated = () => policy().querySelector('[value="per_run"]');
async function click(text) { await act(async () => { button(text).click(); await wait(30); }); }
async function settled() { await act(async () => { await wait(330); }); }
let mountId = 0;
async function mount(selected = "fixed") {
  requests = [];
  const simulation = {id: "fixture", name: "Output fixture", root: "/disposable", entrypoint: "field.py",
    config: {output_dir: "outputs"}, execution: {interpreter: "/usr/bin/python3", cwd: ".", arguments: clone(argv),
      output_dir: "outputs", output_policy: selected, parameter_review: {mode: "manual", fingerprint: null}}};
  await act(async () => { root.render(React.createElement(LaunchSimulation, {key: ++mountId, simulation, done() {}, saved() {}})); });
  await settled();
}
const cases = [];
async function check(name, run) { await run(); cases.push(name); results.textContent = cases.map(s => `PASS ${s}`).join("\n"); }
async function tests() {
  cases.length = 0; errors.length = 0;
  await check("valid metadata restricts allocation, separates byte binding and preserves exact argv", async () => {
    kind = "valid"; binding = "listed bytes verified"; await mount();
    assert(policy().value === "fixed" && coordinated().disabled, "valid policy restriction");
    assert(document.body.textContent.includes("SWSS schema 2 · metadata valid"), "metadata label");
    assert(document.body.textContent.includes("Source binding: listed bytes verified"), "binding label");
    await click("Save settings");
    const saved = requests.find(r => r.method === "PUT");
    assert(saved && JSON.stringify(saved.data.arguments) === JSON.stringify(argv), "exact argv save");
  });
  await check("saved per_run requires explicit correction without silent persistence", async () => {
    await mount("per_run");
    assert(policy().value === "per_run" && coordinated().disabled && button("Save settings").disabled, "stale saved policy");
    assert(button("Start simulation").disabled, "blocked launch");
    assert(!document.querySelector('[aria-label="Output destinations"]'), "no misleading capture preview before policy review");
    assert(!requests.some(r => r.method === "PUT"), "no implicit save");
    await click("Use fixed output parent"); await settled();
    assert(policy().value === "fixed" && !button("Save settings").disabled, "explicit correction");
    assert(!requests.some(r => r.method === "PUT"), "correction is a draft");
    await click("Save settings");
    assert(requests.find(r => r.method === "PUT").data.output_policy === "fixed", "explicit save");
  });
  await check("rescan adoption invalidates a validated manual launch and requires review", async () => {
    kind = "absent"; await mount("per_run");
    assert(!coordinated().disabled, "plain Python still supports both policies");
    await click("Validate interpreter & paths"); assert(!button("Start simulation").disabled, "plain validation");
    kind = "valid"; await click("Rescan parameters");
    assert(coordinated().disabled && button("Start simulation").disabled, "adoption rechecks manual mode");
  });
  await check("unbound and unavailable states never claim conformance", async () => {
    binding = "binding unverified"; await mount();
    assert(document.body.textContent.includes("Source binding: unverified"), "unbound label");
    kind = "unavailable"; binding = "stale / manual-only"; await click("Rescan parameters");
    assert(!document.body.textContent.includes("SWSS schema 2 · metadata valid"), "stale cannot appear valid");
    assert(coordinated().disabled && document.body.textContent.includes("stale / manual-only"), "uncertainty visible");
    assert(!button("Save settings").disabled, "explicit manual fixed remains usable");
  });
  await check("failed refresh blocks stale policy knowledge until successful rescan", async () => {
    scanFails = true; await click("Rescan parameters");
    assert(policy().disabled && button("Save settings").disabled && button("Start simulation").disabled, "failed refresh");
    scanFails = false; kind = "valid"; binding = "listed bytes verified"; await click("Rescan parameters");
    assert(!policy().disabled && coordinated().disabled, "successful refresh");
  });
  await check("New run field grouping and optional content retain spacing", async () => {
    kind = "absent"; await mount();
    const entry = document.querySelector('.launch-setting');
    const label = entry.querySelector('label'), input = label.querySelector('input'), help = label.querySelector('small');
    assert(entry.querySelector('button').disabled, "unchanged entry action stays disabled");
    assert(help.textContent.trim() === "Relative to source folder.", "concise entry guidance");
    const gap = help.getBoundingClientRect().top - input.getBoundingClientRect().bottom;
    assert(gap >= 6 && gap <= 8, "helper stays attached to input");
    const nextGap = document.querySelector('.interpreter-picker').getBoundingClientRect().top - entry.getBoundingClientRect().bottom;
    assert(nextGap >= 24, "separate Python section");
    const outputLabels = document.querySelectorAll('.launch-output > label');
    assert(outputLabels[1].getBoundingClientRect().top - outputLabels[0].getBoundingClientRect().bottom >= 20,
      "capture helper is separated from next setting");
    const fields = document.querySelectorAll('.launch-form > fieldset > .form-grid > label');
    const a = fields[0].getBoundingClientRect(), b = fields[1].getBoundingClientRect();
    assert(b.left > a.left ? Math.abs(a.top - b.top) < 1 : b.top - a.bottom >= 20,
      "fields align in columns or separate when stacked");
    assert(document.body.textContent.includes("Only select interpreters you trust"), "trust disclosure retained");
    assert(document.body.textContent.includes("Interpreter not checked."), "unchecked status retained");
    const progress = document.querySelector('.progress-settings');
    await act(async () => { progress.querySelector('summary').click(); });
    assert(progress.open && !progress.querySelector('select').disabled, "expanded progress control");
    await click("Declare output path");
    assert(document.body.textContent.includes("Output 1 is incomplete"), "incomplete mapping guidance visible");
    await settled();
    assert(button("Save settings").disabled, "incomplete mapping blocks validation");
    await click("Remove mapping"); await settled();
  });
  assert(errors.length === 0, `Console errors: ${errors.join("\n")}`);
  results.textContent += `\n${cases.length} passed; no console errors.`;
}
const runButton = document.querySelector("#run-tests");
runButton.disabled = true;
runButton.onclick = async () => {
  runButton.disabled = true;
  try { await tests(); }
  catch (error) { results.textContent += `\nFAIL ${error.stack}`; }
  finally { runButton.disabled = false; }
};
await mount("per_run");
runButton.disabled = false;
