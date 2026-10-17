import { test } from "node:test";
import assert from "node:assert/strict";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import {
  FutureOutputHelp,
  RunFilesTable,
  runFileRows,
  MasterArchiveStatus,
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

const artifact = {
  id: "a",
  name: "result.csv",
  blob: "hash1",
  size: 3,
  policy: "copy",
  availability: "available",
};
const entry = {
  name: "result.csv",
  blob: "hash1",
  size: 3,
  category: "result",
  artifact_id: "a",
  path: "event/file",
};
const event = {
  id: "initial",
  kind: "initial",
  commit: "abcdef123456",
  repository: { identity: "repo" },
  files: [entry],
  skipped: [],
};
const run = { id: "run-a", status: "completed", artifacts: [artifact] };
const connection = { state: "connected", identity: "repo" };
test("one artifact row joins only exact identity and content without mutation", () => {
  const before = structuredClone({ run, event });
  const rows = runFileRows(run, [event]);
  assert.equal(rows.length, 1);
  assert.equal(rows[0].archived.event.id, "initial");
  assert.deepEqual({ run, event }, before);
  for (const change of [
    { blob: "other" },
    { size: 4 },
    { artifact_id: "other" },
    { artifact_id: null },
    { blob: null },
  ])
    assert.equal(
      runFileRows(run, [{ ...event, files: [{ ...entry, ...change }] }]).length,
      2,
    );
});
test("same-name events retain exact historical downloads, including removed attachments", () => {
  const later = {
    ...event,
    id: "later",
    commit: "123456abcdef",
    files: [{ ...entry, blob: "hash2", artifact_id: "b" }],
  };
  const html = render(RunFilesTable, {
    run,
    events: [event, later],
    connection,
  });
  assert.ok(html.includes("/artifacts/a/file?download=true"));
  assert.ok(html.includes("/runs/run-a/archive/initial/0/file"));
  assert.ok(html.includes("/runs/run-a/archive/later/0/file"));
  assert.equal(runFileRows(run, [event, later]).length, 2);
  assert.equal(
    runFileRows({ ...run, artifacts: [] }, [event, later]).length,
    2,
  );
  // Even an identical repeated archival event remains individually addressable.
  assert.equal(runFileRows(run, [event, { ...event, id: "again" }]).length, 2);
});
test("disconnected or wrong archive never removes workspace download or serves wrong Git revision", () => {
  for (const c of [
    null,
    { state: "disconnected" },
    { state: "unavailable" },
    { state: "connected", identity: "other" },
  ]) {
    const html = render(RunFilesTable, { run, events: [event], connection: c });
    assert.match(html, /Download workspace copy/);
    assert.doesNotMatch(html, /href="[^" ]*archive/);
    assert.match(html, /Archived in Git/);
  }
  const html = render(RunFilesTable, {
    run: { ...run, artifacts: [{ ...artifact, availability: "missing" }] },
    events: [event],
    connection,
  });
  assert.match(html, /Download Git revision/);
  assert.doesNotMatch(html, /Download workspace copy/);
});
test("references, skipped files, filtering and source-only entries remain visible", () => {
  const r = {
    ...run,
    artifacts: [
      {
        ...artifact,
        id: "ref",
        policy: "reference",
        original_path: "/original/result.csv",
      },
      {
        ...artifact,
        id: "skip",
        name: "large.bin",
        policy: "skipped",
        availability: "not-captured",
        reason: "Too large",
      },
    ],
  };
  let html = render(RunFilesTable, { run: r, events: [], filter: "reference" });
  assert.match(html, /Reference only/);
  assert.match(html, /original/);
  assert.doesNotMatch(html, /href=/);
  assert.doesNotMatch(html, /large.bin/);
  html = render(RunFilesTable, { run: r, events: [], filter: "skipped" });
  assert.match(html, /Too large/);
  const source = {
    ...event,
    files: [
      { ...entry, artifact_id: null, category: "source", name: "sim.py" },
    ],
  };
  assert.match(
    render(RunFilesTable, {
      run: r,
      events: [source],
      filter: "archive",
      connection,
    }),
    /sim.py/,
  );
  assert.match(
    render(RunFilesTable, { run: r, events: [source], search: "NO MATCH" }),
    /No files match/,
  );
});
test("selection is limited to unarchived manual copies on finalized runs", () => {
  assert.match(
    render(RunFilesTable, { run, events: [] }),
    /Select for archive/,
  );
  for (const r of [
    { ...run, status: "running" },
    { ...run, artifacts: [{ ...artifact, automatic: true }] },
  ])
    assert.doesNotMatch(
      render(RunFilesTable, { run: r, events: [] }),
      /Select for archive/,
    );
  assert.doesNotMatch(
    render(RunFilesTable, { run, events: [event] }),
    /Select for archive/,
  );
  assert.match(
    render(RunFilesTable, { run, events: [], disabled: true }),
    /type="checkbox" disabled/,
  );
});
test("connection success is explicit, green-classed and never inferred during loading/errors", () => {
  assert.match(
    render(MasterArchiveStatus, { status: connection }),
    /archive-connected/,
  );
  assert.match(
    render(MasterArchiveStatus, { status: connection }),
    /Master simulation archive connected/,
  );
  assert.match(
    render(MasterArchiveStatus, { status: { state: "disconnected" } }),
    /Local archive disconnected/,
  );
  for (const status of [null, { state: "unavailable", reason: "missing" }])
    assert.doesNotMatch(
      render(MasterArchiveStatus, { status }),
      /archive-connected/,
    );
});

test("archived source identifies its exact matching workspace snapshot", () => {
  const source = {
    ...event,
    files: [
      { ...entry, artifact_id: null, category: "source", name: "sim.py" },
    ],
  };
  const r = {
    ...run,
    artifacts: [],
    snapshot: { files: [{ path: "sim.py", blob: "hash1", size: 3 }] },
  };
  const html = render(RunFilesTable, {
    run: r,
    events: [source],
    connection: null,
    openSource: () => {},
  });
  assert.match(html, /Matching workspace source snapshot/);
  assert.match(html, /View in Source/);
  assert.doesNotMatch(html, /No downloadable copy available/);
  assert.doesNotMatch(
    render(RunFilesTable, {
      run: {
        ...r,
        snapshot: { files: [{ path: "sim.py", blob: "other", size: 3 }] },
      },
      events: [source],
      connection: null,
    }),
    /Matching workspace source snapshot/,
  );
});

test("automatic archival has one accessible authoritative switch", async () => {
  const { AutomaticArchiveToggle, ArchiveSettings } =
    await import("./GitArchive.tsx");
  for (const state of ["enabled", "disabled", "review_required"]) {
    const html = render(AutomaticArchiveToggle, {
      name: "Alpha",
      automatic: { state },
      busy: false,
      available: true,
      onChange: () => {},
    });
    assert.equal((html.match(/role="switch"/g) || []).length, 1);
    assert.match(html, new RegExp(`aria-checked="${state === "enabled"}"`));
    assert.match(html, /Automatic archival for Alpha/);
    assert.match(html, /role="status"/);
    assert.doesNotMatch(
      html,
      /Disable for future runs|Enable automatic archive for this simulation/,
    );
  }
  const props = {
    name: "Alpha",
    automatic: { state: "disabled" },
    busy: false,
    available: false,
    onChange: () => {},
  };
  assert.match(render(AutomaticArchiveToggle, props), /disabled/);
  assert.match(
    render(AutomaticArchiveToggle, {
      ...props,
      automatic: { state: "enabled" },
    }),
    /aria-checked="true"/,
  );
  assert.doesNotMatch(
    render(AutomaticArchiveToggle, {
      ...props,
      automatic: { state: "enabled" },
    }),
    / disabled=/,
  );
  assert.match(
    render(AutomaticArchiveToggle, { ...props, available: true, busy: true }),
    / disabled=/,
  );
  const html = render(ArchiveSettings, {
    simulation: { id: "a", name: "Alpha", config: { output_dir: "outputs" } },
  });
  assert.doesNotMatch(
    html,
    /Automatic archive consent|Confirm archival settings|Disable for future runs|Enable automatic archive for this simulation/,
  );
  assert.match(html, /<details><summary>Automatic archival settings/);
});
