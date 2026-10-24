import { test } from "node:test";
import assert from "node:assert/strict";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { overviewWarnings, RunOverviewWarnings } from "./RunOverviewWarnings";
import { CaptureSummary } from "./CaptureSummary";
const healthy = {
  status: "completed",
  capture_status: "complete",
  capture_counts: {
    copied: 3,
    referenced: 1,
    ignored: 2,
    skipped: 0,
    unchanged: 1,
  },
  capture_errors: [],
  artifacts: [],
};
const verified = { state: "verified", connection: "connected" };
test("healthy capture and historical preservation add no routine Overview panel or implied success", () => {
  const before = structuredClone(healthy);
  assert.deepEqual(overviewWarnings(healthy, verified), []);
  assert.deepEqual(
    overviewWarnings(healthy, {
      state: "not_enabled",
      connection: "disconnected",
    }),
    [],
  );
  assert.equal(
    renderToStaticMarkup(
      React.createElement(RunOverviewWarnings, {
        run: healthy,
        preservation: verified,
        openFiles() {},
      }),
    ),
    "",
  );
  assert.deepEqual(healthy, before);
});
test("execution completion cannot hide capture failure, uncertainty, skipped or missing bytes", () => {
  for (const patch of [
    { capture_status: "partial" },
    { capture_status: "incomplete" },
    { capture_status: "unknown" },
    { capture_status: undefined },
    { capture_errors: ["copy failed"] },
    { capture_counts: { skipped: 1 } },
    { artifacts: [{ availability: "missing" }] },
    { artifacts: [{ availability: "another-computer" }] },
    { artifacts: [{ availability: "changed" }] },
  ]) {
    const warnings = overviewWarnings({ ...healthy, ...patch }, verified);
    assert.ok(warnings.length);
    assert.ok(warnings.every((w) => !w.pending));
  }
});
test("running, stopping and post-exit finalization stay pending independently of Git", () => {
  for (const [patch, text] of [
    [{ status: "running" }, "capture is pending"],
    [{ status: "running", stop_requested: true }, "Stopping"],
    [{ status: "completed" }, "Execution ended"],
    [{ status: "interrupted" }, "Execution ended"],
  ]) {
    const warnings = overviewWarnings(
      { ...healthy, capture_status: "pending", ...patch },
      verified,
    );
    assert.equal(warnings.length, 1);
    assert.ok(warnings[0].pending);
    assert.ok(warnings[0].text.includes(text));
  }
});
test("Git warnings use actual preservation and repository states, not process or capture success", () => {
  for (const state of ["partial", "failed", "unavailable", "unknown"]) {
    const w = overviewWarnings(healthy, { state, connection: "connected" });
    assert.equal(w.length, 1);
    assert.equal(w[0].pending, false);
  }
  assert.equal(
    overviewWarnings(healthy, { state: "pending" })[0].pending,
    true,
  );
  for (const connection of ["unavailable", "disconnected", undefined])
    assert.match(
      overviewWarnings(healthy, { state: "verified", connection })[0].text,
      /repository is unavailable/,
    );
  assert.match(
    overviewWarnings(healthy, null)[0].text,
    /status is unavailable/,
  );
  assert.equal(overviewWarnings(healthy, null, true)[0].pending, true);
});
test("actionable notices retain accessible state and a direct Files action without verbose counts", () => {
  const html = renderToStaticMarkup(
    React.createElement(RunOverviewWarnings, {
      run: { ...healthy, capture_status: "partial" },
      preservation: { state: "pending" },
      openFiles() {},
    }),
  );
  assert.match(html, /role="alert"/);
  assert.match(html, /role="status"/);
  assert.equal((html.match(/View details in Files/g) || []).length, 2);
  assert.doesNotMatch(html, /copied|annotation entries|Inspected folder/);
});
test("Files retains recorded path, counts, exclusions, errors and unknown historical counts", () => {
  const run = {
    ...healthy,
    capture_root: "/source/outputs",
    capture_errors: ["specific copy failure"],
  };
  const before = structuredClone(run);
  const html = renderToStaticMarkup(
    React.createElement(CaptureSummary, { run }),
  );
  for (const text of [
    "/source/outputs",
    "3 copied",
    "1 referenced",
    "2 ignored",
    "0 skipped",
    "1 unchanged",
    "specific copy failure",
    "not full output preservation",
    "references need originals",
  ])
    assert.ok(html.includes(text), text);
  assert.deepEqual(run, before);
  assert.match(
    renderToStaticMarkup(
      React.createElement(CaptureSummary, {
        run: { ...run, capture_counts: undefined },
      }),
    ),
    /counts are not available/,
  );
});

test("zero eligible files and declared outside-capture targets remain actionable without claiming failed execution", () => {
  const zero = overviewWarnings(
    {
      ...healthy,
      capture_counts: {
        copied: 0,
        referenced: 0,
        ignored: 0,
        skipped: 0,
        unchanged: 0,
      },
    },
    verified,
  );
  assert.match(zero[0].text, /No eligible files/);
  const outside = overviewWarnings(
    {
      ...healthy,
      launch: { output_review: { targets: [{ covered: false }] } },
    },
    verified,
  );
  assert.match(outside[0].text, /outside capture coverage/);
  assert.ok(!outside.some((w) => w.text.includes("Execution")));
});
