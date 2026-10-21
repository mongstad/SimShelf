import { test } from "node:test";
import assert from "node:assert/strict";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import {
  PreservationReview,
  PreservationSettings,
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
  assert.match(html, /Saved Git policy: loading/);
  assert.match(html, /Reference only/);
  assert.match(html, /simulation creates its own unique subdirectories/);
});
