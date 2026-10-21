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
test("one participation switch precedes advanced options and has no duplicate activation", () => {
  const html = render(PreservationSettings, {
    simulation: { id: "a", name: "Alpha", config: review.config },
    onSaved() {},
  });
  assert.equal((html.match(/role="switch"/g) || []).length, 1);
  assert.match(
    html,
    /aria-label="Archive this simulation" aria-checked="false"/,
  );
  assert.ok(
    html.indexOf("Archive this simulation") <
      html.indexOf("Capture and Git options"),
  );
  assert.doesNotMatch(
    html,
    /Enable Git preservation|Disable Git preservation|Preserve reviewed evidence in|Master Git Archive connection/,
  );
  assert.match(html, /Review preservation settings/);
  assert.doesNotMatch(html, /Confirm preservation settings/);
});
const control = (status, error = "") =>
  render(SimulationPreservationControl, {
    name: "Alpha <science>",
    state: status ? { status } : null,
    busy: false,
    onToggle() {},
    actionRef: React.createRef(),
    error,
  });
for (const global_enabled of [false, true])
  for (const participating of [false, true]) {
    test(`participation stays ${participating} while global is ${global_enabled}`, () => {
      const html = control({
        global_enabled,
        participating,
        connection: "connected",
        state: global_enabled && participating ? "enabled" : "disabled",
        reason: !global_enabled ? "Master Git Archive is OFF." : null,
      });
      assert.equal((html.match(/role="switch"/g) || []).length, 1);
      assert.match(html, new RegExp(`aria-checked="${participating}"`));
      assert.equal(html.includes('disabled=""'), !global_enabled);
      assert.equal(
        html.includes("archive-connected"),
        global_enabled && participating,
      );
      assert.match(html, /Alpha &lt;science&gt;/);
    });
  }
test("unavailable repository never claims active, retains saved preference and blocks new participation", () => {
  for (const participating of [false, true]) {
    const html = control({
      global_enabled: true,
      participating,
      connection: "unavailable",
      state: "unavailable",
      reason: "Repository missing",
    });
    assert.match(html, /Git unavailable/);
    assert.doesNotMatch(html, /archive-connected/);
    assert.equal(html.includes('disabled=""'), !participating);
  }
  assert.match(control(null, "Cannot load status"), /disabled=""/);
});
test("legacy participation displays retained scope without reinterpreting it", () => {
  const state = {
    global_enabled: true,
    participating: true,
    connection: "connected",
    state: "enabled",
    legacy: true,
  };
  const before = structuredClone(state),
    html = control(state);
  assert.match(html, /Existing legacy scope is retained/);
  assert.deepEqual(state, before);
});
