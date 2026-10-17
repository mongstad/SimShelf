import { test } from "node:test";
import assert from "node:assert/strict";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import {
  included,
  FileLabel,
  SelectedRules,
  SelectionStatus,
  sameRules,
  saveSelection,
  GitFiles,
} from "./GitFiles.tsx";
const render = (component, props) =>
  renderToStaticMarkup(React.createElement(component, props));
test("file, folder and extension scope is explicit and includes no defaults", () => {
  assert.equal(included("sim.py", []), false);
  assert.equal(
    included("folder/sim.py", [{ kind: "folder", value: "folder" }]),
    true,
  );
  assert.equal(
    included("folder2/sim.py", [{ kind: "folder", value: "folder" }]),
    false,
  );
  assert.equal(
    included("nested/sim.py", [{ kind: "extension", value: ".py" }]),
    true,
  );
  assert.equal(included(".py", [{ kind: "extension", value: ".py" }]), false);
  assert.equal(
    included("nested/sim.py", [{ kind: "file", value: "sim.py" }]),
    false,
  );
});
test("tracked and ignored are independent of inclusion, and untrusted names escape", () => {
  const file = {
    path: "<input>.npz",
    size: 5000,
    state: "tracked",
    ignored_rule: true,
    risk: "May be scientific input or results",
  };
  const before = structuredClone(file),
    html = render(FileLabel, { file });
  assert.match(html, /Already tracked/);
  assert.match(html, /remains tracked/);
  assert.match(html, /scientific input or results/);
  assert.match(html, /&lt;input&gt;/);
  assert.deepEqual(file, before);
  assert.match(
    render(FileLabel, { file: { ...file, state: "ignored" } }),
    /Ignored by existing Git rules/,
  );
  assert.match(
    render(FileLabel, { file: { ...file, state: "unknown" } }),
    /Git state unknown/,
  );
});
test("optional selected rules enumerate matches and future scope", () => {
  const html = render(SelectedRules, {
    rules: [
      { kind: "extension", value: ".py" },
      { kind: "file", value: "config.json" },
    ],
    files: [{ path: "sim.py" }, { path: "config.json" }],
    remove: () => {},
  });
  assert.match(html, /Selected rules \(2\)/);
  assert.match(html, /sim.py/);
  assert.match(html, /future matching files/);
  assert.match(html, /This path only/);
  assert.doesNotMatch(html, /<details open/);
  assert.match(
    render(SelectionStatus, { count: 2, dirty: true }),
    /2 files selected · Unsaved changes/,
  );
  assert.match(
    render(SelectionStatus, { count: 1, dirty: false }),
    /No unsaved changes/,
  );
  assert.doesNotMatch(
    render(GitFiles, { simulationId: "sample" }),
    /Preview inclusion/,
  );
});
test("saved-state comparison ignores rule order but detects changed intent", () => {
  const rules = [
    { kind: "file", value: "sim.py" },
    { kind: "extension", value: ".py" },
  ];
  assert.equal(sameRules(rules, [...rules].reverse()), true);
  assert.equal(sameRules(rules, [rules[0]]), false);
  assert.equal(sameRules([], [{ kind: "folder", value: "output" }]), false);
});
test("direct save validates displayed revision first and submits exact returned payload", async () => {
  const rules = [
    { kind: "file", value: "sim.py" },
    { kind: "folder", value: "output" },
    { kind: "extension", value: ".json" },
  ];
  const review = {
    revision: "displayed",
    rules,
    selected: ["sim.py", "output/result.csv", "config.json"],
    matches: [],
  };
  const calls = [];
  await saveSelection(
    "/simulations/test/git",
    "displayed",
    rules,
    async (path, opts) => {
      calls.push([path, JSON.parse(opts.body)]);
      return review;
    },
  );
  assert.deepEqual(calls, [
    ["/simulations/test/git/files/preview", { revision: "displayed", rules }],
    ["/simulations/test/git/files/save", { review, confirmed: true }],
  ]);
});
test("stale or invalid preview aborts before saving; save-stage races propagate", async () => {
  const calls = [];
  await assert.rejects(
    saveSelection("/git", "stale", [], async (path) => {
      calls.push(path);
      throw new Error("Refresh and review again");
    }),
    /Refresh/,
  );
  assert.deepEqual(calls, ["/git/files/preview"]);
  await assert.rejects(
    saveSelection("/git", "valid", [], async (path) => {
      if (path.endsWith("/save")) throw new Error("Preferences changed");
      return { revision: "valid", rules: [], matches: [], selected: [] };
    }),
    /Preferences changed/,
  );
});
