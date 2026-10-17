import { test } from "node:test";
import assert from "node:assert/strict";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import {
  FutureOutputHelp,
  ArchiveInventory,
  RunArchive,
  archiveLimits,
} from "./GitArchive.tsx";
const render = (component, props) =>
  renderToStaticMarkup(React.createElement(component, props));
test("future rules explain capture-relative paths and manual outside attachments", () => {
  const html = render(FutureOutputHelp, { directory: "outputs" });
  for (const phrase of [
    "capture directory",
    "outputs",
    "not the Python source folder",
    "manual post-run attachment",
    "logs/*.csv",
  ])
    assert.ok(html.includes(phrase));
});
test("history keeps separate same-name entries and exact event download addresses", () => {
  const files = [
    { name: "result.csv", path: "a", size: 3, category: "result" },
  ];
  const html = render(ArchiveInventory, {
    runId: "run-a",
    events: [
      {
        id: "initial",
        kind: "initial",
        commit: "abcdef123456",
        files,
        skipped: [],
      },
      {
        id: "added",
        kind: "addition",
        commit: "123456abcdef",
        files: [{ ...files[0], path: "b" }],
        skipped: [{ name: "missing.csv", reason: "Missing after execution" }],
      },
    ],
  });
  assert.ok(html.includes("/runs/run-a/archive/initial/0/file"));
  assert.ok(html.includes("/runs/run-a/archive/added/0/file"));
  assert.equal((html.match(/Download result.csv/g) || []).length, 2);
  assert.ok(html.includes("Post-run additions"));
  assert.ok(html.includes("Missing after execution"));
});
test("running runs cannot add attachments; finalized states retain explicit review", () => {
  for (const status of ["completed", "failed", "interrupted"]) {
    const html = render(RunArchive, {
      run: { id: "x", status, artifacts: [] },
      reload: () => {},
    });
    assert.ok(html.includes("Review archive additions"));
    assert.ok(html.includes("Attaching alone does not commit"));
  }
  assert.ok(
    !render(RunArchive, {
      run: { id: "x", status: "running" },
      reload: () => {},
    }).includes("Attach files"),
  );
  assert.ok(archiveLimits.includes("including later additions"));
});
