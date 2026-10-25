import { test } from "node:test";
import assert from "node:assert/strict";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { CaptureSummary } from "./CaptureSummary.tsx";
import { CapturePath, OutputPaths } from "./OutputPaths.tsx";
const render = (Component, props) =>
  renderToStaticMarkup(React.createElement(Component, props));
test("complete inspection with zero files never implies preservation", () => {
  const html = render(CaptureSummary, {
    run: {
      capture_status: "complete",
      capture_root: "/source/outputs",
      capture_counts: {
        copied: 0,
        referenced: 0,
        ignored: 0,
        skipped: 0,
        unchanged: 0,
      },
    },
  });
  assert.match(html, /No eligible files observed/);
  assert.match(html, /not full output preservation/);
  assert.match(html, /Only copies enter library backups/);
});
test("partial and historical runs distinguish counts from missing evidence", () => {
  const partial = render(CaptureSummary, {
    run: {
      capture_status: "partial",
      capture_counts: {
        copied: 3,
        referenced: 1,
        ignored: 1,
        skipped: 1,
        unchanged: 2,
      },
    },
  });
  assert.match(
    partial,
    /3 copied · 1 referenced · 1 ignored · 1 skipped · 2 unchanged/,
  );
  const old = render(CaptureSummary, { run: { capture_status: "complete" } });
  assert.match(old, /counts are not available/);
  assert.doesNotMatch(old, /No eligible files observed/);
});
test("unknown destinations and stale mappings receive explicit guidance", () => {
  const props = {
    args: ["changed.csv"],
    mappings: [],
    review: null,
    error: "",
    change: () => {},
    apply: () => {},
  };
  assert.match(render(OutputPaths, props), /output coverage unknown/);
  const mapped = render(OutputPaths, {
    ...props,
    mappings: [
      { argument_index: 0, value: "old.csv", kind: "file", format: "token" },
    ],
  });
  assert.match(mapped, /This argument changed/);
  assert.match(mapped, /Confirm current token/);
});

import { outputCandidates } from "./outputCandidates.ts";
test("candidate hints retain exact indices and do not inspect post-separator options", () => {
  const args = [
    "--wvz",
    "a b.wvz",
    "--output=x",
    "--custom",
    "elsewhere",
    "--output-dir",
    "results",
    "--",
    "--wvz",
    "positional",
  ];
  assert.deepEqual(outputCandidates(args), [
    { index: 1, flag: "--wvz", format: "token" },
    { index: 2, flag: "--output", format: "equals" },
    { index: 6, flag: "--output-dir", format: "token" },
  ]);
  assert.deepEqual(outputCandidates(["--wvz", "--headless"]), []);
  assert.deepEqual(
    outputCandidates(["--wvz", "a", "--wvz", "b"]).map((c) => c.index),
    [1, 3],
  );
});

test("per-run preview and history distinguish allocation from actual capture", () => {
  const preview = render(CapturePath, {
    error: "",
    review: { output_path: "/source/results", output_policy: "per_run", targets: [], requires_acknowledgement: false },
  });
  assert.match(preview, /Capture parent/);
  assert.match(preview, /allocated at/);
  assert.match(preview, /arguments are unchanged/);
  const history = render(CaptureSummary, { run: {
    output_policy: "per_run", output_base: "/source/results", capture_root: "/source/results/run_abc",
    capture_status: "complete", capture_counts: {copied: 0},
  }});
  assert.match(history, /\/source\/results\/run_abc/);
  assert.match(history, /Writes elsewhere are not inventoried/);
  assert.match(history, /No eligible files observed/);
});

import { incompleteOutputMappings } from "./outputCandidates.ts";
test("new fixed rows are explicit drafts; completing or removing restores eligibility", () => {
  const draft = { argument_index: null, value: "", kind: "file", format: "token" };
  assert.deepEqual(incompleteOutputMappings([draft]), [0]);
  assert.deepEqual(incompleteOutputMappings([{...draft,value:"outputs/new.csv"}]), []);
  assert.deepEqual(incompleteOutputMappings([]), []);
  // Mapped empty/stale arguments still go through authoritative backend checks.
  assert.deepEqual(incompleteOutputMappings([{...draft,argument_index:0}]), []);
  const html = render(OutputPaths, {
    args: [], mappings: [draft], change: () => {}, apply: () => {}, error: "",
    review: null,
  });
  assert.match(html, /Output 1 is incomplete/);
  assert.match(html, /remove this mapping to continue/);
  assert.match(html, /placeholder="Example: outputs\/data.csv"/);
  assert.match(html, /value=""/);
  assert.doesNotMatch(html, /Path review unavailable|role="alert"/);
});

test("capture preview distinguishes resolved, pending and failed paths", () => {
  const props = {review: { output_path: "/source/new-output", output_policy:"per_run", targets:[], requires_acknowledgement:false }, error: ""};
  const html = render(CapturePath,props);
  assert.match(html,/Capture parent/);
  assert.match(html,/\/source\/new-output/);
  const pending = render(CapturePath,{review:null,error:""});
  assert.match(pending,/Checking capture path/);
  assert.doesNotMatch(pending,/\/source\/new-output/);
  const unavailable = render(CapturePath,{review:null,error:"Working directory does not exist"});
  assert.match(unavailable,/Capture path unavailable/);
  assert.match(unavailable,/Working directory does not exist/);
  assert.doesNotMatch(unavailable,/\/source\/new-output/);
});
