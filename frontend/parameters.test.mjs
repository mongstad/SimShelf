import { test } from "node:test";
import assert from "node:assert/strict";
import { appendOverrides, overrideTokens, present } from "./parameters.ts";
const p = {
  name: "--dt",
  flags: ["--dt", "-d"],
  action: "store",
  type: "float",
  choices: null,
  supported: true,
};
test("only explicit overrides contribute argv; manual tokens stay exact", () => {
  const args = ["--unknown", "a b", "--tag=x", "--tag=y", "input.txt"];
  assert.deepEqual(appendOverrides(args, []), args);
  assert.deepEqual(appendOverrides(args, [{ parameter: p, value: "-0.25" }]), [
    ...args,
    "--dt=-0.25",
  ]);
  assert.deepEqual(args, [
    "--unknown",
    "a b",
    "--tag=x",
    "--tag=y",
    "input.txt",
  ]);
  assert.deepEqual(overrideTokens({ ...p, type: "str" }, ""), ["--dt="]);
  assert.deepEqual(overrideTokens({ ...p, type: "str" }, 'a "b"; $HOME'), [
    '--dt=a "b"; $HOME',
  ]);
});
test("existing aliases and equals/attached options never get overwritten", () => {
  for (const args of [["--dt", "2"], ["--dt=2"], ["-d", "2"], ["-d2"]]) {
    assert.equal(present(args, p), true);
    assert.throws(
      () => appendOverrides(args, [{ parameter: p, value: "3" }]),
      /already/,
    );
  }
  assert.throws(
    () => appendOverrides(["--", "x"], [{ parameter: p, value: "3" }]),
    /positional/,
  );
});
test("booleans, types, choices and unsupported constructs", () => {
  for (const action of ["store_true", "store_false"])
    assert.deepEqual(overrideTokens({ ...p, action }, ""), ["--dt"]);
  assert.throws(() => overrideTokens({ ...p, type: "int" }, "1.5"), /integer/);
  assert.throws(() => overrideTokens(p, "Infinity"), /finite/);
  assert.throws(
    () => overrideTokens({ ...p, choices: [1, 2] }, "3"),
    /choices/,
  );
  assert.throws(
    () => overrideTokens({ ...p, supported: false }, "3"),
    /manual/,
  );
});
