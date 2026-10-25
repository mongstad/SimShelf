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
let kind = "valid", binding = "listed bytes verified", requests = [], scanFails = false, captureFails = false;
const errors = [];
const originalError = console.error;
console.error = (...args) => { errors.push(args.join(" ")); originalError(...args); };
function discovery() {
  return { parameters: [], warnings: [], source: "swss.toml", fingerprint: kind,
    provenance: kind === "valid" ? {binding_status: binding, binding_reasons: [], simulation_version: '0.3.1'} : null,
    output_policy: {state: kind, binding, launcher_allowed: kind === "absent",
      reason: kind === "valid" ? "Use Fixed output parent: the simulation creates its unique run directory and SimShelf watches the parent. Metadata does not establish a coordinated-root agreement."
        : kind === "absent" ? "No SWSS metadata. Launcher-coordinated allocation requires explicit script support."
        : "SWSS metadata is unavailable. Output ownership is unknown. Review the capture parent and choose Fixed output parent for manual execution."}};
}
const output = data => ({output_policy: data.output_policy, output_path: "/disposable/" + data.output_dir,
  targets: (data.output_mappings || []).map(m => ({resolved_path: m.value, covered: !m.value.startsWith("/external"),
    reason: m.value.startsWith("/external") ? "Outside capture folder" : "Inside capture folder", suggested_argument: null})),
  requires_acknowledgement: data.output_mappings?.some(m => m.value.startsWith("/external")) || false});
window.fetch = async (url, options = {}) => {
  const data = options.body ? JSON.parse(options.body) : {};
  requests.push({url, method: options.method || "GET", data});
  let value;
  if (url.endsWith("/workspace")) value = {schema_version: 4};
  else if (url.endsWith("/parameters")) {
    if (scanFails) return new Response(JSON.stringify({detail: "Fixture discovery unavailable"}), {status: 500});
    value = discovery();
  } else if (url.endsWith("/interpreters")) value = {candidates: []};
  else if (url.endsWith("/interpreter/check")) return new Response(JSON.stringify({detail: "Fixture interpreter unavailable"}), {status: 400});
  else if (url.endsWith("/execution/outputs")) {
    if (captureFails) return new Response(JSON.stringify({detail: "Fixture capture path unavailable"}), {status: 400});
    value = output(data);
  }
  else if (url.endsWith("/execution/validate")) value = {output_review: output(data), command: data.arguments,
    cwd: "/disposable", output_path: "/disposable/outputs", validation: {version: "3.14", message: "Fixture only"}};
  else if (url.endsWith("/execution")) value = {};
  else if (url.endsWith("/launch")) value = {run_id: "fixture-only"};
  else throw Error(`Unexpected request ${url}`);
  return new Response(JSON.stringify(value), {headers: {"Content-Type": "application/json"}});
};
const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
const assert = (condition, message) => { if (!condition) throw Error(message); };
const button = text => [...document.querySelectorAll("button")].find(b => b.textContent === text);
const policy = () => document.querySelector('select[aria-describedby="output-policy-help"]');
const coordinated = () => policy()?.querySelector('[value="per_run"]');
async function click(text) { await act(async () => { button(text).click(); await wait(30); }); }
async function disclose(selector) { await act(async () => { document.querySelector(selector + ' > summary').click(); }); }
async function fill(node, value) {
  await act(async () => {
    Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value").set.call(node, value);
    node.dispatchEvent(new Event("input", {bubbles:true}));
  });
  await settled();
}
async function settled() { await act(async () => { await wait(330); }); }
let mountId = 0;
async function mount(selected = "fixed", extra = {}) {
  requests = [];
  const simulation = {id: "fixture", name: "Output fixture", root: "/disposable", entrypoint: "field.py",
    config: {output_dir: "outputs"}, execution: {interpreter: "/usr/bin/python3", cwd: ".", arguments: clone(argv),
      output_dir: "outputs", output_policy: selected, parameter_review: {mode: "manual", fingerprint: null}}, ...extra};
  await act(async () => { root.render(React.createElement(LaunchSimulation, {key: ++mountId, simulation, done() {}, saved() {}})); });
  await settled();
}
const cases = [];
async function check(name, run) { await run(); cases.push(name); results.textContent = cases.map(s => `PASS ${s}`).join("\n"); }
async function tests() {
  cases.length = 0; errors.length = 0;
  await check("valid metadata restricts allocation, separates byte binding and preserves exact argv", async () => {
    kind = "valid"; binding = "listed bytes verified"; await mount();
    assert(!policy() && !coordinated(), "inapplicable policy controls are absent");
    assert(!document.querySelector('.capture-override').open && !document.querySelector('.advanced-execution').open && !document.querySelector('.advanced-coverage').open, "advanced settings collapsed");
    assert(document.querySelector('.capture-path').innerText.includes("/disposable/outputs"), "one effective capture path");
    assert(document.querySelector('.capture-coverage').innerText.includes("confirm this is the script’s output parent"), "saved path still needs actual-write review");
    assert(document.body.textContent.includes("SWSS schema 2 · metadata valid"), "metadata label");
    assert(document.body.textContent.includes("Source binding: listed bytes verified"), "binding label");
    assert(document.body.innerText.includes("Current SWSS version for new runs: 0.3.1"), "future-run version explicit");
    await click("Save settings");
    const saved = requests.find(r => r.method === "PUT");
    assert(saved && JSON.stringify(saved.data.arguments) === JSON.stringify(argv), "exact argv save");
  });
  await check("saved per_run requires explicit correction without silent persistence", async () => {
    await mount("per_run");
    assert(!policy() && button("Save settings").disabled, "stale saved policy");
    assert(button("Start simulation").disabled, "blocked launch");
    assert(!document.querySelector('.capture-path'), "no misleading capture preview before policy review");
    assert(!requests.some(r => r.method === "PUT"), "no implicit save");
    await click("Use fixed output parent"); await settled();
    assert(!policy() && !button("Save settings").disabled, "explicit correction");
    assert(!requests.some(r => r.method === "PUT"), "correction is a draft");
    await click("Save settings");
    assert(requests.find(r => r.method === "PUT").data.output_policy === "fixed", "explicit save");
  });
  await check("rescan adoption invalidates a validated manual launch and requires review", async () => {
    kind = "absent"; await mount("per_run");
    assert(coordinated() && !coordinated().disabled && !document.querySelector('.advanced-execution').open, "plain Python preserves advanced coordinated adapter");
    await click("Validate interpreter & paths"); assert(!button("Start simulation").disabled, "plain validation");
    await click("Save settings");
    assert(requests.find(r => r.method === "PUT").data.output_policy === "per_run", "coordinated setting retained");
    kind = "valid"; await click("Rescan parameters");
    assert(!coordinated() && button("Start simulation").disabled, "adoption rechecks manual mode");
  });
  await check("unbound and unavailable states never claim conformance", async () => {
    binding = "binding unverified"; await mount();
    assert(document.body.textContent.includes("Source binding: unverified"), "unbound label");
    kind = "unavailable"; binding = "stale / manual-only"; await click("Rescan parameters");
    assert(!document.body.textContent.includes("SWSS schema 2 · metadata valid"), "stale cannot appear valid");
    assert(!coordinated() && document.body.textContent.includes("stale / manual-only"), "uncertainty discoverable");
    assert(document.body.innerText.includes("New manual runs record unversioned; existing runs stay unchanged"), "manual attribution explicit");
    assert(!button("Save settings").disabled, "explicit manual fixed remains usable");
  });
  await check("failed refresh blocks stale policy knowledge until successful rescan", async () => {
    scanFails = true; await click("Rescan parameters");
    assert(!policy() && button("Save settings").disabled && button("Start simulation").disabled, "failed refresh");
    scanFails = false; kind = "valid"; binding = "listed bytes verified"; await click("Rescan parameters");
    assert(!policy() && !button("Save settings").disabled, "successful refresh");
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
    const disclosures = [...document.querySelectorAll('.launch-output > details')];
    for (let i = 1; i < disclosures.length; ++i) assert(disclosures[i].getBoundingClientRect().top - disclosures[i-1].getBoundingClientRect().bottom >= 12, "compact disclosures stay separated");
    const checks = document.querySelector('.interpreter-checks');
    assert(!checks.open, "checks are opt-in disclosure");
    assert(!document.body.textContent.includes("Interpreter not checked"), "no redundant idle prose");
    await act(async () => { checks.querySelector('summary').click(); });
    assert(checks.innerText.includes("These checks execute the selected Python"), "trust warning at check action");
    const buttons = checks.querySelectorAll('button');
    const first = buttons[0].getBoundingClientRect(), second = buttons[1].getBoundingClientRect();
    assert(second.top > first.top ? second.top - first.bottom >= 12 : second.left - first.right >= 16,
      "check buttons have visible horizontal or wrapped gap");
    await click("Check selected Python");
    const checkRequest = requests.find(r => r.url.endsWith("/interpreter/check"));
    assert(checkRequest.data.confirmed === true && checkRequest.data.interpreter === "/usr/bin/python3", "check consent payload unchanged");
    await act(async () => { checks.querySelector('summary').click(); });
    const checkError = [...document.querySelectorAll('[role="alert"]')].find(e => e.textContent.includes("Fixture interpreter unavailable"));
    assert(checkError && checkError.getBoundingClientRect().height > 0, "specific errors stay visible when checks collapse");
    const progress = document.querySelector('.progress-settings');
    await act(async () => { progress.querySelector('summary').click(); });
    assert(progress.open && !progress.querySelector('select').disabled, "expanded progress control");
    await disclose('.advanced-coverage');
    await click("Declare output path");
    assert(document.body.textContent.includes("Output 1 is incomplete"), "incomplete mapping guidance visible");
    await settled();
    assert(button("Save settings").disabled, "incomplete mapping blocks validation");
    await click("Remove mapping"); await settled();
  });
  await check("cwd is advanced and stays independent of capture; exact settings survive save", async () => {
    kind = "valid"; await mount();
    await disclose('.advanced-execution');
    const cwd = document.querySelector('.advanced-execution input');
    assert(cwd.value === ".", "source-root cwd default");
    await click("Validate interpreter & paths");
    assert(!button("Start simulation").disabled, "validated");
    await fill(cwd, "work");
    assert(button("Start simulation").disabled, "cwd edit invalidates plan");
    assert(document.querySelector('.capture-path').innerText.includes("/disposable/outputs"), "cwd does not infer capture");
    await disclose('.capture-override');
    await fill(document.querySelector('.capture-override input'), "research_results");
    assert(document.querySelector('.capture-path').innerText.includes("/disposable/research_results"), "override resolved");
    assert(document.querySelector('.capture-coverage').innerText.includes("needs review"), "unsaved override identified");
    await click("Save settings");
    const data = requests.find(r => r.method === "PUT").data;
    assert(data.cwd === "work" && data.output_dir === "research_results" && data.output_policy === "fixed" && data.output_mappings.length === 0, "settings unchanged in meaning");
    assert(JSON.stringify(data.arguments) === JSON.stringify(argv), "argv untouched");
  });
  await check("external declarations preserve warnings and explicit launch consent when collapsed", async () => {
    await mount(); await disclose('.advanced-coverage'); await click("Declare output path");
    await fill(document.querySelector('[aria-label="Output 1 path"]'), "/external/results.csv");
    await click("Validate interpreter & paths");
    const ack = [...document.querySelectorAll('input[type="checkbox"]')].find(e => e.parentElement.textContent.includes("Proceed with declared outputs"));
    assert(ack && !ack.checked && button("Start simulation").disabled, "external consent");
    await disclose('.advanced-coverage');
    assert(document.querySelector('.capture-coverage').innerText.includes("outside capture coverage"), "warning outside collapse");
    await act(async () => ack.click());
    assert(!button("Start simulation").disabled, "explicit acknowledgement");
    await click("Start simulation");
    const launch = requests.find(r => r.url.endsWith('/launch')).data;
    assert(launch.acknowledge_outputs && launch.output_mappings[0].value === "/external/results.csv" && launch.cwd === "." && launch.output_dir === "outputs" && launch.output_policy === "fixed", "reviewed launch payload");
    assert(JSON.stringify(launch.arguments) === JSON.stringify(argv), "launch preserves exact argv");
    await disclose('.capture-override'); await fill(document.querySelector('.capture-override input'), "new-parent");
    assert(!ack.checked && button("Start simulation").disabled, "capture edit revokes acknowledgement");
  });
  await check("capture path failures never display an old path or enable validation", async () => {
    await mount(); captureFails = true; await disclose('.capture-override');
    await fill(document.querySelector('.capture-override input'), "invalid");
    assert(document.querySelector('.capture-path').innerText.includes("Fixture capture path unavailable"), "capture error visible");
    assert(!document.querySelector('.capture-path').innerText.includes("/disposable/outputs"), "no stale preview");
    assert(button("Save settings").disabled, "failed path blocks validation");
    captureFails = false;
  });
  await check("fresh settings mark conventional capture as needing review without inventing SWSS defaults", async () => {
    await mount("fixed", {execution: undefined});
    assert(document.querySelector('.advanced-execution input').value === ".", "fresh cwd");
    assert(document.querySelector('.capture-coverage').innerText.includes("Capture setting needs review"), "fresh parent needs review");
    assert(!requests.some(r => r.method === "PUT" || /\/(validate|launch|check)$/.test(r.url)), "no implicit save or execution");
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
