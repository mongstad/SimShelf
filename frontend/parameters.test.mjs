import { test } from "node:test";
import assert from "node:assert/strict";
import {
  parameterRows,
  rowArguments,
  parameterError,
} from "./parameterRows.ts";
const p = {
  name: "--dt",
  flags: ["--dt", "-d"],
  action: "store",
  type: "float",
  choices: null,
  supported: true,
  required: false,
  default_known: true,
  default: 0.1,
};
const flag = {
  ...p,
  name: "--quiet",
  flags: ["--quiet"],
  action: "store_true",
};
test("discovered rows start disabled; defaults never become argv", () => {
  const rows = parameterRows([], [p, flag]);
  assert.equal(rows.length, 2);
  assert.ok(rows.every((r) => !r.enabled && r.value === null));
  assert.deepEqual(rowArguments(rows), []);
  assert.equal(parameterError(rows, [p, flag]), "");
  rows[0].enabled = true;
  assert.match(parameterError(rows, [p, flag]), /needs a value/);
  rows[0].value = "-.25";
  assert.deepEqual(rowArguments(rows), ["--dt=-.25"]);
  rows[1].enabled = true;
  assert.deepEqual(rowArguments(rows), ["--dt=-.25", "--quiet"]);
  rows[0].enabled = false;
  assert.deepEqual(rowArguments(rows), ["--quiet"]);
});
test("saved equals and separate values display separately without changing tokens or alias", () => {
  for (const args of [
    ["--dt", "-0.25"],
    ["--dt=-0.25"],
    ["-d", "-0.25"],
    ["--dt="],
  ]) {
    const rows = parameterRows(args, [p]);
    assert.equal(rows.length, 1);
    assert.ok(!rows[0].token.includes("="));
    assert.deepEqual(rowArguments(rows), args);
  }
  const rows = parameterRows(["--quiet", "input file"], [flag]);
  assert.equal(rows[0].value, null);
  assert.equal(rows[1].token, "input file");
  assert.deepEqual(rowArguments(rows), ["--quiet", "input file"]);
});
test("unknown/repeated/positional and attached/abbreviated forms remain exact manual fallbacks", () => {
  for (const args of [
    ["--unknown", "a b", "--tag=x", "--tag=y", "input.txt"],
    ["-d.25"],
    ["--d=.25"],
    ["--dt=1", "--dt", "2"],
    ["--", "--dt=1", "input.txt"],
  ]) {
    const rows = parameterRows(args, [p]);
    assert.deepEqual(rowArguments(rows), args);
    if (args[0] !== "--")
      assert.equal(
        rows.filter((r) => !r.enabled && r.parameter?.name === "--dt").length,
        args[0] === "--unknown" ? 1 : 0,
      );
  }
  assert.match(
    parameterError(parameterRows(["--dt=1", "--dt", "2"], [p]), [p]),
    /more than once/,
  );
});
test("rescan preserves disabled edited values and marks removed declarations manual", () => {
  let rows = parameterRows([], [p]);
  rows[0].value = "42";
  rows = parameterRows(rowArguments(rows), [{ ...p, default: 0.2 }], rows);
  assert.equal(rows[0].value, "42");
  assert.equal(rows[0].enabled, false);
  assert.deepEqual(rowArguments(rows), []);
  rows = parameterRows(rowArguments(rows), [], rows);
  assert.equal(rows[0].value, "42");
  assert.match(rows[0].manual, /removed/);
});
test("required values, boolean values, types and choices are validated without guessing positionals", () => {
  const required = { ...p, required: true };
  assert.match(
    parameterError(parameterRows([], [required]), [required]),
    /required/,
  );
  assert.match(
    parameterError(parameterRows(["--dt"], [required]), [required]),
    /needs a value/,
  );
  assert.match(
    parameterError(parameterRows(["--dt=Infinity"], [p]), [p]),
    /finite/,
  );
  assert.match(
    parameterError(parameterRows(["--quiet=yes"], [flag]), [flag]),
    /does not accept/,
  );
  assert.match(
    parameterError(parameterRows(["--dt=3"], [{ ...p, choices: [1, 2] }]), [
      { ...p, choices: [1, 2] },
    ]),
    /choices/,
  );
  assert.match(
    parameterError(parameterRows(["--dt=1.5"], [{ ...p, type: "int" }]), [
      { ...p, type: "int" },
    ]),
    /integer/,
  );
  const string = { ...p, type: "str" };
  assert.equal(
    parameterError(parameterRows(["--dt="], [string]), [string]),
    "",
  );
});
test("disabled options before separator enable as options without moving existing tokens", () => {
  const rows = parameterRows(["--", "file"], [p]);
  rows[0].enabled = true;
  rows[0].value = "-.5";
  assert.deepEqual(rowArguments(rows), ["--dt=-.5", "--", "file"]);
});

test("removed and restored declarations recover one disabled row without losing its draft", () => {
  let rows = parameterRows([], [p]);
  rows[0].value = "42";
  rows = parameterRows(rowArguments(rows), [], rows);
  rows = parameterRows(rowArguments(rows), [p], rows);
  assert.equal(rows.length, 1);
  assert.equal(rows[0].value, "42");
  assert.equal(rows[0].enabled, false);
  assert.deepEqual(rowArguments(rows), []);
});
test("ambiguous clusters stay manual and numeric choices compare converted values", () => {
  const rows = parameterRows(["-xd.25"], [p]);
  assert.equal(rows.length, 1);
  assert.deepEqual(rowArguments(rows), ["-xd.25"]);
  assert.match(
    parameterError(parameterRows(["--dt=0x10"], [p]), [p]),
    /finite/,
  );
  const choice = { ...p, choices: [1] };
  assert.equal(
    parameterError(parameterRows(["--dt=1.0"], [choice]), [choice]),
    "",
  );
  assert.deepEqual(rowArguments(parameterRows(["--dt", "-.25"], [p])), [
    "--dt",
    "-.25",
  ]);
});

test("disabled edits survive a declaration becoming unsupported", () => {
  let rows = parameterRows([], [p]);
  rows[0].value = "42";
  rows = parameterRows(
    [],
    [{ ...p, supported: false, reason: "Custom action" }],
    rows,
  );
  assert.equal(rows.length, 1);
  assert.equal(rows[0].value, "42");
  assert.equal(rows[0].enabled, false);
  assert.match(rows[0].manual, /changed/);
  assert.deepEqual(rowArguments(rows), []);
  rows = parameterRows([], [p], rows);
  assert.equal(rows.length, 1);
  assert.equal(rows[0].value, "42");
});

test("repeated boolean flags and identical scalar values remain valid manual rows", () => {
  const args = ["--quiet", "--quiet", "--dt=1", "--dt", "1.0"];
  const rows = parameterRows(args, [p, flag]);
  assert.deepEqual(rowArguments(rows), args);
  assert.equal(parameterError(rows, [p, flag]), "");
  assert.ok(rows.every((r) => r.manual));
});
