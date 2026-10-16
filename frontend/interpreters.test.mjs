import { test } from "node:test";
import assert from "node:assert/strict";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { DependencyResults, InterpreterPicker } from "./InterpreterPicker.tsx";
const render = (component, props) =>
  renderToStaticMarkup(React.createElement(component, props));
test("undeclared dependencies never produce a compatibility claim", () => {
  const html = render(DependencyResults, {
    result: {
      python: { version: "3.14", prefix: "/science env" },
      files: [],
      requirements: [],
      warnings: [],
      undeclared: true,
      message: "Metadata only; no GPU/CUDA check",
    },
  });
  assert.match(html, /Dependencies are undeclared/);
  assert.match(html, /no package compatibility conclusion/);
  assert.match(html, /no GPU\/CUDA check/);
});
test("missing, incompatible and unknown declarations remain distinguishable", () => {
  const html = render(DependencyResults, {
    result: {
      python: { version: "3.14", prefix: "/env" },
      files: ["requirements.txt"],
      requirements: [
        {
          requirement: "numpy>=99",
          source: "requirements.txt",
          installed: "2.0",
          status: "incompatible",
        },
        {
          requirement: "cupy",
          source: "requirements.txt",
          installed: null,
          status: "missing",
        },
        {
          requirement: "-r other.txt",
          source: "requirements.txt",
          installed: null,
          status: "unknown",
        },
      ],
      warnings: ["Hooks not evaluated"],
      undeclared: false,
      message: "Advisory",
    },
  });
  for (const text of [
    "incompatible",
    "missing",
    "unknown",
    "Hooks not evaluated",
  ])
    assert.match(html, new RegExp(text));
});
test("custom saved path stays visible and checks disclose executable boundary", () => {
  const html = render(InterpreterPicker, {
    simulationId: "fixture",
    value: "/custom env/bin/python",
    change: () => {
      throw Error("must not change selection");
    },
  });
  assert.match(html, /\/custom env\/bin\/python/);
  assert.match(html, /Enter custom path/);
  assert.match(html, /Discovery does not run executables/);
  assert.match(html, /Only select interpreters you trust/);
});
