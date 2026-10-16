// Bundle with esbuild --platform=node --format=esm, then run node --test.
import { test } from "node:test";
import assert from "node:assert/strict";
import {
  groupArguments,
  flattenArguments,
  parseArguments,
  formatCommand,
  argumentError,
} from "./arguments.ts";

test("acceptance paste produces pairs and a flag with no value", () => {
  const args = parseArguments(
    "--particles 50000 --n 192 --steps 1000 --render-every 5 --wvz 'outputs/test-simshelf.wvz' --wvz-every 5 --compression none --headless",
  );
  const rows = groupArguments(args);
  assert.equal(rows.length, 8);
  assert.deepEqual(rows[0], { token: "--particles", value: "50000" });
  assert.deepEqual(rows.at(-1), { token: "--headless", value: null });
  assert.deepEqual(flattenArguments(rows), args);
});
test("lossless display and quoted preview for arbitrary existing argv", () => {
  const corpus = [
    "",
    "--",
    "-",
    "--key=value",
    "--repeat",
    "with spaces",
    "\u03bb雪",
    "a'b",
    '"',
    "\\",
    ";",
    "$(touch sentinel)",
    "*",
    "\n",
    "--flag",
    "-2.3",
  ];
  for (const a of corpus)
    for (const b of corpus) {
      const args = [a, b, "", "--", "--option", "positional"];
      assert.deepEqual(flattenArguments(groupArguments(args)), args);
      assert.deepEqual(parseArguments(formatCommand(args)), args);
    }
  assert.deepEqual(
    groupArguments(["--", "--option", "value"]).map((r) => r.value),
    [null, null, null],
  );
});
test("quotes, escapes, concatenation, empties and literal metacharacters", () => {
  assert.deepEqual(
    parseArguments(
      `--name 'path with spaces' "" '' pre"mid"'post' a\\ b "a\\\"b" '$HOME' '*' ';' '$(hi)'`,
    ),
    [
      "--name",
      "path with spaces",
      "",
      "",
      "premidpost",
      "a b",
      'a"b',
      "$HOME",
      "*",
      ";",
      "$(hi)",
    ],
  );
  assert.deepEqual(parseArguments('"C:\\data" a\\\nb\t#literal | &'), [
    "C:\\data",
    "ab",
    "#literal",
    "|",
    "&",
  ]);
  assert.deepEqual(parseArguments(" \\" + "\n "), []);
});
test("malformed input and size limits fail explicitly", () => {
  for (const text of ["'oops", '"oops', "trailing\\", "\0"])
    assert.throws(() => parseArguments(text));
  assert.throws(() => parseArguments(Array(257).fill("a").join(" ")));
  assert.throws(() => parseArguments("a".repeat(8193)));
  assert.throws(() =>
    parseArguments(Array(9).fill("a".repeat(8192)).join(" ")),
  );
  assert.equal(argumentError(["雪".repeat(8192)]), "");
  assert.equal(argumentError(["😀".repeat(8192)]), "");
});
