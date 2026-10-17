import { test } from "node:test";
import assert from "node:assert/strict";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { included, FileLabel, SelectionReview, GitFiles } from "./GitFiles.tsx";
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
test("preview enumerates exact matches and preserves explicit future-review semantics", () => {
  const review = {
    selected: ["sim.py"],
    matches: [{ rule: { kind: "extension", value: ".py" }, paths: ["sim.py"] }],
  };
  const html = render(SelectionReview, { review });
  assert.match(html, /sim.py/);
  assert.match(html, /1 current files/);
  assert.match(html, /does not stage or commit/);
  assert.match(html, /reviewed again/);
  assert.match(
    render(GitFiles, { simulationId: "sample" }),
    /aria-expanded="false"/,
  );
  assert.doesNotMatch(
    render(GitFiles, { simulationId: "sample" }),
    /Save inclusion preferences/,
  );
});
