import { test } from "node:test";
import assert from "node:assert/strict";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import {
  PreservationReview,
  PreservationSettings,
  SimulationPreservationControl,
} from "./PreservationSettings.tsx";
const render = (component, props) =>
  renderToStaticMarkup(React.createElement(component, props));
const review = {
  config: {
    output_dir: "outputs",
    rules: [],
    source_include: [],
    source_exclude: [],
    max_file_mb: 25,
    max_run_mb: 100,
  },
  options: {
    enabled: true,
    all_sources: true,
    extensions: [".json", ".csv", ".log"],
    process_logs: true,
  },
  sources: [{ path: "sim.py", captured: true, selected: true }],
  outputs: {
    total_files: 2,
    files: [
      {
        path: "run_x/summary.json",
        size: 12,
        action: "copy",
        git_selected: true,
        git_reason: null,
      },
      {
        path: "run_x/huge.csv",
        size: 100,
        action: "reference",
        git_selected: false,
        git_reason: "reference",
      },
    ],
    errors: [],
    truncated: false,
  },
  warnings: [],
  record_scope: ["exact argv and cwd"],
  legacy: {},
};
test("one review combines source, recursive copied outputs, explicit exclusions and consent", () => {
  const html = render(PreservationReview, { review });
  for (const value of [
    "Recursive output types",
    ".json, .csv, .log",
    "run_x/summary.json",
    "capture: copy; Git: selected",
    "capture: reference; Git: reference",
    "1 MiB",
    "64 KiB",
    "replaces legacy automatic consent",
    "exact argv and cwd",
  ])
    assert.ok(html.includes(value), value);
});
test("settings default to an unconfirmed draft, not legacy auto-activation", () => {
  const html = render(PreservationSettings, {
    simulation: { id: "a", name: "Alpha", config: review.config },
    onSaved: () => {},
  });
  assert.match(html, /Review preservation settings/);
  assert.doesNotMatch(html, /Confirm preservation settings/);
  assert.match(html, /Checking status/);
  assert.doesNotMatch(html, /Saved Git policy|Preserve reviewed evidence in the shared Git archive/);
  assert.ok(html.indexOf("Git preservation — Alpha") < html.indexOf("Archive location and setup"));
  assert.ok(html.indexOf("Enable Git preservation") < html.indexOf("Capture and Git options"));
  assert.match(html, /Reference only/);
  assert.match(html, /simulation creates its own unique subdirectories/);
});

const control = (state, extra = {}) => render(SimulationPreservationControl, {
  name: "Alpha <science>", state, busy: false, onEnable() {}, onDisable() {}, onReview() {},
  actionRef: React.createRef(), reviewRef: React.createRef(), ...extra,
});
const connected = { connection: {state: "connected"}, status: {state: "disabled"}, policy: {options: {enabled: false}} };
test("connected archive does not imply simulation activation", () => {
  const html = control(connected);
  assert.match(html, /Disabled/);
  assert.match(html, /class="primary">Enable Git preservation/);
  assert.doesNotMatch(html, /archive-connected|Disable Git preservation/);
  assert.match(html, /Git preservation — Alpha &lt;science&gt;/);
});
test("only confirmed enabled state receives the established green indicator", () => {
  const html = control({...connected, status: {state: "enabled"}, policy: {options: {enabled: true}}});
  assert.match(html, /class="archive-connected"/);
  assert.match(html, /Enabled/);
  assert.match(html, /Disable Git preservation/);
  assert.match(html, /Disabling keeps all existing Git history/);
});
test("unavailable connection blocks activation but permits disabling saved consent", () => {
  for (const value of ["disconnected", "unavailable"]) {
    const html = control({...connected, connection: {state: value}});
    assert.match(html, /preservation-unavailable/);
    assert.match(html, /disabled="">Enable Git preservation/);
    assert.doesNotMatch(html, /archive-connected/);
    const enabled = control({...connected, connection: {state: value}, policy: {options: {enabled: true}}});
    assert.match(enabled, /<button>Disable Git preservation/);
  }
});
test("stale consent requires review and failed status fetch never claims enabled", () => {
  const stale = control({...connected, status: {state: "review_required", reason: "Source changed; review again."}, legacy: {rules: []}});
  assert.match(stale, /Unavailable/);
  assert.match(stale, /Source changed; review again/);
  assert.match(stale, /Review Git preservation/);
  const failed = control(null, {error: "Cannot load preservation status."});
  assert.match(failed, /Unavailable/);
  assert.match(failed, /disabled="">Enable Git preservation/);
});
test("legacy enabled status retains legacy scope until explicit review", () => {
  const state = {...connected, policy: null, legacy: {rules: ["sim.py"]}, status: {state: "enabled", legacy: true}};
  const before = structuredClone(state), html = control(state);
  assert.match(html, /archive-connected/);
  assert.match(html, /Legacy choices remain in effect until explicitly reviewed/);
  assert.deepEqual(state, before);
});
